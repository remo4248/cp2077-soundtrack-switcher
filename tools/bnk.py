"""Minimal Wwise bank reader for cp_music.bnk (bank version 150): objects, event actions, segment lengths."""
import struct

TYPES = {2: 'Sound', 3: 'Action', 4: 'Event', 10: 'MusicSegment', 11: 'MusicTrack', 12: 'MusicSwitch', 13: 'MusicRanSeq'}
PLAY, SET_SWITCH = 0x0403, 0x1901
STOP_TYPES = (0x0102, 0x0103, 0x0104, 0x0105)   # Stop, with the engine's four scopes


def parse(path):
    b = open(path, 'rb').read(); i = 0; chunks = {}
    while i < len(b):
        tag = b[i:i + 4]; size = struct.unpack_from('<I', b, i + 4)[0]; chunks[tag] = (i + 8, size); i += 8 + size
    off, _ = chunks[b'HIRC']; n = struct.unpack_from('<I', b, off)[0]; j = off + 4; objs = {}
    for _ in range(n):
        t = b[j]; sz = struct.unpack_from('<I', b, j + 1)[0]; oid = struct.unpack_from('<I', b, j + 5)[0]
        objs[oid] = (t, b[j + 9:j + 5 + sz]); j += 5 + sz
    return objs


def refs(objs, oid):
    # ponytail: byte-scan for known object ids instead of parsing every HIRC layout; rare false refs are harmless here
    data = objs[oid][1]
    return {v for k in range(len(data) - 3) if (v := struct.unpack_from('<I', data, k)[0]) in objs and v != oid}


def action_types(objs, event_id):
    return {struct.unpack_from('<H', objs[a][1], 0)[0] for a in refs(objs, event_id) if objs[a][0] == 3}


def segment_ms(data):
    """MusicSegment tail = fDuration f64, u32 markerCount, markers (u32 id, f64 pos, u8 len + name). Found by fitting from the end."""
    for k in range(len(data) - 12, -1, -1):
        n = struct.unpack_from('<I', data, k + 8)[0]
        if not 1 <= n <= 16: continue
        p = k + 12
        for _ in range(n):
            if p + 13 > len(data): break
            p += 13 + data[p + 12]
        else:
            if p == len(data):
                d = struct.unpack_from('<d', data, k)[0]
                if 0 < d < 3.6e6: return d
    return 0.0


def children(objs, oid, types=(10, 12, 13)):
    """Container child list: u32 count followed by that many ascending ids of the given node types."""
    data = objs[oid][1]
    for k in range(len(data) - 7):
        n = struct.unpack_from('<I', data, k)[0]
        if not 1 <= n <= 512 or k + 4 + 4 * n > len(data): continue
        ids = struct.unpack_from(f'<{n}I', data, k + 4)
        if list(ids) == sorted(set(ids)) and all(objs.get(i, (0,))[0] in types for i in ids):
            return ids
    return ()


def action_targets(objs, event_id, types):
    """What the event's actions of these types point at (action layout: u16 type, u32 target)."""
    out = []
    for a in refs(objs, event_id):
        t, data = objs[a]
        if t == 3 and struct.unpack_from('<H', data, 0)[0] in types:
            tgt = struct.unpack_from('<I', data, 2)[0]
            if tgt in objs: out.append(tgt)
    return out


def play_targets(objs, event_id):
    """Objects that the event's Play actions start."""
    return action_targets(objs, event_id, (PLAY,))


def track_sources(data):
    """Media ids of a MusicTrack (AkBankSourceData: u32 plugin, u8 stream type, u32 media id)."""
    return sorted({struct.unpack_from('<I', data, k + 5)[0] for k in range(len(data) - 9)
                   if struct.unpack_from('<I', data, k)[0] in (0x00040001, 0x00020001, 0x00010001)})


def segments(objs, event_id):
    """Segments the event can play, in container order, each once: [(segment id, ms, [media ids])]."""
    seen, out = set(), []
    def walk(oid):
        if oid in seen: return
        seen.add(oid); t, data = objs[oid]
        if t == 10:
            media = [m for tr in children(objs, oid, (11,)) for m in track_sources(objs[tr][1])]
            out.append((oid, segment_ms(data), media))
        elif t in (12, 13):
            for c in children(objs, oid): walk(c)
        elif t == 2:  # plain Sound instead of music
            out.append((oid, 0.0, track_sources(data)))
        elif t in (5, 9):  # random/sequence or layer container of Sounds
            for c in children(objs, oid, (2, 5, 9)): walk(c)
    for t in play_targets(objs, event_id): walk(t)
    return out


def music_ms(objs, event_id):
    """Total length of the distinct segments the event can play (each segment counted once, loops ignored)."""
    seen, stack, total = set(), play_targets(objs, event_id), 0.0
    while stack:
        oid = stack.pop()
        if oid in seen: continue
        seen.add(oid); t, data = objs[oid]
        if t == 10: total += segment_ms(data)
        elif t in (12, 13): stack += children(objs, oid)
    return total


if __name__ == '__main__':
    import sys
    o = parse(sys.argv[1])
    # Dex cue: segments measured by hand were 21.3+5.7+40+... s; the total must be in the minutes range
    ms = music_ms(o, 723875940)
    assert 60_000 < ms < 600_000, ms
    assert segment_ms(o[18167238][1]) == 21333.333333333332 or abs(segment_ms(o[18167238][1]) - 21333.33) < 1
    segs = segments(o, 723875940)
    assert len(segs) == 8 and all(len(m) == 1 for _, _, m in segs), segs
    assert 409752499 in [m for _, _, ms_ in segs for m in ms_]
    print('ok, dex cue music', round(ms / 1000, 1), 's')
