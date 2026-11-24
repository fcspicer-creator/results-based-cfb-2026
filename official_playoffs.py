"""Read the NCAA's published bracket, isolated from all ranking calculations.
Never infer a committee seed or a winner from model ratings or regular-season games.
"""
import copy
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urljoin

SOURCES = {d: f'https://www.ncaa.com/brackets/football/{d}/2026' for d in ('fbs', 'fcs')}
SELECTION = {'fcs': '2026-11-22T17:00:00+00:00', 'fbs': '2026-12-06T17:00:00+00:00'}
EXPECTED = {'fbs': (12, 12, [4, 4, 2, 1]), 'fcs': (24, 16, [8, 8, 4, 2, 1])}
ALIASES = {'UAlbany': 'UAlbany', 'LIU': 'Long Island University', 'UIW': 'Incarnate Word', 'SFA': 'Stephen F. Austin', 'Lamar University': 'Lamar',
           'Northern Ariz.': 'Northern Arizona', 'Western Ill.': 'Western Illinois',
           'Miami (FL)': 'Miami', 'Miami (OH)': 'Miami (OH)', 'UNI': 'Northern Iowa',
           'ETSU': 'East Tennessee State', 'Southern Ill.': 'Southern Illinois'}

class NuxtData(HTMLParser):
    def __init__(self):
        super().__init__(); self.active = False; self.parts = []
    def handle_starttag(self, tag, attrs):
        if tag == 'script': self.active = dict(attrs).get('id') == '__NUXT_DATA__'
    def handle_endtag(self, tag):
        if tag == 'script': self.active = False
    def handle_data(self, data):
        if self.active: self.parts.append(data)


def championship(html):
    """Decode only the serialized public bracket; never execute page JavaScript."""
    p = NuxtData(); p.feed(html.decode() if isinstance(html, bytes) else html)
    if not p.parts: raise ValueError('Official bracket data is unavailable')
    values = json.loads(''.join(p.parts))
    memo = {}
    def decode(i):
        if i < 0: return None
        if i in memo: return memo[i]
        x = values[i]
        if isinstance(x, dict):
            result = {}; memo[i] = result
            result.update({k: decode(v) for k, v in x.items()})
        elif isinstance(x, list):
            if x and isinstance(x[0], str):
                if x[0] in ('Reactive', 'ShallowReactive', 'Ref', 'ShallowRef'):
                    result = decode(x[1])
                elif x[0] == 'Set': result = [decode(v) for v in x[1:]]
                else: raise ValueError('Unknown official bracket data encoding')
            else: result = [decode(v) for v in x]
        else: result = x
        memo[i] = result
        return result
    return decode(0)['pinia']['main']['championship']


def team_name(t):
    n = t['nameShort'].strip()
    return ALIASES.get(n, re.sub(r'\bSt\.$', 'State', n))


def parse(c, division, season=2026):
    """Keep source slot IDs and advancement edges, including actual bye positions."""
    if int(c['season']) != season or c['divisionName'].lower() != division:
        raise ValueError('Wrong official bracket season or subdivision')
    size, seed_count, counts = EXPECTED[division]
    games = [g for g in c['games'] if g['enabled']]
    field = {}; nodes = []
    for g in games:
        pos = int(g['bracketPositionId']); slots = [None, None]; scores = [None, None]; flagged = []
        for t in g['teams']:
            if not t.get('nameShort') or t['nameShort'] in ('TBA', 'TBD'): continue
            name = team_name(t); slot = 0 if t['isTop'] else 1
            if slots[slot]: raise ValueError('Duplicate official bracket slot')
            slots[slot] = name; scores[slot] = t.get('score')
            seed = int(t['seed']) if t.get('seed') else None
            if name in field and field[name]['seed'] != seed:
                raise ValueError('Conflicting official seeds')
            field[name] = dict(team=name, seed=seed, selection='Committee selection',
                               logo=urljoin('https://www.ncaa.com', t.get('logoUrl') or ''))
            if t.get('isWinner'): flagged.append(name)
        final = g.get('gameState') == 'F' or g.get('statusCodeDisplay') == 'final'
        winner = None
        if final:
            if not all(slots) or any(not isinstance(s, (int, float)) or s < 0 for s in scores) or scores[0] == scores[1]:
                raise ValueError('Official final has invalid teams or score')
            winner = slots[0 if scores[0] > scores[1] else 1]
            if flagged and flagged != [winner]: raise ValueError('Official winner disagrees with final score')
        nxt = g.get('victorBracketPositionId')
        nodes.append(dict(id=pos, contest_id=g['contestId'], round=pos // 100,
                          next=int(nxt) if nxt else None,
                          next_slot=0 if g.get('victorGamePosition') == 'Top' else 1,
                          teams=slots, winner=winner, final=final,
                          date=g.get('startDate', ''), scores=scores if final else [None, None]))
    if not field: return None  # Published empty template is not an announced field.
    if len(field) != size or sorted(t['seed'] for t in field.values() if t['seed']) != list(range(1, seed_count + 1)):
        raise ValueError('Official field is incomplete; retaining last confirmed bracket')
    if [sum(n['round'] == r for n in nodes) for r in range(1, len(counts)+1)] != counts:
        raise ValueError('Unexpected official bracket structure')
    by_id = {n['id']: n for n in nodes}
    if len(by_id) != len(nodes): raise ValueError('Duplicate bracket game ID')
    for n in nodes:
        if n['next']:
            target = by_id.get(n['next'])
            if not target or target['round'] != n['round'] + 1: raise ValueError('Invalid advancement path')
    # Initial entries are the first-round teams plus the second-round bye teams.
    incoming = {(n['next'], n['next_slot']) for n in nodes if n['next']}
    entries = [name for n in nodes for i, name in enumerate(n['teams']) if name and (n['id'], i) not in incoming]
    if len(entries) != size or set(entries) != set(field): raise ValueError('Missing or duplicated original bracket entrants')
    names = {int(r['roundNumber']): r['title'] for r in c['rounds']}
    return dict(mode='official', field=sorted(field.values(), key=lambda t: (t['seed'] or 99, t['team'])),
                nodes=nodes, round_names=names, source_url=SOURCES[division], season=season)


