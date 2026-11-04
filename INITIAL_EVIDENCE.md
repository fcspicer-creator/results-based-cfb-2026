# Results-based FBS Top 25 — November 3, 2026

Calculated from 624 completed 2026 games (502 FBS–FBS and 122 FBS–FCS), 138 FBS teams, and all 46 recorded 2025 postseason FBS games. Tuesday Ohio–Akron and Miami (OH)–Buffalo finals were added from ESPN. No live game scores are used.

## Top 25

| Rank | Team | W–L | Score | Three most valuable wins (points) | All losses (opponents) | Sensitivity rank range |
|---:|---|---:|---:|---|---|---|
| 1 | Miami | 8–0 | 54.14 | Wake Forest (+8.3); Clemson (+7.1); Pittsburgh (+6.9) | None | 1–1 |
| 2 | Utah | 8–0 | 51.62 | Houston (+7.4); Cincinnati (+7.2); Iowa State (+6.3) | None | 2–2 |
| 3 | UCLA | 8–0 | 50.33 | Oregon (+7.0); Wisconsin (+6.9); Purdue (+5.4) | None | 3–3 |
| 4 | Indiana | 8–1 | 43.21 | North Texas (+7.1); Northwestern (+6.9); Michigan (+6.7) | Ohio State 15–19 | 4–4 |
| 5 | Kentucky | 7–1 | 38.27 | LSU (+7.3); South Carolina (+6.6); Oklahoma (+6.5) | Alabama 17–45 | 5–5 |
| 6 | Georgia | 7–1 | 36.17 | Alabama (+7.9); Florida (+7.3); Oklahoma (+6.5) | Auburn 24–27 | 6–6 |
| 7 | BYU | 7–1 | 35.74 | Notre Dame (+7.5); Arizona (+7.3); Iowa State (+6.0) | UCF 31–39 | 7–7 |
| 8 | Texas Tech | 7–1 | 34.78 | Arizona (+7.2); Houston (+7.0); Oregon State (+6.3) | Cincinnati 24–37 | 8–9 |
| 9 | Notre Dame | 7–1 | 34.37 | Wisconsin (+7.2); North Carolina (+6.1); Purdue (+6.0) | BYU 24–28 | 9–10 |
| 10 | Texas | 6–2 | 33.93 | UTSA (+7.8); Ole Miss (+7.6); Tennessee (+7.2) | Oklahoma 24–27; Florida 24–27 | 8–13 |
| 11 | Wake Forest | 7–1 | 33.87 | Louisville (+6.3); NC State (+5.9); Stanford (+5.4) | Miami 20–33 | 10–12 |
| 12 | Boise State | 7–1 | 33.47 | Memphis (+7.5); Western Michigan (+6.8); Fresno State (+6.1) | Oregon 27–34 | 11–14 |
| 13 | USC | 7–2 | 33.36 | Ohio State (+7.8); Fresno State (+6.2); Penn State (+6.1) | Oregon 27–41; Wisconsin 7–24 | 12–13 |
| 14 | Alabama | 6–2 | 33.07 | Kentucky (+9.0); South Carolina (+7.2); Mississippi State (+6.9) | Georgia 17–20; Tennessee 10–26 | 11–14 |
| 15 | LSU | 6–2 | 32.03 | Louisiana Tech (+7.1); Clemson (+6.7); Auburn (+6.7) | Ole Miss 24–32; Kentucky 34–35 | 15–15 |
| 16 | Ole Miss | 6–2 | 30.64 | LSU (+7.8); Missouri (+7.7); Auburn (+6.4) | Florida 28–52; Texas 27–34 | 16–18 |
| 17 | Ohio State | 6–2 | 30.62 | Indiana (+8.5); Iowa (+7.9); Illinois (+6.6) | Texas 23–24; USC 18–30 | 16–17 |
| 18 | UTSA | 7–1 | 30.12 | South Florida (+6.3); Tulane (+5.9); Texas State (+5.6) | Texas 6–30 | 16–18 |
| 19 | Houston | 6–2 | 28.20 | Oklahoma State (+6.0); Oregon State (+6.0); Kansas State (+5.8) | Texas Tech 26–28; Utah 13–21 | 19–20 |
| 20 | New Mexico | 7–1 | 26.97 | North Dakota State (+6.9); Central Michigan (+4.7); San José State (+4.5) | Oklahoma 6–14 | 19–23 |
| 21 | Memphis | 7–2 | 26.89 | Army (+6.4); UNLV (+6.0); UAB (+5.3) | Boise State 20–38; Tulane 17–31 | 20–21 |
| 22 | North Dakota State | 7–2 | 26.11 | Jacksonville State (+6.7); Air Force (+6.6); Wyoming (+5.8) | UNLV 7–13; New Mexico 16–21 | 22–24 |
| 23 | Missouri | 6–2 | 25.94 | Florida (+7.4); Texas A&M (+6.2); Arkansas (+5.8) | Mississippi State 24–31; Ole Miss 3–31 | 21–24 |
| 24 | Liberty | 7–1 | 25.90 | Delaware (+5.2); Coastal Carolina (+4.8); Florida International (+4.6) | James Madison 13–20 | 22–27 |
| 25 | Iowa | 6–2 | 25.65 | Wisconsin (+7.2); Washington (+6.9); Michigan (+6.3) | Ohio State 14–31; Minnesota 10–13 | 22–27 |

