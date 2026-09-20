"""Renders original.ogg into every cue folder, from your own copy of the game, so you can hear what
a cue sounds like before replacing it.

Needs, both on PATH:
  cp77tools   WolvenKit's command line tool:  dotnet tool install -g WolvenKit.CLI
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


def tool(name):
    found = shutil.which(name)
    if not found:
        sys.exit(f'{name} is not on your PATH - see the notes at the top of this script.')
    return found


def run(*args):
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode:
        sys.exit(f'{args[0]} failed:\n{result.stdout[-800:]}{result.stderr[-800:]}')
    return result.stdout


def main():
    root = os.path.dirname(os.path.abspath(__file__))
    mod = os.path.dirname(root)          # this package sits inside the mod's cue tree
    game = None
    if '--game' in sys.argv:
        game = sys.argv[sys.argv.index('--game') + 1]
    if not game or not os.path.isdir(os.path.join(game, 'archive', 'pc', 'content')):
        sys.exit('Pass your game folder, e.g.  python make_previews.py --game "D:\\Games\\Cyberpunk2077"')

    cp77tools, ffmpeg = tool('cp77tools'), tool('ffmpeg')
    content = os.path.join(game, 'archive', 'pc', 'content')
    cues = json.load(open(os.path.join(mod, CUES), encoding='utf-8'))
    work = tempfile.mkdtemp(prefix='sts_previews_')
    print(f'working in {work}')

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
    run(cp77tools, 'export', media, '-o', media, '-v', 'Minimal')
    have = {int(f[:-4]) for f in os.listdir(media) if f.endswith('.ogg')}

    print('4/4  rendering a preview per cue')
    folders = {}
    for quest in os.listdir(mod):
        qdir = os.path.join(mod, quest)
        if not os.path.isdir(qdir): continue
        for folder in os.listdir(qdir):
            token = folder.split(' ')[0]
            cue = token if token in cues else token + '_START'
            if cue in cues: folders[cue] = os.path.join(qdir, folder)

    jobs = []
    for cue, segs in per_cue.items():
        out = os.path.join(folders.get(cue, ''), 'original.ogg') if cue in folders else None
        if not out or os.path.exists(out): continue
        inputs, graph = filter_graph(segs, have)
        if inputs: jobs.append((cue, inputs, graph, out))
    with ThreadPoolExecutor(os.cpu_count() or 4) as pool:
        for (cue, *_), err in zip(jobs, pool.map(lambda j: render(ffmpeg, media, *j[1:]), jobs)):
            if err: print('  failed:', cue, err)
    print(f'done - {len(jobs)} preview(s) written. Delete any original.ogg to reclaim the space.')
    shutil.rmtree(work, ignore_errors=True)


if __name__ == '__main__':
    main()
