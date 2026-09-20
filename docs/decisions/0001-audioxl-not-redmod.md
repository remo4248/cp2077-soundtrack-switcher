# ADR-0001: Replace music through AudioXL rather than REDmod

## Status
Accepted

## Date
2026-09-19

## Context
The mod has to make the game play a player's own audio file in place of a score
cue. The player asked explicitly to avoid REDmod if possible.

## Decision
Use AudioXL. A row registered under a vanilla event name makes the engine play
that file wherever the event fires, and AudioXL skips a row whose file is
missing - which is exactly the rule we wanted ("no file, nothing changes").

## Alternatives considered
- **REDmod custom sounds.** Works, but needs `-modded`, a deploy step after
  every change, and the thing the player asked to avoid. Rejected.
- **Replacing the .wem media inside the archives.** Keeps all of the game's
  interactive behaviour for free, because nothing about the game's logic
  changes. Rejected: every file would have to be encoded with Wwise's authoring
  tool and match the original length, so "drop an mp3 in a folder" is
  impossible.

## Consequences
- AudioXL, RED4ext, redscript and Codeware become requirements.
- Replacement happens by event name, which is why the unit of replacement is a
  cue rather than a song (ADR-0002).
- We inherit AudioXL's bugs; see ADR-0005.
