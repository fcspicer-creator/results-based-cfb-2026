# Results Only CFB Rankings

Results-only rankings for FBS and FCS college football, with separate Top 25 views and combined team evidence. Version 2.5 approved for publication on November 4, 2026.

## Views

- FBS Top 25: the FBS subset of the shared résumé-score calculation.
- Team evidence: all 266 Division I teams ranked together by combined score, with subdivision labels and every game's contribution.
- FCS: retains a separately labeled FCS-only comparison; these scores are not mixed into the combined ranking.

## Subdivision adjustment

The existing results-only calculation produces initial FCS strength values and internal FBS comparison strengths. A common log-odds shift is then fitted against completed FCS–FBS game outcomes, accounting for both participating teams' initial strengths. Two balanced smoothing games (one win, one loss) avoid infinite shifts when all cross-subdivision outcomes go one way. The fitted FCS strengths are fixed while all Division I teams' combined résumé scores are calculated using the existing win/loss, margin, venue and conference rules. FCS opponents receive no FBS conference context. This is an in-sample modeling choice, not a validated prediction probability or a proof of ranking accuracy. Cross-subdivision venue imbalance is not separately fitted.

Every Division I win uses normal credit with the adjusted opponent strength. No flat FCS-win cap remains. Non-Division I wins earn exactly 0.05 total points with no margin/road bonus and do not increase the unbeaten bonus. Every loss remains negative. Any undefeated Division I team, FBS or FCS, receives 0.11 times wins over FBS opponents squared. Wins over FCS or non-Division I opponents do not increase it. Any loss removes it.

The separate FCS-only view retains its own calculation and game ledger, with the same FBS-opponent-only unbeaten-bonus rule. Its opponent strengths and scores can differ from the combined view, as explicitly labeled on the site.

## Data and operation

SportsDataverse provides FBS inputs. ESPN season-specific membership and individual team regular-season schedules supply FCS coverage. Reciprocal FCS games must agree, and shared FBS games must match existing final scores. Team IDs join sources. Canceled/postponed games are listed in fcs_coverage.json and excluded until final. These checks do not independently establish source completeness.

Use `python build.py --snapshot` to rebuild saved results offline, or `python build.py --refresh` for live results. Dependencies are in requirements.txt. Tests in the build reconcile records and points, validate dates and coverage, require convergence, and check shuffled-input stability. Eight weight variations show FBS sensitivity ranges.

The update schedule is Mondays at 15:00 UTC (8 a.m. MST), ending after December 7, 2026. Army–Navy and postseason playoff/bowl games are excluded. No paid API keys are required. A failed build preserves the prior live site.

Downloads include combined_rankings.csv, full_rankings.csv (FBS), fcs_rankings.csv (FCS-only), game_evidence.csv (combined), fcs_game_evidence.csv (FCS-only), full report JSON, inputs, coverage metadata and calculation source. INITIAL_EVIDENCE.md is an archived pre-FCS-treatment report, not the current draft methodology.
