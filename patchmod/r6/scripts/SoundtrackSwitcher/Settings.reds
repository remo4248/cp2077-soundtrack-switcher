// The in-game switch, shown by Mod Settings (Settings -> Mods -> Soundtrack Switcher).
//
// Turning it off clears each replaced cue's entry in the engine's custom-sound table, so the game
// finds nothing of ours and plays its own music again; turning it on puts the entries back. A cue
// already playing stops at once, and no restart is needed either way.
//
// Without Mod Settings installed this file compiles to nothing and replacements are simply on.
module SoundtrackSwitcher

@if(ModuleExists("AudioXL"))
import AudioXL.*

@if(ModuleExists("ModSettingsModule"))
public class SoundtrackSwitcherApply extends DelayCallback {
  public let settings: wref<SoundtrackSwitcherSettings>;

  public func Call() -> Void {
    if IsDefined(this.settings) {
      this.settings.Apply();
    }
  }
}

@if(ModuleExists("ModSettingsModule"))
public class SoundtrackSwitcherSettings extends ScriptableSystem {
  @runtimeProperty("ModSettings.mod", "Soundtrack Switcher")
  @runtimeProperty("ModSettings.category", "Soundtrack Switcher")
  @runtimeProperty("ModSettings.displayName", "Replace the game's music")
  @runtimeProperty("ModSettings.description", "Off plays the game's own music again. No restart needed.")
  public let enabled: Bool = true;

  private func OnAttach() -> Void {
    ModSettings.RegisterListenerToClass(this);
    // The rows only exist once the game has set its audio up, a few seconds in, so the switch is
    // applied again then. Applying it twice costs nothing: setting a row to what it already is
    // does nothing.
    let later = new SoundtrackSwitcherApply();
    later.settings = this;
    GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(later, 20.0, false);
  }

  private func OnDetach() -> Void {
    ModSettings.UnregisterListenerToClass(this);
  }

  public cb func OnModSettingsChange() -> Void {
    this.Apply();
  }

  public func Apply() -> Void {
    let cues = SoundtrackSwitcherCues.List();
    let i: Int32 = 0;
    while i < ArraySize(cues) {
      this.SetCue(cues[i], this.enabled);
      i += 1;
    }
  }

  @if(ModuleExists("AudioXL"))
  private func SetCue(cue: CName, on: Bool) -> Void {
    AudioXLAPI.SetRowEnabled(cue, on);
  }

  @if(!ModuleExists("AudioXL"))
  private func SetCue(cue: CName, on: Bool) -> Void {}
}
