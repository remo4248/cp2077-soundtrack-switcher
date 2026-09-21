"""Renders original.ogg into every cue folder, from your own copy of the game, so you can hear what
a cue sounds like before replacing it.

Needs, both on PATH:
  WolvenKit's CLI, either name: cp77tools (dotnet tool install -g WolvenKit.CLI, needs the .NET
              SDK) or WolvenKit.CLI (the WolvenKit.Console zip from WolvenKit's releases, needs
              only the .NET runtime)
  ffmpeg      https://ffmpeg.org/download.html

Usage (from the folder this sits in):
  python make_previews.py --game "D:\\Games\\Cyberpunk2077"

Nothing is downloaded and nothing is shared: the audio is read out of your own installed game.
"""
import json, os, re, shutil, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bnk import parse, segments
from previews import filter_graph, render

CUES = 'cues.json'
BANK = r'base\sound\soundbanks\cp_music.bnk'


def wwise_id(name):
    """The engine's id for an event name: FNV-1, 32 bit, over the lowercased name."""
    h = 2166136261
    for c in name.lower().encode():
        h = ((h * 16777619) & 0xFFFFFFFF) ^ c
    return h


def find_mod(start):
    """The mod root is whichever folder above us holds cues.json - so this package works unpacked
    next to rescan.bat, in a previews sub-folder, or anywhere else inside the mod."""
    d = start
    while True:
        if os.path.exists(os.path.join(d, CUES)):
            return d
        up = os.path.dirname(d)
        if up == d:
            sys.exit('Put this package inside the SoundtrackSwitcher folder - the one holding '
                     'cues.json and rescan.bat - and run it again.')
        d = up


def exported_ids(media_dir):
    """The media ids WolvenKit managed to convert. It writes .Ogg with a capital O, which is why
    this compares lowercased - matching case-sensitively found nothing and reported success."""
    return {int(os.path.splitext(f)[0]) for f in os.listdir(media_dir)
            if os.path.splitext(f)[1].lower() == '.ogg'}


def tool(*names):
    """WolvenKit's CLI is called cp77tools when installed as a dotnet tool and WolvenKit.CLI in the
    WolvenKit.Console download, so both are accepted."""
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    sys.exit(f'{" or ".join(names)} is not on your PATH - see the notes at the top of this script.')


def run(*args):
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode:
        raise SystemExit(f'{args[0]} failed:\n{result.stdout[-800:]}{result.stderr[-800:]}')
    return result.stdout


def main():
    root = os.path.dirname(os.path.abspath(__file__))
    mod = find_mod(root)
    game = None
    if '--game' in sys.argv:
        game = sys.argv[sys.argv.index('--game') + 1]
    if not game or not os.path.isdir(os.path.join(game, 'archive', 'pc', 'content')):
        sys.exit('Pass your game folder, e.g.  python make_previews.py --game "D:\\Games\\Cyberpunk2077"')

    cp77tools, ffmpeg = tool('cp77tools', 'WolvenKit.CLI'), tool('ffmpeg')
    content = os.path.join(game, 'archive', 'pc', 'content')
    cues = json.load(open(os.path.join(mod, CUES), encoding='utf-8'))
    work = tempfile.mkdtemp(prefix='sts_previews_')
    print(f'working in {work} - it needs a few GB and is removed when this finishes')
    try:
        render_all(cp77tools, ffmpeg, game, content, mod, cues, work)
    finally:
        shutil.rmtree(work, ignore_errors=True)   # several GB, gone even if a step failed


def render_all(cp77tools, ffmpeg, game, content, mod, cues, work):

    print('1/4  reading the music soundbank')
    run(cp77tools, 'unbundle', os.path.join(content, 'audio_2_soundbanks.archive'), '-o', work,
        '-r', re.escape(BANK).replace('\\\\', '.'), '-v', 'Minimal')
    objs = parse(os.path.join(work, BANK))

    print('2/4  working out which pieces of audio each cue uses')
    wanted, per_cue = set(), {}
    for cue in cues:
        segs = segments(objs, wwise_id(cue))
        per_cue[cue] = segs
        wanted.update(m for _, _, media in segs for m in media)
    print(f'     {len(wanted)} audio files for {len(cues)} cues')

    print('3/4  extracting and converting them (this is the slow part)')
    ids = '|'.join(str(i) for i in sorted(wanted))
    run(cp77tools, 'unbundle', os.path.join(content, 'audio_2_soundbanks.archive'), '-o', work,
        '-r', f'media.({ids})[.]wem$', '-v', 'Minimal')
    media = os.path.join(work, r'base\sound\soundbanks\media')
    # WolvenKit 9 refuses to export without a game path, even when only .wem files are involved.
    run(cp77tools, 'export', media, '-o', media, '--gamepath', game, '-v', 'Minimal')
    have = exported_ids(media)
    if not have:
        raise SystemExit('WolvenKit exported no audio - nothing to build previews from.')

    print('4/4  rendering a preview per cue')
    # Folder names drop the _START most cues carry, and 14 cues end in a lowercase _start, so the
    # match is made without case and the cue keeps the spelling cues.json gives it.
    by_name = {c.lower(): c for c in cues}
    folders = {}
    for quest in os.listdir(mod):
        qdir = os.path.join(mod, quest)
        if not os.path.isdir(qdir): continue
        for folder in os.listdir(qdir):
            token = folder.split(' ')[0].lower()
            cue = by_name.get(token) or by_name.get(token + '_start')
            if cue: folders[cue] = os.path.join(qdir, folder)

    jobs = []
    for cue, segs in per_cue.items():
        out = os.path.join(folders.get(cue, ''), 'original.ogg') if cue in folders else None
        if not out or os.path.exists(out): continue
        inputs, graph = filter_graph(segs, have)
        if inputs: jobs.append((cue, inputs, graph, out))
    failed = 0
    with ThreadPoolExecutor(os.cpu_count() or 4) as pool:
        for (cue, *_), err in zip(jobs, pool.map(lambda j: render(ffmpeg, media, *j[1:]), jobs)):
            if err:
                failed += 1
                print('  failed:', cue, err)
    if failed:
        print(f'{failed} cue(s) could not be rendered - the game audio for them did not convert.')
    if not jobs:
        raise SystemExit('No previews were built. Every cue folder either has an original.ogg '
                         'already, or none of its audio came out of the game files.')
    print(f'done - {len(jobs) - failed} preview(s) written. Delete any original.ogg to reclaim the space.')


if __name__ == '__main__':
    main()
