AudioXL patch for Soundtrack Switcher
======================================

This replaces AudioXL's plugin and script with a build of AudioXL 0.4.3 that adds what
Soundtrack Switcher needs:

  stopOn        a sound can name the game's own events that end it, so a replaced track stops
                where the original would have instead of running into the next scene
  SetRowEnabled turn one sound off and back on, which is the in-game switch
  PlayingRows   one call that returns what is currently playing (no longer used by this mod,
                kept because it is part of the upstream offer)

Install AFTER AudioXL so these files win. Everything else in AudioXL is unchanged,
and the source of this build is at https://github.com/DigitalVixenSWE/cp2077-audio-xl.
AudioXL is MIT licensed; its licence is in AudioXL-LICENSE.md next to this file.

These changes are being offered to AudioXL's author. Once they are in an official release,
remove this patch and keep the official AudioXL.
