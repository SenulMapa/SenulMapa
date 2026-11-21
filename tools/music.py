#!/usr/bin/env python3
"""Beat-synced original score for a reel. Pure numpy/scipy synthesis (no samples, no licensing).

compose(total, drop, outro, bpm, seed, path, whooshes, ticks, hits)
  drop     : title reveal. Riser into it, half a beat of SILENCE, then impact + full beat.
  outro    : end lockup. Drums stop, a chime lands on the lockup, pad rings out.
  whooshes : times of whip/zoom transitions (sound only where the picture moves, not on every cut)
  ticks    : word-slam times in type cards (tiny percussive clicks, keeps type and sound locked)
  hits     : montage hard-cut times (accent snaps)
Restraint rule: every sound must be tied to something on screen.
"""
import numpy as np, wave
from scipy.signal import butter, sosfilt

SR = 44100
PROGS = [
    [(57, [0, 3, 7, 10]), (53, [0, 4, 7, 11]), (48, [0, 4, 7, 11]), (55, [0, 4, 7, 9])],   # Am7 Fmaj7 Cmaj7 G6
    [(50, [0, 3, 7, 10]), (46, [0, 4, 7, 11]), (53, [0, 4, 7, 11]), (48, [0, 4, 7, 9])],   # Dm7 Bbmaj7 Fmaj7 C6
    [(52, [0, 3, 7, 10]), (48, [0, 4, 7, 11]), (55, [0, 4, 7, 9]), (50, [0, 3, 7, 10])],   # Em7 Cmaj7 G6 Dm7
]

def hz(m): return 440.0 * 2 ** ((m - 69) / 12)
def filt(x, kind, f, order=2): return sosfilt(butter(order, f, btype=kind, fs=SR, output="sos"), x, axis=0)
def saw(f, n, phase=0.0): t = np.arange(n) / SR; return 2 * ((t * f + phase) % 1.0) - 1
def env(n, a, d): t = np.arange(n) / SR; return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)

def add(buf, x, at, pan=0.0):
    i = int(round(at * SR))
    if i >= len(buf) or i + len(x) <= 0: return
    if i < 0: x = x[-i:]; i = 0
    x = x[: len(buf) - i]
    buf[i:i + len(x), 0] += x * np.sqrt(0.5 * (1 - pan)); buf[i:i + len(x), 1] += x * np.sqrt(0.5 * (1 + pan))

def kick(vol=1.0):
    n = int(0.5 * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * np.cumsum(42 + 110 * np.exp(-t * 32)) / SR) * np.exp(-t * 6.5)
    x[:200] += np.random.randn(200) * 0.3 * np.linspace(1, 0, 200)
    return np.tanh(x * 1.6) * vol

def hat(vol, d=0.035): n = int(0.12 * SR); return filt(np.random.randn(n), "high", 7500) * env(n, 0.001, d) * vol

def clap(vol):
    n = int(0.35 * SR); x = filt(np.random.randn(n), "band", [900, 3200]); t = np.arange(n) / SR; e = np.zeros(n)
    for o in (0, 0.011, 0.022): e += (t >= o) * np.exp(-np.maximum(t - o, 0) / (0.012 if o < 0.02 else 0.11))
    return x * e * vol

def tick(vol=0.22):
    n = int(0.06 * SR); t = np.arange(n) / SR
    return (filt(np.random.randn(n), "band", [2500, 7000]) * np.exp(-t / 0.006) + np.sin(2 * np.pi * 1900 * t) * np.exp(-t / 0.012) * 0.5) * vol

def snap(vol=0.3):
    n = int(0.25 * SR); t = np.arange(n) / SR
    return filt(np.random.randn(n), "high", 5000) * np.exp(-t / 0.06) * vol

def whoosh(vol=0.10, length=0.4):
    n = int(length * SR); x = filt(np.random.randn(n), "band", [500, 5000]); return x * np.linspace(0, 1, n) ** 3 * vol

