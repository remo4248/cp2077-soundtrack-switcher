SOUNDTRACK SWITCHER - original music previews
=============================================

This renders original.ogg into every cue folder, so you can hear what a cue sounds
like in the game before you replace it. The audio comes from your own installed
game; nothing is downloaded and nothing is shipped with this tool.

WHAT YOU NEED
  Python 3      https://www.python.org/downloads/
  WolvenKit CLI  dotnet tool install -g WolvenKit.CLI
  ffmpeg         https://ffmpeg.org/download.html  (must be on your PATH)

WHERE TO PUT IT
  Unpack this into the Soundtrack Switcher mod, next to rescan.bat, so you end up
  with ...\AudioXL\sounds\SoundtrackSwitcher\previews\make_previews.py

HOW TO RUN IT
  Double-click make_previews.bat and give it your game folder when asked, or run:
    python make_previews.py --game "D:\Games\Cyberpunk2077"

It takes a while the first time and writes about 1.3 GB of previews. Delete any
original.ogg you do not want; rescan.bat ignores them either way.
