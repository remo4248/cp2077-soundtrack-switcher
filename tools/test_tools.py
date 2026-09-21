"""The checks that need no game data, so CI can run them. Anything needing the game's archives is
verified by the self-checks inside bnk.py and generate.py, which run when those are invoked.

Usage: python tools/test_tools.py
"""
import glob, json, os, shutil, struct, subprocess, sys, tempfile, wave

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate import EXCLUDE, display_name, fmt, folder_name, quest_of
from previews import filter_graph


def test_cue_naming():
    assert quest_of('mus_q005_dex_confrontation_01_p1') == 'q005'
    assert quest_of('mus_sts_wat_nid_07_facing_aaron_01_START') == 'sts_wat_nid_07'
    assert quest_of('mus_finalboards_START') == 'Credits'
    assert display_name('mus_q101_js_death_01_START') == 'mus_q101_js_death_01'
    assert display_name('mus_q005_dex_confrontation_01_p1') == 'mus_q005_dex_confrontation_01_p1'
    assert fmt(191800) == '3m12s'
    # accents are dropped: AudioXL opens files through narrow-string paths
    assert folder_name('q110', {'q110_x': "M'ap Tann Pèlen: A"}) == "q110 - M'ap Tann Pelen - A"


def test_excluded_families():
    for name in ('mus_radio_vexelstrom_01', 'mus_ow_arasaka_START', 'mus_q005_the_heist_START_silent',
                 'mus_q101_gig_START', 'mus_sq028_kerry_guitar_01_start'):
        assert EXCLUDE.search(name), name
    for name in ('mus_q005_dex_confrontation_01_p1', 'mus_mq301_yuri_combat_START'):
        assert not EXCLUDE.search(name), name


def test_filter_graph():
    inputs, graph = filter_graph([(1, 2000, [10, 11]), (2, 0, [12]), (3, 500, [99])], {10, 11, 12})
    assert inputs == ['10.ogg', '11.ogg', '12.ogg'], inputs
    assert '[i0][i1]amix=inputs=2' in graph and 'atrim=0:2.000' in graph and 'concat=n=2' in graph


def sine_wav(path, seconds=3, rate=48000, amplitude=0.02):
    """A quiet tone: prepare.exe should raise it towards the target and not clip."""
    with wave.open(path, 'wb') as w:
        w.setnchannels(2), w.setsampwidth(2), w.setframerate(rate)
        frames = bytearray()
        for i in range(seconds * rate):
            v = int(amplitude * 32767 * __import__('math').sin(2 * 3.14159 * 440 * i / rate))
            frames += struct.pack('<hh', v, v)
        w.writeframes(bytes(frames))


def peak_of(path):
    with wave.open(path, 'rb') as w:
        data = w.readframes(w.getnframes())
    return max(abs(s) for s, in struct.iter_unpack('<h', data)) / 32768.0


def test_prepare_normalises(prepare):
    with tempfile.TemporaryDirectory() as tmp:
        src, out = os.path.join(tmp, 'in.wav'), os.path.join(tmp, 'out.wav')
        sine_wav(src)
        result = subprocess.run([prepare, src, out, '--target', '-16'], capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr
        assert os.path.exists(out), result.stdout
        assert '-16.0' in result.stdout, result.stdout          # it reports the target it hit
        assert peak_of(out) <= 0.95, peak_of(out)               # the limiter kept it below the ceiling
        assert peak_of(out) > peak_of(src), 'a quiet input should have been raised'


RESCAN = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'mod', 'red4ext', 'plugins',
                      'AudioXL', 'sounds', 'SoundtrackSwitcher', 'rescan.ps1')


def run_rescan(tmp, folders):
    """A throwaway copy of the mod tree: drop the given files in each cue folder, run rescan, read
    back what it decided to play. prepare.exe is not copied in, so the files stay untouched."""
    root = os.path.join(tmp, 'red4ext', 'plugins', 'AudioXL', 'sounds', 'SoundtrackSwitcher')
    for folder, files in folders.items():
        d = os.path.join(root, 'q000 - Test', folder)
        os.makedirs(d, exist_ok=True)
        for f in files:
            open(os.path.join(d, f), 'wb').close()
    cues = [os.path.basename(d).split(' ')[0] + '_START'
            for d in glob.glob(os.path.join(root, '*', 'mus_*'))] +            [folder.split(' ')[0] + '_START' for folder in folders]
    os.makedirs(root, exist_ok=True)
    with open(os.path.join(root, 'cues.json'), 'w') as f:
        json.dump(cues, f)
    shutil.copy(RESCAN, root)
    r = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                        os.path.join(root, 'rescan.ps1')], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    with open(os.path.join(root, 'sounds.json'), encoding='utf-8') as f:
        return {row['name']: row for row in json.load(f)['sounds']}, r.stdout