def render(bracket):
    """Rebuild later rounds from confirmed finals, never from an in-progress lead."""
    b = copy.deepcopy(bracket); nodes = sorted(b['nodes'], key=lambda n:n['id']); by_id = {n['id']:n for n in nodes}
    for n in nodes:
        if n['next']:
            target = by_id[n['next']]; slot = n['next_slot']; observed = target['teams'][slot]
            if observed and n['winner'] and observed != n['winner']: raise ValueError('Advancing team conflicts with official winner')
            # A later-round listing alone is not evidence that a matchup is final.
            target['teams'][slot] = n['winner']
        if n['final'] and (not all(n['teams']) or n['winner'] not in n['teams']):
            raise ValueError('Final has an unresolved preceding matchup')
    b['rounds'] = []
    for r in sorted({n['round'] for n in nodes}):
        group = [n for n in nodes if n['round'] == r]
        next_group = [n for n in nodes if n['round'] == r+1]
        indexes = {n['id']: i for i, n in enumerate(next_group)}
        b['rounds'].append(dict(name=b['round_names'].get(str(r), b['round_names'].get(r)),
                                games=[n['teams'] for n in group], winners=[n['winner'] for n in group],
                                next_indices=[indexes.get(n['next']) for n in group]))
    b['champion'] = nodes[-1]['winner']; b['completed_games'] = sum(n['final'] for n in nodes)
    return b


def update(previous, fetch, now):
    cache = copy.deepcopy(previous or {}); stamp = now.isoformat()
    for div in SOURCES:
        old = cache.get(div, {}); current = old
        if now < datetime.fromisoformat(SELECTION[div]):
            cache[div] = dict(mode='projected', checked_at=stamp)
            continue
        try:
            candidate = parse(championship(fetch(SOURCES[div])), div)
            if candidate is None:
                if old.get('mode') == 'official': raise ValueError('Official feed lost the announced field')
                current = dict(mode='projected')
            else:
                if old.get('mode') == 'official':
                    if {(t['team'], t['seed']) for t in old['field']} != {(t['team'], t['seed']) for t in candidate['field']}:
                        raise ValueError('Official field changed; retaining confirmed field for review')
                    prior = {n['id']:n for n in old['nodes']}
                    for n in candidate['nodes']:
                        p = prior[n['id']]
                        if p['next'] != n['next'] or p['next_slot'] != n['next_slot']:
                            raise ValueError('Official advancement path changed')
                        if p['final'] and not n['final']:
                            n.update(teams=p['teams'], winner=p['winner'], final=True, scores=p['scores'])
                render(candidate)  # Validate before replacing the saved bracket.
                candidate['updated_at'] = stamp
                current = candidate
            current.pop('warning', None)
        except Exception as exc:
            current = copy.deepcopy(old) or dict(mode='projected')
            current['warning'] = 'Official bracket could not be refreshed; last confirmed information is shown.'
            print(f'{div.upper()} bracket refresh retained: {exc}')
        current['checked_at'] = stamp; cache[div] = current
    return cache


def apply(projections, cache):
    result = copy.deepcopy(projections)
    for div in SOURCES:
        saved = cache.get(div, {})
        if saved.get('mode') == 'official': result[div] = render(saved)
        else:
            result[div]['mode'] = 'projected'
            for key in ('warning', 'checked_at'):
                if key in saved: result[div][key] = saved[key]
    return result
