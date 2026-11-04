"""Build a validated static site. --refresh downloads current public results first."""
import argparse, csv, hashlib, io, json, math, shutil, time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen
import numpy as np
import pandas as pd
import model
import fcs

ROOT=Path(__file__).resolve().parent
SEASON=2026
FIELDS=['game_id','season','week','season_type','start_date','completed','neutral_site','home_team','home_division','home_conference','home_points','away_team','away_division','away_conference','away_points']
SOURCE=model.URL.format(SEASON)

def fetch(url):
    for attempt in range(3):
        try:
            with urlopen(Request(url,headers={'User-Agent':'ResultsOnlyFBS/1.0 (public scores)'}),timeout=40) as r:return r.read()
        except Exception:
            if attempt==2:raise
            time.sleep(2**attempt)

def normalize(df):
    if not set(FIELDS)<=set(df.columns):raise ValueError('Required source columns missing')
    df=df[FIELDS].copy()
    for c in ['completed','neutral_site']:
        df[c]=df[c].astype(str).str.lower().map({'true':True,'false':False})
        if df[c].isna().any():raise ValueError('Unknown boolean value in '+c)
    df['game_id']=pd.to_numeric(df.game_id,errors='raise').astype('int64')
    for c in ['home_points','away_points']:df[c]=pd.to_numeric(df[c],errors='coerce')
    if not df.game_id.is_unique:raise ValueError('Duplicate game IDs')
    df.start_date=pd.to_datetime(df.start_date,utc=True,errors='raise')
    if df[['home_team','away_team']].isna().any().any():raise ValueError('Missing team metadata')
    for c in ['home_division','away_division']:df[c]=df[c].fillna('other')
    return df

def refresh(previous,now):
    fresh=normalize(pd.read_csv(io.BytesIO(fetch(SOURCE))))
    if set(fresh.season.astype(int))!={SEASON}:raise ValueError('Wrong season')
    # Preserve known completed games if an upstream refresh temporarily loses them.
    fresh=fresh.set_index('game_id');old=previous.set_index('game_id')
    for gid,r in old[old.completed].iterrows():
        if gid not in fresh.index or not fresh.loc[gid,'completed']:fresh.loc[gid]=r
    reconciled=set()
    for ago in range(14):
        day=(now-timedelta(days=ago)).strftime('%Y%m%d')
        url=f'https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard?dates={day}&groups=80&limit=1000'
        events=json.loads(fetch(url))['events']
        if len(events)>=1000:raise ValueError('Scoreboard pagination required')
        for e in events:
            if not e['status']['type']['completed']:continue
            # Jan 2027 postseason belongs to season 2026; do not confuse Jan 2026.
            if int(e.get('season',{}).get('year',SEASON))!=SEASON:continue
            gid=int(e['id'])
            if gid not in fresh.index:raise ValueError(f'ESPN final {gid} missing from schedule; review required')
            for c in e['competitions'][0]['competitors']:
                side=c['homeAway'];fresh.loc[gid,side+'_points']=int(c['score'])
            fresh.loc[gid,'completed']=True;reconciled.add(gid)
    fresh=fresh.reset_index()
    if len(model.completed(fresh))<len(model.completed(previous)):raise ValueError('Completed game coverage regressed')
    return fresh,len(reconciled)

