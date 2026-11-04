"""Results-only 2026 FBS ratings; no polls, ELO, rosters, recruiting, or betting.
Run: python results_based_2026_rankings.py
Requires: pandas, numpy, requests
Can also supply 2026/2025 CSVs locally via --games-2026 and --games-2025.
"""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd

URL = 'https://raw.githubusercontent.com/sportsdataverse/cfbfastR-data/main/schedules/csv/cfb_schedules_{}.csv'


def load(year, local=None):
    src = local if local else URL.format(year)
    return pd.read_csv(src, low_memory=False)


def completed(df, cutoff=None):
    x = df.copy()
    x['start_date'] = pd.to_datetime(x['start_date'], utc=True, errors='coerce')
    done = x['completed'].astype(str).str.lower().eq('true')
    x = x.loc[done & x.home_points.notna() & x.away_points.notna()].copy()
    if cutoff is not None:
        x = x.loc[x.start_date < pd.Timestamp(cutoff, tz='UTC')].copy()
    # No pregame or postgame ratings are ever used.
    return x


def records(df):
    results = {}
    for r in df.itertuples(index=False):
        h,a = str(r.home_team),str(r.away_team)
        if r.home_points == r.away_points: continue
        w, l = (h,a) if r.home_points > r.away_points else (a,h)
        results.setdefault(w, [0,0])[0] += 1
        results.setdefault(l, [0,0])[1] += 1
    return results


def conf_postseason_2025(df):
    all_2025 = completed(df)
    rec = records(all_2025)
    # postseason games may be marked as 'postseason' depending on API schema
    post = all_2025.loc[~all_2025.season_type.astype(str).str.lower().eq('regular')].copy()
    # Limit to two FBS opponents; FCS games do not benchmark FBS conferences.
    post = post.loc[(post.home_division == 'fbs') & (post.away_division == 'fbs')]
    # Weighted victories use full-season win rate of opponent, not any ranking.
    scores, counts = {}, {}
    for r in post.itertuples(index=False):
        if r.home_points == r.away_points: continue
        if r.home_conference == r.away_conference: continue
        homewon = r.home_points > r.away_points
        wc = str(r.home_conference if homewon else r.away_conference)
        opponent = str(r.away_team if homewon else r.home_team)
        ow,ol=rec.get(opponent,(0,0))
        value=1.0 + (ow/(ow+ol) if ow+ol else 0.5)
        scores[wc]=scores.get(wc,0)+value
        counts[wc]=counts.get(wc,0)+1
    return scores,counts, len(post)


