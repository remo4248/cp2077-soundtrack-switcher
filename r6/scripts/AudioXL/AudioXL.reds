// AudioXL - merge mods audio-metadata additions into the game's metadata at load. (｡◕‿◕｡)

module AudioXL

import Codeware.*
import Codeware.Localization.*

@if(ModuleExists("RedConsole"))
import RedConsole.*

@if(ModuleExists("RedLogger"))
import RedLogger.*

public abstract class AudioXLLog {
  @if(ModuleExists("RedLogger"))
  public static func Write(line: String) -> Void {
    RedLog.Append("AudioXL", line);
  }
  @if(!ModuleExists("RedLogger"))
  public static func Write(line: String) -> Void {}
}

public class AudioXLContribution {
  public let modName: String;
  public let resourcePath: ResRef;
  
  public let listOn: array<String>;
  public let resource: ref<audioCookedMetadataResource>;
  public let spliced: Bool;
}

public class AudioXLBank {
  public let name: CName;
  public let resourcePath: ResRef;
  public let resident: Bool;
  public let added: Bool;
}

public class AudioXLEvent {
  public let name: CName;
  public let wwiseId: Uint32;
  public let added: Bool;
}

public native class AudioXLNative extends IScriptable {
  public static native func Available() -> Bool
  public static native func Status() -> String
  
  public static native func IsResourceRequested(path: ResRef) -> Bool
  
  public static native func HttpAllowed() -> Bool
  public static native func HttpStatus() -> String        
  
  public static native func Poll() -> Int32               
  public static native func PendingRemote() -> Int32       
  
  public static native func StreamTitle(name: CName) -> String
  
  public static native func RegisterSound(name: CName, type: CName, path: String, gain: Float, pitch: Float, distance: Float) -> Bool
  
  public static native func RegisterSoundEx(name: CName, type: CName, path: String, gain: Float, pitch: Float, distance: Float, loop: Bool, fadeIn: Float, fadeOut: Float, start: Float, end: Float, rate: Float, stream: Bool) -> Bool
  public static native func Mute(name: CName) -> Bool     
  public static native func LoadManifest(path: String) -> Int32   
  
  public static native func Stop(name: CName, fadeOut: Float) -> Bool
  public static native func SetGain(name: CName, gain: Float) -> Bool
  public static native func IsPlaying(name: CName) -> Bool
  
  public static native func PlayFrom(name: CName, seconds: Float) -> Bool
  public static native func Position(name: CName) -> Float            
  
  public static native func Pause(name: CName, fadeOut: Float) -> Float
  
  public static native func Enabled() -> Bool
  public static native func WwiseId(name: CName) -> Uint32  
  
  public static native func LoadBank(path: String) -> Int32
  public static native func RetryBanks() -> Int32
  public static native func Duration(name: CName) -> Float            
  public static native func Subtitle(name: CName, locale: String) -> String   
  public static native func Speaker(name: CName) -> String   
  public static native func Has(name: CName) -> Bool      
  public static native func Count() -> Int32
  public static native func Report() -> array<String>     
  public static native func SlotReport() -> array<String> 
  
  public static native func CreateEmitter(name: CName, x: Float, y: Float, z: Float) -> Bool
  public static native func MoveEmitter(name: CName, x: Float, y: Float, z: Float) -> Bool
  
  public static native func AttachEmitter(name: CName, entity: ref<GameObject>) -> Bool
  public static native func DetachEmitter(name: CName) -> Bool
  public static native func IsEmitterAttached(name: CName) -> Bool
  public static native func AttachedEmitterCount() -> Int32
  public static native func TickEmitters() -> Int32
  public static native func SetEmitterReverb(name: CName, bus: CName, level: Float) -> Bool   
  public static native func PlayOn(emitter: CName, sound: CName) -> Bool
  public static native func StopOn(emitter: CName, sound: CName, fadeOut: Float) -> Bool      
  public static native func DestroyEmitter(name: CName) -> Bool
  public static native func DestroyAllEmitters() -> Int32
  public static native func HasEmitter(name: CName) -> Bool
  public static native func EmitterCount() -> Int32
}

public abstract class AudioXLPatcher {
  
  public let applied: Int32;
  public let missed: Int32;
  public let appliedEP1: Int32;
  public let missedEP1: Int32;

  public func Name() -> String { return "unnamed patcher"; }
  public func Apply(md: ref<audioCookedMetadataResource>) -> Void {}
  
