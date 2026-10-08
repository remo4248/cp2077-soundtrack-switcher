"""Builds the SoundtrackSwitcher folder tree: one folder per quest, one sub-folder per story music cue.

Inputs (DATA dir, extracted from the game with WolvenKit, JSON via cr2w_to_json):
  eventsmetadata.json            base\\sound\\event\\eventsmetadata.json          (audio_1_general.archive)
  cp_music.bnk                   base\\sound\\soundbanks\\cp_music.bnk            (audio_2_soundbanks.archive)
  base_journal.json, ep1_journal.json      base|ep1\\journal\\cooked_journal.journal (ep1_2_gamedata.archive)
  base_onscreens.json, ep1_onscreens.json  base|ep1\\localization\\en-us\\onscreens\\onscreens.json (lang_en_text.archive)
Usage: python generate.py <DATA> <mod root>   (mod root = the folder that holds red4ext\\)
"""
import json, os, re, sys, unicodedata
from bnk import parse, action_types, action_targets, music_ms, play_targets, PLAY, STOP_TYPES

# In-world music (bands, radios, instruments on screen), gameplay-state families (silent/stealth/combat) and dev leftovers.
EXCLUDE = re.compile(r'^mus_(radio|custom_radio|ow_|ep1_ow_|e3|test|arcade|cp_arcade)|'
                     r'source|busker|guitar|vinyl|piano|handpan|gig|concert|jukebox|emitter|party|club|dj_|'
                     r'Miles_Davis|chippin_in|elevator|roach_race|_silent|stealth', re.I)
BAD_CHARS = re.compile(r'[<>:"/\\|?*]')

# --- the extras mod: everything the mod above leaves out, except the radio ---
#
# Radio stays out (replacing it is a solved problem elsewhere), and so do dev leftovers: the E3
# demo cues, the Miles Davis test, emitter stubs and anything the bank gives no duration for.
EXTRAS_OUT = re.compile(r'^mus_(radio|custom_radio|e3|test)|jukebox|dj_|emitter|Miles_Davis|e3demo', re.I)

# What the folder is called, by family rather than by quest: these cues are how a place or a fight
# sounds, not how a mission sounds, so a player looks for "the combat beds", not for q005.
EXTRAS_GROUPS = (
    (re.compile(r'busker', re.I),                        'Buskers'),
    (re.compile(r'concert|_club|club_|party', re.I),     'Concerts and clubs'),
    (re.compile(r'guitar|piano|handpan|vinyl|chippin_in', re.I), 'Guitars, pianos and records'),
    (re.compile(r'source', re.I),                        'Source music in scenes'),
    (re.compile(r'stealth', re.I),                       'Stealth'),
    (re.compile(r'_silent$|_silent_|silent_START', re.I), 'Combat and district beds'),
    (re.compile(r'^mus_(ep1_)?ow_', re.I),               'Open world'),
    (re.compile(r'arcade|elevator|roach_race|gig', re.I), 'Arcades, elevators and gigs'),
)


def extras_group(cue):
    for pattern, folder in EXTRAS_GROUPS:
        if pattern.search(cue): return folder
    return 'Other'


def load(path):
    return json.load(open(path, encoding='utf-8'))


def quest_titles(data):
    """journal quest id -> English title"""
    loc = {}
    for f in ('base_onscreens.json', 'ep1_onscreens.json'):
        for e in load(os.path.join(data, f))['Data']['RootChunk']['root']['Data']['entries']:
            loc[e['primaryKey']] = e['femaleVariant'] or e['maleVariant']
    out = {}
    def walk(x):
        if isinstance(x, dict):
            if x.get('$type') == 'gameJournalQuest':
                key = re.sub(r'\D', '', x.get('title', {}).get('value', ''))
                if loc.get(key): out[x['id']] = loc[key]
            for v in x.values(): walk(v)
        elif isinstance(x, list):
            for v in x: walk(v)
    for f in ('base_journal.json', 'ep1_journal.json'):
        walk(load(os.path.join(data, f)))
    return out


def quest_of(event):
    """mus_q005_dex_... -> q005 ; mus_sts_wat_nid_07_... -> sts_wat_nid_07 ; mus_mq022_... -> mq022"""
    if re.match(r'mus_(mainmenu|game_menus)', event): return 'Menus'
    if re.match(r'mus_(finalboards|ep1_credits)', event): return 'Credits'
    m = re.match(r'mus_(sts_ep1_\d+|sts_[a-z]+_[a-z]+_\d+|[a-z]*q\d+)', event, re.I)
    return m.group(1).lower() if m else 'Other'


def folder_name(qid, titles):
    names = [titles[qid]] if qid in titles else sorted({t for jid, t in titles.items() if jid.startswith(qid + '_')})
    name = (f"{qid} - {', '.join(names)}" if names else qid).replace(': ', ' - ')
    # ASCII only: AudioXL opens files through narrow-string paths, which mangle accents on Windows
    return BAD_CHARS.sub('', unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode())


def display_name(cue):
    """What the folder is called: the event name without the _START that most cues carry."""
    return re.sub(r'_(START|start)$', '', cue)


def fmt(ms):
    s = round(ms / 1000)
    return f'{s // 60}m{s % 60:02d}s'


