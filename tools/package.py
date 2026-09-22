"""Builds the downloads into dist/, which is what gets uploaded:

  SoundtrackSwitcher.zip                    the mod: cue folders (empty ones kept), rescan, script
  AudioXL_patch_for_SoundtrackSwitcher.zip  our AudioXL build, its licence and the two scripts
  SoundtrackSwitcher_previews.zip           the optional tool that renders the game's own music
  SoundtrackSwitcher_prepare.zip            prepare.exe on its own, plus the raw prepare.exe

prepare.exe is packaged separately because a mod archive holding an unsigned binary gets
quarantined by the file scanner. The mod runs without it - tracks are then played as they are,
without loudness matching - so it is an optional download rather than part of the main one.

No audio ships in any of them: not the game's (original.*), not anyone's own tracks, not the
prepared copies made from them.
"""
import os, shutil, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
DIST = os.path.join(ROOT, 'dist')
PREPARE = os.path.join(HERE, 'prepare', 'build', 'prepare.exe')
AUDIO = ('.mp3', '.ogg', '.flac', '.wav')
PREPARE_NOTE = """SOUNDTRACK SWITCHER - prepare.exe (loudness matching)
=====================================================

Put prepare.exe next to rescan.bat, in the mod's SoundtrackSwitcher folder, then run
rescan.bat. Every track you have added is brought to the loudness of the game's own
music before the game starts.

Without it the mod still works: your tracks are played exactly as they are, so a quiet
one stays quiet and a loud one drowns the dialogue.

It reads the one file rescan.bat points it at, measures its loudness (EBU R128), applies
gain and a peak limiter, and writes a .wav beside your track. It opens no network
connection and writes nothing anywhere else.

Source and the build that produced it:
https://github.com/remo4248/cp2077-soundtrack-switcher  (tools/prepare/)
"""
PREPARE_IN_MOD = os.path.join(ROOT, 'mod', 'red4ext', 'plugins', 'AudioXL', 'sounds',
                              'SoundtrackSwitcher', 'prepare.exe')


def write(src, out, skip=('prepare.exe',)):
    """Zip a folder as the mod managers expect it: paths relative to that folder, empty ones kept."""
    os.makedirs(DIST, exist_ok=True)   # dist/ is not in git
    out = os.path.join(DIST, out)
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for d, dirs, files in os.walk(src):
            dirs[:] = [x for x in dirs if x != '__pycache__']   # running the tests leaves these
            rel = os.path.relpath(d, src)
            if rel != '.': z.write(d, rel.replace(os.sep, '/') + '/')
            for f in files:
                if os.path.splitext(f)[1].lower() in AUDIO: continue   # someone's tracks, or the game's
                if f.lower() in skip: continue                         # its own download, see above
                z.write(os.path.join(d, f), os.path.join(rel, f))
    names = zipfile.ZipFile(out).namelist()
    assert not any(os.path.splitext(n)[1].lower() in AUDIO for n in names), out
    assert not any(n.endswith('.pyc') or '__pycache__' in n for n in names), out
    print(f'{len(names):4} entries, {os.path.getsize(out) / 1024:6.0f} KB -> {os.path.normpath(out)}')
    return names


if os.path.exists(PREPARE):
    shutil.copy2(PREPARE, PREPARE_IN_MOD)   # the built tool ships with the mod, not with the source

mod = write(os.path.join(ROOT, 'mod'), 'SoundtrackSwitcher.zip')
assert any(n.endswith('rescan.bat') for n in mod)
assert not any(n.lower().endswith(('.exe', '.dll')) for n in mod), 'no binaries in the mod download'
assert any(n.endswith('SoundtrackSwitcher.reds') for n in mod)
assert not any(n.endswith('.dll') for n in mod), 'the patch mod ships the dll, this one does not'

patch = write(os.path.join(ROOT, 'patchmod'), 'AudioXL_patch_for_SoundtrackSwitcher.zip')
assert any(n.endswith('AudioXL.dll') for n in patch)
assert any(n.endswith('AudioXL-LICENSE.md') for n in patch), 'we redistribute AudioXL, so its licence ships'
assert any(n.endswith('Settings.reds') for n in patch)

previews = write(os.path.join(HERE, 'previews_package'), 'SoundtrackSwitcher_previews.zip')
assert any(n.endswith('make_previews.bat') for n in previews)

# prepare.exe on its own: as a zip for people who want the note with it, and raw for anyone who
# would rather scan or drop in a single file.
if os.path.exists(PREPARE):
    os.makedirs(DIST, exist_ok=True)
    staging = os.path.join(DIST, '_prepare')
    shutil.rmtree(staging, ignore_errors=True)
    os.makedirs(staging)
    shutil.copy2(PREPARE, os.path.join(staging, 'prepare.exe'))
    open(os.path.join(staging, 'README.txt'), 'w', newline=chr(13) + chr(10)).write(PREPARE_NOTE)
    tool = write(staging, 'SoundtrackSwitcher_prepare.zip', skip=())
    assert any(n.endswith('prepare.exe') for n in tool)
    shutil.rmtree(staging, ignore_errors=True)
    shutil.copy2(PREPARE, os.path.join(DIST, 'prepare.exe'))
    print(f'     also raw: {os.path.normpath(os.path.join(DIST, "prepare.exe"))}')
