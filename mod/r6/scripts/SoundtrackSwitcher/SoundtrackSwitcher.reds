// Two callbacks, no polling.
//
// A replaced cue ends where the game ends its own music: rescan.bat writes the game's own stop
// events into sounds.json, and AudioXL stops the track when one of them is posted. 255 of the 281
// cues have such an event. The 26 that do not are the credits, two stingers, four scene pieces and
// nineteen fragments of Kerry, the nomad bard and Johnny performing - if you replace one of those,
// your track runs until the next cue starts.
//
// Earlier versions watched every replaced cue four times a second to stop an older one when a newer
// started. Stop events made that unnecessary; see docs/decisions/0007.
//
// What is left is session end: a track still playing when the session ends leaves AudioXL holding a
// voice for it, which survives into the next session (its own SlotReport calls it ORPHANED).
module SoundtrackSwitcher

@if(ModuleExists("AudioXL"))
import AudioXL.*

@if(ModuleExists("AudioXL"))
public class SoundtrackSwitcherService extends ScriptableService {
  private cb func OnLoad() {
    let cb = GameInstance.GetCallbackSystem();
    cb.RegisterCallback(n"Session/Ready", this, n"OnSessionReady");
    cb.RegisterCallback(n"Session/BeforeEnd", this, n"OnSessionEnd");
  }

  // One line a session: enough to tell, from a user's log, whether the mod was live and how much it
  // was asked to do. The list is bound to a local because counting the call inline reported 0.
  private cb func OnSessionReady(event: ref<GameSessionEvent>) -> Void {
    if event.IsPreGame() {
      return;
    }
    let cues = SoundtrackSwitcherCues.List();
    AudioXLLog.Write("[SoundtrackSwitcher] session start: " + ToString(ArraySize(cues)) + " cue(s) replaced");
  }

  private cb func OnSessionEnd(event: ref<GameSessionEvent>) -> Void {
    if event.IsPreGame() || !AudioXLNative.Enabled() {
      return;
    }
    let cues = SoundtrackSwitcherCues.List();
    let i: Int32 = 0;
    while i < ArraySize(cues) {
      AudioXLAPI.Stop(cues[i], 0.0);   // a cue that is not playing ignores this
      i += 1;
    }
  }
}
