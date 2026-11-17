#!/usr/bin/env python3
"""Launch-reel engine, Apple-keynote style.
Usage: python3 tools/reel.py projects/<slug>/spec.json [--frames]

Philosophy (keep this when editing):
- MOMENTUM. Nothing ever sits still: every scene has a slow continuous push-in and drift, and cuts
  whip through with matching velocity (outgoing accelerates up + motion blur, incoming decelerates
  in from below). Expo-out easing on entrances.
- BEAT. Everything is on a BPM grid: scene durations are whole beats, so every cut lands on a
  beat, and words slam in on beats. The original score (tools/music.py) is built from the same cut list.
- TYPE. Huge, confident display type that slams in (scale-down + fade), one idea per card. Accent colour
  for the payoff word.
- PRODUCT AS HERO. Phones rotate in from a 3D tilt and settle, with a specular light sweep.
- Deep near-black backgrounds, soft drifting accent glow, vignette.
--frames : write key stills to out/<slug>/frames/ for review, no video.
"""
import json, math, os, re, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1350, 30
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import music

FONTS = os.path.join(ROOT, "fonts")
_fc = {}
def font(name, size):
    k = (name, size)
    if k not in _fc: _fc[k] = ImageFont.truetype(os.path.join(FONTS, name + ".woff"), size)
    return _fc[k]

DISPLAY = "fraunces-latin-600-normal"
SANS = "schibsted-grotesk-latin-500-normal"
SANS_B = "schibsted-grotesk-latin-700-normal"
MONO = "jetbrains-mono-latin-600-normal"
M = 90

def hexc(h, a=255): h = h.lstrip("#"); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4)) + (a,)
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def expo(t): t = clamp(t); return 1.0 if t >= 1 else 1 - 2 ** (-10 * t)
def ease_out(t): t = clamp(t); return 1 - (1 - t) ** 4
def ease_in3(t): t = clamp(t); return t ** 3
def back_out(t, s=1.3): t = clamp(t) - 1; return 1 + (s + 1) * t ** 3 + s * t ** 2
def prog(t, s, d): return clamp((t - s) / d)

# ---------------- drawing helpers ----------------
def text_sprite(txt, fnt, color, track=0):
    asc, desc = fnt.getmetrics()
    if not track:
        l, _, r, _ = fnt.getbbox(txt)
        im = Image.new("RGBA", (r - l + 6, asc + desc + 10), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((3 - l, 5), txt, font=fnt, fill=color); return im
    w = int(sum(fnt.getlength(c) + track for c in txt)) + 8
    im = Image.new("RGBA", (w, asc + desc + 10), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 4
    for c in txt: d.text((x, 5), c, font=fnt, fill=color); x += fnt.getlength(c) + track
    return im

def paste(canvas, spr, x, y, alpha=1.0, scale=1.0):
    if alpha <= 0.01: return
    if abs(scale - 1) > 0.002:
        w, h = max(1, int(spr.width * scale)), max(1, int(spr.height * scale))
        x += (spr.width - w) / 2; y += (spr.height - h) / 2
        spr = spr.resize((w, h), Image.BICUBIC)
    if alpha < 0.999:
        spr = spr.copy(); spr.putalpha(spr.getchannel("A").point(lambda v: int(v * alpha)))
    x, y = int(round(x)), int(round(y))
    sx, sy = max(0, -x), max(0, -y)  # alpha_composite needs a non-negative dest: crop instead
    if sx >= spr.width or sy >= spr.height or x >= canvas.width or y >= canvas.height: return
    canvas.alpha_composite(spr, (max(0, x), max(0, y)), (sx, sy))

def wrap(txt, fnt, maxw):
    out, cur = [], ""
    for w in txt.split():
        t = (cur + " " + w).strip()
        if fnt.getlength(t) <= maxw or not cur: cur = t
        else: out.append(cur); cur = w
    if cur: out.append(cur)
    return out

class Words:
    """Wrapped words; each word slams in (scale 1.35->1, fade) or rises, with stagger."""
    def __init__(self, txt, fnt, color, maxw, x, y, align="left", lh=1.08, accent_words=(), accent=None):
        self.items = []; sp = fnt.getlength(" ")
        asc, desc = fnt.getmetrics(); lineh = int((asc + desc) * lh)
        aw = set(w.lower() for w in accent_words); lines = wrap(txt, fnt, maxw)
        for li, line in enumerate(lines):
            ws = line.split(); wd = [fnt.getlength(w) for w in ws]; tot = sum(wd) + sp * (len(ws) - 1)
            cx = x if align == "left" else x - tot / 2
            for w, d in zip(ws, wd):
                col = accent if accent and w.strip(".,!?:;").lower() in aw else color
                self.items.append((text_sprite(w, fnt, col), cx, y + li * lineh)); cx += d + sp
        self.height = len(lines) * lineh
    def draw(self, c, t, start=0.0, stagger=0.06, dur=0.45, mode="slam"):
        for i, (s, x, y) in enumerate(self.items):
            p = prog(t, start + i * stagger, dur)
            if p <= 0: continue
            if mode == "slam": paste(c, s, x, y, clamp(p * 3), 1 + 0.35 * (1 - expo(p)))
            else: paste(c, s, x, y + (1 - expo(p)) * 40, clamp(p * 2.5))

def rounded(im, r):
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), r, fill=255)
    o = im.convert("RGBA"); o.putalpha(m); return o