## Formula and decisions

Every FBS team starts with opponent quality 0.5. Recursively calculate results, with damping, until the maximum quality change is below 1e-8. Quality is 0.5 + 0.28 × (score − FBS median)/FBS standard deviation (minimum spread 8), clipped to [0.04, 0.96].

Win credit = 2 + 6 × adjusted opponent quality + margin bonus + 0.35 for a true road win. Margin bonus = (1 − exp(−min(margin,28)/10))/(1 − exp(−2.8)), capped at 1. Loss penalty = 2 + 6 × (1 − adjusted winner quality) + 0.30 for a true home loss. Every loss is negative, regardless of opponent. No close-loss credit. Neutral sites get neither location adjustment. Perfect season bonus = 0.11 × wins², otherwise zero. Total = win credits − loss penalties + perfect bonus.

Adjusted opponent quality = 94% individual results quality + 6% conference context. Conference context uses total FBS interconference wins weighted by (0.5 + defeated opponent quality), normalized by the largest total. This rewards head-to-head conference victories and opponent quality; it deliberately rewards quantity and therefore larger conferences can benefit. Independent programs share an accounting group, not a claimed conference. No arbitrary head-to-head override: each direct result is already credited and penalized.

Conference context is 97.3156% 2026 and 2.6844% 2025 postseason baseline in week 10. Historical baseline sums interconference postseason victories weighted by 1 + opponent full-season win percentage. Same-conference postseason games are included in coverage but excluded from interconference strength. The direct historical coefficient in adjusted quality is only 0.1611%.

FCS schedule coverage is absent in the 2026 file. All FCS opponents therefore receive an explicit common quality of 0.15; no invented FCS records. This is a modeling assumption and does not distinguish strong FCS opponents. Source classification includes transitioning FBS teams. All weights are modeling choices, not empirically proven optimal weights.

## Validation and limitations

Passed duplicate-ID, no-tie, 138-team coverage, record reconciliation, score component reconciliation, shuffled-input stability, excluded-Elo/probability-column invariance, and convergence checks. Compared 25 unique completed events against ESPN scores, covering selected 2025 postseason and 2026 games. This is a spot check, not an independent audit of all 624 scores. The CSV contains no unfinished games dated before November 4 UTC; Tuesday updates were reconciled separately. Expanded audit: all 624 included 2026 games and all 46 included 2025 postseason games match ESPN final scores (368 scoreboard matches plus 302 game-summary matches). This verifies every included score; independent schedule completeness remains unverified because the scoreboard responses did not enumerate every scheduled game.

Eight one-at-a-time ±20% weight scenarios were run. Rank ranges are shown above; these are sensitivity ranges, not statistical confidence intervals. Exact middle and bubble positions should not be treated as certain.

## Conference evidence

| Group | 2026 opponent-weighted interconference win total |
|---|---:|
| Big Ten | 26.405 |
| SEC | 25.099 |
| Big 12 | 20.124 |
| ACC | 14.508 |
| American Athletic | 12.439 |
| Sun Belt | 11.002 |
| Mountain West | 8.185 |
| FBS Independents | 8.047 |
| Pac-12 | 7.822 |
| Mid-American | 5.613 |
| Conference USA | 5.002 |

## Sources and reproduction

[SportsDataverse 2026 CSV](https://raw.githubusercontent.com/sportsdataverse/cfbfastR-data/main/schedules/csv/cfb_schedules_2026.csv), [2025 CSV](https://raw.githubusercontent.com/sportsdataverse/cfbfastR-data/main/schedules/csv/cfb_schedules_2025.csv), [ESPN November 3 scoreboard](https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard?dates=20261103&groups=80&limit=1000). Elo, probabilities, and poll fields are excluded from every calculation.

Install numpy and pandas. Run `python results_based_2026_rankings.py --games-2026 games_2026.csv --games-2025 games_2025.csv --cutoff 2026-11-04T07:00:00 --out full_rankings.csv`. Saved data are a frozen snapshot, not a live feed.

Changes from recovered original: neutral-site treatment and reversed home-loss flag corrected; FCS assumption made explicit; convergence required; unrounded scores determine order; same-conference postseason wins removed from baseline; deterministic alphabetical tie resolution; weights exposed for sensitivity checks.