  public func ApplyEP1(md: ref<audioCookedMetadataResource>) -> Void {}
}

public abstract class AudioXLAPI {
  
  public static func Register(modName: String, resource: ResRef, opt listOn: array<String>) -> Void {
    let sys = AudioXLSystem.Get();
    if !IsDefined(sys) {
      AudioXLLog.Write(s"too early to register '\(modName)'");
      return;
    }
    let c = new AudioXLContribution();
    c.modName = modName;
    c.resourcePath = resource;
    c.listOn = listOn;
    sys.Add(c);
  }

  public static func RegisterBank(name: CName, resource: ResRef, opt resident: Bool) -> Void {
    let sys = AudioXLSystem.Get();
    if !IsDefined(sys) {
      AudioXLLog.Write(s"too early to register bank '\(name)'");
      return;
    }
    sys.AddBank(name, resource, resident);
  }

  public static func RegisterEvent(name: CName) -> Void {
    let sys = AudioXLSystem.Get();
    if !IsDefined(sys) {
      AudioXLLog.Write(s"too early to register event '\(name)'");
      return;
    }
    sys.AddEvent(name, AudioXLNative.WwiseId(name));
  }

  public static func PlayLine(name: CName, opt entityID: EntityID, opt speaker: CName) -> Bool {
    let gi = GetGameInstance();
    let chosen: CName = AudioXLAPI.ResolveVariant(name, gi);
    if !AudioXLNative.Has(chosen) {
      AudioXLLog.Write(s"PlayLine: no row for \(name)");
      return false;
    }
    if EntityID.IsDefined(entityID) {
      GameInstance.GetAudioSystem(gi).Play(chosen, entityID, speaker);
    } else {
      GameInstance.GetAudioSystem(gi).Play(chosen);
    }
    let locale: String = NameToString(LocalizationSystem.GetInstance(gi).GetSubtitleLanguage());
    let text: String = AudioXLNative.Subtitle(chosen, locale);
    if StrLen(text) > 0 {
      let who: String = AudioXLNative.Speaker(chosen);
      if StrLen(who) == 0 { who = NameToString(speaker); }
      let dur: Float = AudioXLNative.Duration(chosen);
      if dur <= 0.0 { dur = 3.0; }
      AudioXLSubtitles.Get(gi).Show(chosen, text, who, entityID, dur);
    }
    return true;
  }

  public static func ResolveVariant(name: CName, gi: GameInstance) -> CName {
    let player = GetPlayer(gi);
    let female: Bool = IsDefined(player) && Equals(player.GetResolvedGenderName(), n"Female");
    let want: CName = StringToName(NameToString(name) + (female ? "_f" : "_m"));
    if AudioXLNative.Has(want) { return want; }
    let other: CName = StringToName(NameToString(name) + (female ? "_m" : "_f"));
    if AudioXLNative.Has(other) { return other; }
    return name;
  }

  public static func FootwearSets() -> array<CName> {
    let sys = AudioXLSystem.Get();
    let empty: array<CName>;
    if !IsDefined(sys) { return empty; }
    return sys.FootwearSets();
  }

  public static func HasFootwearSet(set: CName) -> Bool {
    let sets: array<CName> = AudioXLAPI.FootwearSets();   
    return ArrayContains(sets, set);
  }

  public static func RegisterSound(modName: String, name: CName, type: CName, path: String,
                                   opt gain: Float, opt pitch: Float, opt distance: Float) -> Bool {
    let g: Float = gain > 0.0 ? gain : 1.0;
    let ok: Bool = AudioXLNative.RegisterSound(name, type, path, g, pitch, distance);
    let sys = AudioXLSystem.Get();
    if IsDefined(sys) {
      sys.NoteSound(modName, name, ok);
    }
    return ok;
  }

  public static func HttpAllowed() -> Bool {
    return AudioXLNative.HttpAllowed();
  }

  public static func HttpStatus() -> String {
    return AudioXLNative.HttpStatus();
  }

  public static func PendingStations() -> Int32 {
    return AudioXLNative.PendingRemote();
  }

  public static func StreamTitle(name: CName) -> String {
    return AudioXLNative.StreamTitle(name);
  }

  public static func Stop(name: CName, opt fadeOut: Float) -> Bool {
    return AudioXLNative.Stop(name, fadeOut);
  }