def build_phone(path, h):
    shot = Image.open(path).convert("RGB")
    bez = int(h * 0.02); sh = h - 2 * bez; sw = int(shot.width * sh / shot.height)
    shot = rounded(shot.resize((sw, sh), Image.LANCZOS), int(sw * 0.115))
    body = Image.new("RGBA", (sw + 2 * bez, h), (0, 0, 0, 0)); d = ImageDraw.Draw(body)
    r = int(body.width * 0.15)
    d.rounded_rectangle((0, 0, body.width - 1, h - 1), r, fill=(12, 12, 14, 255))
    d.rounded_rectangle((1, 1, body.width - 2, h - 2), r, outline=(140, 140, 150, 120), width=3)  # titanium rim
    body.alpha_composite(shot, (bez, bez))
    return body

def build_window(path, w, title=""):
    shot = Image.open(path).convert("RGB"); bar = int(w * 0.045)
    sh = int(shot.height * w / shot.width); shot = shot.resize((w, sh), Image.LANCZOS)
    body = Image.new("RGBA", (w, sh + bar), (24, 24, 28, 255)); d = ImageDraw.Draw(body)
    for i, col in enumerate([(255, 95, 87), (254, 188, 46), (40, 200, 64)]):
        cx, cy, r = int(bar * 0.7 + i * bar * 0.55), bar // 2, int(bar * 0.16); d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col)
    if title:
        f = font(MONO, int(bar * 0.38)); d.text((w / 2 - f.getlength(title) / 2, bar * 0.28), title, font=f, fill=(255, 255, 255, 120))
    body.paste(shot, (0, bar)); return rounded(body, int(w * 0.02))

def sweep(img, p, strength=70):
    """Diagonal specular band crossing the image at progress p (0..1)."""
    if p <= 0 or p >= 1: return img
    w, h = img.size
    xx = np.arange(w)[None, :] + np.arange(h)[:, None] * 0.45
    center = -0.3 * w + p * (w + 0.45 * h + 0.6 * w)
    band = np.exp(-((xx - center) / (w * 0.10)) ** 2) * strength
    a = (band * (np.asarray(img.getchannel("A"), dtype=np.float32) / 255)).astype("uint8")
    hl = Image.new("RGBA", (w, h), (255, 255, 255, 0)); hl.putalpha(Image.fromarray(a))
    o = img.copy(); o.alpha_composite(hl); return o

def _coeffs(dst, src):
    A = []
    for (x, y), (X, Y) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -X * x, -X * y]); A.append([0, 0, 0, x, y, 1, -Y * x, -Y * y])
    return np.linalg.solve(np.array(A, float), np.array(src, float).reshape(8)).tolist()

def tilt(img, ang):
    """Fake 3D rotation about the vertical axis. ang in degrees; +ve = right edge recedes."""
    if abs(ang) < 0.3: return img
    w, h = img.size; a = math.radians(abs(ang))
    nw = max(2, int(w * math.cos(a))); d = h * 0.16 * math.sin(a)
    if ang > 0: dst = [(0, 0), (nw, d), (nw, h - d), (0, h)]
    else: dst = [(0, d), (nw, 0), (nw, h), (0, h - d)]
    return img.transform((nw, h), Image.PERSPECTIVE, _coeffs(dst, [(0, 0), (w, 0), (w, h), (0, h)]), Image.BICUBIC)

