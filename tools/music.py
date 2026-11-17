#!/usr/bin/env python3
"""Beat-synced original score for a reel. Pure numpy/scipy synthesis (no samples, no licensing).

music.compose(total, cuts, drop, outro, bpm, seed, path)
  total : seconds of audio
  cuts  : scene-cut times (s) -> whoosh into each cut
  drop  : time of the drop (title reveal): riser before, impact on it, full beat after
  outro : time the end card starts: impact, drums stop, pad rings out
"""
import numpy as np, wave
from scipy.signal import butter, sosfilt

SR = 44100
PROGS = [  # (root midi, chord intervals) per bar
    [(57, [0, 3, 7, 10]), (53, [0, 4, 7, 11]), (48, [0, 4, 7, 11]), (55, [0, 4, 7, 9])],   # Am7 Fmaj7 Cmaj7 G6
    [(50, [0, 3, 7, 10]), (46, [0, 4, 7, 11]), (53, [0, 4, 7, 11]), (48, [0, 4, 7, 9])],   # Dm7 Bbmaj7 Fmaj7 C6
    [(52, [0, 3, 7, 10]), (48, [0, 4, 7, 11]), (55, [0, 4, 7, 9]), (50, [0, 3, 7, 10])],   # Em7 Cmaj7 G6 Dm7
]

def hz(m): return 440.0 * 2 ** ((m - 69) / 12)
def filt(x, kind, f, order=2):
    return sosfilt(butter(order, f, btype=kind, fs=SR, output="sos"), x, axis=0)

def saw(f, n, phase=0.0):
    t = np.arange(n) / SR
    return 2 * ((t * f + phase) % 1.0) - 1

def add(buf, x, at, pan=0.0):
    i = int(at * SR)
    if i >= len(buf): return
    x = x[: len(buf) - i]
    l, r = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
    buf[i:i + len(x), 0] += x * l; buf[i:i + len(x), 1] += x * r

def env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)

def kick(vol=1.0):
    n = int(0.5 * SR); t = np.arange(n) / SR
    f = 42 + 110 * np.exp(-t * 32)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6.5)
    x[:200] += np.random.randn(200) * 0.3 * np.linspace(1, 0, 200)
    return np.tanh(x * 1.6) * vol

def hat(vol, d=0.035):
    n = int(0.12 * SR); return filt(np.random.randn(n), "high", 7500) * env(n, 0.001, d) * vol

def clap(vol):
    n = int(0.35 * SR); x = filt(np.random.randn(n), "band", [900, 3200])
    e = np.zeros(n); t = np.arange(n) / SR
    for o in (0, 0.011, 0.022): e += (t >= o) * np.exp(-np.maximum(t - o, 0) / (0.012 if o < 0.02 else 0.11))
    return x * e * vol

def whoosh(at_cut, vol=0.12, length=0.45):
    n = int(length * SR); x = np.random.randn(n)
    x = filt(x, "band", [600, 6000])
    t = np.linspace(0, 1, n); e = t ** 3  # swell into the cut
    return x * e * vol, at_cut - length

def riser(length, vol=0.2):
    n = int(length * SR); t = np.linspace(0, 1, n)
    x = np.random.randn(n); out = np.zeros(n); seg = int(0.05 * SR)
    for s in range(0, n, seg):  # sweep bandpass upward
        c = 400 + 7000 * (s / n) ** 2
        out[s:s + seg] = filt(x[s:s + seg + 0], "band", [c * 0.7, min(c * 1.4, 20000)])
    tone = np.sin(2 * np.pi * np.cumsum(200 + 600 * t ** 2) / SR) * 0.25
    return (out + tone) * t ** 2.5 * vol

def impact(vol=1.0):
    n = int(2.2 * SR); t = np.arange(n) / SR
    boom = np.sin(2 * np.pi * np.cumsum(35 + 60 * np.exp(-t * 12)) / SR) * np.exp(-t * 2.2)
    crash = filt(filt(np.random.randn(n), "high", 3500), "low", 12000) * np.exp(-t * 2.8) * 0.10
    return (np.tanh(boom * 1.4) + crash) * vol

def pad_bar(root, ivs, dur, vol):
    n = int(dur * SR); x = np.zeros(n)
    for iv in ivs:
        for det in (-0.08, 0.0, 0.08):
            x += saw(hz(root + 12 + iv + det), n, np.random.rand())
    x = filt(x, "low", 1400) / (len(ivs) * 3)
    e = np.minimum(1, np.arange(n) / (0.08 * SR)) * np.minimum(1, (n - np.arange(n)) / (0.05 * SR))
    return x * e * vol