def calculate(df,old,now):
    prior,counts,post=model.conf_postseason_2025(old)
    if post!=46:raise ValueError('2025 postseason coverage changed; review required')
    # model accepts an exclusive UTC date. Completion and future-time checks apply below.
    cutoff=(now+timedelta(days=1)).strftime('%Y-%m-%d')
    done=model.completed(df,cutoff)
    done=done[(done.home_division.isin(['fbs','fcs'])|done.away_division.isin(['fbs','fcs'])) & done.season_type.eq('regular')]
    fbs_done=done[(done.home_division=='fbs')|(done.away_division=='fbs')]
    fcs_done=done[(done.home_division=='fcs')|(done.away_division=='fcs')]
    if (done.start_date>now).any():raise ValueError('A future game is marked complete')
    if len(fbs_done)<624:raise ValueError('Initial 624-game coverage regressed')
    if (done.home_points==done.away_points).any():raise ValueError('Tied final score')
    if done[['home_points','away_points']].isna().any().any() or (done[['home_points','away_points']]<0).any().any():raise ValueError('Invalid final score')
    # Refuse to silently publish an old snapshot when known past games lack final status.
    pending=df[(~df.completed)&df.season_type.eq('regular')&(df.start_date<now-timedelta(hours=12))]
    if len(pending):raise ValueError('Past games lack finals: '+', '.join(pending.game_id.astype(str)))
    out,confs,week,prior_weight,ng=model.model(df,prior,cutoff)
    if ng!=len(fbs_done) or out.attrs['all_games_count']!=len(done):raise ValueError('Some completed Division I games were omitted')
    fcs_out=out.attrs['fcs_rankings']
    if len(fcs_out)!=128:raise ValueError('FCS team coverage changed')
    records=model.records(done)
    assert len(out)==138
    qualities=out.attrs['quality'];contexts=out.attrs['conference_context']
    teams=set(out.team)|set(fcs_out.team);ledger=[]
    for g in done.itertuples():
        for side,opp in [('home','away'),('away','home')]:
            t=getattr(g,side+'_team');other=getattr(g,opp+'_team')
            if t not in teams:continue
            pf=int(getattr(g,side+'_points'));pa=int(getattr(g,opp+'_points'));win=pf>pa
            q=qualities[other];neutral=bool(g.neutral_site)
            mb=(1-math.exp(-min(abs(pf-pa),28)/10))/(1-math.exp(-2.8)) if win else 0
            location=.35 if win and side=='away' and not neutral else (-.30 if not win and side=='home' and not neutral else 0)
            points=2+6*q+mb+location if win else -(2+6*(1-q))+location
            opponent_division=getattr(g,opp+'_division')
            if win and opponent_division not in ('fbs','fcs'):points=.05
            context=6*.06*contexts.get(getattr(g,opp+'_conference'),0) if getattr(g,opp+'_division')=='fbs' else 0
            ledger.append(dict(game_id=int(g.game_id),date=g.start_date.isoformat(),team=t,division=getattr(g,side+'_division'),opponent=other,opponent_division=opponent_division,result='W' if win else 'L',points_for=pf,points_against=pa,site='neutral' if neutral else side,opponent_quality=q,game_points=points,conference_context_points=context,opponent_record='–'.join(map(str,records.get(other,[]))) if other in teams else 'Non-Division I'))
    by={t:sorted([g for g in ledger if g['team']==t],key=lambda g:g['date']) for t in teams}
    for r in pd.concat([out,fcs_out]).itertuples():
        assert tuple(records[r.team])==(r.wins,r.losses)
        assert abs(sum(g['game_points'] for g in by[r.team])+r.undefeated_bonus-r.score)<1e-8
        assert all((g['game_points']>0)==(g['result']=='W') for g in by[r.team])
    # Poll and predictive fields cannot affect output; source is allowlisted above.
    shuffled=model.model(df.sample(frac=1,random_state=17),prior,cutoff)[0]
    assert list(out.team)==list(shuffled.team)
    assert np.allclose(out.score,shuffled.score,atol=1e-8,rtol=0)
    assert list(fcs_out.team)==list(shuffled.attrs['fcs_rankings'].team)
    ranges={t:[int(r)] for t,r in zip(out.team,out['rank'])};checks=[]
    for key,base in [('quality_weight',6),('margin_weight',1),('bonus_weight',.11),('conference_weight',.06)]:
        for factor in [.8,1.2]:
            a=model.model(df,prior,cutoff,**{key:base*factor})[0]
            checks.append({'parameter':key,'factor':factor,'top25_overlap':len(set(a.head(25).team)&set(out.head(25).team)),'number_one':a.iloc[0].team})
            for r in a.itertuples():ranges[r.team].append(r.rank)
    teamrows=[];fcsrows=[]
    for r in out.to_dict('records'):
        r['games']=by[r['team']];r['min_rank']=min(ranges[r['team']]);r['max_rank']=max(ranges[r['team']]);r['conference_context_points']=sum(g['conference_context_points'] for g in r['games']);teamrows.append(r)
    for r in fcs_out.to_dict('records'):
        r['games']=by[r['team']];fcsrows.append(r)
    return dict(model_version='2.0-fcs-results',fcs_teams=fcsrows,fcs_team_count=len(fcs_out),fcs_games_count=len(fcs_done),all_d1_games_count=len(done),non_d1_games_count=int((~done.home_division.isin(['fbs','fcs'])|~done.away_division.isin(['fbs','fcs'])).sum()),season=SEASON,generated_at=now.isoformat(),latest_game=max(g['date'] for g in ledger),games_count=ng,team_count=len(out),postseason_2025_games=post,week=week,prior_weight=prior_weight,teams=teamrows,conferences=[{'conference':c,'weighted_wins':float(v),'context':contexts[c]} for c,v in sorted(confs.items(),key=lambda z:-z[1])],sensitivity=checks),out,ledger

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--refresh',action='store_true');ap.add_argument('--snapshot',action='store_true');ap.add_argument('--as-of',help='ISO UTC time for reproducible offline build');args=ap.parse_args()
    now=datetime.fromisoformat(args.as_of) if args.as_of else datetime.now(timezone.utc)
    if args.snapshot:
        stamp=json.loads((ROOT/'latest.json').read_text())['generated_at'] if (ROOT/'latest.json').exists() else '2026-11-04T06:00:00+00:00'
        now=datetime.fromisoformat(stamp)
    if args.refresh and now>=datetime(2026,12,8,tzinfo=timezone.utc):
        raise ValueError('2026 update window closed. Use --snapshot to rebuild the saved final report.')
    if now.tzinfo is None:raise ValueError('--as-of needs timezone')
    df=normalize(pd.read_csv(ROOT/'games_2026.csv'));old=normalize(pd.read_csv(ROOT/'games_2025.csv'))
    before=hashlib.sha256(df.to_csv(index=False).encode()).hexdigest();reconciled=0
    coverage=json.loads((ROOT/'fcs_coverage.json').read_text())
    if args.refresh:
        df,reconciled=refresh(df,now)
        df,coverage=fcs.collect(df,fetch)
        df=normalize(df)
    data,out,ledger=calculate(df,old,now)
    data['fcs_coverage']=coverage
    data['recent_espn_checks']=reconciled;data['refresh_mode']='live' if args.refresh else 'frozen';data['source_url']=SOURCE
    # Only write outputs after all checks succeed. Failed Actions runs preserve the live site.
    target=ROOT/'site';target.mkdir(exist_ok=True)
    encoded=json.dumps(data,allow_nan=False).replace('</','<\\/')
    html=(ROOT/'template.html').read_text().replace('__RANKINGS_DATA__',encoded)
    (target/'index.html').write_text(html);(target/'rankings.json').write_text(json.dumps(data,indent=2,allow_nan=False))
    out.to_csv(target/'full_rankings.csv',index=False);pd.DataFrame(ledger).to_csv(target/'game_evidence.csv',index=False)
    pd.DataFrame([{k:v for k,v in t.items() if k!='games'} for t in data['fcs_teams']]).to_csv(target/'fcs_rankings.csv',index=False)
    pd.DataFrame([g for g in ledger if g['division']=='fcs']).to_csv(target/'fcs_game_evidence.csv',index=False)
    (target/'fcs_coverage.json').write_text(json.dumps(coverage,indent=2))
    df.to_csv(target/'games_2026.csv',index=False);shutil.copy(ROOT/'games_2025.csv',target/'games_2025.csv')
    shutil.copy(ROOT/'model.py',target/'model.py');shutil.copy(ROOT/'fcs.py',target/'fcs.py');shutil.copy(ROOT/'INITIAL_EVIDENCE.md',target/'INITIAL_EVIDENCE.md')
    # Commit only public, result-only columns. Upstream Elo, probabilities, etc. are discarded.
    df.to_csv(ROOT/'games_2026.csv',index=False);old.to_csv(ROOT/'games_2025.csv',index=False)
    (ROOT/'latest.json').write_text(json.dumps({k:v for k,v in data.items() if k not in ('teams','fcs_teams')},indent=2))
    (ROOT/'fcs_coverage.json').write_text(json.dumps(coverage,indent=2))
    print(f'Validated {len(out)} teams and {len(ledger)} team-game entries; {data["games_count"]} games. Built site/index.html')

if __name__=='__main__':main()
