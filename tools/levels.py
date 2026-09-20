"""Measures how loud each cue's original music is, so a replacement can be matched to it.

Reads the original.ogg previews in the mod tree (rendered by previews.py from the player's own game
files) and writes levels.json: cue -> mean RMS in dBFS. rescan.bat puts that number in each row and
AudioXL measures the replacement the same way, then sets the row's gain from the difference.

ponytail: plain RMS, not EBU R128 loudness - the same metric on both sides is what matters here, and
a per-cue offset covers the rest. Move both sides to LUFS if matching turns out to feel wrong.

Usage: python levels.py <mod root> <ffmpeg.exe>
"""
import json, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

MEAN = re.compile(r'mean_volume:\s*(-?\d+(?:\.\d+)?) dB')
LUFS = re.compile(r'\bI:\s*(-?\d+(?:\.\d+)?) LUFS')


def measure(ffmpeg, path):
    """Integrated loudness (LUFS) - the two-pass perceptual measure, same one ffmpeg's loudnorm uses."""
    out = subprocess.run([ffmpeg, '-hide_banner', '-nostats', '-i', path, '-map', '0:a',
                          '-af', 'ebur128=framelog=quiet', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    hit = LUFS.search(out)
    return float(hit.group(1)) if hit else None


def main(mod_root, ffmpeg):
    root = os.path.join(mod_root, 'red4ext', 'plugins', 'AudioXL', 'sounds', 'SoundtrackSwitcher')
    jobs = []
    for quest in os.listdir(root):
        qdir = os.path.join(root, quest)
        if not os.path.isdir(qdir): continue
        for cue in os.listdir(qdir):
            preview = os.path.join(qdir, cue, 'original.ogg')
            if os.path.exists(preview): jobs.append((cue.split(' ')[0], preview))

    levels = {}
    with ThreadPoolExecutor(os.cpu_count() or 4) as pool:
        for (name, _), db in zip(jobs, pool.map(lambda j: measure(ffmpeg, j[1]), jobs)):
            if db is not None: levels[name] = round(db, 1)
    with open(os.path.join(root, 'levels.json'), 'w', encoding='utf-8') as f:
        json.dump(levels, f, indent=1, sort_keys=True)
    loud = sorted(levels.items(), key=lambda kv: kv[1])
    print(f'{len(levels)} of {len(jobs)} cues measured -> levels.json')
    if loud:
        print(f'  quietest {loud[0][0]} {loud[0][1]} dB, loudest {loud[-1][0]} {loud[-1][1]} dB, '
              f'average {sum(levels.values()) / len(levels):.1f} dB')


if __name__ == '__main__':
    main(*sys.argv[1:])