def riser(length, vol=0.2):
    n = int(length * SR); t = np.linspace(0, 1, n); x = np.random.randn(n); out = np.zeros(n); seg = int(0.05 * SR)
    for s in range(0, n, seg):
        c = 400 + 7000 * (s / n) ** 2; out[s:s + seg] = filt(x[s:s + seg], "band", [c * 0.7, min(c * 1.4, 20000)])
    tone = np.sin(2 * np.pi * np.cumsum(200 + 600 * t ** 2) / SR) * 0.25
    return (out + tone) * t ** 2.5 * vol

def impact(vol=1.0):
    n = int(2.2 * SR); t = np.arange(n) / SR
    boom = np.sin(2 * np.pi * np.cumsum(35 + 60 * np.exp(-t * 12)) / SR) * np.exp(-t * 2.2)
    crash = filt(filt(np.random.randn(n), "high", 3500), "low", 12000) * np.exp(-t * 2.8) * 0.10
    return (np.tanh(boom * 1.4) + crash) * vol

def chime(root_hz=1046.5, vol=0.3):
    n = int(2.8 * SR); t = np.arange(n) / SR; x = np.zeros(n)
    for ratio, amp, dec in ((1, 1, 1.4), (2.0, 0.35, 0.9), (2.76, 0.25, 0.6), (5.4, 0.1, 0.3)):
        x += np.sin(2 * np.pi * root_hz * ratio * t) * amp * np.exp(-t / dec)
    return x * np.minimum(1, t / 0.002) * vol

def pad_bar(root, ivs, dur, vol):
    n = int(dur * SR); x = np.zeros(n)
    for iv in ivs:
        for det in (-0.08, 0.0, 0.08): x += saw(hz(root + 12 + iv + det), n, np.random.rand())
    x = filt(x, "low", 1400) / (len(ivs) * 3)
    e = np.minimum(1, np.arange(n) / (0.08 * SR)) * np.minimum(1, (n - np.arange(n)) / (0.05 * SR))
    return x * e * vol

def pluck(m, vol):
    n = int(0.3 * SR); t = np.arange(n) / SR
    return filt((np.sin(2 * np.pi * hz(m) * t) + 0.3 * saw(hz(m), n)) * np.exp(-t * 14), "low", 4000) * vol

def bass(m, dur, vol):
    n = int(dur * SR); x = saw(hz(m), n) + 0.6 * np.sin(2 * np.pi * hz(m) * np.arange(n) / SR)
    return filt(x, "low", 380) * env(n, 0.004, dur * 0.7) * vol