  public static func SetGain(name: CName, gain: Float) -> Bool {
    return AudioXLNative.SetGain(name, gain);
  }

  public static func IsPlaying(name: CName) -> Bool {
    return AudioXLNative.IsPlaying(name);
  }

  public static func PlayFrom(name: CName, seconds: Float) -> Bool {
    return AudioXLNative.PlayFrom(name, seconds);
  }

  public static func Position(name: CName) -> Float {
    return AudioXLNative.Position(name);
  }

  public static func Pause(name: CName, opt fadeOut: Float) -> Float {
    return AudioXLNative.Pause(name, fadeOut);
  }

  public static func Mute(modName: String, name: CName) -> Bool {
    let ok: Bool = AudioXLNative.Mute(name);
    let sys = AudioXLSystem.Get();
    if IsDefined(sys) {
      sys.NoteSound(modName, name, ok);
    }
    return ok;
  }

  public static func CreateEmitter(name: CName, pos: Vector4) -> Bool {
    return AudioXLNative.CreateEmitter(name, pos.X, pos.Y, pos.Z);
  }
  
  public static func AttachEmitter(name: CName, entity: ref<GameObject>) -> Bool {
    if !IsDefined(entity) { return false; }
    let ok: Bool = AudioXLNative.AttachEmitter(name, entity);
    if ok { AudioXLFollow.Wake(); }
    return ok;
  }

  public static func DetachEmitter(name: CName) -> Bool {
    return AudioXLNative.DetachEmitter(name);
  }

  public static func IsEmitterAttached(name: CName) -> Bool {
    return AudioXLNative.IsEmitterAttached(name);
  }

  public static func MoveEmitter(name: CName, pos: Vector4) -> Bool {
    return AudioXLNative.MoveEmitter(name, pos.X, pos.Y, pos.Z);
  }
  
  public static func SetEmitterReverb(name: CName, bus: CName, level: Float) -> Bool {
    return AudioXLNative.SetEmitterReverb(name, bus, level);
  }
  public static func PlayOn(emitter: CName, sound: CName) -> Bool {
    return AudioXLNative.PlayOn(emitter, sound);
  }
  
  public static func StopOn(emitter: CName, opt sound: CName, opt fadeOut: Float) -> Bool {
    return AudioXLNative.StopOn(emitter, sound, fadeOut);
  }
  public static func DestroyEmitter(name: CName) -> Bool {
    return AudioXLNative.DestroyEmitter(name);
  }
  public static func HasEmitter(name: CName) -> Bool {
    return AudioXLNative.HasEmitter(name);
  }

  public static func RegisterPatcher(patcher: ref<AudioXLPatcher>) -> Void {
    let sys = AudioXLSystem.Get();
    if !IsDefined(sys) {
      AudioXLLog.Write(s"too early to register patcher '\(patcher.Name())'");
      return;
    }
    sys.AddPatcher(patcher);
  }
}

public class AudioXLSystem extends ScriptableService {

  private let m_pending: array<ref<AudioXLContribution>>;
  private let m_cooked: ref<audioCookedMetadataResource>;
  private let m_cookedEP1: ref<audioCookedMetadataResource>;
  private let m_tokens: array<ref<ResourceToken>>;
  private let m_log: array<String>;
  private let m_patchers: array<ref<AudioXLPatcher>>;
  private let m_banks: array<ref<AudioXLBank>>;
  private let m_events: array<ref<AudioXLEvent>>;
  private let m_eventTable: ref<audioAudioEventArray>;
  
  private let m_askedEvents: Bool;
  private let m_askedCooked: Bool;
  private let m_askedEP1: Bool;
  
  private let m_patched: Int32;
  private let m_patchedEP1: Int32;

  public static func Get() -> ref<AudioXLSystem> {
    return GameInstance.GetScriptableServiceContainer()
      .GetService(n"AudioXL.AudioXLSystem") as AudioXLSystem;
  }

  private func Note(msg: String) -> Void {
    ArrayPush(this.m_log, msg);
    AudioXLLog.Write(s"\(msg)");
  }

  public func Report() -> String {
    let out: String = "";
    let i: Int32 = 0;
    while i < ArraySize(this.m_log) {
      out += this.m_log[i] + "\n";
      i += 1;
    }
    return out;
  }

