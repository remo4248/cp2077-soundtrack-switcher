# ADR-0005: Never let a replacement stream from disk

## Status
Accepted

## Date
2026-09-20

## Context
The game crashed on save loads - sometimes the first load after launch,
sometimes after eight. Four crash dumps all show the same null dereference
inside the game's own audio code (`Cyberpunk2077.exe+0x4d7efe`,
`mov r8b,[rdx+0x155]` with RDX=0), with no mod code on the stack. It happens
with AudioXL and replacement rows registered, with our script removed entirely.

Measured behaviour: with rows that stream (compressed, 45 s+), loads failed
within a load or two. With every row held in memory, the same save survived 15
loads before failing once - about 1 in 9 measured across 18 loads.

## Decision
Ship only prepared WAV files, which AudioXL memory-maps. Never register a row
that AudioXL would stream.

## Alternatives considered
- **`"stream": false` in the row.** It does not force in-memory; anything
  compressed and long always streams. Verified in AudioXL's source.
- **Fixing the streaming path ourselves.** Rejected: the fault is in engine
  code we cannot see, and the one leak we did find and fix (an orphaned voice
  surviving sessions) did not stop the crash.

## Consequences
- Disk cost of ~10 MB per minute of replaced music, generated locally.
- A residual crash remains at roughly 1 in 9 loads. A failed load succeeds on
  retry. This is stated in the mod's documentation rather than hidden.
- The evidence (dumps, addresses, the rate measurements, the orphaned-voice
  leak) is worth handing to AudioXL's author.