def compose(total, drop, outro, bpm=120, seed=0, path="music.wav", whooshes=(), ticks=(), hits=(), flavor="keynote"):
    """flavor: keynote (four-on-floor + 16th plucks), poster (half-time swung boom-bap, sparse keys, warm lowpass),
    pulse (driving 16th bass + hats, arp ticking under the intro, for the terminal look)."""
    np.random.seed(seed)
    beat = 60 / bpm; bar = beat * 4; prog = PROGS[seed % len(PROGS)]
    n = int((total + 0.5) * SR)
    drums = np.zeros((n, 2)); music = np.zeros((n, 2)); fx = np.zeros((n, 2)); kicks = []
    for b in range(int(total / beat) + 1):
        tb = b * beat
        if tb >= outro: break
        if tb < drop:
            if b % 2 == 0 and tb < drop - beat: add(drums, kick(0.5), tb); kicks.append(tb)
        elif flavor == "poster":
            if b % 4 in (0, 3) or (b % 8 == 2): add(drums, kick(0.95), tb + (beat * 0.5 if b % 8 == 2 else 0)); kicks.append(tb)
            if b % 2 == 1: add(drums, clap(0.42), tb, 0.05)
            add(drums, hat(0.22), tb + beat * 0.58, 0.25); add(drums, hat(0.14, 0.02), tb, -0.25)
        elif flavor == "pulse":
            add(drums, kick(1.0), tb); kicks.append(tb)
            if b % 2 == 1: add(drums, clap(0.30), tb, 0.05)
            for q in range(4): add(drums, hat(0.20 if q == 2 else 0.11, 0.018), tb + q * beat / 4, 0.3 if q % 2 else -0.3)
        else:
            add(drums, kick(1.0), tb); kicks.append(tb)
            if b % 2 == 1: add(drums, clap(0.38), tb, 0.05)
            add(drums, hat(0.30), tb + beat / 2, 0.25)
            add(drums, hat(0.12, 0.02), tb + beat / 4, -0.3); add(drums, hat(0.12, 0.02), tb + 3 * beat / 4, -0.3)
    for i in range(int(total / bar) + 1):
        tb = i * bar
        if tb >= outro: break
        root, ivs = prog[i % len(prog)]
        add(music, pad_bar(root, ivs, min(bar, outro - tb), 0.18 if flavor == "pulse" else 0.30), tb)
        notes = [root + 24 + iv for iv in ivs]
        if flavor == "poster":
            for k in (0, 3, 6):
                t8 = tb + k * beat / 2
                if drop <= t8 < outro: add(music, bass(root - 12, beat * 0.9, 0.6), t8)
            for k, n_ in ((0, 0), (5, 1), (10, 2), (14, 1)):
                t16 = tb + k * beat / 4
                if drop + bar * 0.5 <= t16 < outro: add(music, pluck(notes[n_ % len(notes)] - 12, 0.2), t16, 0.3 if k % 2 else -0.3)
            continue
        steps = 16 if flavor == "pulse" else 8
        for k in range(steps):
            t8 = tb + k * bar / steps
            if drop <= t8 < outro: add(music, bass(root - 12 + (12 if flavor == "pulse" and k % 4 == 2 else 0), bar / steps, 0.5), t8)
        for k in range(16):
            t16 = tb + k * beat / 4
            pre = flavor == "pulse" and t16 < drop - beat and k % 2 == 0
            if pre: add(music, pluck(notes[(k // 2) % len(notes)] + 12, 0.06), t16, 0.35 if k % 4 else -0.35)
            if drop + bar * 0.5 <= t16 < outro:
                add(music, pluck(notes[k % len(notes)] + (12 if k % 8 == 7 else 0), 0.15), t16, 0.35 if k % 2 else -0.35)
    root, ivs = prog[int(outro / bar) % len(prog)]
    add(music, pad_bar(root, ivs, total - outro + 0.4, 0.40), outro)
    sc = np.ones(n)
    for k in kicks:
        i = int(k * SR); tt = np.arange(min(int(0.35 * SR), n - i)) / SR
        sc[i:i + len(tt)] = np.minimum(sc[i:i + len(tt)], 1 - 0.55 * np.exp(-tt / 0.1))
    music *= sc[:, None]
    if flavor == "poster": music = filt(music, "low", 2600)
    # the breath: half a beat of silence right before the drop
    g0, g1 = int((drop - beat / 2) * SR), int(drop * SR)
    if g0 > 0:
        ramp = int(0.01 * SR)
        for buf in (drums, music):
            buf[g0:g1] = 0; buf[g0 - ramp:g0] *= np.linspace(1, 0, ramp)[:, None]
    # fx, each tied to something on screen
    for w in whooshes: add(fx, whoosh(), w - 0.4)
    for tk in ticks: add(fx, tick(), tk, np.random.uniform(-0.3, 0.3))
    for h in hits: add(fx, snap(), h, 0.1)
    rl = 2 * beat; add(fx, riser(rl), drop - beat / 2 - rl)
    add(fx, impact(1.0), drop)
    add(fx, impact(0.35), outro); add(fx, chime(hz(prog[int(outro / bar) % len(prog)][0] + 24)), outro + 0.02)
    mix = filt(drums * 0.9 + music * 0.85 + fx * 0.8, "high", 28)
    t = np.arange(n) / SR
    mix *= (np.minimum(1, t / 0.05) * np.clip((total - t) / 1.2, 0, 1))[:, None]
    mix = np.tanh(mix * 1.2); mix = mix / (np.abs(mix).max() + 1e-9) * 0.89
    mix = mix[: int(total * SR)]
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype("<i2").tobytes())
    return path
