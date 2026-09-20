# ADR-0004: Extend AudioXL as a removable patch mod, not our own plugin

## Status
Accepted (supersedes the standalone plugin in plugin/)

## Date
2026-09-20

## Context
Two things AudioXL could not do were needed: end a replacement when the game
ends its own music, and ask cheaply what is playing. The first attempt was our
own RED4ext plugin that hooked the sound engine. It crashed the game three
times - a null instance passed to the SDK, a cue list rebuilt on one thread
while another read it, and a sweep of AudioXL's voice list from the wrong
thread. Each failure came from working blind against someone else's internals.

## Decision
Build the features inside AudioXL itself, distributed as a separate patch mod
that overrides AudioXL's DLL and script, with the changes kept as a patch file
against a named upstream commit. The base mod stays installable with the
official AudioXL and never references the new calls.

## Alternatives considered
- **Our own plugin alongside AudioXL.** Two hooks on the same engine function
  and duplicated work if AudioXL ever adds the same features. Rejected after
  the crashes.
- **Fork AudioXL and ship the fork as "AudioXL".** Rejected: two different
  AudioXL.dll files in the wild is a support problem for its author and for
  every user.

## Consequences
- The patch mod must load after both AudioXL and this mod (it wins 3 files).
- Scripts using the new calls live in the patch mod only: a missing native
  breaks redscript's entire compile, taking every script mod down with it.
- When the changes land upstream, the patch mod is deleted and nothing else
  changes.