  public func Add(c: ref<AudioXLContribution>) -> Void {
    ArrayPush(this.m_pending, c);
    this.Note(s"registered '\(c.modName)'");
    
    let t = GameInstance.GetResourceDepot().LoadResource(c.resourcePath);
    if IsDefined(t) {
      ArrayPush(this.m_tokens, t);
      
      t.RegisterCallback(this, n"OnContributionReady");
    } else {
      this.Note(s"  '\(c.modName)': LoadResource returned nothing - is the archive installed?");
    }
  }

  private cb func OnContributionReady(token: ref<ResourceToken>) -> Void {
    let c = this.MatchContribution(token.GetPath());
    if !IsDefined(c) || IsDefined(c.resource) {
      return;   
    }
    let res = token.GetResource() as audioCookedMetadataResource;
    if !IsDefined(res) {
      this.Note(s"  '\(c.modName)': resource did not load - is the archive installed?");
      return;
    }
    c.resource = res;
    this.Note(s"'\(c.modName)': contribution loaded (late path), \(ArraySize(res.entries)) entries");
    this.SpliceReady();
  }

  private cb func OnLoad() {
    let cb = GameInstance.GetCallbackSystem();
    cb.RegisterCallback(n"Resource/Load", this, n"OnResourceLoad")
      .AddTarget(ResourceTarget.Type(n"audioCookedMetadataResource"));
    cb.RegisterCallback(n"Resource/Load", this, n"OnSoundBanks")
      .AddTarget(ResourceTarget.Path(r"base\\sound\\event\\soundbanks.json"));
    cb.RegisterCallback(n"Resource/Load", this, n"OnEventTable")
      .AddTarget(ResourceTarget.Path(r"base\\sound\\event\\eventsmetadata.json"));
    this.Note("listening on Resource/Load for audioCookedMetadataResource + soundbanks.json");
    
    cb.RegisterCallback(n"Session/Ready", this, n"OnSessionReadyBanks");
    
    cb.RegisterCallback(n"Session/BeforeEnd", this, n"OnSessionEndEmitters");
    this.Note(s"native: \(AudioXLNative.Status())");
    
    this.AddEvent(n"axl_voice_2d", AudioXLNative.WwiseId(n"axl_voice_2d"));
    this.AddEvent(n"axl_music_2d", AudioXLNative.WwiseId(n"axl_music_2d"));
    this.AddEvent(n"axl_radio_2d", AudioXLNative.WwiseId(n"axl_radio_2d"));
    this.AddEvent(n"axl_sfx_2d", AudioXLNative.WwiseId(n"axl_sfx_2d"));
    this.AddEvent(n"axl_master_2d", AudioXLNative.WwiseId(n"axl_master_2d"));
    this.AddEvent(n"axl_radioport_2d", AudioXLNative.WwiseId(n"axl_radioport_2d"));
    
    this.AddEvent(n"axl_radio_3d", AudioXLNative.WwiseId(n"axl_radio_3d"));
    this.AddEvent(n"axl_radio_veh3d", AudioXLNative.WwiseId(n"axl_radio_veh3d"));

    this.RequestMetadata(true);
  }

  private cb func OnInitialize() {
    this.RequestMetadata(false);
  }

  private func RequestMetadata(onlyIfRequested: Bool) -> Void {
    let depot = GameInstance.GetResourceDepot();
    let when: String = onlyIfRequested ? "at OnLoad, already requested by another mod" : "at OnInitialize";

    let events: ResRef = r"base\\sound\\event\\eventsmetadata.json";
    if !this.m_askedEvents && !IsDefined(this.m_eventTable)
       && (!onlyIfRequested || AudioXLNative.IsResourceRequested(events)) {
      this.m_askedEvents = true;
      this.Note(s"requesting the events table (\(when))");
      let et = depot.LoadResource(events);
      if IsDefined(et) {
        ArrayPush(this.m_tokens, et);
        et.RegisterCallback(this, n"OnEventTableReady");
      }
    }

    let base: ResRef = r"base\\sound\\metadata\\cooked_metadata.audio_metadata";
    if !this.m_askedCooked && !IsDefined(this.m_cooked)
       && (!onlyIfRequested || AudioXLNative.IsResourceRequested(base)) {
      this.m_askedCooked = true;
      this.Note(s"requesting the base metadata (\(when))");
      let t = depot.LoadResource(base);
      if IsDefined(t) {
        ArrayPush(this.m_tokens, t);
        t.RegisterCallback(this, n"OnCookedReady");
      } else {
        this.Note("  WARNING: could not request the base metadata");
      }
    }

    let ep1: ResRef = r"ep1\\sound\\metadata\\cooked_metadata.audio_metadata";
    if !this.m_askedEP1 && !IsDefined(this.m_cookedEP1)
       && (!onlyIfRequested || AudioXLNative.IsResourceRequested(ep1)) {
      this.m_askedEP1 = true;
      this.Note(s"requesting the EP1 metadata (\(when))");
      let e1 = depot.LoadResource(ep1);
      if IsDefined(e1) {
        ArrayPush(this.m_tokens, e1);
        e1.RegisterCallback(this, n"OnCookedEP1Ready");
      }
    }
  }