_shadow_cache = {}
def shadow_for(img, blur=45, alpha=170):
    k = (img.size[1], blur)  # cache by height; width changes with tilt but shadow is soft anyway
    if k not in _shadow_cache:
        pad = blur * 2; s = Image.new("RGBA", (img.width + 2 * pad, img.height + 2 * pad), (0, 0, 0, 0))
        s.paste((0, 0, 0, alpha), (pad, pad, pad + img.width, pad + img.height), img.getchannel("A"))
        _shadow_cache[k] = (s.filter(ImageFilter.GaussianBlur(blur)), pad)
    return _shadow_cache[k]

# ---------------- background ----------------
class BG:
    def __init__(self, spec):
        self.bg = hexc(spec["bg"]); acc = hexc(spec["accent"])
        yy, xx = np.mgrid[0:1000, 0:1000]; r2 = ((xx - 500) ** 2 + (yy - 500) ** 2) / (210.0 ** 2)
        g = Image.fromarray((np.exp(-r2) * 255).astype("uint8"), "L")
        self.g1 = Image.new("RGBA", g.size, acc[:3] + (0,)); self.g1.putalpha(g.point(lambda v: int(v * 0.26)))
        self.g2 = Image.new("RGBA", g.size, acc[:3] + (0,)); self.g2.putalpha(g.point(lambda v: int(v * 0.13)))
    def frame(self, T):
        c = Image.new("RGBA", (W, H), self.bg)
        paste(c, self.g1, W * 0.65 + math.sin(T * 0.45) * 190 - 500, H * 0.15 + math.cos(T * 0.33) * 140 - 500)
        paste(c, self.g2, W * 0.18 + math.cos(T * 0.38) * 170 - 500, H * 0.88 + math.sin(T * 0.5) * 110 - 500)
        return c

