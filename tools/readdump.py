"""Names the code that crashed, from a Windows minidump: the faulting module, plus the modules on the
faulting thread's stack (a rough call stack - stack scanning, so expect some stale entries).
Usage: python readdump.py <file.dmp>
"""
import struct, sys
from bisect import bisect_right

MODULE_LIST, MEMORY_LIST, EXCEPTION = 4, 5, 6


def streams(buf):
    sig, _, count, rva = struct.unpack_from('<4sIII', buf, 0)
    assert sig == b'MDMP', sig
    out = {}
    for i in range(count):
        kind, size, at = struct.unpack_from('<III', buf, rva + 12 * i)
        out[kind] = (at, size)
    return out


def utf16(buf, rva):
    length = struct.unpack_from('<I', buf, rva)[0]
    return buf[rva + 4:rva + 4 + length].decode('utf-16le', 'replace')


def modules(buf, at):
    count = struct.unpack_from('<I', buf, at)[0]
    out = []
    for i in range(count):
        base, size, _, _, name_rva = struct.unpack_from('<QIIII', buf, at + 4 + 108 * i)
        out.append((base, size, utf16(buf, name_rva).split('\\')[-1]))
    return sorted(out)


def owner(mods, addr):
    i = bisect_right(mods, (addr, float('inf'), '')) - 1
    if i >= 0 and mods[i][0] <= addr < mods[i][0] + mods[i][1]:
        return f'{mods[i][2]}+0x{addr - mods[i][0]:x}'
    return None


def main(path):
    buf = open(path, 'rb').read()
    s = streams(buf)
    mods = modules(buf, s[MODULE_LIST][0])

    at = s[EXCEPTION][0]
    thread_id, _, code, flags, _, address = struct.unpack_from('<IIIIQQ', buf, at)
    ctx_size, ctx_rva = struct.unpack_from('<II', buf, at + 8 + 152)
    print(f'exception 0x{code:08x} at 0x{address:x} -> {owner(mods, address) or "unknown module"}')
    print(f'thread {thread_id}')

    rsp = struct.unpack_from('<Q', buf, ctx_rva + 0x98)[0]   # CONTEXT_AMD64.Rsp
    stack = None
    if MEMORY_LIST in s:
        at = s[MEMORY_LIST][0]
        for i in range(struct.unpack_from('<I', buf, at)[0]):
            start, size, rva = struct.unpack_from('<QII', buf, at + 4 + 16 * i)
            if start <= rsp < start + size:
                stack = (start, buf[rva:rva + size])
    if not stack:
        print('no stack memory in this dump')
        return
    print(f'\nstack from 0x{rsp:x} (nearest first, may include stale frames):')
    start, data = stack
    seen, shown = set(), 0
    for off in range(rsp - start, len(data) - 8, 8):
        who = owner(mods, struct.unpack_from('<Q', data, off)[0])
        if who and who.split('+')[0] not in seen or (who and shown < 40):
            seen.add(who.split('+')[0])
            print('   ', who)
            shown += 1
        if shown >= 40:
            break


if __name__ == '__main__':
    main(sys.argv[1])