  private cb func OnResourceLoad(event: ref<ResourceEvent>) {
    let res = event.GetResource() as audioCookedMetadataResource;
    if !IsDefined(res) {
      return;
    }
    let c = this.MatchContribution(event.GetPath());
    if IsDefined(c) {
      c.resource = res;
      this.Note(s"'\(c.modName)': contribution loaded, \(ArraySize(res.entries)) entries");
      this.SpliceReady();
      return;
    }
    
    if Equals(ResRef.GetHash(event.GetPath()),
              ResRef.GetHash(r"base\\sound\\metadata\\cooked_metadata.audio_metadata")) {
      this.m_cooked = res;
      this.Note(s"base metadata via Resource/Load (EARLY path), \(ArraySize(res.entries)) entries");
      this.SpliceReady();
    } else {
      if Equals(ResRef.GetHash(event.GetPath()),
                ResRef.GetHash(r"ep1\\sound\\metadata\\cooked_metadata.audio_metadata")) {
        this.m_cookedEP1 = res;
        this.Note(s"EP1 metadata via Resource/Load (EARLY path), \(ArraySize(res.entries)) entries");
        
        this.RunPatchers();
      } else {
        this.Note(s"ignoring another audioCookedMetadataResource (\(ArraySize(res.entries)) entries)");
      }
    }
  }

  private cb func OnCookedReady(token: ref<ResourceToken>) {
    if IsDefined(this.m_cooked) {
      return;   
    }
    let res = token.GetResource() as audioCookedMetadataResource;
    if !IsDefined(res) {
      this.Note("token delivered the metadata but the cast failed");
      return;
    }
    this.m_cooked = res;
    this.Note(s"base metadata via TOKEN (late path), \(ArraySize(res.entries)) entries");
    this.SpliceReady();
  }

  private cb func OnCookedEP1Ready(token: ref<ResourceToken>) {
    if IsDefined(this.m_cookedEP1) {
      return;
    }
    let res = token.GetResource() as audioCookedMetadataResource;
    if !IsDefined(res) {
      return;   
    }
    this.m_cookedEP1 = res;
    this.Note(s"EP1 metadata via TOKEN (late path), \(ArraySize(res.entries)) entries");
    this.RunPatchers();
  }

  private func SpliceReady() -> Void {
    if !IsDefined(this.m_cooked) {
      return;
    }
    let i: Int32 = 0;
    while i < ArraySize(this.m_pending) {
      let c = this.m_pending[i];
      if !c.spliced && IsDefined(c.resource) {
        c.spliced = true;
        let n: Int32 = 0;
        let j: Int32 = 0;
        while j < ArraySize(c.resource.entries) {
          ArrayPush(this.m_cooked.entries, c.resource.entries[j]);
          n += 1;
          j += 1;
        }
        this.Note(s"'\(c.modName)': spliced \(n) entries, base now \(ArraySize(this.m_cooked.entries))");
        this.ApplyListOn(c);
      }
      i += 1;
    }
    
    this.RunPatchers();
  }

  public func NoteSound(modName: String, name: CName, ok: Bool) -> Void {
    if ok {
      this.Note(s"'\(modName)': sound \(name) registered (\(AudioXLNative.Count()) rows)");
    } else {
      this.Note(s"'\(modName)': sound \(name) NOT registered - see red4ext/logs/AudioXL");
    }
  }

  public func AddBank(name: CName, resource: ResRef, resident: Bool) -> Void {
    let b = new AudioXLBank();
    b.name = name;
    b.resourcePath = resource;
    b.resident = resident;
    ArrayPush(this.m_banks, b);
    this.Note(s"registered bank '\(name)'");
  }