# ---------------- momentum compositor ----------------
WHIP_IN, WHIP_OUT, DIST = 0.42, 0.26, 0.34
def compose(bg, layer, t, dur, first, last):
    dy, blur = 0.0, 0.0
    if not first and t < WHIP_IN:
        v = 1 - expo(t / WHIP_IN); dy += v * H * DIST; blur = max(blur, v)
    if not last and t > dur - WHIP_OUT:
        v = ease_in3((t - (dur - WHIP_OUT)) / WHIP_OUT); dy -= v * H * DIST; blur = max(blur, v)
    push = 1.0 + 0.045 * (t / dur)  # continuous push-in
    L = layer
    if push != 1.0:
        w, h = int(W * push), int(H * push)
        L = L.resize((w, h), Image.BILINEAR).crop(((w - W) // 2, (h - H) // 2, (w - W) // 2 + W, (h - H) // 2 + H))
    if blur > 0.03:  # vertical motion blur
        k = 1 + int(blur * 22); L = L.resize((W, max(1, H // k)), Image.BILINEAR).resize((W, H), Image.BILINEAR)
    paste(bg, L, 0, dy)
    if last and t > dur - 0.7:
        bg.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * ease_out((t - (dur - 0.7)) / 0.7)))))
    return bg

# ---------------- scenes (draw on a transparent layer; t is scene-local) ----------------
def kick_sprite(spec, txt, size=26):
    return text_sprite(txt.upper(), font(MONO, size), hexc(spec["accent"]), track=3)

def fit_font(txt, maxw, maxsize, minsize=60, face=DISPLAY):
    s = maxsize
    while s > minsize and max(font(face, s).getlength(w) for w in txt.split()) > maxw * 0.92: s -= 4
    return font(face, s)

def scene_hook(spec, s, B):
    """Cards of big type, one idea each, hard-switching on the beat. Last card in accent."""
    cards = s["cards"]; fg, acc = hexc(spec["fg"]), hexc(spec["accent"])
    built, t0 = [], 0.0
    for i, cd in enumerate(cards):
        txt = cd["text"]; f = fit_font(txt, W - 2 * M, cd.get("size", 150))
        col = acc if cd.get("accent", i == len(cards) - 1) else fg
        tmp = Words(txt, f, col, W - 2 * M, W // 2, 0, align="center", lh=1.0)
        wds = Words(txt, f, col, W - 2 * M, W // 2, int(H / 2 - tmp.height / 2 - 20), align="center", lh=1.0)
        d = cd["beats"] * B; built.append((t0, d, wds)); t0 += d
    def draw(c, t):
        for st, d, wds in built:
            if st <= t < st + d:
                wds.draw(c, t - st, stagger=min(0.09, d * 0.5 / max(1, len(wds.items))), dur=0.38)
    return t0, draw

def scene_title(spec, s, B):
    fg, acc = hexc(spec["fg"]), hexc(spec["accent"])
    name = text_sprite(spec["name"], font(DISPLAY, s.get("size", 300)), fg)
    gp = 70; gl = Image.new("RGBA", (name.width + 2 * gp, name.height + 2 * gp), acc[:3] + (0,))
    a = Image.new("L", gl.size, 0); a.paste(name.getchannel("A").point(lambda v: int(v * 0.85)), (gp, gp)); gl.putalpha(a)
    gl = gl.filter(ImageFilter.GaussianBlur(40))
    tag = Words(spec["tagline"], font(SANS, 46), hexc(spec["fg"], 200), W - 2 * M - 40, W // 2, 820, align="center", lh=1.25)
    kk = kick_sprite(spec, spec.get("kicker", "Jedach"))
    dur = s.get("beats", 6) * B
    def draw(c, t):
        p = prog(t, 0.0, 0.7); sc = 1 + 0.5 * (1 - expo(p)); y = 560 - name.height / 2
        paste(c, gl, W / 2 - gl.width / 2, y - gp, clamp(p * 1.5) * (0.6 + 0.25 * math.sin(t * 3)), sc)
        nm = sweep(name, prog(t, 0.55, 1.1), 150)
        paste(c, nm, W / 2 - nm.width / 2, y, clamp(p * 3), sc)
        paste(c, kk, W / 2 - kk.width / 2, 360, ease_out(prog(t, 0.35, 0.5)))
        tag.draw(c, t, start=0.6, stagger=0.04, mode="rise")
    return dur, draw

def head(spec, s, y0=105):
    kk = kick_sprite(spec, s.get("kicker", ""))
    f = fit_font(s["title"], W - 2 * M, s.get("size", 84), 56)
    title = Words(s["title"], f, hexc(spec["fg"]), W - 2 * M, M, y0 + 48, lh=1.04, accent_words=s.get("accent_words", []), accent=hexc(spec["accent"]))
    sub = Words(s["sub"], font(SANS, 36), hexc(spec["fg"], 165), W - 2 * M, M, y0 + 70 + title.height, lh=1.3) if s.get("sub") else None
    bottom = y0 + 70 + title.height + (sub.height if sub else 0)
    def draw(c, t):
        paste(c, kk, M, y0, ease_out(prog(t, 0.05, 0.4)))
        title.draw(c, t, start=0.1, stagger=0.055)
        if sub: sub.draw(c, t, start=0.45, stagger=0.025, mode="rise")
    return draw, bottom

def scene_phone(spec, s, B, idx=0):
    dur = s.get("beats", 6) * B; hd, bottom = head(spec, s)
    ph = build_phone(os.path.join(spec["_dir"], s["image"]), int(min(930, H - bottom + 140)))
    side = 1 if idx % 2 == 0 else -1
    def draw(c, t):
        hd(c, t)
        p = expo(prog(t, 0.12, 1.1))
        ang = side * (34 * (1 - p) + 7) - side * 3 * math.sin(t * 0.9)  # settle, then keep breathing
        img = tilt(sweep(ph, prog(t, 0.7, 1.3), 60), ang)
        x = W / 2 - img.width / 2 + side * (1 - p) * 160
        y = bottom + 40 + (1 - p) * 300 - t * 14
        sh, pad = shadow_for(img)
        paste(c, sh, x - pad - side * 18, y - pad + 34, clamp(p * 2) * 0.9)
        paste(c, img, x, y, clamp(prog(t, 0.12, 0.25)))
    return dur, draw

def scene_window(spec, s, B, idx=0):
    dur = s.get("beats", 6) * B; hd, bottom = head(spec, s)
    win = build_window(os.path.join(spec["_dir"], s["image"]), W - 2 * M + 30, s.get("window_title", ""))
    def draw(c, t):
        hd(c, t)
        p = expo(prog(t, 0.12, 1.1)); sc = 0.86 + 0.14 * p + 0.03 * (t / dur)
        img = sweep(win, prog(t, 0.7, 1.3), 45); y = bottom + 50 + (1 - p) * 260
        sh, pad = shadow_for(img)
        paste(c, sh, W / 2 - img.width / 2 - pad, y - pad + 30, clamp(p * 2) * 0.9, sc)
        paste(c, img, W / 2 - img.width / 2, y, clamp(prog(t, 0.12, 0.25)), sc)
    return dur, draw

def scene_trio(spec, s, B):
    """Three phones fanned out; centre one forward. Staggered on the beat."""
    dur = s.get("beats", 6) * B; hd, bottom = head(spec, s)
    hgt = int(min(820, H - bottom + 100))
    phones = [build_phone(os.path.join(spec["_dir"], im), hgt) for im in s["images"]]
    order = [(0, -1), (2, 1), (1, 0)]  # sides first, centre on top
    def draw(c, t):
        hd(c, t)
        for k, (i, pos) in enumerate(order):
            st = 0.15 + k * B * 0.5
            p = expo(prog(t, st, 1.0))
            if p <= 0: continue
            sc = 0.80 if pos else 1.0
            img = tilt(phones[i], -pos * (14 + 20 * (1 - p))) if pos else sweep(phones[i], prog(t, 1.0, 1.2), 55)
            x = W / 2 - img.width / 2 + pos * (270 + (1 - p) * 120)
            y = bottom + 50 + (1 - p) * 360 + (40 if pos else 0) - t * 10
            sh, pad = shadow_for(img, 35)
            paste(c, sh, x - pad, y - pad + 28, clamp(p * 2) * 0.8, sc)
            paste(c, img, x, y, clamp(p * 3), sc)
    return dur, draw

def scene_stat(spec, s, B):
    dur = s.get("beats", 6) * B; acc = hexc(spec["accent"])
    f = font(DISPLAY, s.get("size", 280))
    lbl = Words(s["label"], font(SANS, 48), hexc(spec["fg"], 210), W - 2 * M, W // 2, 840, align="center", lh=1.25)
    kk = kick_sprite(spec, s.get("kicker", ""))
    m = re.match(r"^([^\d]*)([\d,\.]+)(.*)$", s["value"])
    def draw(c, t):
        p = expo(prog(t, 0.05, 1.3))
        if m:
            num = float(m.group(2).replace(",", "")); dec = "." in m.group(2); v = num * p
            txt = m.group(1) + (f"{v:,.1f}" if dec else f"{int(round(v)):,}") + m.group(3)
        else: txt = s["value"]
        spr = text_sprite(txt, f, acc)
        paste(c, spr, W / 2 - spr.width / 2, 480, clamp(p * 3), 1 + 0.3 * (1 - expo(prog(t, 0.05, 0.5))))
        paste(c, kk, W / 2 - kk.width / 2, 400, ease_out(prog(t, 0.1, 0.4)))
        lbl.draw(c, t, start=0.5, stagger=0.04, mode="rise")
    return dur, draw

def scene_stack(spec, s, B):
    dur = s.get("beats", 6) * B; fg, acc = hexc(spec["fg"]), hexc(spec["accent"])
    f = font(MONO, 40); chips = []
    for it in s["items"]:
        w, h = int(f.getlength(it) + 64), 88
        ch = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(ch)
        d.rounded_rectangle((0, 0, w - 1, h - 1), 44, fill=hexc(spec["fg"], 16), outline=acc[:3] + (160,), width=2)
        d.text((32, 18), it, font=f, fill=fg); chips.append(ch)
    rows, cur, cw = [], [], 0
    for ch in chips:
        if cw + ch.width > W - 2 * M and cur: rows.append((cur, cw - 18)); cur, cw = [], 0
        cur.append(ch); cw += ch.width + 18
    rows.append((cur, cw - 18))
    block_h = len(rows) * 106
    hd, bottom = head(spec, {"kicker": s.get("kicker", "Built with"), "title": s.get("title", "The stack."), "size": 110}, y0=int(H / 2 - (block_h + 230) / 2))
    placed, y = [], bottom + 50
    for r, rw in rows:
        x = W / 2 - rw / 2
        for ch in r: placed.append((ch, x, y)); x += ch.width + 18
        y += 106
    def draw(c, t):
        hd(c, t)
        for i, (ch, x, y) in enumerate(placed):
            p = prog(t, 0.3 + i * B / 4, 0.4)  # 16th-note stagger
            if p > 0: paste(c, ch, x, y, clamp(p * 4), 0.55 + 0.45 * back_out(p))
    return dur, draw

def scene_end(spec, s, B):
    dur = s.get("beats", 8) * B; fg, acc = hexc(spec["fg"]), hexc(spec["accent"])
    name = text_sprite(spec["name"], font(DISPLAY, 190), fg)
    line = Words(s.get("line", "Built by Senul Mapa"), font(SANS_B, 46), fg, W - 2 * M, W // 2, 760, align="center")
    sub = Words(s.get("sub", "Jedach · Colombo"), font(SANS, 36), hexc(spec["fg"], 150), W - 2 * M, W // 2, 772 + line.height, align="center")
    cta = text_sprite(s["cta"], font(MONO, 36), acc) if s.get("cta") else None
    cy = 812 + line.height + sub.height
    def draw(c, t):
        p = expo(prog(t, 0.0, 0.8))
        paste(c, sweep(name, prog(t, 0.5, 1.2), 140), W / 2 - name.width / 2, 470, clamp(p * 3), 1 + 0.4 * (1 - p))
        line.draw(c, t, start=0.4, stagger=0.05, mode="rise")
        sub.draw(c, t, start=0.65, stagger=0.03, mode="rise")
        if cta:
            q = expo(prog(t, 0.95, 0.6))
            if q > 0.01:
                d = ImageDraw.Draw(c); bw, bh = cta.width + 64, 84; bx, by = W / 2 - bw / 2, cy + (1 - q) * 30
                d.rounded_rectangle((bx, by, bx + bw, by + bh), 42, fill=acc[:3] + (int(30 * q),), outline=acc[:3] + (int(255 * q),), width=3)
                paste(c, cta, W / 2 - cta.width / 2, by + 15, q)
    return dur, draw

BUILDERS = {"hook": scene_hook, "title": scene_title, "phone": scene_phone, "window": scene_window,
            "trio": scene_trio, "stat": scene_stat, "stack": scene_stack, "end": scene_end}

def main():
    spec_path = sys.argv[1]; frames_only = "--frames" in sys.argv
    spec = json.load(open(spec_path)); spec["_dir"] = os.path.dirname(os.path.abspath(spec_path))
    bpm = spec.get("bpm", 120); B = 60 / bpm
    slug = spec["slug"]; out = os.path.join(ROOT, "out", slug); os.makedirs(out, exist_ok=True)
    bg = BG(spec); scenes = []; dev_i = 0
    for s in spec["scenes"]:
        if s["type"] in ("phone", "window"): d, fn = BUILDERS[s["type"]](spec, s, B, dev_i); dev_i += 1
        else: d, fn = BUILDERS[s["type"]](spec, s, B)
        scenes.append((s, d, fn))
    starts = np.cumsum([0] + [d for _, d, _ in scenes]).tolist(); total = starts[-1]
    if frames_only:
        fd = os.path.join(out, "frames"); os.makedirs(fd, exist_ok=True)
        for i, (s, d, fn) in enumerate(scenes):
            for frac in (0.06, 0.6, 0.97):
                t = d * frac; L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); fn(L, t)
                c = compose(bg.frame(starts[i] + t), L, t, d, i == 0, i == len(scenes) - 1)
                c.convert("RGB").save(os.path.join(fd, f"{i:02d}_{s['type']}_{int(frac*100):02d}.jpg"), quality=88)
        print("frames:", fd, "total", round(total, 2), "s"); return
    parts = []
    for i, (s, d, fn) in enumerate(scenes):
        tmp, fin = os.path.join(out, f"s{i:02d}.tmp.mp4"), os.path.join(out, f"s{i:02d}.mp4")
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                               "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
        for k in range(int(round(d * FPS))):
            t = k / FPS; L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); fn(L, t)
            ff.stdin.write(compose(bg.frame(starts[i] + t), L, t, d, i == 0, i == len(scenes) - 1).convert("RGB").tobytes())
        ff.stdin.close()
        if ff.wait() != 0: sys.exit(f"ffmpeg failed on scene {i}")
        os.replace(tmp, fin); parts.append(fin); print(f"scene {i} {s['type']} {d:.2f}s", flush=True)
    lst = os.path.join(out, "list.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    joined = os.path.join(out, "joined.mp4")
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined])
    types = [s["type"] for s, _, _ in scenes]
    drop = starts[types.index("title")] if "title" in types else starts[1]
    outro = starts[types.index("end")] if "end" in types else total - 3
    wav = music.compose(total, starts[1:-1], drop, outro, bpm=bpm, seed=spec.get("music_seed", 0), path=os.path.join(out, "score.wav"))
    final = os.path.join(ROOT, "reels", f"{slug}.mp4"); os.makedirs(os.path.dirname(final), exist_ok=True)
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", joined, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", final])
    print("final", final, round(total, 2), "s")

if __name__ == "__main__":
    main()
