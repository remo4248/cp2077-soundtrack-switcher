# ADR-0006: Folder names drop the _START suffix, with the old names still accepted

## Status
Accepted

## Date
2026-09-21

## Context
225 of the 281 cue folders ended in `_START`, which is engine noise to a player
choosing where to put a track. Removing it is safe: stripping the suffix
produces no duplicate and never collides with another cue's real name.

Players already have folders under the old names, with their own tracks inside
them. Renaming in a release would silently orphan those tracks.

## Decision
Name folders without the suffix, and have `rescan.bat` resolve a folder name
back to the real event: exact match first, then with `_START` appended, using
the shipped `cues.json`. Both forms therefore work.

## Alternatives considered
- **Rename and tell players to move their files.** Rejected: silent breakage
  for anyone who skips the note.
- **Keep the suffix.** Rejected: it is noise in every folder name.

## Consequences
- Old folders keep working indefinitely; there is no removal deadline, and the
  compatibility is two lines in rescan.
- `cues.json` ships with the mod, and an unknown folder name is now reported as
  skipped rather than silently written into the manifest.
