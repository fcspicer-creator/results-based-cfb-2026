# Results-Only FBS Rankings

Free public GitHub Pages site. The model uses only completed game results.

Updates Mondays at 15:00 UTC (8 a.m. Mountain Standard Time), through December 7, 2026. The final update includes conference championships, excludes bowls/playoffs and Army–Navy, and disables the scheduled workflow after successful publication. GitHub may delay scheduled runs.

Run locally: `pip install -r requirements.txt`, then `python build.py --refresh`. For the initial frozen snapshot: `python build.py --as-of 2026-11-04T06:00:00+00:00`.

The complete initial report is INITIAL_EVIDENCE.md. Website team details contain every win/loss, scores, opponent records, location, and model points. Downloads include all rankings, per-game evidence, input scores, and the model. All model weights are unchanged from the report: conference coefficient 0.06.

Failed data or calculation checks prevent deployment and preserve the previous live site. Known incomplete past games cause failure for human review; postponed/canceled games may need source correction. ESPN is used to reconcile recent finals but scoreboard coverage is not guaranteed exhaustive. No paid API keys or services are needed.

To run manually: Actions → Update rankings and publish → Run workflow. Initial publishing uses frozen validated data; scheduled/manual refresh downloads results. To stop early: open that workflow’s menu and choose Disable workflow.
