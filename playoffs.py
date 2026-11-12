"""2026 field projections; never feeds back into résumé scores.
Rules: collegefootballplayoff.com/sports/2024/5/29/12-team-format
ncaaorg.s3.amazonaws.com/championships/sports/football/d1/2026-27D1MFB_PreChampManual.pdf
"""
from itertools import permutations

FBS_AQ = ('ACC', 'Big Ten', 'Big 12', 'SEC')
FBS_OTHER = ('American Athletic', 'Conference USA', 'Mid-American', 'Mountain West', 'Pac-12', 'Sun Belt')
FCS_AQ = ('Big Sky', 'Coastal Athletic', 'Ivy', 'MVFC', 'NEC', 'OVC',
          'Patriot', 'Pioneer', 'Southern', 'Southland', 'UAC')
FCS_INELIGIBLE = {'Mercyhurst', 'New Haven', 'West Florida', 'West Georgia', 'Florida A&M'}
SWAC_EAST = {'Alabama A&M', 'Alabama State', 'Bethune-Cookman', 'Florida A&M',
             'Jackson State', 'Mississippi Valley State'}


def field(rows, automatic, size):
    selected = {t['team']: (t, why) for t, why in automatic}
    for t in rows:
        if len(selected) == size:
            break
        selected.setdefault(t['team'], (t, 'At-large'))
    if len(selected) != size:
        raise ValueError('Not enough eligible teams for playoff projection')
    return [dict(team=t['team'], conference=t['conference'], model_rank=t['rank'],
                 seed=i if size == 12 or i <= 16 else None, selection=why)
            for i, (t, why) in enumerate(sorted(selected.values(), key=lambda x:x[0]['rank']), 1)]


def leader(rows, conference):
    candidates = [t for t in rows if t['conference'] == conference]
    if not candidates:
        raise ValueError('Missing playoff AQ conference: ' + conference)
    return candidates[0]


def project(data):
    if data['season'] != 2026:
        raise ValueError('Playoff rules must be reviewed for a new season')
    fbs = sorted(data['teams'], key=lambda t:t['rank'])
    automatic = [(leader(fbs, c), 'Projected ' + c + ' champion') for c in FBS_AQ]
    other = next(t for t in fbs if t['conference'] in FBS_OTHER)
    automatic.append((other, 'Highest-ranked team from the other six FBS conferences'))
    nd = next((t for t in fbs if t['team'] == 'Notre Dame'), None)
    if nd and nd['rank'] <= 12:
        automatic.append((nd, 'Notre Dame top-12 provision (model rank proxy)'))
    fbs_field = field(fbs, automatic, 12)
    fs = {t['seed']:t['team'] for t in fbs_field}
    fbs_rounds = [dict(name='First round', games=[[fs[a],fs[b]] for a,b in [(8,9),(5,12),(6,11),(7,10)]]),
                  dict(name='Quarterfinals', games=[[fs[s],None] for s in [1,4,3,2]]),
                  dict(name='Semifinals', games=[[None,None]]*2),
                  dict(name='Championship', games=[[None,None]])]

    fcs = sorted((t for t in data['fcs_teams'] if t['team'] not in FCS_INELIGIBLE), key=lambda t:t['rank'])
    # Project Celebration Bowl/SWAC championship commitments using the same ranking proxy.
    unavailable = [leader(fcs, 'MEAC')['team']]
    swac = [t for t in fcs if t['conference'].startswith('SWAC')]
    for east in (True, False):
        group = [t for t in swac if (t['team'] in SWAC_EAST) == east]
        if group:
            unavailable.append(group[0]['team'])
    eligible = [t for t in fcs if t['team'] not in unavailable]
    automatic = [(leader(eligible,c), 'Projected ' + c + ' champion') for c in FCS_AQ]
    fcs_field = field(eligible, automatic, 24)
    seeded = {t['seed']:t['team'] for t in fcs_field if t['seed']}
    # Unseeded placements are illustrative, not the NCAA's geographic assignments.
    # Avoid prohibited first-round conference rematches; prefer no rematches at all.
    by_name = {t['team']:t for t in fcs}
    hosts = [seeded[s] for s in [16,9,12,13,14,11,10,15]]
    visitors = [t['team'] for t in fcs_field if t['seed'] is None]
    def cost(pair):
        a,b = (by_name[n] for n in pair)
        played = any(g['opponent'] == b['team'] for g in a['games'])
        return (1000 if played and a['conference']==b['conference'] else 0) + (10 if played else 0)
    placement = min(permutations(visitors), key=lambda p:sum(cost(x) for x in zip(hosts,p)))
    if any(cost(p)>=1000 for p in zip(hosts,placement)):
        raise ValueError('Cannot avoid prohibited FCS first-round conference rematches')
    fcs_rounds = [dict(name='First round', games=[list(p) for p in zip(hosts,placement)]),
                  dict(name='Second round', games=[[seeded[s],None] for s in [1,8,5,4,3,6,7,2]]),
                  dict(name='Quarterfinals', games=[[None,None]]*4),
                  dict(name='Semifinals', games=[[None,None]]*2),
                  dict(name='Championship', games=[[None,None]])]
    return dict(as_of=data['generated_at'], rules_season=2026,
                fbs=dict(field=fbs_field, rounds=fbs_rounds),
                fcs=dict(field=fcs_field, rounds=fcs_rounds,
                         unavailable=unavailable, ineligible=sorted(FCS_INELIGIBLE)))
