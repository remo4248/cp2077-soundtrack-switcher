// Keeps two replaced music cues from playing over each other.
//
// AudioXL swaps a cue's music for the player's own file, but the game's own "stop this cue" events
// act on the game's music objects, not on our file - so when the next cue starts, the previous file
// keeps playing underneath it. Four times a second this asks AudioXL how far into each replaced cue
// it is; anything above zero is playing, and the one with the least time played is the one that
// started last, so the others are stopped.
//
// The cue list lives in Cues.reds, which rescan.bat writes next to the player's files.
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
    this.Schedule();
  }

  private cb func OnSessionEnd(event: ref<GameSessionEvent>) -> Void {
    this.m_running = false;
    ArrayClear(this.m_fadingOut);
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
    let cues = SoundtrackSwitcherCues.List();
    let newest: CName = n"";
    let newestPos: Float = 0.0;
    let playing: array<CName>;
    let i: Int32 = 0;
    while i < ArraySize(cues) {
      let pos: Float = AudioXLAPI.Position(cues[i]);
      if pos > 0.0 {
        ArrayPush(playing, cues[i]);
        if !IsNameValid(newest) || pos < newestPos {
          newest = cues[i];
          newestPos = pos;
        }
      } else {
        ArrayRemove(this.m_fadingOut, cues[i]);   // done fading, so it may be stopped again later
      }
      i += 1;
    }
    if ArraySize(playing) > 1 {
      i = 0;
      while i < ArraySize(playing) {
        // A cue still counts as playing while it fades, so asking twice would keep restarting the
        // fade and it would never end.
        if !Equals(playing[i], newest) && !ArrayContains(this.m_fadingOut, playing[i]) {
          AudioXLAPI.Stop(playing[i], 2.0);   // seconds; the fade in is the row's fadeIn in sounds.json
          ArrayPush(this.m_fadingOut, playing[i]);
        }
        i += 1;
      }
    }
    this.Schedule();
  }
}
