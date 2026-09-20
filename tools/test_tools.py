"""The checks that need no game data, so CI can run them. Anything needing the game's archives is
verified by the self-checks inside bnk.py and generate.py, which run when those are invoked.

Usage: python tools/test_tools.py
"""
import os, struct, subprocess, sys, tempfile, wave

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


if __name__ == '__main__':
    test_cue_naming()
    test_excluded_families()
    test_filter_graph()
    built = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'prepare', 'build', 'prepare.exe')
    if os.path.exists(built):
        test_prepare_normalises(built)
        print('ok - naming, filters and prepare.exe')
    else:
        print('ok - naming and filters (prepare.exe not built, skipped its check)')
