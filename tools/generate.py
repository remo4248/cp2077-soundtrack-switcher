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


def cues(data):
    objs = parse(os.path.join(data, 'cp_music.bnk'))
    events = load(os.path.join(data, 'eventsmetadata.json'))['Data']['RootChunk']['root']['Data']['events']
    seen = {}
    for e in events:
        name = e['redId']['$value']
        if name.startswith('mus') and not EXCLUDE.search(name) and e['wwiseId'] in objs \
                and PLAY in action_types(objs, e['wwiseId']):
            seen[name] = music_ms(objs, e['wwiseId'])
    return seen


def stop_events(data):
    """{cue: [events that stop it]} - an event stops a cue when its Stop action points at the same
    music object the cue plays. Derived from the bank, so it covers cues the quests post directly as
    well as those an audio scene starts."""
    objs = parse(os.path.join(data, 'cp_music.bnk'))
    ids = {e['redId']['$value']: e['wwiseId'] for e in
           load(os.path.join(data, 'eventsmetadata.json'))['Data']['RootChunk']['root']['Data']['events']}
    stoppers = {}
    for name, wid in ids.items():
        if not name.startswith('mus') or wid not in objs: continue
        for target in action_targets(objs, wid, STOP_TYPES):
            stoppers.setdefault(target, set()).add(name)
    out = {}
    for cue in cues(data):
        found = {n for t in play_targets(objs, ids[cue]) for n in stoppers.get(t, ())} if cue in ids else set()
        if found: out[cue] = sorted(found)
    return out


def main(data, mod_root):
    root = os.path.join(mod_root, 'red4ext', 'plugins', 'AudioXL', 'sounds', 'SoundtrackSwitcher')
    titles = quest_titles(data)
    found = cues(data)
    for name, ms in sorted(found.items()):
        length = fmt(ms) if ms else 'length unknown'
        os.makedirs(os.path.join(root, folder_name(quest_of(name), titles),
                                 f'{display_name(name)} [{length}]'), exist_ok=True)
    with open(os.path.join(root, 'cues.json'), 'w', encoding='utf-8') as f:
        json.dump(sorted(found), f, indent=1)   # rescan maps a folder name back to the real event
    stops = stop_events(data)
    with open(os.path.join(root, 'stops.json'), 'w', encoding='utf-8') as f:
        json.dump(stops, f, indent=1, sort_keys=True)
    print(len(found), 'cues in', len({quest_of(n) for n in found}), 'quest folders ->', root)
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
    main(sys.argv[1], sys.argv[2])
