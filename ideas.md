# Weekly project ideas

## Week of 2026-11-23

Mix: 2 extend (Hermes, qml-rice-dots) · 2 fresh (LMT Live, Decoy) · 1 wildcard (Agent Pager).
Timely: Metro bus is all over LK LinkedIn right now (new routes since Aug, GPS tracking rolling out); agent harnesses are the dev-tools story of the month.

### 1. Hermes, but it has a computer (extend: hermes-agent / personal Grok Bot)
- **Pitch:** Hermes stops being a Telegram bot and gets its own sandboxed Linux desktop: you text it, it drives a real screen.
- **Demo moment:** split screen. Left: iPhone sending "find the cheapest flight CMB→SIN in Jan and screenshot it". Right: the agent's VM desktop opening a browser, clicking, typing. Ends with the screenshot landing back in the chat.
- **Stack:** hermes-agent fork, Rakazo's computer-use loop ported as a Hermes tool, Xvfb + noVNC in a Docker container, Claude computer-use / any vision model behind the existing router, iMessage/Slack/Telegram front-ends.
- **Split:** Mon: VM container (Xvfb, noVNC, xdotool) · Tue: port the screenshot→action loop as a Hermes tool · Wed: model-agnostic wrapper + step budget · Thu: second front-end (Slack proxy you already have) · Fri: kill switch + per-task VM reset · Sat: record 3 real tasks · Sun: cut the reel.
- **Hard part:** model-agnostic computer use (coordinate systems differ per model) and a hard sandbox: throwaway VM per task, no host creds, live-watchable.
- **Scope:** real but tight. Cut the second front-end if the loop eats Wed.

### 2. Island for Linux (extend: qml-rice-dots)
- **Pitch:** A Dynamic Island for Hyprland that shows what your AI agents are doing: Claude Code progress, approvals, media, notifications, all one morphing pill.
- **Demo moment:** Claude Code running a task; the island grows into a progress strip, morphs into an "approve?" card, collapses to a ✓. Interrupt it mid-animation with a Spotify track change and it re-targets without a hitch.
- **Stack:** Quickshell/QML, your MotionValue primitive + a new spring solver, Claude Code hooks → Unix socket → Quickshell, MPRIS, notification daemon.
- **Split:** Mon: spring solver (critically damped, velocity-carrying) · Tue: persistent-node island shell, 3 states · Wed: Claude Code hooks → socket bridge · Thu: media + notifications · Fri: interruption polish at 60 Hz, frame-time graph · Sat: record on the 240 Hz monitor + T480 · Sun: reel.
- **Hard part:** velocity-preserving interruption: re-targeting a spring mid-flight across shape and size without a frame of discontinuity. That's the "optimise for continuity" thesis, made visible.
- **Scope:** very doable. The motion polish is the bottomless pit, so timebox it.

### 3. LMT Live: Metro buses, no signup (fresh)
- **Pitch:** Open the link, see every Colombo Metro bus moving live, tap a stop, get an ETA. No NIC, no account, no Google Maps bill.
- **Demo moment:** a Colombo map with buses gliding smoothly along their routes (interpolated, not jumping), tap a stop on Galle Rd, ETA card counts down, the bus arrives on screen.
- **Stack:** Bun + Hono on Cloudflare Workers polling the feed, Durable Object fan-out over WebSocket, MapLibre GL + free OSM/Protomaps tiles, PWA (Tanka energy).
- **Split:** Mon: confirm feed access/format first (GTFS-RT or reverse the LMT-GO API); if blocked, pivot to Decoy · Tue: Worker poller + normalise · Wed: map + smooth interpolation · Thu: snap-to-route + stop ETAs · Fri: PWA polish, share link · Sat: ride a bus, screen-record it live · Sun: reel.
- **Hard part:** ETAs from noisy, sparse GPS pings: map-matching to the route shape and learning segment speeds by time of day. Gliding buses that don't drive through buildings.
- **Scope:** riskiest data dependency of the five. Monday is go/no-go.

### 4. Decoy: anti-wallhack you can see working (fresh, security path)
- **Pitch:** A tiny multiplayer arena that proves your CS2 idea: the server only sends enemies you could plausibly see, and feeds ghost decoys to suspected cheaters.
- **Demo moment:** split screen. The honest player sees 1 enemy. The "cheater" running an ESP overlay sees 6 red boxes, 5 fake. They peek the wrong one and get flagged.
- **Stack:** top-down browser shooter (Canvas/Pixi) + authoritative Bun WebSocket server, grid raycast visibility, a deliberate "cheat client" that reads raw packets, decoy-movement model built from recorded real-player paths.
- **Split:** Mon: server tick loop + movement · Tue: line-of-sight culling · Wed: write the wallhack (yes, cheat yourself) · Thu: predictive peek window (send just before visible, so no pop-in) · Fri: decoys + "shot at a ghost" flagging · Sat: record the side-by-side · Sun: reel + post it to r/GlobalOffensive too.
- **Hard part:** peek prediction: send positions early enough that legit players never see pop-in at 100 ms ping, late enough that walls are useless. Plus decoys that move like humans.
- **Scope:** a week if the game stays ugly-on-purpose. Don't build a real shooter.

### 5. Agent Pager (wildcard, ESP32)
- **Pitch:** A pocket gadget that buzzes when Claude Code needs your approval. Press a physical button to allow or deny from across the room.
- **Demo moment:** walk away from the desk, the agent hits an `rm -rf` / deploy permission, the pager buzzes, OLED shows the command, click Deny, cut to the terminal saying denied. Real hardware hits different on LinkedIn.
- **Stack:** your ESP32 + 0.96" OLED + 4 buttons (pocket deck reborn), Claude Code PermissionRequest/Notification hooks → tiny Bun relay → MQTT or WebSocket to the ESP32, optional buzzer.
- **Split:** Mon: firmware (Wi-Fi, OLED, buttons) · Tue: hook script + relay · Wed: round trip working end to end · Thu: HMAC-signed approvals so nobody on uni Wi-Fi can approve your deploy · Fri: multi-session queue + 3D-printed/cardboard case · Sat: film it · Sun: reel.
- **Hard part:** making remote approval safe: signed, single-use, expiring tokens, and failing closed when the pager is offline.
- **Scope:** most fun-per-hour on this list. Hardware gremlins are the only risk.
