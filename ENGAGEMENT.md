# Engagement log (shared by the build + research autopilots)

Source: Buffer `list_posts` (LinkedIn channel, includeMetrics). Times in Asia/Colombo. Metrics lag ~24h;
posts < 2 days old are marked *incomplete*. Last pulled: 2026-11-27 14:30 (+05:30), metrics updated 2026-11-27 04:46 (+05:30).

## Metrics table

| date | type | day / time | topic | hook style | media | link in body | tags | CTA q | impr | reach | react | comm | ER% | video views | watch min | viewers | watch s/viewer |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-26 | research | Thu 19:30 | Sinhala vs Singlish in open LLMs (IIT paper) *incomplete (<2d)* | relatable SL fact ("Most Sri Lankans don't type Sinhala in Sinhala.") | none | source line, no URL | 4 | yes | 137 | 91 | 1 | 1 | 1.46 | - | - | - | - |
| 2026-11-25 | research | Wed 19:30 | lean Linux browser / engine choice | personal intent ("I wanted to build a lean browser") | none | source line, no URL | 3 | yes | 65 | 45 | 0 | 0 | 0.00 | - | - | - | - |
| 2026-11-24 | build | Tue 22:00 | Hermes Native: iOS app built on Linux (fallback, new) | contrarian ("You need a Mac to ship an iOS app.") | terminal reel 24s | yes, end | 3 | yes (either/or) | 55 | 26 | 2 | 0 | 3.64 | 11 | 1.07 | 9 | ~7 |
| 2026-11-20 | build | Fri 19:30 | Tanka + Jedach Fuel API (fallback; same project already posted twice in March) | contrast ("Three apps. Zero shared data.") | keynote reel 27s | yes, end | 3 | yes | 56 | 25 | 1 | 1 | 3.57 | 20 | 8.50 | 11 | ~46 |
| 2026-11-17 | build | Tue 22:00 | Gruv finance app (fallback, never posted before) | contrarian fact ("SL doesn't have open banking") | keynote reel 28s | yes, end | 3 | yes (open "what's missing") | 1036 | 597 | 18 | 5 | 2.22 | 337 | 92.7 | 316 | ~18 |
| 2026-05-01 | legacy | Fri 13:01 | digital identity / e-signature rabbit hole | story question | image | no | 15 | yes | 177 | 83 | 4 | 0 | 2.26 | - | - | - | - |
| 2026-04-08 | legacy | Wed 23:17 | LinkedIn Learning cert | auto | none | yes | 1 | no | 141 | 71 | 6 | 1 | 4.96 | - | - | - | - |
| 2026-04-08 | legacy | Wed 22:53 | LinkedIn Learning cert | auto | none | yes | 1 | no | 106 | 56 | 6 | 1 | 6.60 | - | - | - | - |
| 2026-03-19 | legacy | Thu 22:02 | Tanka launch announcement | "Tomorrow I'm open sourcing" | none | yes, 2 links | 15 | no | 35 | 11 | 1 | 0 | 2.86 | - | - | - | - |
| 2026-03-18 | legacy | Wed 23:12 | Jedach Fuel API overnight build | "I spent tonight building" | none | yes, 2 links | 0 | no | 305 | 159 | 4 | 1 | 1.64 | - | - | - | - |
| 2026-02-28 | legacy | Sat 12:29 | first CTF, 20th place | all-caps win | none | no | 0 | no | 189 | 103 | 9 | 0 | 4.76 | - | - | - | - |
| 2026-02-28 | legacy | Sat 11:31 | "AI is not here to replace SWEs" essay | all-caps opinion | none | yes | 19 | no | 323 | 219 | 1 | 0 | 0.31 | - | - | - | - |
| 2026-01-08 | legacy | Thu 23:12 | free Opal quiz tool | "I've been experimenting" | none | yes | 7 | no | 413 | 221 | 6 | 3 | 2.18 | - | - | - | - |


## Current best-known patterns (early signals; n = 3 autopilot build posts + 2 research posts)
- **Gruv is the outlier, not the baseline.** Every other autopilot post sits at 55-137 impr / 25-91 reach. Gruv: 1036 / 597.
  Timing is now ruled out as the main driver (see Hermes grade below). "Fresh topic" alone is not enough either (Hermes was fresh).
- **Leading hypothesis now: broad, relatable everyday problem > niche dev-infra.** The two best non-legacy posts are both
  "Sri Lankan everyday life" hooks (Gruv: no open banking, 597 reach; Sinhala/Singlish research: 91 reach). The niche
  developer posts (iOS-on-Linux CI, Linux browser engines, fuel API repeat) all sit at 25-45 reach. Still n=6, so: early signal.
- **Reels: watch time per viewer collapsed on the terminal look** (~7s/viewer on Hermes vs ~18s Gruv keynote, ~46s Tanka keynote). n=1 per look; don't conclude yet, but the terminal look is not proven.
- **Reach per post is low (25-91) outside Gruv**, so the first-hour engagement that triggers wider distribution isn't happening.
  Comments only came on Gruv (5, open "what would you want X to do" question) and 1 each on Tanka/Sinhala. Either/or CTAs (Hermes, browser) got 0.
- Text-only research posts reach about as far as reel build posts (45-91 vs 25-26), so the reel by itself isn't buying distribution.
- Hashtag soup (15-19 tags) never helped (legacy). 3-4 tags is fine.

## Experiments
| post | variable changed (vs current best = Gruv) | hypothesis | result |
|---|---|---|---|
| 2026-11-24 hermes-native | **Posting slot back to Tue 22:00** (Gruv's slot, vs Tanka's Fri 19:30). Held constant: never-posted project, reel, link at end, 3 tags, specific either/or CTA. Unavoidable confound: playbook look rotation (terminal look instead of keynote). | If Tanka's collapse was mainly topic fatigue/timing, a fresh topic at Gruv's slot should land in the Gruv range (>=300 impr, >=150 reach). If it lands near Tanka (<100), the drop is something else (e.g. reach throttling after 2 posts in 3 days, or the account's baseline is ~150 and Gruv was the outlier). | **Not confirmed.** 55 impr / 26 reach / 0 comments, same as Tanka. Slot is not the driver; the baseline is ~50-140 and Gruv was the outlier. Next suspect: topic breadth (niche dev infra vs everyday problem) and format. |
| 2026-11-27 reflow | **Format: LinkedIn document carousel (10 pages, poster look) instead of a reel.** Held constant: never-posted project, link at end, 3 tags, Gruv-style open "what's missing" CTA, problem-first hook. Deliberate topic choice (not the experiment variable): a relatable everyday problem (study timetables) over niche infra (TANI), applying the leading hypothesis. Time back to the playbook default Fri 19:30 (timing ruled out as a driver). | Carousels earn swipes (dwell) that LinkedIn rewards. If this beats the last two build reels clearly (>=100 impr or >=50 reach) and gets >=1 comment, the static carousel + relatable topic combo is worth repeating. If it lands at ~25 reach, format isn't the lever and the account just needs more first-hour engagement (Senul replying/commenting early). | grade next run |

## Next ideas to test (one at a time)
- Link out of body ("repo on my profile") vs link at end.
- Hook: number-first ("16 hours.") vs contrarian fact.
- Keynote vs poster vs terminal reel looks (watch s/viewer), once there are 2+ posts per look.
- Hook: personal story first line ("I built this for my own exams") vs problem statement.
- TANI (next fallback) framed as an everyday problem, not an architecture diagram.