def pluck(m, vol):
    n = int(0.3 * SR); t = np.arange(n) / SR
    x = (np.sin(2 * np.pi * hz(m) * t) + 0.3 * saw(hz(m), n)) * np.exp(-t * 14)
    return filt(x, "low", 4000) * vol

def bass(m, dur, vol):
    n = int(dur * SR); x = saw(hz(m), n) + 0.6 * np.sin(2 * np.pi * hz(m) * np.arange(n) / SR)
    return filt(x, "low", 380) * env(n, 0.004, dur * 0.7) * vol

def compose(total, cuts, drop, outro, bpm=120, seed=0, path="music.wav"):
    rng = np.random.default_rng(seed); np.random.seed(seed)
    beat = 60 / bpm; bar = beat * 4
    prog = PROGS[seed % len(PROGS)]
    n = int((total + 0.5) * SR)
    drums = np.zeros((n, 2)); music = np.zeros((n, 2)); fx = np.zeros((n, 2))
    nbeats = int(total / beat) + 1
    kicks = []
    for b in range(nbeats):
        tb = b * beat
        if tb >= outro: break
        if tb < drop:
            if b % 2 == 0: add(drums, kick(0.55), tb); kicks.append(tb)
        else:
            add(drums, kick(1.0), tb); kicks.append(tb)
            if b % 2 == 1: add(drums, clap(0.38), tb, 0.05)
            add(drums, hat(0.32), tb + beat / 2, 0.25)
            add(drums, hat(0.13, 0.02), tb + beat / 4, -0.3); add(drums, hat(0.13, 0.02), tb + 3 * beat / 4, -0.3)
        if drop - 2 * beat <= tb < drop and tb >= 0:  # snare roll into drop
            for k in range(4): add(drums, clap(0.10 + 0.06 * k), tb + k * beat / 4)
    # harmony
    nb = int(total / bar) + 1
    for i in range(nb):
        tb = i * bar; root, ivs = prog[i % len(prog)]
        if tb >= total: break
        add(music, pad_bar(root, ivs, bar, 0.30 if tb < outro else 0.38), tb, 0.0)
        if drop <= tb < outro or (tb < drop and tb + bar > drop):
            for k in range(8):  # 8th-note pumping bass
                t8 = tb + k * beat / 2
                if drop <= t8 < outro: add(music, bass(root - 12, beat / 2, 0.55), t8)
        # arp after drop+1 bar
        for k in range(16):
            t16 = tb + k * beat / 4
            if drop + bar * 0.5 <= t16 < outro:
                notes = [root + 24 + iv for iv in ivs]
                m = notes[k % len(notes)] + (12 if k % 8 == 7 else 0)
                add(music, pluck(m, 0.16), t16, 0.35 if k % 2 else -0.35)
    # outro: let final chord ring
    root, ivs = prog[int(outro / bar) % len(prog)]
    add(music, pad_bar(root, ivs, total - outro + 0.4, 0.42), outro)
    # sidechain pump on music
    sc = np.ones(n)
    for k in kicks:
        i = int(k * SR); L = int(0.35 * SR); tt = np.arange(min(L, n - i)) / SR
        sc[i:i + len(tt)] = np.minimum(sc[i:i + len(tt)], 1 - 0.55 * np.exp(-tt / 0.1))
    music *= sc[:, None]
    # fx
    for c in cuts:
        if abs(c - drop) < 0.01 or abs(c - outro) < 0.01: continue
        w, at = whoosh(c); add(fx, w, at, 0.0)
    rl = 2 * beat; add(fx, riser(rl), drop - rl)
    add(fx, impact(1.0), drop); add(fx, impact(0.75), outro)
    mix = drums * 0.9 + music * 0.85 + fx * 0.8
    mix = filt(mix, "high", 28)
    # master: fade in/out, soft clip, normalize
    t = np.arange(n) / SR
    fade = np.minimum(1, t / 0.05) * np.clip((total - t) / 1.4, 0, 1)
    mix *= fade[:, None]
    mix = np.tanh(mix * 1.2)
    mix = mix / (np.abs(mix).max() + 1e-9) * 0.89
    mix = mix[: int(total * SR)]
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype("<i2").tobytes())
    return path

if __name__ == "__main__":
    compose(16, [4, 8, 12], 4, 12, path="/tmp/test.wav"); print("ok")
