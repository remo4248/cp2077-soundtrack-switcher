Soundtrack Switcher
Music is a very potent factor in setting a mood (check the demo video). It can completely change how a scene feels, sometimes with its own absence. This mod is to help you set the right mood and/or add a fresh twist to a play-through. 
You provide the music. No preinstalled songs. No REDmod. No game file is modified: everything this mod does happens through AudioXL's custom sounds and one script.
How it Works
Internal quest names for the folders, that hold folders for the specific cues (that's where you place your file)
.mp3, .ogg, .flac and .wav all work. Nothing has to be renamed. (WARNING: CHECK PERFORMANCE SECTION FOR INFO ABOUT STORAGE)
Loudness matched to the game's own score, so it's not too loud or quiet. 
Tracks end where the game ends its own music, with a fade. That covers 255 of the 281 cues. The other 26 have no stop event of their own, so a track there plays until the next cue starts - those 26 are the end credits, two short stingers, four scene pieces and nineteen fragments of Kerry, the nomad bard and Johnny performing.
Looping until next song (NOT TESTED SO USE WITH DISCRETION): end the filename with .loop
ON/OFF switch in Mod Settings. No restart for turning OFF, yes restart for turning ON.
Story score only. (For now...)


Requirements

RED4ext
redscript
AudioXL (0.4.3)
AudioXL patch for Soundtrack Switcher - the second file on this page. Install it after AudioXL.
Mod Settings (optional, only for the in-game on/off switch)

Why there are two downloads

AudioXL is what lets a mod play its own file where the game asked for its own music. It is excellent, and this mod would not exist without it. However there are two things it cannot do yet that this mod needs:

1. Ending your track where the scene ends. When the game finishes a piece of music it fires a stop event, but that event acts on the game's own music, not on a replacement. So without the patch your track does not stop when the scene does - it plays on through until some other cue happens to start. The patch lets a sound name the events that end it, so your track ends on the same beat the original would have, with a fade.

2. Turning replacements off in game. The on/off switch works by clearing your cues from the engine's sound table and putting them back, which is what gives you the game's own music again. AudioXL has no way to do that from outside.

Do you have to install it? The mod works without it: your tracks still play. What you lose is the ending - your track runs past the scene it belongs to until another cue starts - and the in-game switch. That first one is why the patch is listed as required rather than optional.

Installing

Install AudioXL, then SoundtrackSwitcher, then AudioXL patch for Soundtrack Switcher, in that order, so the patch wins AudioXL's two files.
Open the mod's SoundtrackSwitcher folder, find the quest, find the cue.
Drop your track into that cue's folder.
Run rescan.bat in the SoundtrackSwitcher folder. It prints what it found.
Start the game.

To undo a replacement, delete your track, run rescan.bat again, restart. A folder with no track of yours plays the game's own music.

Vortex: the mod deploys into your game folder, so everything lives at \red4ext\plugins\AudioXL\sounds\SoundtrackSwitcher. You can add rescan.bat as a tool on Vortex's dashboard (Add Tool) if you'd rather launch it from there. Your own tracks are not managed by Vortex, so updating the mod leaves them where they are. If Vortex ever asks about external changes to sounds.json or Cues.reds, keep the changed version - rescan.bat wrote those.

Mod Organizer 2: run rescan.bat straight from mods\SoundtrackSwitcher, not through MO2, so what it writes lands in the mod folder instead of Overwrite.

About prepare.exe

The mod ships a small tool called prepare.exe, and rescan.bat runs it on each track you add. It decodes your file, measures its loudness the way broadcast does (EBU R128), brings it to the level of the game's own music, limits the peaks so a quiet track can be raised without clipping, and writes the result next to your file.

It runs before you start the game, which is the whole point: nothing is decoded, measured or converted while you are playing.

It never touches the network. It reads the one file you point it at and writes one file beside it.
It is not code-signed, so Windows SmartScreen may say "Windows protected your PC" the first time, and a virus scanner may flag it simply for being an unknown new binary. Both are false positives.
The source is on GitHub and every release is built by GitHub Actions, so you can read exactly what it does, or build it yourself and drop your own build in.
You can also just delete it. The mod still works and your files are then played as they are, without loudness matching.

Add the original songs as a preview

This is useful for understanding what you are replacing, especially when there are multiple cues in a quest folder. 
The separate previews download renders the game's own music for every cue into that cue's folder as original.ogg, from your own installed game files. Nothing copyrighted is distributed. It needs WolvenKit's CLI and ffmpeg, which is why it is a separate optional file.


CRASHING
- can crash while loading a save, most often the first load after adding or changing songs. Load again and it goes through.
- it is a null dereference inside the game's own audio code, and it happens with AudioXL and any custom sound registered, with or without this mod's script, so the mod cannot catch it from the outside. Still being chased.
- Feedback is appreciated

Performance

The design rule was simple: all the expensive work happens when you run rescan.bat, none of it while you are playing.

Storage
The mod itself, with no tracks added: 2.6 MB. That is 281 cue folders, the cue data and prepare.exe.
Each track you add costs your own file plus a prepared copy at 10.6 MB per minute of audio (uncompressed 16-bit stereo; what lets the game play it without decoding anything). A 3 minute track is about 32 MB.
Ten replaced tracks is roughly 350 MB. Replacing every cue - 24.5 hours of music across the 278 whose length the game tells us - would be about 15 GB. That is the (expected) ceiling.
The optional previews download renders the game's own music into the folders: about 1.4 GB if you render all of them. Delete them when you are done comparing.

RAM
Only the cues you replaced cost anything: 10.6 MB per minute of replaced audio, the same as on disk. Four replaced tracks of about 3 minutes each is roughly 130 MB.
That memory is a file mapping, not a heap allocation - Windows backs it with the file on disk and is free to drop those pages when something else needs the RAM, then read them back.
A single file may not exceed 500 MB, which is about 47 minutes of audio.
Cues you did not replace cost nothing at all.

while playing (CPU)
Nothing of this mod runs while you play. No timer, no polling, no per-frame work. The game starts your track by name and the game's own stop event ends it; the mod's script only runs when a session starts and when it ends.
Your track is mixed as one stereo voice with no decoding, because it was converted ahead of time. It is the cheapest kind of sound the engine has.
The patch adds one atomic read per sound event the game posts, and does real work only when a track of yours is playing and the game fires the event that ends it.
Nothing in the game is wrapped, replaced or hooked in script, so no other script mod pays for this one being installed.

when loading (CPU)
Your tracks are registered once, while the game sets up audio: 22 ms for four tracks, measured. The first launch after adding a track also reads that track off disk once.
The small script files compile with everything else redscript compiles; you will not see it in the load time.
As for concrete performance impact, I didn't notice anything in my testing. Feedback is appreciated.

GPU
Nothing. The mod draws nothing at all. The on/off switch is a row in Mod Settings' existing menu.

Credits

DigitalVixen for AudioXL, which does the actual work of playing a custom sound where the game asked for its own. The patch file on this page is a build of AudioXL with the two additions described above, shared under AudioXL's MIT licence, and those additions have been offered upstream.
WopsS and the RED4ext team, jac3km4 and the redscript team, psiberx for the tooling the scene runs on.

Source and permissions

https://github.com/remo4248/cp2077-soundtrack-switcher

Do what you like with it, credit appreciated.
