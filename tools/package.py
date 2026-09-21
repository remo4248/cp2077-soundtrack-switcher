"""Builds the three downloads into dist/, which is what gets uploaded:

  SoundtrackSwitcher.zip                    the mod: cue folders (empty ones kept), rescan, script
  AudioXL_patch_for_SoundtrackSwitcher.zip  our AudioXL build, its licence and the two scripts
  SoundtrackSwitcher_previews.zip           the optional tool that renders the game's own music

No audio ships in any of them: not the game's (original.*), not anyone's own tracks, not the
prepared copies made from them.
"""
import os, shutil, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
DIST = os.path.join(ROOT, 'dist')
PREPARE = os.path.join(HERE, 'prepare', 'build', 'prepare.exe')
AUDIO = ('.mp3', '.ogg', '.flac', '.wav')
PREPARE_IN_MOD = os.path.join(ROOT, 'mod', 'red4ext', 'plugins', 'AudioXL', 'sounds',
                              'SoundtrackSwitcher', 'prepare.exe')


def write(src, out):
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
                z.write(os.path.join(d, f), os.path.join(rel, f))
    names = zipfile.ZipFile(out).namelist()
    assert not any(os.path.splitext(n)[1].lower() in AUDIO for n in names), out
    assert not any(n.endswith('.pyc') or '__pycache__' in n for n in names), out
    print(f'{len(names):4} entries, {os.path.getsize(out) / 1024:6.0f} KB -> {os.path.normpath(out)}')
    return names


if os.path.exists(PREPARE):
    shutil.copy2(PREPARE, PREPARE_IN_MOD)   # the built tool ships with the mod, not with the source

mod = write(os.path.join(ROOT, 'mod'), 'SoundtrackSwitcher.zip')
assert any(n.endswith('rescan.bat') for n in mod) and any(n.endswith('prepare.exe') for n in mod)
assert any(n.endswith('SoundtrackSwitcher.reds') for n in mod)
assert not any(n.endswith('.dll') for n in mod), 'the patch mod ships the dll, this one does not'

patch = write(os.path.join(ROOT, 'patchmod'), 'AudioXL_patch_for_SoundtrackSwitcher.zip')
assert any(n.endswith('AudioXL.dll') for n in patch)
assert any(n.endswith('AudioXL-LICENSE.md') for n in patch), 'we redistribute AudioXL, so its licence ships'
assert any(n.endswith('Settings.reds') for n in patch)

previews = write(os.path.join(HERE, 'previews_package'), 'SoundtrackSwitcher_previews.zip')
assert any(n.endswith('make_previews.bat') for n in previews)
