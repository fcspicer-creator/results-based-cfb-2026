# Results Only CFB Rankings

Results-only rankings for FBS and FCS college football, with separate Top 25 views and combined team evidence. Version 3.1 includes the full 2026 season, through the January 2027 national championships.

## Views

- FBS Top 25: the FBS subset of the shared résumé-score calculation.
- Team evidence: all 266 Division I teams ranked together by combined score, with subdivision labels and every game's contribution.
- FCS: retains a separately labeled FCS-only comparison; these scores are not mixed into the combined ranking.

## Subdivision adjustment

The existing results-only calculation produces initial FCS strength values and internal FBS comparison strengths. A common log-odds shift is then fitted against completed FCS–FBS game outcomes, accounting for both participating teams' initial strengths. Two balanced smoothing games (one win, one loss) avoid infinite shifts when all cross-subdivision outcomes go one way. The fitted FCS strengths are fixed while all Division I teams' combined résumé scores are calculated using the existing win/loss, margin and venue rules. Neither subdivision receives a conference adjustment. The 2025 input is retained for archival compatibility but has zero influence. This is an in-sample modeling choice, not a validated prediction probability or a proof of ranking accuracy. Cross-subdivision venue imbalance is not separately fitted.

Every Division I win starts with 1 guaranteed point, plus credit for adjusted opponent strength and the existing margin/venue bonuses. Loss-penalty weights are unchanged. No flat FCS-win cap remains. Non-Division I wins earn exactly 0.05 total points with no margin/road bonus and do not increase the unbeaten bonus. Every loss remains negative. Any undefeated Division I team, FBS or FCS, receives 0.11 times wins over FBS opponents squared. Wins over FCS or non-Division I opponents do not increase it. Any loss removes it.

The separate FCS-only view retains its own calculation and game ledger, with the same FBS-opponent-only unbeaten-bonus rule. Its opponent strengths and scores can differ from the combined view, as explicitly labeled on the site.

## Data and operation

SportsDataverse provides FBS inputs. ESPN season-specific membership and individual team regular-season and postseason schedules supply FCS coverage. Reciprocal FCS games must agree, and shared FBS games must match existing final scores. Team IDs join sources. Canceled/postponed games are listed in fcs_coverage.json and excluded until final. These checks do not independently establish source completeness.

Use `python build.py --snapshot` to rebuild saved results offline, or `python build.py --refresh` for live results. Dependencies are in requirements.txt. Tests in the build reconcile records and points, validate dates and coverage, require convergence, and check shuffled-input stability. Six weight variations show FBS sensitivity ranges.

The update schedule is Sundays at 17:00 UTC (10 a.m. Mountain Standard Time), with the final update January 31, 2027, after the January 25 CFP championship. Army–Navy, bowls, and FBS/FCS playoffs are included. The 2026 season window falls entirely in Mountain Standard Time after this November 8 change. Team and conference rankings recalculate on each refresh. No paid API keys are required. A failed build preserves the prior live site.

Downloads include combined_rankings.csv, full_rankings.csv (FBS), fcs_rankings.csv (FCS-only), game_evidence.csv (combined), fcs_game_evidence.csv (FCS-only), full report JSON, inputs, coverage metadata and calculation source. INITIAL_EVIDENCE.md is an archived pre-FCS-treatment report, not the current methodology.

## Earned conference network

Only current-season, completed interconference Division I games determine conference strength. Each game is counted once. Conference nodes span FBS and FCS; independents are individual team nodes. Non-DI games and within-conference games are excluded. No margins, venue, team résumé averages, rank bonuses, historical seeds, or external ratings enter this solve.

A Colley-style linear system uses C = 2I + schedule Laplacian and b = 1 + (wins - losses)/2, then solves C r = b simultaneously. The published score is 100r. The equal neutral regularizer is not earned credit or conference reputation: it supplies two units of neutral weight to keep sparse/unbeaten samples finite. An unplayed node is 50. Equal network scores share a rank. Weakly linked or disconnected schedules limit cross-group comparability.

Team opponent strengths now derive only from team results; conference membership and the archived 2025 baseline cannot affect a team's score. Conference network strength is display-only and never fed into team calculations. Average member résumé is descriptive only. Previous-ranking columns preserve the actual previous weekly report, which may use the earlier methodology.

Method reference: [Colley's original matrix-method explanation](https://www.colleyrankings.com/matrate.pdf). This implementation applies the joint solve to conference nodes and individual independents rather than using an external team ranking.


## Playoff field projections (2026 rules)
`playoffs.py` runs on every snapshot and weekly refresh, after rankings are calculated. It never alters team scores. FBS selection uses four major-conference projected champions, the highest-ranked other-six-conference team, Notre Dame's top-12 provision, and remaining at-large teams. FCS uses its separate ranking, 11 projected champions and 13 at-large teams. The highest-ranked eligible team is the champion proxy; these are not official standings or clinched bids.

FCS excludes four reclassifying programs and Florida A&M, plus projected MEAC/SWAC postseason commitments. Unseeded placement is illustrative, avoids prohibited conference rematches and does not model travel geography. Later-round slots remain blank. The pages link current official rules. The existing Sunday schedule rebuilds both fields through January 31, 2027; after selection they remain hypothetical model fields, not official results brackets. Review eligibility and rules before reusing for another season.
