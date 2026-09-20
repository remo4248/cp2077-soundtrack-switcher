"""Writes original.ogg into every cue folder: the cue's segments back to back, layered tracks mixed.
For the author's own copy only; package.py leaves these files out of the release zip.

Usage: python previews.py <DATA> <mod root> <folder of converted .ogg media> <ffmpeg.exe>
The .ogg media come from the game's base\\sound\\soundbanks\\media\\<id>.wem (audio_2_soundbanks.archive)
converted with WolvenKit's wwise_export.
"""
import json, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from bnk import parse, segments


def filter_graph(segs, have):
    """ffmpeg inputs + filter_complex for one cue. segs = [(id, ms, [media])]; have = media ids with an .ogg."""
    inputs, parts, n_seg = [], [], 0
    for _, ms, media in segs:
        media = [m for m in media if m in have]
        if not media: continue
        labels = ''
        for m in media:  # same format on every input, or amix fails on mono + stereo layers
            k = len(inputs)
            parts.append(f'[{k}:a]aformat=sample_rates=48000:channel_layouts=stereo[i{k}]')
            labels += f'[i{k}]'
            inputs.append(f'{m}.ogg')
        # ponytail: every track of a segment is mixed, so alternate (switch) tracks play on top of each other
        mix = f'amix=inputs={len(media)}:normalize=0,' if len(media) > 1 else 'anull,'
        trim = f'atrim=0:{ms / 1000:.3f},' if ms > 0 else ''
        parts.append(f'{labels}{mix}{trim}anull[s{n_seg}]')
        n_seg += 1
    if not n_seg: return None, None
    graph = ';'.join(parts) + ';' + ''.join(f'[s{i}]' for i in range(n_seg)) + f'concat=n={n_seg}:v=0:a=1,alimiter[out]'
    return inputs, graph


def render(ffmpeg, media_dir, inputs, graph, out):
    cmd = [ffmpeg, '-hide_banner', '-loglevel', 'error', '-y']
    for i in inputs: cmd += ['-i', i]
    cmd += ['-filter_complex', graph, '-map', '[out]', '-c:a', 'libvorbis', '-q:a', '4', out + '.part.ogg']
    r = subprocess.run(cmd, cwd=media_dir, capture_output=True, text=True)
    if r.returncode: return r.stderr.strip()[-300:]
    os.replace(out + '.part.ogg', out)


def main(data, mod_root, media_dir, ffmpeg):
    objs = parse(os.path.join(data, 'cp_music.bnk'))
    ids = {e['redId']['$value']: e['wwiseId'] for e in
           json.load(open(os.path.join(data, 'eventsmetadata.json'), encoding='utf-8'))['Data']['RootChunk']['root']['Data']['events']}
    have = {int(f[:-4]) for f in os.listdir(media_dir) if f.endswith('.ogg')}
    root = os.path.join(mod_root, 'red4ext', 'plugins', 'AudioXL', 'sounds', 'SoundtrackSwitcher')
    jobs = []
    for quest in os.listdir(root):
        qdir = os.path.join(root, quest)
        if not os.path.isdir(qdir): continue
        for cue in os.listdir(qdir):
            out = os.path.join(qdir, cue, 'original.ogg')
            name = cue.split(' ')[0]
            if name not in ids: name += '_START'   # folder names drop the _START most cues carry
            if os.path.exists(out) or name not in ids: continue
            inputs, graph = filter_graph(segments(objs, ids[name]), have)
            if inputs: jobs.append((name, inputs, graph, out))
            else: print('no audio:', name)
    print(len(jobs), 'previews to render')
    with ThreadPoolExecutor(os.cpu_count() or 4) as pool:
        for (name, *_), err in zip(jobs, pool.map(lambda j: render(ffmpeg, media_dir, *j[1:]), jobs)):
            if err: print('FAILED', name, err)


if __name__ == '__main__':
    ins, g = filter_graph([(1, 2000, [10, 11]), (2, 0, [12]), (3, 500, [99])], {10, 11, 12})
    assert ins == ['10.ogg', '11.ogg', '12.ogg'], ins
    assert '[i0][i1]amix=inputs=2' in g and 'atrim=0:2.000' in g and 'concat=n=2' in g, g
    main(*sys.argv[1:])
