# Changelog

All notable changes to Soundtrack Switcher, newest first.

## [0.3.0] - 2026-09-26

### Changed
- **Requires AudioXL 0.5.0**, which added all three things this mod needed, so
  the separate patch download is gone. One mod, one install, official AudioXL.
  Delete `AudioXL patch for Soundtrack Switcher` if you have it.
- The manifest field is AudioXL's `stopEvents` rather than our `stopOn`, and the
  in-game switch calls `AudioXLAPI.SetEnabled`. **Re-run rescan.bat** after
  updating so `sounds.json` uses the new field.
- `prepare.exe` is a separate download: a mod archive holding an unsigned binary
  gets quarantined by Nexus's scanner. The mod works without it; tracks are then
  played as they are. It also carries version metadata now and is built with
  /guard:cf.

### Removed
- The four-times-a-second watcher. Stop events end a replaced track for 255 of
  the 281 cues, which makes the watcher insurance for 26 - 19 of them seven-second
  performance fragments. Nothing of this mod now runs while you play. Replacing
  one of the other 7 (the credits, two mq304 stingers, the Heist-to-flashback
  bridge, three q110/q112 pieces) means that track plays until the next cue
  starts. See docs/decisions/0007.

### Fixed
- The 14 cues whose names end in a lowercase `_start` were written out as
  `_START`, which the game hashes to something else, so a track in one of those
  folders played nothing and said nothing. Among them: Johnny's goodbye in
  *Where is My Mind*, the braindance cues and Kerry's hum.

## [0.2.0] - 2026-09-21

### Changed
- A replacement can be called anything. Any audio file in a cue folder is the
  replacement, so tracks no longer have to be renamed to `replace.mp3`.
  Existing folders keep working. `original.*` is never a replacement, and the
  prepared copy is named after the track, so swapping tracks cannot leave the
  old one playing.
- Looping is now a name ending in `.loop`, e.g. `My Song.loop.mp3`.

### Fixed
- The session line in the log always said "watching 0 cue(s)": it counted the
  cue list inline rather than through a local, as the working call sites do.
- The 26 cues with no stop event wrote `stopOn: [null]` instead of nothing, and
  the run never warned that those tracks end only when the next cue starts.

## [0.1.0] - 2026-09-21

First working version. Two mods: **Soundtrack Switcher** (install this) and
**AudioXL patch for Soundtrack Switcher** (install after it, and after AudioXL).

### Added
- 281 cue folders, one per story music cue, grouped by quest under the quest's
  in-game name, each showing how much music the original holds.
- `rescan.bat`: prepares every track you drop in and writes what the game reads.
  Run it after adding or removing tracks.
- Loudness matching. Every replacement is brought to -16 LUFS, the middle of the
  game's own music, with a limiter so quiet tracks can be raised without
  clipping. A `volume.txt` holding e.g. `-3` nudges one cue by ear.
- Tracks end where the game ends its own music, for the 255 cues that have a
  stop event. Otherwise a track ends when the next cue starts.
- A newer cue always takes over from an older one, with a 2 second fade.
- Looping: name a file `replace.loop.mp3` to repeat it until the game moves on.
- In-game on/off switch under Settings -> Mods (needs Mod Settings and the
  patch mod). Off gives you the game's own music back without a restart.
- Separate previews download: renders the original music of every cue from your
  own game files, so you can hear a cue before replacing it.

### Known issues
- The game can crash while loading a save, at roughly 1 in 9 loads. Loading
  again works. The fault is in the game's own audio code and happens with
  AudioXL and any replacement registered, with or without this mod's script;
  see `docs/decisions/0005-streaming-and-the-load-crash.md`.
- Cues whose music starts silent and rises through stealth and combat are not
  replaceable; neither is radio or music played by something on screen.
