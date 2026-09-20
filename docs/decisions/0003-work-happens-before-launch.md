# ADR-0003: Do the audio work in rescan.bat, not in the game

## Status
Accepted (supersedes the runtime loudness matching and the in-game bake)

## Date
2026-09-20

## Context
Matching a replacement to the game's loudness needs the file decoded and
measured. The first two attempts did this while the game loaded: a `bake` step
that decoded mp3 to WAV at startup, and a gain worked out from the decoded PCM.
Both ran on every launch, and the measuring code crashed the game twice.

## Decision
Everything measurable happens when the player runs `rescan.bat`. `prepare.exe`
decodes, measures, normalises and writes a plain WAV; the game only plays it.

## Alternatives considered
- **ffmpeg** for the decode/measure/normalise step. Rejected: it would mean a
  ~90 MB download bundled with the mod or a manual install. `prepare.exe` is
  ~450 KB and uses the same decoders AudioXL already vendors.
- **Keep it at load, but fix the bugs.** Rejected on the player's instruction:
  in-game work should be as close to nothing as possible.

## Consequences
- Adding a track costs a few seconds in the bat instead of a few seconds of
  every launch, and the prepared WAVs cost disk (~10 MB per minute).
- The game does no decoding, measuring or streaming - which also avoids
  AudioXL's streaming path (ADR-0005).
- The AudioXL patch shrank: the loudness code came back out.
