# Soundtrack Switcher

Replace Cyberpunk 2077's score with your own music, one cue at a time, without
REDmod and without touching any game file. Drop a track into a folder, run a
bat, and the game plays it where its own music would have played.

## For players

1. Install **AudioXL**, then **SoundtrackSwitcher.zip**, then
   **AudioXL_patch_for_SoundtrackSwitcher.zip** — in that order in your mod
   manager, so the patch wins its three files.
2. Open the mod's `SoundtrackSwitcher` folder, find a quest, find a cue.
3. Drop your track in. Any name, any of `.mp3`, `.ogg`, `.flac`, `.wav`.
   A name ending in `.loop` repeats until the game moves on.
4. Run `rescan.bat`. Start the game.

A folder with no track keeps the game's own music. `SoundtrackSwitcher_previews.zip`
renders the original music into each folder so you can hear it first.

## For developers

| Path | What it is |
|---|---|
| `mod/` | the mod as shipped, minus anything generated |
| `patchmod/` | the AudioXL patch mod: our AudioXL build (MIT, licence included) and its scripts |
| `patches/` | our AudioXL changes, as a patch against a named upstream commit |
| `tools/` | the generator, the loudness tool, packaging, crash-dump reader |
| `docs/decisions/` | why the mod works the way it does |

```
tools\prepare\build.bat     builds prepare.exe (MSVC, no CMake)
python tools\generate.py <data> mod    rebuilds the cue tree from game data
python tools\package.py     builds the release zips into dist\
python tools\test_tools.py  runs the checks that need no game data
```

Building the patch needs a clone of AudioXL with `patches/*.patch` applied; see
`docs/decisions/0004-patch-mod-not-own-plugin.md`.

## Credits and licence

Cue data is read from the player's own game; no game audio is redistributed.
The patch mod builds on [AudioXL](https://github.com/DigitalVixenSWE/cp2077-audio-xl)
(MIT). `prepare.exe` bundles dr_libs, stb_vorbis and libebur128.
