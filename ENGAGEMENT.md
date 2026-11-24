# Engagement log (shared by the build + research autopilots)

Source: Buffer `list_posts` (LinkedIn channel, includeMetrics). Times in Asia/Colombo. Metrics lag ~24h;
posts < 2 days old are marked *incomplete*. Last pulled: 2026-11-24 14:20 (+05:30), metrics updated 2026-11-24 07:21.

## Metrics table

| date | type | day / time | topic | hook style | media | link in body | tags | CTA q | impr | reach | react | comm | ER% | video views | watch min | viewers | watch s/viewer |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-20 | build | Fri 19:30 | Tanka + Jedach Fuel API (fallback; same project already posted twice in March) | contrast ("Three apps. Zero shared data.") | keynote reel 27s | yes, end | 3 | yes | 48 | 21 | 1 | 1 | 4.17 | 18 | 8.39 | 10 | ~50 |
| 2026-11-17 | build | Tue 22:00 | Gruv finance app (fallback, never posted before) | contrarian fact ("SL doesn't have open banking") | keynote reel 28s | yes, end | 3 | yes | 960 | 570 | 13 | 3 | 1.67 | 318 | 82.37 | 302 | ~16 |
| 2026-05-01 | legacy | Fri 13:01 | digital identity / e-signature rabbit hole | story question | image | no | 15 | yes | 177 | 83 | 4 | 0 | 2.26 | - | - | - | - |
| 2026-04-08 | legacy | Wed 23:17 | LinkedIn Learning cert | auto | none | yes | 1 | no | 141 | 71 | 6 | 1 | 4.96 | - | - | - | - |
| 2026-04-08 | legacy | Wed 22:53 | LinkedIn Learning cert | auto | none | yes | 1 | no | 106 | 56 | 6 | 1 | 6.60 | - | - | - | - |
| 2026-03-19 | legacy | Thu 22:02 | Tanka launch announcement | "Tomorrow I'm open sourcing" | none | yes, 2 links | 15 | no | 35 | 11 | 1 | 0 | 2.86 | - | - | - | - |
| 2026-03-18 | legacy | Wed 23:12 | Jedach Fuel API overnight build | "I spent tonight building" | none | yes, 2 links | 0 | no | 305 | 159 | 4 | 1 | 1.64 | - | - | - | - |
| 2026-02-28 | legacy | Sat 12:29 | first CTF, 20th place | all-caps win | none | no | 0 | no | 189 | 103 | 9 | 0 | 4.76 | - | - | - | - |
| 2026-02-28 | legacy | Sat 11:31 | "AI is not here to replace SWEs" essay | all-caps opinion | none | yes | 19 | no | 323 | 219 | 1 | 0 | 0.31 | - | - | - | - |
| 2026-01-08 | legacy | Thu 23:12 | free Opal quiz tool | "I've been experimenting" | none | yes | 7 | no | 413 | 221 | 6 | 3 | 2.18 | - | - | - | - |

No research-tagged posts have been sent yet.

## Current best-known patterns (early signals, n is tiny: 2 autopilot posts)
- **Gruv (960 impr) vs Tanka (48 impr) is a 20x gap.** Same format (keynote reel, link at end, 3 tags, CTA question).
  Differences: (a) Tanka was the 3rd post about the same project (Mar 18, Mar 19, Nov 20), Gruv was new;
  (b) Tue 22:00 vs Fri 19:30; (c) Tanka went out 3 days after Gruv. Can't separate these yet.
- **Fresh topic > repeat topic** is the leading hypothesis (the March Tanka launch post also flopped at 35 impr).
- Reels get watched: Gruv 302 unique viewers out of 570 reach (~53%). Tanka viewers watched longer per head (~50s, i.e. rewatches) but tiny n.
- Hashtag soup (15-19 tags) never helped: those legacy posts sit at 35-323 impr.
- Comments are the scarce metric (max 3). Specific, opinion-inviting questions beat generic "thoughts?".
- Legacy late-night (22:00-23:15) posts did fine (305-413 impr); nothing suggests 22:00 hurts.

## Experiments
| post | variable changed (vs current best = Gruv) | hypothesis | result |
|---|---|---|---|
| 2026-11-24 hermes-native | **Posting slot back to Tue 22:00** (Gruv's slot, vs Tanka's Fri 19:30). Held constant: never-posted project, reel, link at end, 3 tags, specific either/or CTA. Unavoidable confound: playbook look rotation (terminal look instead of keynote). | If Tanka's collapse was mainly topic fatigue/timing, a fresh topic at Gruv's slot should land in the Gruv range (>=300 impr, >=150 reach). If it lands near Tanka (<100), the drop is something else (e.g. reach throttling after 2 posts in 3 days, or the account's baseline is ~150 and Gruv was the outlier). | grade next run |

## Next ideas to test (one at a time)
- Link out of body ("repo on my profile") vs link at end.
- Hook: number-first ("16 hours.") vs contrarian fact.
- Static carousel vs reel (format rotation brings this up anyway).