  private cb func OnSoundBanks(event: ref<ResourceEvent>) {
    let res = event.GetResource() as SoundBanksJson;
    if !IsDefined(res) {
      return;
    }
    let before: Int32 = ArraySize(res.soundBanks);
    let i: Int32 = 0;
    while i < ArraySize(this.m_banks) {
      let b = this.m_banks[i];
      if !b.added {
        b.added = true;
        let e: SoundBankEntry;
        e.name = b.name;
        e.isResident = b.resident;
        e.resourcePath = b.resourcePath;
        ArrayPush(res.soundBanks, e);
      }
      i += 1;
    }
    this.Note(s"soundbanks.json: \(before) banks -> \(ArraySize(res.soundBanks)) after our additions");
  }

  private cb func OnSessionReadyBanks(event: ref<GameSessionEvent>) -> Void {
    let n: Int32 = AudioXLNative.RetryBanks();
    if n > 0 {
      this.Note(s"banks: \(n) loaded at session start");
    }
  }

  private cb func OnSessionEndEmitters(event: ref<GameSessionEvent>) -> Void {
    let n: Int32 = AudioXLNative.DestroyAllEmitters();
    if n > 0 {
      this.Note(s"emitters: \(n) destroyed at session end");
    }
  }

  public func AddEvent(name: CName, wwiseId: Uint32) -> Void {
    let e = new AudioXLEvent();
    e.name = name;
    e.wwiseId = wwiseId;
    ArrayPush(this.m_events, e);
    this.Note(s"registered event '\(name)' (wwiseId \(wwiseId))");
    if IsDefined(this.m_eventTable) {
      this.AddPendingEvents();
    }
  }

  private cb func OnEventTable(event: ref<ResourceEvent>) {
    let res = event.GetResource() as JsonResource;
    if !IsDefined(res) { return; }
    let root = res.root as audioAudioEventArray;
    if !IsDefined(root) { return; }
    this.m_eventTable = root;
    this.Note(s"events table via Resource/Load, \(ArraySize(root.events)) entries");
    this.AddPendingEvents();
  }

  private cb func OnEventTableReady(token: ref<ResourceToken>) {
    if IsDefined(this.m_eventTable) { return; }
    let res = token.GetResource() as JsonResource;
    if !IsDefined(res) { return; }
    let root = res.root as audioAudioEventArray;
    if !IsDefined(root) { return; }
    this.m_eventTable = root;
    this.Note(s"events table via TOKEN, \(ArraySize(root.events)) entries");
    this.AddPendingEvents();
  }

  private func AddPendingEvents() -> Void {
    if ArraySize(this.m_eventTable.events) == 0 { return; }
    let added: Int32 = 0;
    let i: Int32 = 0;
    while i < ArraySize(this.m_events) {
      let e = this.m_events[i];
      if !e.added {
        e.added = true;
        let row = this.m_eventTable.events[0];
        row.redId = e.name;
        row.wwiseId = e.wwiseId;
        ArrayPush(this.m_eventTable.events, row);
        added += 1;
      }
      i += 1;
    }
    if added > 0 {
      this.Note(s"events table: +\(added), now \(ArraySize(this.m_eventTable.events)) entries");
    }
  }

  public func AddPatcher(patcher: ref<AudioXLPatcher>) -> Void {
    ArrayPush(this.m_patchers, patcher);
    this.Note(s"registered patcher '\(patcher.Name())'");
    
    this.RunPatchers();
  }

  private func RunPatchers() -> Void {
    if IsDefined(this.m_cooked) {
      while this.m_patched < ArraySize(this.m_patchers) {
        let p = this.m_patchers[this.m_patched];
        this.m_patched += 1;
        p.Apply(this.m_cooked);
        if p.missed > 0 {
          this.Note(s"  patcher '\(p.Name())': \(p.applied) records edited, \(p.missed) NOT FOUND");
        } else {
          this.Note(s"  patcher '\(p.Name())': \(p.applied) records edited");
        }
      }
    }
    if IsDefined(this.m_cookedEP1) {
      while this.m_patchedEP1 < ArraySize(this.m_patchers) {
        let p = this.m_patchers[this.m_patchedEP1];
        this.m_patchedEP1 += 1;
        p.ApplyEP1(this.m_cookedEP1);
        
        if p.missedEP1 > 0 {
          this.Note(s"  patcher '\(p.Name())': EP1 \(p.appliedEP1) records edited, \(p.missedEP1) NOT FOUND");
        } else {
          if p.appliedEP1 > 0 {
            this.Note(s"  patcher '\(p.Name())': EP1 \(p.appliedEP1) records edited");
          }
        }
      }
    }
  }