def test_rescan_takes_any_filename():
    """Any audio file in a cue folder is the replacement - no renaming. original.* is the game's own
    music and never a replacement, and our own prepared file is not an input."""
    with tempfile.TemporaryDirectory() as tmp:
        rows, out = run_rescan(tmp, {
            'mus_test_named_01 [1m00s]': ['My Song.mp3', 'original.ogg', 'notes.txt'],
            'mus_test_loop_01 [1m00s]':  ['Some Track.loop.flac'],
            'mus_test_orig_01 [1m00s]':  ['original.ogg'],
            'mus_test_left_01 [1m00s]':  ['original.ogg', 'replace.prepared.wav'],
            'mus_test_two_01 [1m00s]':   ['b song.mp3', 'a song.mp3'],
            'mus_test_old_01 [1m00s]':   ['replace.mp3'],
        })
        assert set(rows) == {'mus_test_named_01_START', 'mus_test_loop_01_START',
                             'mus_test_two_01_START', 'mus_test_old_01_START'}, (sorted(rows), out)
        assert rows['mus_test_named_01_START']['file'].endswith('My Song.mp3'), rows
        assert rows['mus_test_named_01_START']['loop'] is False
        assert rows['mus_test_named_01_START']['stopOn'] == [], 'a cue with no stop event gets none'
        assert rows['mus_test_loop_01_START']['loop'] is True, 'a .loop. file loops'
        assert rows['mus_test_two_01_START']['file'].endswith('a song.mp3'), 'first by name wins'
        assert 'b song.mp3' in out, 'the file it did not use should be named in the output'
        assert rows['mus_test_old_01_START']['file'].endswith('replace.mp3'), 'old folders keep working'


def test_rescan_prepared_name_is_ascii(prepare):
    """AudioXL opens its files through narrow-string paths, so what prepare.exe writes must stay
    ASCII however the player named their track - and the row must point at that prepared file."""
    with tempfile.TemporaryDirectory() as tmp:
        root = os.path.join(tmp, 'red4ext', 'plugins', 'AudioXL', 'sounds', 'SoundtrackSwitcher')
        os.makedirs(os.path.join(root, 'q000 - Test', 'mus_test_utf8_01 [1m00s]'))
        sine_wav(os.path.join(root, 'q000 - Test', 'mus_test_utf8_01 [1m00s]', 'Café Søng.wav'))
        shutil.copy(prepare, root)
        rows, out = run_rescan(tmp, {})
        row = rows['mus_test_utf8_01_START']
        assert row['file'].endswith('.prepared.wav'), row
        assert row['file'].isascii(), row
        assert os.path.exists(os.path.join(root, row['file'].replace('/', os.sep))), (row, out)


def test_script_does_not_poll():
    """ADR-0007: the script runs at session start and session end, never while you play. A timer
    creeping back in is the regression this guards."""
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'mod', 'r6', 'scripts',
                            'SoundtrackSwitcher', 'SoundtrackSwitcher.reds'), encoding='utf-8').read()
    for banned in ('DelayCallback', 'DelaySystem', 'PlayingRows', 'Position('):
        assert banned not in src.split('module SoundtrackSwitcher')[1], banned
    assert 'Session/Ready' in src and 'Session/BeforeEnd' in src


if __name__ == '__main__':
    test_cue_naming()
    test_excluded_families()
    test_filter_graph()
    test_rescan_takes_any_filename()
    test_script_does_not_poll()
    built = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'prepare', 'build', 'prepare.exe')
    if os.path.exists(built):
        test_prepare_normalises(built)
        test_rescan_prepared_name_is_ascii(built)
        print('ok - naming, filters and prepare.exe')
    else:
        print('ok - naming and filters (prepare.exe not built, skipped its check)')
