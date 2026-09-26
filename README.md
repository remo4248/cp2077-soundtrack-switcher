# Soundtrack Switcher

Replace Cyberpunk 2077's score with your own music, one cue at a time, without
REDmod and without touching any game file. Drop a track into a folder, run a
bat, and the game plays it where its own music would have played.

## For players

1. Install **AudioXL 0.5.0 or newer**, then **SoundtrackSwitcher.zip**.
2. Open the mod's `SoundtrackSwitcher` folder, find a quest, find a cue.
3. Drop your track in. Any name, any of `.mp3`, `.ogg`, `.flac`, `.wav`.
   A name ending in `.loop` repeats until the game moves on.
4. Run `rescan.bat`. Start the game.

A folder with no track keeps the game's own music. `SoundtrackSwitcher_previews.zip`
renders the original music into each folder so you can hear it first.

`prepare.exe`, which `rescan.bat` calls, matches your track to the loudness of the
game's own music before you launch. It never touches the network, it is not code
signed (so SmartScreen may warn once), it is built by CI from `tools/prepare/`, and
deleting it only costs you the loudness matching.

## For developers

| Path | What it is |
|---|---|
| `mod/` | the mod as shipped, minus anything generated |
| `tools/` | the generator, the loudness tool, packaging, crash-dump reader |
| `docs/decisions/` | why the mod works the way it does |

```
tools\prepare\build.bat     builds prepare.exe (MSVC, no CMake)
python tools\generate.py <data> mod    rebuilds the cue tree from game data
python tools\package.py     builds the release zips into dist\
python tools\test_tools.py  runs the checks that need no game data
```

## Credits and licence

Cue data is read from the player's own game; no game audio is redistributed.
The mod plays through [AudioXL](https://github.com/DigitalVixenSWE/cp2077-audio-xl)
(MIT), whose 0.5.0 added the three things this mod needs — `stopEvents`,
`SetEnabled` and `PlayingSounds` — so the patch mod this repo used to ship is
gone; see `docs/decisions/0008-patch-mod-retired.md`.
`prepare.exe` bundles dr_libs, stb_vorbis and libebur128.
