# ADR-0008: The patch mod is retired; AudioXL 0.5.0 carries the additions

## Status
Accepted, supersedes ADR-0004

## Date
2026-09-26

## Context
ADR-0004 shipped a second download holding a build of AudioXL with three
additions this mod needed, because a mod cannot add a native to another mod's
plugin from outside. The additions were offered upstream as
DigitalVixenSWE/cp2077-audio-xl#2.

AudioXL 0.5.0 includes all three, under its author's names:

| ours | AudioXL 0.5.0 |
|---|---|
| `stopOn` row field | `stopEvents` |
| `SetRowEnabled` | `AudioXLAPI.SetEnabled` / `IsEnabled` |
| `PlayingRows` | `AudioXLAPI.PlayingSounds` |

Its changelog credits them: "All three ideas from remo4248."

## Decision
Delete the patch mod, the patch and the machinery around it: `patchmod/`,
`patches/`, `tools/check_patch.py` and CI's patch step. `Settings.reds` moves
into the mod and calls `AudioXLAPI.SetEnabled`; `rescan.bat` writes
`stopEvents`. The mod now requires AudioXL 0.5.0 and ships nothing of AudioXL's.

`PlayingSounds` is used by nothing here - the watcher it existed for went in
ADR-0007 - and that is fine: it is AudioXL's API now, not ours to carry.

## Alternatives considered
- **Keep the patch for players still on 0.4.3.** Rejected: two code paths for
  one call, and a download whose whole purpose is to overwrite another mod's
  files is worth removing the moment it is unnecessary.
- **Accept either field name in the manifest.** Rejected: `stopOn` was never in
  a released AudioXL, so nothing outside this repo ever wrote it.

## Consequences
- One download instead of two, and no file of AudioXL's is replaced, so an
  AudioXL update can never be undone by installing this mod.
- Players on AudioXL 0.4.3 must update. A `sounds.json` written by an older
  rescan still parses, but its `stopOn` is ignored, so tracks would run past
  their scene until the next cue - hence "re-run rescan.bat" in the changelog.
- Nothing in this repo needs a C++ toolchain for AudioXL any more; `prepare.exe`
  is the only thing still built.