def cues(data, extras=False):
    objs = parse(os.path.join(data, 'cp_music.bnk'))
    events = load(os.path.join(data, 'eventsmetadata.json'))['Data']['RootChunk']['root']['Data']['events']
    seen = {}
    for e in events:
        name = e['redId']['$value']
        if not name.startswith('mus') or e['wwiseId'] not in objs: continue
        if PLAY not in action_types(objs, e['wwiseId']): continue
        if extras:
            # the extras mod takes what the main one leaves out, minus radio and dev leftovers,
            # and minus anything with no music behind it to replace
            if not EXCLUDE.search(name) or EXTRAS_OUT.search(name): continue
            if not music_ms(objs, e['wwiseId']): continue
        elif EXCLUDE.search(name):
            continue
        seen[name] = music_ms(objs, e['wwiseId'])
    return seen


def paired_stop(cue, events):
    """The bank also names a stop event after the cue it ends: X_START -> X_STOP, keeping whatever
    follows. Used where the match below finds nothing, which is every open world and combat bed -
    their stop acts on a parent container rather than on the object the cue plays."""
    for start, stop in (('_START', '_STOP'), ('_start', '_stop')):
        if start in cue:
            candidate = cue.replace(start, stop, 1)
            if candidate != cue and candidate in events: return candidate
    return None


def stop_events(data, extras=False):
    """{cue: [events that stop it]} - an event stops a cue when its Stop action points at the same
    music object the cue plays, or when it is the cue's name with START swapped for STOP. Derived
    from the bank, so it covers cues the quests post directly as well as those an audio scene
    starts."""
    objs = parse(os.path.join(data, 'cp_music.bnk'))
    ids = {e['redId']['$value']: e['wwiseId'] for e in
           load(os.path.join(data, 'eventsmetadata.json'))['Data']['RootChunk']['root']['Data']['events']}
    stoppers = {}
    for name, wid in ids.items():
        if not name.startswith('mus') or wid not in objs: continue
        for target in action_targets(objs, wid, STOP_TYPES):
            stoppers.setdefault(target, set()).add(name)
    out = {}
    for cue in cues(data, extras):
        found = {n for t in play_targets(objs, ids[cue]) for n in stoppers.get(t, ())} if cue in ids else set()
        if not found:
            named = paired_stop(cue, ids)
            if named: found = {named}
        if found: out[cue] = sorted(found)
    return out


def main(data, mod_root, extras=False):
    mod = 'SoundtrackSwitcherExtras' if extras else 'SoundtrackSwitcher'
    root = os.path.join(mod_root, 'red4ext', 'plugins', 'AudioXL', 'sounds', mod)
    titles = quest_titles(data)
    found = cues(data, extras)
    for name, ms in sorted(found.items()):
        length = fmt(ms) if ms else 'length unknown'
        group = extras_group(name) if extras else folder_name(quest_of(name), titles)
        os.makedirs(os.path.join(root, group, f'{display_name(name)} [{length}]'), exist_ok=True)
    with open(os.path.join(root, 'cues.json'), 'w', encoding='utf-8') as f:
        json.dump(sorted(found), f, indent=1)   # rescan maps a folder name back to the real event
    stops = stop_events(data, extras)
    with open(os.path.join(root, 'stops.json'), 'w', encoding='utf-8') as f:
        json.dump(stops, f, indent=1, sort_keys=True)
    groups = {extras_group(n) for n in found} if extras else {quest_of(n) for n in found}
    print(len(found), 'cues in', len(groups), 'folders ->', root)
    print(len(stops), 'of them have stop events (stops.json)')


if __name__ == '__main__':
    assert quest_of('mus_q005_dex_confrontation_01_p1') == 'q005'
    assert quest_of('mus_sts_wat_nid_07_facing_aaron_01_START') == 'sts_wat_nid_07'
    assert quest_of('mus_mq022_maglev_01_START') == 'mq022'
    assert EXCLUDE.search('mus_q005_the_heist_START_silent') and EXCLUDE.search('mus_ow_arasaka_START')
    assert not EXCLUDE.search('mus_q005_dex_confrontation_01_p1')
    assert quest_of('mus_sts_ep1_08_01_START') == 'sts_ep1_08' and quest_of('mus_finalboards_START') == 'Credits'
    assert not EXCLUDE.search('mus_mq301_yuri_combat_START')
    assert folder_name('q110', {'q110_x': "M'ap Tann P\u00e8len: A"}) == "q110 - M'ap Tann Pelen - A"
    assert display_name('mus_q101_js_death_01_START') == 'mus_q101_js_death_01'
    assert display_name('mus_q005_dex_confrontation_01_p1') == 'mus_q005_dex_confrontation_01_p1'
    assert fmt(191800) == '3m12s'
    _stops = stop_events(sys.argv[1])
    assert 'mus_q005_dex_confrontation_05_gunshot_end' in _stops['mus_q005_dex_confrontation_01_p1'], _stops
    assert extras_group('mus_ow_animals_START_silent') == 'Combat and district beds'
    assert extras_group('mus_ow_busker_fingers_01_start') == 'Buskers'
    assert extras_group('mus_q204_js_apartment_vinyl_01_START') == 'Guitars, pianos and records'
    assert extras_group('mus_ow_arasaka_START') == 'Open world'
    assert EXTRAS_OUT.search('mus_radio_vexelstrom_01') and EXTRAS_OUT.search('mus_e3demo_end_START')
    assert not EXTRAS_OUT.search('mus_ow_animals_START_silent')
    assert paired_stop('mus_ow_animals_START_silent', {'mus_ow_animals_STOP_silent'}) == 'mus_ow_animals_STOP_silent'
    assert paired_stop('mus_q005_dex_confrontation_01_p1', {'anything'}) is None
    main(sys.argv[1], sys.argv[2], extras='--extras' in sys.argv)
