# Results-Only FBS Rankings

Free public GitHub Pages site. The model uses only completed game results.

Updates Mondays at 15:00 UTC (8 a.m. Mountain Standard Time), through December 7, 2026. The final update includes conference championships, excludes bowls/playoffs and Army–Navy, and disables the scheduled workflow after successful publication. GitHub may delay scheduled runs.

Run locally: `pip install -r requirements.txt`, then `python build.py --refresh`. For the initial frozen snapshot: `python build.py --as-of 2026-11-04T06:00:00+00:00`.

The complete initial report is INITIAL_EVIDENCE.md. Website team details contain every win/loss, scores, opponent records, location, and model points. Downloads include all rankings, per-game evidence, input scores, and the model. All model weights are unchanged from the report: conference coefficient 0.06.

Failed data or calculation checks prevent deployment and preserve the previous live site. Known incomplete past games cause failure for human review; postponed/canceled games may need source correction. ESPN is used to reconcile recent finals but scoreboard coverage is not guaranteed exhaustive. No paid API keys or services are needed.

To run manually: Actions → Update rankings and publish → Run workflow. Initial publishing uses frozen validated data; scheduled/manual refresh downloads results. To stop early: open that workflow’s menu and choose Disable workflow.

## Individual FCS ratings (model 2.0)

FCS teams now share the results-only recursive strength calculation with FBS teams, with separate standings. ESPN season-specific membership identifies 128 FCS programs (playoff TBA placeholders excluded). Each program's regular-season schedule is downloaded; reciprocal FCS games must agree and shared FBS games must match the existing inputs. Team IDs, not fuzzy name matching, join sources. Canceled/postponed games are recorded in `fcs_coverage.json` and do not count until completed. The source is not independently complete merely because these checks pass.

FCS opponent quality is no longer fixed at 0.15. It is calculated from that team's score using the same FBS median/spread reference as the existing model, with no FBS conference context applied to FCS teams. Results across both subdivisions are recalculated together until convergence. Sparse cross-subdivision play and capped quality values remain limitations; strength is not a predicted win probability.

A win over a non-Division I opponent earns exactly **0.05 total points**. Margin and road bonuses do not apply, and such wins do not increase the undefeated bonus. A non-Division I opponent has quality zero, so a loss costs 8 points plus 0.30 for a true home loss and removes the unbeaten bonus. The unbeaten bonus is now 0.11 × Division I wins squared for teams with no losses of any kind. Records still show all completed games. No separate elite-win bonus was added.

The FCS tab includes Top 25 standings and searchable game evidence for all 128 teams. Downloads include `fcs_rankings.csv`, `fcs_game_evidence.csv`, and source coverage. `game_evidence.csv` now includes both subdivisions. The original report is an archived historical report; current website methodology and downloadable model supersede its flat FCS assumption. Existing weights and Monday schedule remain unchanged. FCS regular-season results only are included; FCS playoff games are excluded.

`python build.py --snapshot` rebuilds the saved inputs without networking. `python build.py --refresh` refreshes both FBS and FCS sources, validates and rebuilds. Publish all required files together: `model.py`, `build.py`, `fcs.py`, `fcs_coverage.json`, `games_2026.csv`, `template.html`, and `latest.json`. The workflow saves the refreshed coverage file alongside score inputs.
