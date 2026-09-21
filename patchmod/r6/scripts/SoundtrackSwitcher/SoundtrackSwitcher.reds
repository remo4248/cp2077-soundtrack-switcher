// Same job as the shipped script, but built on AudioXLAPI.PlayingRows() - one call that returns
// everything AudioXL currently has playing. The cost then follows what is playing (normally one
// track) instead of how many cues the player replaced.
//
// NEEDS a build of AudioXL that has PlayingRows. Until that is released, ship the other version.
module SoundtrackSwitcher

@if(ModuleExists("AudioXL"))
import AudioXL.*

@if(ModuleExists("AudioXL"))
public class SoundtrackSwitcherTick extends DelayCallback {
  public let service: wref<SoundtrackSwitcherService>;

  public func Call() -> Void {
    if IsDefined(this.service) {
      this.service.Tick();
    }
  }
}

@if(ModuleExists("AudioXL"))
public class SoundtrackSwitcherService extends ScriptableService {
  private let m_running: Bool;
  private let m_fadingOut: array<CName>;

  private cb func OnLoad() {
    let cb = GameInstance.GetCallbackSystem();
    cb.RegisterCallback(n"Session/Ready", this, n"OnSessionReady");
    cb.RegisterCallback(n"Session/BeforeEnd", this, n"OnSessionEnd");
  }

  private cb func OnSessionReady(event: ref<GameSessionEvent>) -> Void {
    if event.IsPreGame() || this.m_running {
      return;
    }
    this.m_running = true;
    // One line a session: enough to tell, from a user's log, whether the mod was live and how much
    // it was asked to do. The full AudioXL slot report is in tools/diagnostics.reds when needed.
    //
    // The list is bound to a local first. Called inline inside ArraySize() this logged 0 on every
    // session of 2026-09-21 while the switch and the overlap watcher, which both bind it to a local,
    // worked on the same list.
    let watching = SoundtrackSwitcherCues.List();
    AudioXLLog.Write("[SoundtrackSwitcher] session start: watching " +
                     ToString(ArraySize(watching)) + " cue(s)");
    this.Schedule();
  }

  // A track still playing when the session ends leaves AudioXL holding a voice for it, which then
  // survives into later sessions (its own SlotReport calls it ORPHANED). Stopping our own tracks
  // here keeps that from happening, through AudioXL's public calls rather than its internals.
  private cb func OnSessionEnd(event: ref<GameSessionEvent>) -> Void {
    this.m_running = false;
    ArrayClear(this.m_fadingOut);
    if event.IsPreGame() || !AudioXLNative.Enabled() {
      return;
    }
    let cues = SoundtrackSwitcherCues.List();
    let playing = AudioXLAPI.PlayingRows();
    let i: Int32 = 0;
    while i < ArraySize(playing) {
      if ArrayContains(cues, playing[i]) {
        AudioXLAPI.Stop(playing[i], 0.0);
        AudioXLLog.Write("[SoundtrackSwitcher] session end: stopped " + NameToString(playing[i]));
      }
      i += 1;
    }
  }

  private func Schedule() -> Void {
    let tick = new SoundtrackSwitcherTick();
    tick.service = this;
    GameInstance.GetDelaySystem(GetGameInstance()).DelayCallback(tick, 0.25, false);
  }

  public func Tick() -> Void {
    if !this.m_running {
      return;   // session over: stop ticking rather than reschedule
    }
    // PlayingRows covers every AudioXL sound, including other mods' - keep only our own cues.
    let cues = SoundtrackSwitcherCues.List();
    let playing = AudioXLAPI.PlayingRows();
    let ours: array<CName>;
    let i: Int32 = 0;
    while i < ArraySize(playing) {
      if ArrayContains(cues, playing[i]) {
        ArrayPush(ours, playing[i]);
      } else {
        ArrayRemove(this.m_fadingOut, playing[i]);
      }
      i += 1;
    }
    if ArraySize(ours) < 2 {
      if ArraySize(ours) == 1 {
        ArrayRemove(this.m_fadingOut, ours[0]);   // it outlived a fade, so it may be stopped again
      } else {
        ArrayClear(this.m_fadingOut);
      }
      this.Schedule();
      return;
    }
    // The cue that started last is the one with the least time played.
    let newest: CName = ours[0];
    let newestPos: Float = AudioXLAPI.Position(ours[0]);
    i = 1;
    while i < ArraySize(ours) {
      let pos: Float = AudioXLAPI.Position(ours[i]);
      if pos > 0.0 && (newestPos <= 0.0 || pos < newestPos) {
        newest = ours[i];
        newestPos = pos;
      }
      i += 1;
    }
    i = 0;
    while i < ArraySize(ours) {
      // A cue still counts as playing while it fades, so asking twice would keep restarting the
      // fade and it would never end.
      if !Equals(ours[i], newest) && !ArrayContains(this.m_fadingOut, ours[i]) {
        AudioXLAPI.Stop(ours[i], 2.0);
        ArrayPush(this.m_fadingOut, ours[i]);
      }
      i += 1;
    }
    this.Schedule();
  }
}