def model(df, baseline2025, cutoff, quality_weight=6.0, margin_weight=1.0, bonus_weight=0.11, conference_weight=0.06):
    x=completed(df,cutoff)
    x=x.loc[x.home_division.isin(['fbs','fcs']) & x.away_division.isin(['fbs','fcs'])].copy()
    x=x.loc[x.season_type.astype(str).str.lower().eq('regular')].copy()
    teams=set(df.loc[df.home_division=='fbs','home_team'].dropna()) | set(df.loc[df.away_division=='fbs','away_team'].dropna())
    teams=sorted(teams)
    all_teams=sorted(set(x.home_team)|set(x.away_team)|set(teams))
    div={}
    conf={}
    for r in df.itertuples(index=False):
        div[str(r.home_team)]=str(r.home_division)
        div[str(r.away_team)]=str(r.away_division)
        if str(r.home_division)=='fbs':conf[str(r.home_team)]=str(r.home_conference)
        if str(r.away_division)=='fbs':conf[str(r.away_team)]=str(r.away_conference)
    n=len(all_teams)
    ix={t:i for i,t in enumerate(all_teams)}
    won=np.zeros(n,dtype=int);lost=np.zeros(n,dtype=int)
    # game tuples: winner, loser, margin, winner away, loser home, conference info
    games=[]
    for r in x.itertuples(index=False):
        if r.home_points==r.away_points:continue
        hw=r.home_points>r.away_points
        wi=ix[str(r.home_team if hw else r.away_team)]
        li=ix[str(r.away_team if hw else r.home_team)]
        margin=abs(float(r.home_points-r.away_points))
        won[wi]+=1;lost[li]+=1
        games.append((wi,li,margin,not hw and not r.neutral_site,not hw and not r.neutral_site, str(r.home_conference),str(r.away_conference),
                      str(r.home_division),str(r.away_division)))
    # Historical baseline applies ONLY to conference context, not to individual 2025 records.
    week=int(x.week.max()) if len(x) else 1
    prior_weight=0.20*(0.80**max(0,week-1))
    max2025=max(baseline2025.values(),default=1.0)
    prior={c:v/max2025 for c,v in baseline2025.items()}
    q=np.full(n,0.5)
    raw=np.zeros(n)
    # All opponent qualities derive from 2026 played results; 2025 only tiny conference prior.
    for _ in range(1000):
        win_pts=np.zeros(n);loss_pts=np.zeros(n)
        # Conference head-to-head total opponent-adjusted wins, NOT percentage.
        cwin={}
        for wi,li,margin,away,home, hc,ac,hd,ad in games:
            wteam=all_teams[wi];lteam=all_teams[li]
            if div.get(wteam)=='fbs' and div.get(lteam)=='fbs' and conf.get(wteam)!=conf.get(lteam):
                wc=conf[wteam];cwin[wc]=cwin.get(wc,0)+ (0.5+q[li])
        maxc=max(cwin.values(),default=1.0)
        cs={c:v/maxc for c,v in cwin.items()}
        adjusted=q.copy()
        for i,t in enumerate(all_teams):
            if div.get(t)=='fbs':
                curr=cs.get(conf.get(t),0)
                past=prior.get(conf.get(t),0)
                adjusted[i]=(1-conference_weight)*q[i]+conference_weight*((1-prior_weight)*curr+prior_weight*past)
            else:
                # FCS schedules are absent: explicit common conservative quality, not an inferred record.
                adjusted[i]=0.15
        for wi,li,margin,away,home,hc,ac,hd,ad in games:
            opp=adjusted[li]
            # Diminishing margin returns; near saturation at 28, no more after 28.
            margin_bonus=margin_weight*(1-np.exp(-min(margin,28)/10.0))/(1-np.exp(-2.8))
            victory=2.0+quality_weight*opp+margin_bonus+(0.35 if away else 0)
            win_pts[wi]+=victory
            wquality=adjusted[wi]
            penalty=2.0+quality_weight*(1-wquality)+(0.30 if home else 0)
            loss_pts[li]+=penalty
        # No loser receives positive points, even for close losses.
        # Only a season with no losses qualifies for the perfect-record bonus.
        perfect=np.where(lost==0,bonus_weight*won**2,0.0)
        raw=win_pts-loss_pts+perfect
        fbs_ix=[ix[t] for t in teams if t in ix]
        values=raw[fbs_ix]
        # Smooth monotone rescaling prevents a single week of outliers from dominating recursion.
        mid=np.median(values); spread=max(8.0,float(np.std(values)))
        newq=np.clip(0.5+0.28*(raw-mid)/spread,0.04,0.96)
        # FCS games can influence quality without FCS programs entering the FBS rankings.
        newq=0.55*q+0.45*newq
        if np.max(abs(newq-q))<1e-8:
            q=newq;break
        q=newq
    else:
        raise RuntimeError('Opponent quality did not converge')
    # Recalculate component scores with converged quality.
    cwin={}
    for wi,li,_,_,_,_,_,_,_ in games:
        wteam=all_teams[wi];lteam=all_teams[li]
        if div.get(wteam)=='fbs' and div.get(lteam)=='fbs' and conf.get(wteam)!=conf.get(lteam):
            wc=conf[wteam];cwin[wc]=cwin.get(wc,0)+0.5+q[li]
    maxc=max(cwin.values(),default=1.0)
    adj=q.copy()
    for i,t in enumerate(all_teams):
        if div.get(t)=='fbs':
            adj[i]=(1-conference_weight)*q[i]+conference_weight*((1-prior_weight)*cwin.get(conf.get(t),0)/maxc+prior_weight*prior.get(conf.get(t),0))
        else:adj[i]=0.15
    winscore=np.zeros(n);lossscore=np.zeros(n)
    best={t:[] for t in teams}
    bad={t:[] for t in teams}
    for wi,li,margin,away,home,_,_,_,_ in games:
        wteam,lteam=all_teams[wi],all_teams[li]
        mb=(1-np.exp(-min(margin,28)/10))/(1-np.exp(-2.8))
        val=2+quality_weight*adj[li]+margin_weight*mb+(0.35 if away else 0)
        penalty=2+quality_weight*(1-adj[wi])+(0.30 if home else 0)
        winscore[wi]+=val;lossscore[li]+=penalty
        if wteam in best: best[wteam].append((val,lteam))
        if lteam in bad:bad[lteam].append((penalty,wteam))
    bonuses=np.where(lost==0,bonus_weight*won**2,0)
    rows=[]
    for t in teams:
        i=ix[t]
        top=sorted(best[t],reverse=True)[:3]
        worst=sorted(bad[t],reverse=True)[:2]
        rows.append(dict(team=t,conference=conf.get(t,'Unknown'),wins=won[i],losses=lost[i],
                         win_points=round(winscore[i],2),loss_penalty=round(lossscore[i],2),
                         undefeated_bonus=round(bonuses[i],2),score=float(winscore[i]-lossscore[i]+bonuses[i]),
                         best_wins='; '.join(f'{opp} (+{val:.1f})' for val,opp in top),
                         most_damaging_losses='; '.join(f'{opp} (-{val:.1f})' for val,opp in worst)))
    out=pd.DataFrame(rows).sort_values(['score','wins','team'],ascending=[False,False,True]).reset_index(drop=True)
    out.insert(0,'rank',np.arange(1,len(out)+1))
    out.attrs['quality']={t:float(adj[ix[t]]) for t in all_teams}
    out.attrs['individual_quality']={t:float(q[ix[t]]) for t in all_teams}
    out.attrs['conference_context']={c:float((1-prior_weight)*v/maxc+prior_weight*prior.get(c,0)) for c,v in cwin.items()}
    return out,cwin,week,prior_weight,len(games)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--games-2026')
    ap.add_argument('--games-2025')
    ap.add_argument('--cutoff',default='2026-11-04T07:00:00',help='UTC exclusive date; completed flag also required')
    ap.add_argument('--out',default='2026_results_based_full_rankings.csv')
    args=ap.parse_args()
    df26=load(2026,args.games_2026);df25=load(2025,args.games_2025)
    prior,post_counts,post_games=conf_postseason_2025(df25)
    out,cwin,week,weight,n=model(df26,prior,args.cutoff)
    print('2026 completed matchups included:',n,'Week:',week)
    print('2025 postseason FBS-vs-FBS games included:',post_games)
    print('2025 historical influence within conference term:',round(weight*100,2),'percent')
    print('\nTop 25:\n',out.head(25).to_string(index=False))
    print('\n2026 opponent-weighted interconference FBS win totals:',sorted(cwin.items(),key=lambda x:-x[1]))
    print('\n2025 FBS-vs-FBS postseason wins:',sorted(post_counts.items(),key=lambda x:-x[1]))
    out.to_csv(args.out,index=False)
    print('\nSaved',args.out)

if __name__=='__main__':main()
