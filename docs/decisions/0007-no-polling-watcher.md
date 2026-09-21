# ADR-0007: No polling watcher; stop events carry the whole job

## Status
Accepted, supersedes the watcher introduced with ADR-0002's cue model

## Date
2026-09-21

## Context
Before the AudioXL patch existed, a replaced track had no way to end: the
game's stop events act on its own music objects, not on a custom sound. The
answer at the time was a script that asked AudioXL four times a second which
replaced cues were playing and stopped all but the newest.

`stopOn` then made the game's own stop events end the track, and the watcher
became insurance rather than the mechanism. Measuring what it still covers:

- **255 of 281 cues have a stop event.** For those, the track cannot outlive
  its scene however long it is.
- **26 have none.** 19 of those are performance fragments nobody replaces:
  fourteen 7-second pieces of Kerry's vocals in *Boat Drinks*, three of him
  warming up in *Second Conflict*, the nomad bard, and Johnny playing
  *Johnny B. Goode*. The other 7 are the end credits, two mq304 stingers of 9
  and 21 seconds, the 39-second bridge from The Heist into the flashback, and
  three q110/q112 scene pieces.

A claim that a stop event might not fire on some path was checked and dropped.
The game's audio metadata holds scene state machines that post events, but
`mus_q101_arasaka_raid_07_as_outro_STOP` is absent from it and was still
observed firing in game at 224.8 s, and only 163 of 281 cue STARTs appear there
while the rest plainly start. Events are posted from quest and scene files too,
so absence from the metadata says nothing, and no stop event has ever been seen
failing to fire.

## Decision
Remove the tick. The script keeps two callbacks: one log line at session start,
and at session end a `Stop` on each replaced cue so AudioXL is not left holding
a voice into the next session. Neither runs during play.

Because that needs only `Stop`, which official AudioXL has, one script now
serves both installs and the patch mod no longer overrides it.

## Alternatives considered
- **Watch only the cues with no stop event.** Rejected as not worth its own
  code path: it protects 7 realistic cues at the cost of a mechanism, a
  generated list with two meanings, and a tick that still runs for anyone who
  replaces the credits.
- **Keep watching everything.** Rejected: a permanent four-per-second cost for
  a case the stop events already handle.

## Consequences
- In-game cost while playing is now zero: no callback of ours runs at all.
- Replacing one of the 26 cues without a stop event means that track plays until
  the next cue starts. Stated on the mod page.
- `Cues.reds` is still generated: the session-end stop and the Mod Settings
  switch both read it.
- `PlayingRows`, added to AudioXL for the watcher, is no longer used by this
  mod. It stays in the patch and in the upstream offer, where `stopOn` and
  `SetRowEnabled` are the two that matter.