  public func FindRecord(md: ref<audioCookedMetadataResource>, name: CName) -> ref<audioAudioMetadata> {
    if !IsDefined(md) {
      return null;
    }
    let i: Int32 = 0;
    while i < ArraySize(md.entries) {
      if Equals(md.entries[i].name, name) {
        return md.entries[i];
      }
      i += 1;
    }
    return null;
  }

  private func MatchContribution(path: ResRef) -> ref<AudioXLContribution> {
    let i: Int32 = 0;
    let hit: ref<AudioXLContribution>;
    while i < ArraySize(this.m_pending) {
      if Equals(ResRef.GetHash(this.m_pending[i].resourcePath), ResRef.GetHash(path)) {
        hit = this.m_pending[i];
      }
      i += 1;
    }
    return hit;
  }

  private func ApplyListOn(c: ref<AudioXLContribution>) -> Void {
    let listed: Int32 = 0;
    let dupes: Int32 = 0;
    let i: Int32 = 0;
    while i < ArraySize(c.listOn) {
      let pair: String = c.listOn[i];
      if StrContains(pair, "=") {
        let matName: CName = StringToName(StrBeforeFirst(pair, "="));
        let recName: CName = StringToName(StrAfterFirst(pair, "="));
        let fs = this.FindFootsteps(matName);
        if IsDefined(fs) {
          
          if !ArrayContains(fs.footwearMetadataArray, recName) {
            ArrayPush(fs.footwearMetadataArray, recName);
            listed += 1;
          } else {
            dupes += 1;
          }
        } else {
          this.Note(s"  '\(c.modName)': material \(matName) not found");
        }
      } else {
        
        this.Note(s"  '\(c.modName)': listOn entry '\(pair)' is not a pair - it must read " +
                  s"vanilla_material=your_record (e.g. lcm_footsteps_concrete=lcm_concrete_mine). " +
                  s"Only footwear records need listOn; leave it out for anything else.");
      }
      i += 1;
    }
    if listed > 0 || dupes > 0 {
      let extra: String = dupes > 0 ? s", \(dupes) already listed by another mod" : "";
      this.Note(s"  '\(c.modName)': listed on \(listed) materials" + extra);
    }
  }

  public func FootwearSets() -> array<CName> {
    let out: array<CName>;
    let i: Int32 = 0;
    while i < ArraySize(this.m_pending) {
      let c: ref<AudioXLContribution> = this.m_pending[i];
      if c.spliced {
        let j: Int32 = 0;
        while j < ArraySize(c.listOn) {
          let pair: String = c.listOn[j];
          if StrContains(pair, "=") {
            let mat: String = StrAfterFirst(StrBeforeFirst(pair, "="), "lcm_footsteps_");
            let rec: String = StrAfterFirst(pair, "=");
            let prefix: String = "lcm_" + mat + "_";
            if StrLen(mat) > 0 && StrBeginsWith(rec, prefix) {
              let set: CName = StringToName(StrAfterFirst(rec, prefix));
              if NotEquals(set, n"") && !ArrayContains(out, set) { ArrayPush(out, set); }
            }
          }
          j += 1;
        }
      }
      i += 1;
    }
    return out;
  }

  private func FindFootsteps(name: CName) -> ref<audioFootstepsMetadata> {
    let i: Int32 = 0;
    let hit: ref<audioFootstepsMetadata>;
    while i < ArraySize(this.m_cooked.entries) {
      let fs = this.m_cooked.entries[i] as audioFootstepsMetadata;
      if IsDefined(fs) && Equals(fs.name, name) {
        hit = fs;
      }
      i += 1;
    }
    return hit;
  }
}

public class AudioXLSubtitles extends ScriptableSystem {
  private let m_delay: DelayID;
  private let m_line: scnDialogLineData;
  private let m_active: Bool;

  public static func Get(gi: GameInstance) -> ref<AudioXLSubtitles> {
    return GameInstance.GetScriptableSystemsContainer(gi).Get(n"AudioXL.AudioXLSubtitles") as AudioXLSubtitles;
  }

