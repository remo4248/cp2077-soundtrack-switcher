# ADR-0002: Replace a cue, not a song

## Status
Accepted

## Date
2026-09-19

## Context
Players think in songs. The game has no songs: it has ~1,450 score events, and
the audio behind them is ~1,270 stems arranged into ~2,100 segments that the
game layers and switches through live. One album track can be spread over
several cues; one cue can contain pieces of several tracks.

## Decision
The unit of replacement is a cue: the event that *starts* a piece of music
(a Play action in the bank). One folder per cue, named after the event, showing
how much music the original holds.

## Alternatives considered
- **Per song.** No such unit exists in the game data. Rejected.
- **Per segment**, so a replacement could follow the scene's intensity changes.
  Rejected: it needs a file per segment from the player and a way to switch
  between them mid-scene, which is far more than "drop a track in".

## Consequences
- A replacement plays straight through; it does not follow the story beats the
  original was written around. The folder name carries the original's length so
  a player can pick something of the right size.
- Switch events inside a cue do nothing once the cue itself is replaced.
- Cues that start silent and rise through stealth/combat states are excluded -
  they are a different mechanism and would need per-state files.
