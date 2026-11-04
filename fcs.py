"""Fetch result-only FCS schedules, using season-specific membership and ESPN team IDs."""
import json, re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pandas as pd
CORE='https://sports.core.api.espn.com/v2/sports/football/leagues/college-football/seasons/2026/types/2/groups/{}/teams?limit=1000'
SCHEDULE='https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams/{}/schedule?season=2026&seasontype=2'

def collect(previous, fetch, cache=None):
    def membership(group):
        if cache and group==81: x=json.loads((Path(cache)/'core.json').read_text())
        else:x=json.loads(fetch(CORE.format(group)))
        if x['pageCount']!=1 or x['count']!=len(x['items']):raise ValueError('Incomplete ESPN membership list')
        return {re.search(r'/teams/(\d+)',r['$ref']).group(1) for r in x['items']}
    fcs_ids=membership(81);fbs_ids=membership(80)
    def schedule(t):
        if cache:return t,json.loads((Path(cache)/'schedules'/f'{t}.json').read_text())
        return t,json.loads(fetch(SCHEDULE.format(t)))
    with ThreadPoolExecutor(max_workers=8) as pool:schedules=dict(pool.map(schedule,sorted(fcs_ids)))
    # ESPN includes playoff placeholders in the membership endpoint; they are not programs.
    placeholders={t for t,x in schedules.items() if x['team']['location']=='TBA'}
    if any(e['competitions'][0]['status']['type']['completed'] for t in placeholders for e in schedules[t]['events']):raise ValueError('Placeholder has completed games')
    fcs_ids-=placeholders
    if len(fcs_ids)!=128:raise ValueError('2026 FCS membership changed; review required')
    old=previous.set_index('game_id');names={};divs={};confs={}
    # Crosswalk IDs to existing canonical names through shared games, never fuzzy text matches.
    for tid in sorted(fcs_ids):
        for e in schedules[tid]['events']:
            gid=int(e['id'])
            if gid not in old.index:continue
            r=old.loc[gid]
            for c in e['competitions'][0]['competitors']:
                side=c['homeAway'];t=str(c['id']);name=r[side+'_team']
                if t in names and names[t]!=name:raise ValueError('Conflicting team ID crosswalk')
                names[t]=name;divs[t]=r[side+'_division'];confs[t]=r[side+'_conference']
    for t in fcs_ids:
        if t in divs and divs[t]!='fcs':raise ValueError('FCS classification conflicts with FBS source')
        names.setdefault(t,schedules[t]['team']['location']);divs[t]='fcs'
        label=schedules[t]['team'].get('standingSummary','')
        confs.setdefault(t,label.split(' in ',1)[-1] if ' in ' in label else 'FCS Independent')
    events={};appearances={};excluded={}
    for tid in sorted(fcs_ids):
        x=schedules[tid]
        if int(x['season']['year'])!=2026:raise ValueError('Wrong FCS season')
        for e in x['events']:
            if int(e['season']['year'])!=2026 or int(e['seasonType']['type'])!=2:continue
            comp=e['competitions'][0];status=comp['status']['type'];gid=int(e['id'])
            if status['name'] in ['STATUS_CANCELED','STATUS_POSTPONED']:
                excluded[gid]=status['name'];continue
            row=dict(game_id=gid,season=2026,week=int(e['week']['number']),season_type='regular',start_date=e['date'],completed=bool(status['completed']),neutral_site=bool(comp['neutralSite']))
            for c in comp['competitors']:
                side=c['homeAway'];t=str(c['id']);division='fcs' if t in fcs_ids else ('fbs' if t in fbs_ids else 'other')
                if t in divs and divs[t]!=division:raise ValueError('Division crosswalk mismatch: '+t)
                if division=='fbs' and gid not in old.index:raise ValueError('FCS schedule contains FBS game absent from primary schedule')
                names.setdefault(t,c['team']['location']);divs[t]=division
                score=c.get('score');points=score.get('value') if isinstance(score,dict) else score
                row.update({side+'_team':names[t],side+'_division':division,side+'_conference':confs.get(t,'Non-Division I'),side+'_points':float(points) if points is not None else None})
            if gid in events and events[gid]!=row:raise ValueError('Team schedules disagree: '+str(gid))
            events[gid]=row;appearances.setdefault(gid,set()).add(tid)
    for gid,r in events.items():
        expected=sum(r[s+'_division']=='fcs' for s in ['home','away'])
        if len(appearances[gid])!=expected:raise ValueError('Missing reciprocal FCS schedule entry: '+str(gid))
        if gid in old.index and bool(old.loc[gid,'completed']) and r['completed']:
            for col in ['home_points','away_points','home_team','away_team']:
                if r[col]!=old.loc[gid,col]:raise ValueError('Existing final conflicts with FCS schedule: '+str(gid))
        if gid in old.index and bool(old.loc[gid,'completed']) and not r['completed']:
            raise ValueError('FCS source lost a known final: '+str(gid))
    extra=pd.DataFrame(events.values())
    known=previous[(previous.home_division=='fcs')|(previous.away_division=='fcs')]
    missing=set(known.loc[known.completed,'game_id'])-set(events)
    if missing:raise ValueError('FCS source omitted known finals: '+str(sorted(missing)))
    combined=pd.concat([previous[~previous.game_id.isin(extra.game_id)],extra],ignore_index=True)
    audit={'source':'ESPN season-specific FCS membership and individual regular-season schedules','source_url':CORE.format(81),'schedule_url_template':SCHEDULE,'fcs_team_count':len(fcs_ids),'schedule_games':len(events),'completed_games':int(extra.completed.sum()),'reciprocal_schedule_checks':True,'excluded_games':[{'game_id':g,'status':s} for g,s in sorted(excluded.items())],'teams':[{'id':t,'team':names[t]} for t in sorted(fcs_ids)]}
    return combined,audit