  public func Show(name: CName, text: String, speaker: String, entityID: EntityID, duration: Float) -> Void {
    let gi = this.GetGameInstance();
    this.Hide();
    let line: scnDialogLineData;
    line.duration = duration;
    line.id = CreateCRUID(StringToUint64(NameToString(name)));
    line.isPersistent = false;
    if EntityID.IsDefined(entityID) {
      line.speaker = GameInstance.FindEntityByID(gi, entityID) as GameObject;
    }
    line.speakerName = speaker;
    line.text = text;
    line.type = scnDialogLineType.Regular;
    let board = GameInstance.GetBlackboardSystem(gi).Get(GetAllBlackboardDefs().UIGameData);
    board.SetVariant(GetAllBlackboardDefs().UIGameData.ShowDialogLine, ToVariant([line]), true);
    this.m_line = line;
    this.m_active = true;
    let cb = new AudioXLHideLineCallback();
    cb.system = this;
    this.m_delay = GameInstance.GetDelaySystem(gi).DelayCallback(cb, duration);
  }

  public func Hide() -> Void {
    let gi = this.GetGameInstance();
    if this.m_active {
      let board = GameInstance.GetBlackboardSystem(gi).Get(GetAllBlackboardDefs().UIGameData);
      board.SetVariant(GetAllBlackboardDefs().UIGameData.HideDialogLine, ToVariant([this.m_line.id]), true);
      this.m_active = false;
    }
    if NotEquals(this.m_delay, GetInvalidDelayID()) {
      GameInstance.GetDelaySystem(gi).CancelCallback(this.m_delay);
      this.m_delay = GetInvalidDelayID();
    }
  }
}

public class AudioXLHideLineCallback extends DelayCallback {
  public let system: wref<AudioXLSubtitles>;
  public func Call() -> Void {
    if IsDefined(this.system) { this.system.Hide(); }
  }
}

@if(ModuleExists("RedConsole"))
public class AudioXLStatusCmd extends RedConsoleCmd {
  public func Name() -> String { return "audioxl"; }
  public func Help() -> String { return "what AudioXL registered and spliced this session"; }
  public func Run(gi: GameInstance, args: array<String>) -> String {
    let sys = AudioXLSystem.Get();
    if !IsDefined(sys) {
      return "AudioXL system not running";
    }
    let out: String = sys.Report();
    let lines: array<String> = AudioXLNative.Report();
    let i: Int32 = 0;
    out += s"native: \(AudioXLNative.Status()), \(AudioXLNative.Count()) rows, \(AudioXLNative.EmitterCount()) emitters
";
    while i < ArraySize(lines) {
      out += lines[i] + "
";
      i += 1;
    }
    return out;
  }
}

@if(ModuleExists("RedConsole"))
public class AudioXLConsoleHook extends ScriptableService {
  private cb func OnInitialize() {
    GameInstance.GetCallbackSystem().RegisterCallback(n"Session/Ready", this, n"OnSessionReady");
  }
  private cb func OnSessionReady(event: ref<GameSessionEvent>) -> Void {
    RedConsoleAPI.Register(GetGameInstance(), new AudioXLStatusCmd());
  }
}

public class AudioXLFollowTick extends DelayCallback {
  public func Call() -> Void {
    AudioXLFollow.Run();
  }
}

public class AudioXLFollow extends ScriptableService {
  private let m_running: Bool;

  public final static func Get() -> ref<AudioXLFollow> {
    return GameInstance.GetScriptableServiceContainer().GetService(n"AudioXL.AudioXLFollow") as AudioXLFollow;
  }

  public final static func Wake() -> Void {
    let self = AudioXLFollow.Get();
    if IsDefined(self) { self.Start(); }
  }

  public final static func Run() -> Void {
    let self = AudioXLFollow.Get();
    if IsDefined(self) { self.Step(); }
  }

  private func Start() -> Void {
    if this.m_running { return; }
    this.m_running = true;
    this.Arm();
  }

  private func Arm() -> Void {
    let gi = GetGameInstance();
    let delay = GameInstance.GetDelaySystem(gi);
    if !IsDefined(delay) {
      
      this.m_running = false;
      return;
    }
    GameInstance.GetDelaySystem(gi).DelayCallback(new AudioXLFollowTick(), AudioXLFollow.Interval());
  }

  private func Step() -> Void {
    if AudioXLNative.AttachedEmitterCount() <= 0 {
      this.m_running = false;     
      return;
    }
    AudioXLNative.TickEmitters();
    this.Arm();
  }

  public final static func Interval() -> Float { return 0.033; }
}
