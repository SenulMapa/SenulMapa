# LinkedIn autopilot — playbook

Branch `launch-reels` of SenulMapa/SenulMapa. Not the profile README (that's `main`, never touch it).
Every scheduled run starts cold: read this whole file first.

## Cadence
- **Monday** — project ideas for the week (no post).
- **Tuesday + Friday** — one LinkedIn post each. Goal: >= 2 posts/week, every week.
- Posts are scheduled in Buffer for **19:30 Asia/Colombo** (= 9:00 ET, US morning; Senul targets US remote startups).
- Autopilot starts **Fri 2026-11-20**. The Gruv post (Nov 17) was left as a Buffer DRAFT for Senul to approve
  as a pipeline check. If it's still a draft, leave it alone. Don't re-post Gruv (it's in posted.json as drafted).

## Buffer
- Org `My organization` id `6ac47acd6feb218bec4087a0`
- LinkedIn channel "Senul Mapa" id `6ac47afc6a5c39ccb62b0e04`
- Free plan: max 10 scheduled posts. Never queue more than 2 ahead.
- Create with `mode: customScheduled`, `schedulingType: automatic`, `dueAt` = same day 19:30+05:30 (if already past, next day 19:30).
- **Dedupe:** before posting, `list_posts` for the channel with status scheduled/sent over the last 2 days + next 3 days. If a post already exists in that window, do NOT add another — log "skipped (already queued)" and stop.
- Video asset URL: pin it to the commit so caches never serve an old cut:
  `https://raw.githubusercontent.com/SenulMapa/SenulMapa/<commit-sha>/reels/<slug>.mp4`
  (push first, then `curl -sI` it and confirm HTTP 200 + a content-length matching the local file before posting).
- Free plan: **no first comments** (Buffer rejects them). Put the link on its own line near the end of the post body.

## What to post about (in this order)
1. **This week's work.** Look at the last 7 days:
   - GitHub: `list_repos` for SenulMapa sorted by pushed_at; clone repos pushed in the last 7 days and read `git log --since="7 days ago"`. Public + private both count.
   - OpenViking (`viking://resources/claude-ai-memory/`, `viking://resources/claude-notes/`, `viking://resources/claude-memory/`): search for recent work.
   - Past claude.ai chats (conversation_search / recent_chats, last 7 days).
   Pick the most impressive thing he actually built/shipped/figured out. Uni coursework only if genuinely interesting.
2. **Fallback — old projects** if the week is thin. Use the lineup below, next one not in `posted.json`.

## Off limits
- Client work (HATCH, Cova/Pawsy/Day Zero, Webshell client sites, Adam/Dollars), Nautix (team project) — not without Senul saying so.
- Personal life: relationships, family, money, location details beyond "Colombo", age.
- Anything private-repo-sensitive: secrets, keys, internal URLs, the Cloudflare account id, etc.

## Voice — "max larp", but true
- Confident builder energy. Hook first line (it's all that shows before "...see more"). Short punchy lines, white space, no hashtag soup (max 3 at the end), no emoji walls (0-2).
- Frame like a founder shipping: problem -> the gnarly part -> what he did -> what's next. Lean on the "no resources, still shipped" story (iOS apps without a Mac via CI, real infra with zero budget) where it fits.
- **Hype the framing, never the facts.** Every number, user count, feature or result must be real (from README/commits/notes). No invented users, revenue, stars, or "acquired"/"raised". He's job hunting; recruiters click the repo.
- End with a soft hook (a question), then the link on its own line, then hashtags.
- 120-220 words. English. No "I'm thrilled to announce".

## The reel (every post gets one)
**Philosophy: Apple-keynote motion, benchmarked against award-winning work** (see the 8 rules in the
docstring at the top of `tools/reel.py` and follow them): one idea per shot, varied tempo, camera
language (punch-ins, montage, trio), at least one beat that ANIMATES THE MEANING, mixed transitions,
near-black + rim light, sparse synced sound (ticks, snaps, silence before the drop, chime on lockup),
product inside the first ~6s. Body copy goes in the LinkedIn post, never in the video.
- Engine: `python3 tools/reel.py projects/<slug>/spec.json` -> `reels/<slug>.mp4` (1080x1350, 30fps, ~25-30s, with score).
  ALWAYS run `--frames` first and LOOK at every still; then render and check a 2fps contact sheet
  (`ffmpeg -i reels/<slug>.mp4 -vf "fps=2,scale=180:225,tile=14x4" sheet.jpg`). If any 3 consecutive
  tiles look the same, the shot is too static: fix it.
- Reference spec: `projects/gruv/spec.json`. Durations in `beats` (0.5s). Per-scene `"in"`: whip | zoom | cut | flash.
  Scene types:
  - `type` cards [{text, beats, size?, accent?, accent_words?, kicker?}]: the statement shots. 2-3 beats each.
  - `title`: name slam + glow (the drop; score goes silent half a beat before it).
  - `morph`: the "animate the meaning" beat: a message's key words fly out into a structured record.
    Use it, or invent a better bespoke beat for the project (e.g. a counter, a before/after); add new scene types to the engine when needed.
  - `focus` {image, rect:[x0,y0,x1,y1] normalized, label?}: phone settles, camera punches into one UI detail.
  - `phone` {image}: hero phone with 3D settle. `trio` {images x3, title?}. `window` (desktop screenshot).
  - `montage` {images, beats_each:1}: fast hard cuts, tempo change.
  - `stat` {value, label}: numbers count up. `stack` {items}. `end` {line, sub, cta}: short lockup + chime.
  Rough shape: type hook (6b) -> title (6b) -> morph/bespoke (7b) -> type (3b) -> focus (6b) -> type (3b) ->
  focus/phone (5b) -> montage (5x1b) -> trio (5b) -> stack (4b) -> end (6b).
- Change `music_seed` (0, 1, 2) between consecutive posts so the score isn't identical every time.
- Visuals: use real screenshots from the repo (README images, docs/screenshots, assets). If none exist but the project is a web app with a public URL, you may screenshot it with playwright. If there are truly no visuals, build the reel from hook + title + stat + stack + end scenes (no fake UI).
- Pick `bg`/`accent` from the project's own palette.
- Fonts live in `fonts/` (Fraunces display, Schibsted Grotesk sans, JetBrains Mono).
- Commit spec + screenshots + reel to this branch: `git add projects/<slug> reels/<slug>.mp4 posted.json && git commit && git -c push.negotiate=true push origin launch-reels`. Don't commit `out/`.

## Monday ideas
- 5 project ideas sized for one week (evenings, he's a full-time uni student). Mix: 2 extending live areas, 2 fresh, 1 wildcard. Each: one-line pitch, why it's postable on LinkedIn (the demo moment), stack, day-by-day split, the "hard part" that makes it impressive.
- Ground them in his world: agent harnesses/Hermes/TANI, cybersecurity path, Sri Lanka infra problems (fuel, LMT buses, payments), Linux/Hyprland ricing, ESP32 hardware, iOS-without-a-Mac CI pipelines, AI video/creative pipelines.
- Check `ideas.md` so you don't repeat; append the week's list there.
- Deliver: send the list as the run's final message and a push notification.

## Fallback lineup (old projects, in order)
| slug | project | source | visuals |
|---|---|---|---|
| gruv | Gruv — finance app | SenulMapa/gruv-case-study | screenshots/ |
| tanka | Tanka + Jedach Fuel API — SL fuel tracker | SenulMapa/TankaPWA, jedach-fuel-api | stat: 872 stations; check repo for imgs |
| hermes-native | Hermes Native — SwiftUI iOS client built on Linux, CI-only Mac | SenulMapa/hermes-native | check repo |
| tani | TANI — multi-tenant agent platform | SenulMapa/tani | packages/frontend/projects-live.png |
| reflow | Reflow — A-level study planner + AI tutor | SenulMapa/reflow | docs/screenshots/ |
| qml-rice | qml-rice-dots — Quickshell Hyprland desktop | SenulMapa/qml-rice-dots-share | ask/none yet: stat+stack |
| personal-site | senulmapa.com | SenulMapa/senulmapa-site | screenshot live site |
| bag-counting | YOLOv8 + ByteTrack logistics counter | SenulMapa/Bag-Counting | check repo |
| onecli | OneCLI PR #541 (open-source contribution) | SenulMapa/onecli fork | stat+stack |

## Logs
- `posted.json` — append `{date, slug, topic, buffer_post_id, source: "week"|"fallback"}` after every post.
- `ideas.md` — weekly idea lists.
