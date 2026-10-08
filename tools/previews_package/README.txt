SOUNDTRACK SWITCHER - original music previews
=============================================

This renders original.ogg into every cue folder, so you can hear what a cue sounds
like in the game before you replace it. The audio comes from your own installed
game; nothing is downloaded and nothing is shipped with this tool.

It works for both mods. Unpack a copy into whichever one you want previews for -
Soundtrack Switcher, Soundtrack Switcher Extras, or both, one copy each. It renders
whatever cue folders it finds beside it.

WHAT YOU NEED
  Python 3      https://www.python.org/downloads/
  WolvenKit CLI  either way, and it must be on your PATH:
                   - download WolvenKit.Console-<version>.zip from
                     https://github.com/WolvenKit/WolvenKit/releases and unpack it. It needs
                     the .NET 10 runtime: https://dotnet.microsoft.com/download
                   - or, if you have the .NET SDK: dotnet tool install -g WolvenKit.CLI
  ffmpeg         https://ffmpeg.org/download.html  (must be on your PATH)

None of this is needed to use the mod itself - only to render these previews.

WHERE TO PUT IT
  Unpack this into the Soundtrack Switcher mod, next to rescan.bat, so make_previews.bat
  sits in the same folder as cues.json. Do not install it with your mod manager - it is a
  tool you run once, not a mod. A previews sub-folder inside that folder works too.

HOW TO RUN IT
  Double-click make_previews.bat and give it your game folder when asked, or run:
    python make_previews.py --game "D:\Games\Cyberpunk2077"

In the main mod it renders 275 of the 281 cues and writes about 1.4 GB; in the extras mod
143 of the 145, about 580 MB. The few it cannot do use game audio WolvenKit will not
convert, and they are named when the run finishes. Previews of cues the game gives no
length for can run longer than the folder name says; the music is the same.

It takes a while the first time. While it runs it also needs a few GB free in your
Windows temp folder, which it clears up afterwards. Delete any
original.ogg you do not want; rescan.bat ignores them either way.
