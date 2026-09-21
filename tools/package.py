"""Zips mod/ into dist/SoundtrackSwitcher.zip for MO2: the cue folders (keeps the empty ones), the
rescan script and the redscript that stops an older cue when a new one starts. Leaves out audio: the game's
own (original.*), anyone's own tracks, and the prepared copies made from them."""
import os, shutil, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.join(HERE, '..', 'mod')
DIST = os.path.join(HERE, '..', 'dist')
PREPARE = os.path.join(HERE, 'prepare', 'build', 'prepare.exe')
AUDIO = ('.mp3', '.ogg', '.flac', '.wav')
PREPARE_IN_MOD = os.path.join(MOD, 'red4ext', 'plugins', 'AudioXL', 'sounds', 'SoundtrackSwitcher', 'prepare.exe')


def write(out):
    os.makedirs(os.path.dirname(out), exist_ok=True)   # dist/ is not in git
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for d, _, files in os.walk(MOD):
            rel = os.path.relpath(d, MOD)
            if rel != '.': z.write(d, rel.replace('\\', '/') + '/')
            for f in files:
                if os.path.splitext(f)[1].lower() in AUDIO: continue   # someone's tracks, or the game's
                z.write(os.path.join(d, f), os.path.join(rel, f))
    names = zipfile.ZipFile(out).namelist()
    assert not any(os.path.splitext(n)[1].lower() in AUDIO for n in names)
    print(len(names), 'entries,', os.path.getsize(out), 'bytes ->', os.path.normpath(out))
    return names


if os.path.exists(PREPARE):
    shutil.copy2(PREPARE, PREPARE_IN_MOD)   # the built tool ships with the mod, not with the source
names = write(os.path.join(DIST, 'SoundtrackSwitcher.zip'))
assert any(n.endswith('SoundtrackSwitcher.reds') for n in names)
assert any(n.endswith('rescan.bat') for n in names)
assert not any(n.endswith('.dll') for n in names)
