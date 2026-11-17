#!/usr/bin/env python3
"""Launch-reel engine v3, Apple-keynote style.
Usage: python3 tools/reel.py projects/<slug>/spec.json [--frames]

Philosophy (benchmarked against award-winning motion work; keep this when editing):
1. ONE IDEA PER SHOT. A type card says the idea; the next shot shows it. Never headline + paragraph + product
   in one frame. Body copy belongs in the LinkedIn post, not the video.
2. VARY THE TEMPO. Fast runs (montage, 1 beat per cut), held breaths (statement cards), a silence before the drop,
   a hard stop on the lockup. Never the same scene length 6x in a row.
3. CAMERA LANGUAGE. Scale contrast: full phone -> punch-in on one UI detail (focus) -> fanned trio -> montage.
4. ANIMATE THE MEANING. At least one bespoke beat where the visual does what the words say (morph: SMS -> ledger).
5. MIXED TRANSITIONS. whip (vertical, motion blur), zoom (scale-through), cut (hard, on beat), flash (white frame).
6. CONTRAST. Near-black background; the product pops with a soft accent rim light behind it.
7. SOUND IS SYNCED + SPARING. Ticks on word slams, snaps on montage cuts, whoosh only on whip/zoom,
   half-beat of silence before the title drop, chime on the end lockup (tools/music.py).
8. PRODUCT EARLY. Show product inside the first ~6s.
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
TRACK = {}   # face name -> tracking in em (negative = tighter, the Apple display look)
def font(name, size):
    k = (name, size)
    if k not in _fc:
        for ext in (".woff", ".otf", ".ttf", ""):
            fp = os.path.join(FONTS, name + ext)
            if os.path.exists(fp): break
        f = ImageFont.truetype(fp, size); f.face_name = name; _fc[k] = f
    return _fc[k]
def trk(fnt): return TRACK.get(getattr(fnt, "face_name", ""), 0.0) * fnt.size
def tlen(fnt, txt): return fnt.getlength(txt) + trk(fnt) * max(0, len(txt) - 1)
SHINE = False   # specular sweep on screenshots/logo. Off by default (reads as a cheap effect).
GRAD = None     # (c1, c2) gradient fill for accent words, or None for solid accent
MUTED = (134, 134, 139, 255)

DISPLAY = "fraunces-latin-600-normal"
SANS = "schibsted-grotesk-latin-500-normal"
SANS_B = "schibsted-grotesk-latin-700-normal"
MONO = "jetbrains-mono-latin-600-normal"
M = 90

def hexc(h, a=255): h = h.lstrip("#"); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4)) + (a,)
ACCENT_SOLID = [None]
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def expo(t): t = clamp(t); return 1.0 if t >= 1 else 1 - 2 ** (-10 * t)
def ease_out(t): t = clamp(t); return 1 - (1 - t) ** 4
def ease_in3(t): t = clamp(t); return t ** 3
def ease_io(t): t = clamp(t); return 4 * t ** 3 if t < .5 else 1 - (-2 * t + 2) ** 3 / 2
def back_out(t, s=1.3): t = clamp(t) - 1; return 1 + (s + 1) * t ** 3 + s * t ** 2
def prog(t, s, d): return clamp((t - s) / d)
def lerp(a, b, p): return a + (b - a) * p

# ---------------- drawing helpers ----------------
def text_sprite(txt, fnt, color, track=0):
    asc, desc = fnt.getmetrics()
    if color == "ACCENT" or (GRAD and color == ACCENT_SOLID[0]):
        m = text_sprite(txt, fnt, (255, 255, 255, 255), track)
        if not GRAD: o = Image.new("RGBA", m.size, ACCENT_SOLID[0]); o.putalpha(m.getchannel("A")); return o
        g = np.linspace(0, 1, m.width)[None, :, None]
        c1, c2 = np.array(GRAD[0][:3], float), np.array(GRAD[1][:3], float)
        rgb = np.broadcast_to(c1 + (c2 - c1) * g, (m.height, m.width, 3)).astype("uint8")
        o = Image.fromarray(np.ascontiguousarray(rgb), "RGB").convert("RGBA"); o.putalpha(m.getchannel("A")); return o
    t_em = trk(fnt)
    if t_em and not track:
        l, _, r, _ = fnt.getbbox(txt); w = int(tlen(fnt, txt) - l + 10)
        im = Image.new("RGBA", (max(1, w), asc + desc + 10), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        for i, ch in enumerate(txt): d.text((3 - l + fnt.getlength(txt[:i]) + t_em * i, 5), ch, font=fnt, fill=color)
        return im
    if not track:
        l, _, r, _ = fnt.getbbox(txt)
        im = Image.new("RGBA", (max(1, r - l + 6), asc + desc + 10), (0, 0, 0, 0))
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
        if tlen(fnt, t) <= maxw or not cur: cur = t
        else: out.append(cur); cur = w
    if cur: out.append(cur)
    return out

class Words:
    """Wrapped words; each word slams in (scale 1.35->1, fade) or rises, with stagger."""
    def __init__(self, txt, fnt, color, maxw, x, y, align="left", lh=1.08, accent_words=(), accent=None):
        self.items = []; sp = fnt.getlength(" ")
        asc, desc = fnt.getmetrics(); lineh = int((asc + desc) * lh)
        aw = set(w.lower().strip(".,!?:;") for w in accent_words); lines = wrap(txt, fnt, maxw)
        for li, line in enumerate(lines):
            ws = line.split(); wd = [tlen(fnt, w) for w in ws]; tot = sum(wd) + sp * (len(ws) - 1)
            cx = x if align == "left" else x - tot / 2
            for w, d in zip(ws, wd):
                col = accent if accent and w.strip(".,!?:;").lower() in aw else color
                self.items.append((text_sprite(w, fnt, col), cx, y + li * lineh)); cx += d + sp
        self.height = len(lines) * lineh
    def starts(self, start, stagger): return [start + i * stagger for i in range(len(self.items))]
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
    d.rounded_rectangle((1, 1, body.width - 2, h - 2), r, outline=(150, 150, 160, 130), width=3)  # titanium rim
    body.alpha_composite(shot, (bez, bez))
    body.info["screen"] = (bez, bez, sw, sh)
    return body

def build_window(path, w, title=""):
    shot = Image.open(path).convert("RGB"); bar = int(w * 0.045)
    sh = int(shot.height * w / shot.width); shot = shot.resize((w, sh), Image.LANCZOS)
    body = Image.new("RGBA", (w, sh + bar), (24, 24, 28, 255)); d = ImageDraw.Draw(body)
    for i, col in enumerate([(255, 95, 87), (254, 188, 46), (40, 200, 64)]):
        cx, cy, r = int(bar * 0.7 + i * bar * 0.55), bar // 2, int(bar * 0.16); d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col)
    if title:
        f = font(MONO, int(bar * 0.38)); d.text((w / 2 - f.getlength(title) / 2, bar * 0.28), title, font=f, fill=(255, 255, 255, 120))
    body.paste(shot, (0, bar)); out = rounded(body, int(w * 0.02)); out.info["screen"] = (0, bar, w, sh); return out

def sweep(img, p, strength=70):
    """Diagonal specular band crossing the image at progress p (0..1)."""
    if not SHINE or p <= 0 or p >= 1: return img
    w, h = img.size
    xx = np.arange(w)[None, :] + np.arange(h)[:, None] * 0.45
    center = -0.3 * w + p * (w + 0.45 * h + 0.6 * w)
    band = np.exp(-((xx - center) / (w * 0.10)) ** 2) * strength
    a = (band * (np.asarray(img.getchannel("A"), dtype=np.float32) / 255)).astype("uint8")
    hl = Image.new("RGBA", (w, h), (255, 255, 255, 0)); hl.putalpha(Image.fromarray(a))
    o = img.copy(); o.alpha_composite(hl); o.info.update(img.info); return o

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
    dst = [(0, 0), (nw, d), (nw, h - d), (0, h)] if ang > 0 else [(0, d), (nw, 0), (nw, h), (0, h - d)]
    return img.transform((nw, h), Image.PERSPECTIVE, _coeffs(dst, [(0, 0), (w, 0), (w, h), (0, h)]), Image.BICUBIC)

_shadow_cache = {}
def shadow_for(img, blur=45, alpha=170):
    k = (img.size[1], blur)
    if k not in _shadow_cache:
        pad = blur * 2; s = Image.new("RGBA", (img.width + 2 * pad, img.height + 2 * pad), (0, 0, 0, 0))
        s.paste((0, 0, 0, alpha), (pad, pad, pad + img.width, pad + img.height), img.getchannel("A"))
        _shadow_cache[k] = (s.filter(ImageFilter.GaussianBlur(blur)), pad)
    return _shadow_cache[k]

_rim_cache = {}
def rim(c, spec, cx, cy, w, h, a=1.0):
    """Soft accent light behind the hero object."""
    k = (int(w), int(h))
    if k not in _rim_cache:
        gw, gh = int(w * 1.9), int(h * 1.15)
        yy, xx = np.mgrid[0:gh, 0:gw]
        r2 = ((xx - gw / 2) / (gw * 0.30)) ** 2 + ((yy - gh / 2) / (gh * 0.36)) ** 2
        g = Image.new("RGBA", (gw, gh), hexc(spec["accent"])[:3] + (0,))
        g.putalpha(Image.fromarray((np.exp(-r2) * 255 * spec.get("rim", 0.42)).astype("uint8")))
        _rim_cache[k] = g
    g = _rim_cache[k]; paste(c, g, cx - g.width / 2, cy - g.height / 2, a)

def draw_device(c, spec, img, x, y, alpha=1.0, scale=1.0, rim_a=1.0, shadow=True):
    w, h = img.width * scale, img.height * scale
    if rim_a > 0.01: rim(c, spec, x + img.width / 2, y + img.height / 2, w, h, rim_a * alpha)
    if shadow:
        sh, pad = shadow_for(img)
        paste(c, sh, x - pad, y - pad + 34, alpha * 0.9, scale)
    paste(c, img, x, y, alpha, scale)

# ---------------- background ----------------
class BG:
    def __init__(self, spec):
        self.bg = hexc(spec["bg"]); acc = hexc(spec["accent"]); amb = spec.get("ambient", 0.10)
        yy, xx = np.mgrid[0:1000, 0:1000]; r2 = ((xx - 500) ** 2 + (yy - 500) ** 2) / (230.0 ** 2)
        g = Image.fromarray((np.exp(-r2) * 255).astype("uint8"), "L")
        self.g1 = Image.new("RGBA", g.size, acc[:3] + (0,)); self.g1.putalpha(g.point(lambda v: int(v * amb)))
        self.g2 = Image.new("RGBA", g.size, acc[:3] + (0,)); self.g2.putalpha(g.point(lambda v: int(v * amb * 0.5)))
    def frame(self, T):
        c = Image.new("RGBA", (W, H), self.bg)
        paste(c, self.g1, W * 0.65 + math.sin(T * 0.45) * 190 - 500, H * 0.12 + math.cos(T * 0.33) * 140 - 500)
        paste(c, self.g2, W * 0.18 + math.cos(T * 0.38) * 170 - 500, H * 0.9 + math.sin(T * 0.5) * 110 - 500)
        return c

# ---------------- transitions + momentum compositor ----------------
def compose(bg, layer, t, dur, tin, tout, last, push_amt=0.045):
    """tin = how this scene enters ('none' if first); tout = how the NEXT scene enters (None if last).
    Outgoing motion is chosen to match the incoming one so velocity carries across the cut."""
    dy, blur, scale, alpha, flash = 0.0, 0.0, 1.0 + push_amt * (t / dur), 1.0, 0.0
    if tin == "whip" and t < 0.42: v = 1 - expo(t / 0.42); dy += v * H * 0.34; blur = max(blur, v)
    if tin == "zoom" and t < 0.45: v = 1 - expo(t / 0.45); scale *= 1 - 0.22 * v; alpha *= clamp(t / 0.12)
    if tin == "flash" and t < 0.25: flash = 1 - ease_out(t / 0.25)
    if tout == "whip" and t > dur - 0.26: v = ease_in3((t - (dur - 0.26)) / 0.26); dy -= v * H * 0.34; blur = max(blur, v)
    if tout == "zoom" and t > dur - 0.28: v = ease_in3((t - (dur - 0.28)) / 0.28); scale *= 1 + 0.9 * v; alpha *= 1 - v ** 2
    if tout == "flash" and t > dur - 0.1: flash = max(flash, ease_in3((t - (dur - 0.1)) / 0.1))
    L = layer
    if abs(scale - 1) > 0.001:
        w, h = int(W * scale), int(H * scale)
        if scale >= 1: L = L.resize((w, h), Image.BILINEAR).crop(((w - W) // 2, (h - H) // 2, (w - W) // 2 + W, (h - H) // 2 + H))
        else: base = Image.new("RGBA", (W, H), (0, 0, 0, 0)); base.alpha_composite(L.resize((w, h), Image.BILINEAR), ((W - w) // 2, (H - h) // 2)); L = base
    if blur > 0.03:
        k = 1 + int(blur * 22); L = L.resize((W, max(1, H // k)), Image.BILINEAR).resize((W, H), Image.BILINEAR)
    paste(bg, L, 0, dy, alpha)
    if flash > 0.01: bg.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(255 * flash))))
    if last and t > dur - 0.35:
        bg.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * ease_out((t - (dur - 0.35)) / 0.35)))))
    return bg

# ---------------- scenes ----------------
# Each builder returns (dur, draw). draw(c, t) paints on a transparent layer, t scene-local.
# Optional draw.ticks / draw.hits = lists of scene-local times for sound sync. draw.push = push-in amount.
def kick_sprite(spec, txt, size=26):
    return text_sprite(txt.upper(), font(SANS_B, size), MUTED, track=int(size * 0.14))

def fit_font(txt, maxw, maxsize, minsize=60, face=None):
    face = face or DISPLAY; s = maxsize
    while s > minsize and max(tlen(font(face, s), w) for w in txt.split()) > maxw * 0.92: s -= 4
    return font(face, s)

def scene_type(spec, s, B):
    """Statement cards: big type, one idea each, hard-switching on the beat.
    cards: [{text, beats, size?, accent? (whole card), accent_words?, kicker?}]"""
    fg, acc = hexc(spec["fg"]), hexc(spec["accent"])
    built, t0, ticks = [], 0.0, []
    for cd in s["cards"]:
        txt = cd["text"]; f = fit_font(txt, W - 2 * M, cd.get("size", 170))
        col = acc if cd.get("accent") else fg
        tmp = Words(txt, f, col, W - 2 * M, W // 2, 0, align="center", lh=1.0)
        y = int(H / 2 - tmp.height / 2 - 20)
        wds = Words(txt, f, col, W - 2 * M, W // 2, y, align="center", lh=1.0, accent_words=cd.get("accent_words", []), accent=acc)
        kk = kick_sprite(spec, cd["kicker"]) if cd.get("kicker") else None
        d = cd["beats"] * B; stag = min(B / 2, d * 0.5 / max(1, len(wds.items)))
        built.append((t0, d, wds, stag, kk, y)); ticks += [t0 + x for x in wds.starts(0, stag)]; t0 += d
    def draw(c, t):
        for st, d, wds, stag, kk, y in built:
            if st <= t < st + d:
                lt = t - st
                if kk: paste(c, kk, W / 2 - kk.width / 2, y - 80, ease_out(prog(lt, 0, 0.3)))
                wds.draw(c, lt, stagger=stag, dur=0.36)
    draw.ticks = ticks; draw.push = 0.06
    return t0, draw

def scene_title(spec, s, B):
    fg, acc = hexc(spec["fg"]), hexc(spec["accent"])
    name = text_sprite(spec["name"], font(DISPLAY, s.get("size", 300)), fg)
    gp = 70; gl = Image.new("RGBA", (name.width + 2 * gp, name.height + 2 * gp), acc[:3] + (0,))
    a = Image.new("L", gl.size, 0); a.paste(name.getchannel("A").point(lambda v: int(v * 0.85)), (gp, gp)); gl.putalpha(a)
    gl = gl.filter(ImageFilter.GaussianBlur(40))
    tag = Words(spec["tagline"], font(SANS, 46), MUTED, W - 2 * M - 40, W // 2, 820, align="center", lh=1.25)
    kk = kick_sprite(spec, spec.get("kicker", "Jedach"))
    dur = s.get("beats", 6) * B
    def draw(c, t):
        p = prog(t, 0.0, 0.7); sc = 1 + 0.5 * (1 - expo(p)); y = 560 - name.height / 2
        paste(c, gl, W / 2 - gl.width / 2, y - gp, clamp(p * 1.5) * (0.6 + 0.25 * math.sin(t * 3)), sc)
        paste(c, sweep(name, prog(t, 0.55, 1.1), 150), W / 2 - name.width / 2, y, clamp(p * 3), sc)
        paste(c, kk, W / 2 - kk.width / 2, 360, ease_out(prog(t, 0.35, 0.5)))
        tag.draw(c, t, start=0.6, stagger=0.04, mode="rise")
    return dur, draw

def head(spec, s, y0=105):
    if not s.get("title"): return (lambda c, t: None), 60
    kk = kick_sprite(spec, s.get("kicker", "")) if s.get("kicker") else None
    f = fit_font(s["title"], W - 2 * M, s.get("size", 84), 56)
    title = Words(s["title"], f, hexc(spec["fg"]), W - 2 * M, M, y0 + (48 if kk else 0), lh=1.04, accent_words=s.get("accent_words", []), accent=hexc(spec["accent"]))
    bottom = y0 + (48 if kk else 0) + title.height
    def draw(c, t):
        if kk: paste(c, kk, M, y0, ease_out(prog(t, 0.05, 0.4)))
        title.draw(c, t, start=0.1, stagger=0.055)
    return draw, bottom

def scene_phone(spec, s, B, idx=0):
    """Single hero phone, 3D tilt settle. Title optional (prefer a type card before it instead)."""
    dur = s.get("beats", 6) * B; hd, bottom = head(spec, s)
    ph = build_phone(os.path.join(spec["_dir"], s["image"]), int(min(s.get("height", 1180), H - bottom - 60)))
    side = 1 if idx % 2 == 0 else -1
    def draw(c, t):
        hd(c, t)
        p = expo(prog(t, 0.05, 1.1))
        ang = side * (34 * (1 - p) + 6) - side * 3 * math.sin(t * 0.9)
        img = tilt(sweep(ph, prog(t, 0.7, 1.3), 60), ang)
        x = W / 2 - img.width / 2 + side * (1 - p) * 160
        y = bottom + 40 + (1 - p) * 300 - t * 14 + (H - bottom - 40 - ph.height) / 2
        draw_device(c, spec, img, x, y, clamp(prog(t, 0.05, 0.2)), rim_a=p)
    return dur, draw

def scene_focus(spec, s, B, idx=0):
    """Hero phone settles, then the camera punches in on one UI detail (rect = normalized screen coords
    [x0,y0,x1,y1]). Optional label pill once zoomed."""
    dur = s.get("beats", 6) * B
    ph = build_phone(os.path.join(spec["_dir"], s["image"]), s.get("height", 1160))
    bx, by, sw, sh = ph.info["screen"]
    x0n, y0n, x1n, y1n = s["rect"]
    px, py = W / 2 - ph.width / 2, (H - ph.height) / 2 + 20
    fx, fy = px + bx + (x0n + x1n) / 2 * sw, py + by + (y0n + y1n) / 2 * sh
    zt = clamp((W * 0.92) / ((x1n - x0n) * sw), 1, 4.0)
    lbl = None
    if s.get("label"):
        f = font(SANS_B, 40); tw = f.getlength(s["label"])
        lbl = Image.new("RGBA", (int(tw + 72), 88), (0, 0, 0, 0)); d = ImageDraw.Draw(lbl)
        d.rounded_rectangle((0, 0, lbl.width - 1, 87), 44, fill=(22, 22, 24, 240), outline=(255, 255, 255, 50), width=2)
        d.text((36, 18), s["label"], font=f, fill=hexc(spec["fg"]))
    z0 = s.get("zoom_at", 0.42)
    def draw(c, t):
        p = expo(prog(t, 0.0, 0.9))
        L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        img = tilt(sweep(ph, prog(t, 0.4, 1.0), 60), 22 * (1 - p))
        draw_device(L, spec, img, px + (ph.width - img.width) / 2, py + (1 - p) * 260, clamp(prog(t, 0, 0.15)), rim_a=p)
        q = ease_io(prog(t, dur * z0, dur * 0.32))
        if q > 0.001:
            z = lerp(1, zt, q); ax, ay = lerp(W / 2, fx, q), lerp(H / 2, fy, q); sx, sy = W / 2, lerp(H / 2, H * 0.44, q)
            L = L.crop((int(ax - sx / z), int(ay - sy / z), int(ax + (W - sx) / z), int(ay + (H - sy) / z))).resize((W, H), Image.BICUBIC)
        c.alpha_composite(L)
        if lbl:
            r = expo(prog(t, dur * (z0 + 0.3), 0.5))
            paste(c, lbl, W / 2 - lbl.width / 2, H - 230 + (1 - r) * 40, r)
    draw.push = 0.02
    return dur, draw

def scene_montage(spec, s, B):
    """Fast run: hard cuts on every beat (beats_each), varied scale/position/tilt per cut. Tempo change."""
    each = s.get("beats_each", 1) * B; imgs = s["images"]
    phones = [build_phone(os.path.join(spec["_dir"], im), 1100) for im in imgs]
    layouts = [(0, 0, 1.0), (-150, 14, 0.92), (150, -14, 0.92), (0, 0, 1.14), (-110, -10, 0.96), (110, 10, 0.96)]
    dur = each * len(imgs)
    def draw(c, t):
        k = min(len(imgs) - 1, int(t / each)); lt = t - k * each
        dx, ang, sc = layouts[k % len(layouts)]
        p = expo(prog(lt, 0, 0.35))
        img = tilt(phones[k], ang * (1 + 0.6 * (1 - p)))
        s2 = sc * (1.10 - 0.10 * p) * (1 + 0.03 * lt / each)
        x = W / 2 - img.width / 2 + dx; y = (H - img.height) / 2 + 30 - lt * 20
        draw_device(c, spec, img, x, y, 1.0, s2)
    draw.hits = [i * each for i in range(1, len(imgs))]; draw.push = 0.0
    return dur, draw

def scene_trio(spec, s, B):
    dur = s.get("beats", 6) * B; hd, bottom = head(spec, s)
    hgt = int(min(900, H - bottom - 40))
    phones = [build_phone(os.path.join(spec["_dir"], im), hgt) for im in s["images"]]
    order = [(0, -1), (2, 1), (1, 0)]
    def draw(c, t):
        hd(c, t)
        for k, (i, pos) in enumerate(order):
            p = expo(prog(t, 0.1 + k * B * 0.5, 1.0))
            if p <= 0: continue
            sc = 0.80 if pos else 1.0
            img = tilt(phones[i], -pos * (14 + 20 * (1 - p))) if pos else sweep(phones[i], prog(t, 1.0, 1.2), 55)
            x = W / 2 - img.width / 2 + pos * (275 + (1 - p) * 120)
            y = bottom + 40 + (H - bottom - 40 - hgt) / 2 + (1 - p) * 360 + (40 if pos else 0) - t * 10
            draw_device(c, spec, img, x, y, clamp(p * 3), sc, rim_a=0 if pos else p)
    draw.ticks = [0.1 + k * B * 0.5 for k in range(3)]
    return dur, draw

def scene_morph(spec, s, B):
    """ANIMATE THE MEANING: a message bubble's key words fly out and assemble into a structured record.
    from: {label, text, highlight:[{word, to:'title'|'amount'}]}; to: {title, sub, amount, icon?}; title (headline)."""
    dur = s.get("beats", 7) * B; fg, acc = hexc(spec["fg"]), hexc(spec["accent"])
    hd, bottom = head(spec, s)
    fr, to = s["from"], s["to"]
    bf = font(SANS, 54); bw = W - 2 * M; pad = 48
    lines = wrap(fr["text"], bf, bw - 2 * pad); asc, desc = bf.getmetrics(); lh = int((asc + desc) * 1.22)
    bh = len(lines) * lh + 2 * pad; ch = 200; gap = 170
    block = bh + gap + ch; top = bottom + 80
    bxx, byy = M, int(top + max(0, (H - 60 - top - block) / 2))
    bubble = Image.new("RGBA", (bw, bh), (0, 0, 0, 0)); ImageDraw.Draw(bubble).rounded_rectangle((0, 0, bw - 1, bh - 1), 44, fill=(44, 44, 50, 255))
    hl = {h["word"]: h["to"] for h in fr.get("highlight", [])}
    words = []  # (sprite_fg, sprite_acc, x, y, target|None)
    for li, line in enumerate(lines):
        cx = bxx + pad
        for w in line.split():
            key = w.strip(".,;:")
            words.append((text_sprite(w, bf, (235, 235, 240, 255)), text_sprite(w, bf, acc), cx, byy + pad + li * lh, hl.get(key)))
            cx += bf.getlength(w + " ")
    lab = kick_sprite(spec, fr.get("label", "message"))
    cw = W - 2 * M; cxx, cyy = M, byy + bh + gap
    card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0)); d = ImageDraw.Draw(card)
    d.rounded_rectangle((0, 0, cw - 1, ch - 1), 40, fill=hexc(spec["fg"], 16), outline=(255, 255, 255, 46), width=2)
    d.ellipse((36, 44, 148, 156), fill=acc[:3] + (60,))
    ic = to.get("icon", to["title"][:1]); fi = font(SANS_B, 54); d.text((92 - fi.getlength(ic) / 2, 62), ic, font=fi, fill=acc)
    tsp = text_sprite(to["title"], font(SANS_B, 54), fg); ssp = text_sprite(to.get("sub", ""), font(SANS, 34), MUTED)
    asp = text_sprite(to["amount"], font(SANS_B, 54), fg)
    targets = {"title": (cxx + 178, cyy + 30, tsp), "amount": (cxx + cw - 44 - asp.width, cyy + 30, asp)}
    arrow = text_sprite("↓", font(SANS_B, 64), acc)
    T_HL, T_CARD, T_FLY = 0.7, 1.0, 1.35
    def draw(c, t):
        hd(c, t)
        p = back_out(prog(t, 0.05, 0.45), 1.1); a = clamp(prog(t, 0.05, 0.15))
        paste(c, lab, bxx + 10, byy - 50, a)
        paste(c, bubble, bxx, byy, a, 0.9 + 0.1 * p)
        hlp = ease_out(prog(t, T_HL, 0.3))
        for k, (sf, sa, x, y, tg) in enumerate(words):
            wa = a * clamp(prog(t, 0.15 + k * 0.012, 0.2))
            if tg:
                paste(c, sf, x, y, wa * (1 - hlp)); paste(c, sa, x, y, wa * hlp * (0.4 if t > T_FLY else 1.0))
            else: paste(c, sf, x, y, wa * (1 - 0.45 * prog(t, T_FLY, 0.4)))
        cp = expo(prog(t, T_CARD, 0.6))
        paste(c, arrow, W / 2 - arrow.width / 2, byy + bh + gap / 2 - arrow.height / 2 + math.sin(t * 6) * 6, cp)
        paste(c, card, cxx, cyy + (1 - cp) * 60, cp)
        fly_i = 0
        for (sf, sa, x, y, tg) in words:
            if not tg: continue
            tx, ty, tsprite = targets[tg]; st = T_FLY + fly_i * 0.15; fly_i += 1
            q = prog(t, st, 0.55)
            if 0 < q < 1:
                e = ease_io(q); xx, yy = lerp(x, tx, e), lerp(y, ty, e) - math.sin(math.pi * e) * 90
                paste(c, sa, xx, yy, 1.0, 1 + 0.25 * math.sin(math.pi * e))
            if q >= 1: paste(c, tsprite, tx, ty, ease_out(prog(t, st + 0.55, 0.15)), 1 + 0.12 * (1 - expo(prog(t, st + 0.55, 0.3))))
        paste(c, ssp, cxx + 178, cyy + 112, ease_out(prog(t, T_FLY + 0.9, 0.3)) * cp)
    draw.ticks = [T_HL, T_FLY + 0.55, T_FLY + 0.7]
    return dur, draw

def scene_stat(spec, s, B):
    dur = s.get("beats", 6) * B; acc = hexc(spec["accent"])
    f = font(DISPLAY, s.get("size", 280))
    lbl = Words(s["label"], font(SANS, 48), hexc(spec["fg"], 210), W - 2 * M, W // 2, 840, align="center", lh=1.25)
    kk = kick_sprite(spec, s.get("kicker", "")) if s.get("kicker") else None
    m = re.match(r"^([^\d]*)([\d,\.]+)(.*)$", s["value"])
    def draw(c, t):
        p = expo(prog(t, 0.05, 1.3))
        if m:
            num = float(m.group(2).replace(",", "")); dec = "." in m.group(2); v = num * p
            txt = m.group(1) + (f"{v:,.1f}" if dec else f"{int(round(v)):,}") + m.group(3)
        else: txt = s["value"]
        spr = text_sprite(txt, f, acc)
        paste(c, spr, W / 2 - spr.width / 2, 480, clamp(p * 3), 1 + 0.3 * (1 - expo(prog(t, 0.05, 0.5))))
        if kk: paste(c, kk, W / 2 - kk.width / 2, 400, ease_out(prog(t, 0.1, 0.4)))
        lbl.draw(c, t, start=0.5, stagger=0.04, mode="rise")
    return dur, draw

def scene_stack(spec, s, B):
    dur = s.get("beats", 6) * B; fg, acc = hexc(spec["fg"]), hexc(spec["accent"])
    f = font(SANS, 40); chips = []
    for it in s["items"]:
        w, h = int(f.getlength(it) + 64), 88
        ch = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(ch)
        d.rounded_rectangle((0, 0, w - 1, h - 1), 44, fill=hexc(spec["fg"], 14), outline=(255, 255, 255, 46), width=2)
        d.text((32, 16), it, font=f, fill=fg); chips.append(ch)
    rows, cur, cw = [], [], 0
    for ch in chips:
        if cw + ch.width > W - 2 * M and cur: rows.append((cur, cw - 18)); cur, cw = [], 0
        cur.append(ch); cw += ch.width + 18
    rows.append((cur, cw - 18))
    block_h = len(rows) * 106
    hd, bottom = head(spec, {"kicker": s.get("kicker", "Built with"), "title": s.get("title", "The stack."), "size": 110}, y0=int(H / 2 - (block_h + 230) / 2))
    placed, y = [], bottom + 60
    for r, rw in rows:
        x = W / 2 - rw / 2
        for ch in r: placed.append((ch, x, y)); x += ch.width + 18
        y += 106
    st = [0.3 + i * B / 4 for i in range(len(placed))]
    def draw(c, t):
        hd(c, t)
        for i, (ch, x, y) in enumerate(placed):
            p = prog(t, st[i], 0.4)
            if p > 0: paste(c, ch, x, y, clamp(p * 4), 0.55 + 0.45 * back_out(p))
    draw.ticks = st
    return dur, draw

def scene_end(spec, s, B):
    """Minimal lockup, hard landing with the chime. Short."""
    dur = s.get("beats", 6) * B; fg, acc = hexc(spec["fg"]), hexc(spec["accent"])
    name = text_sprite(spec["name"], font(DISPLAY, 190), fg)
    line = Words(s.get("line", "Built by Senul Mapa"), font(SANS_B, 46), fg, W - 2 * M, W // 2, 760, align="center")
    sub = Words(s.get("sub", "Jedach · Colombo"), font(SANS, 36), MUTED, W - 2 * M, W // 2, 772 + line.height, align="center")
    cta = text_sprite(s["cta"], font(SANS_B, 34), fg) if s.get("cta") else None
    cy = 812 + line.height + sub.height
    def draw(c, t):
        p = expo(prog(t, 0.0, 0.5))
        paste(c, sweep(name, prog(t, 0.3, 1.0), 140), W / 2 - name.width / 2, 470, clamp(p * 4), 1 + 0.25 * (1 - p))
        line.draw(c, t, start=0.35, stagger=0.04, mode="rise")
        sub.draw(c, t, start=0.55, stagger=0.03, mode="rise")
        if cta:
            q = expo(prog(t, 0.8, 0.5))
            if q > 0.01:
                d = ImageDraw.Draw(c); bw, bh = cta.width + 64, 82; bx, by = W / 2 - bw / 2, cy + (1 - q) * 30
                d.rounded_rectangle((bx, by, bx + bw, by + bh), 41, fill=(255, 255, 255, int(18 * q)), outline=(255, 255, 255, int(70 * q)), width=2)
                paste(c, cta, W / 2 - cta.width / 2, by + 15, q)
    draw.push = 0.02
    return dur, draw

def apply_style(spec):
    """Typography + colour system from spec["style"]: {display, sans, sans_b, track (em), muted, accent2, shine}."""
    global DISPLAY, SANS, SANS_B, GRAD, MUTED, SHINE
    st = spec.get("style", {})
    DISPLAY = st.get("display", DISPLAY); SANS = st.get("sans", SANS); SANS_B = st.get("sans_b", SANS_B)
    TRACK.clear(); TRACK[DISPLAY] = st.get("track", 0.0); TRACK[SANS_B] = st.get("track_ui", 0.0)
    MUTED = hexc(st.get("muted", "#86868b")); SHINE = st.get("shine", False)
    ACCENT_SOLID[0] = hexc(spec["accent"])
    GRAD = (hexc(spec["accent"]), hexc(st["accent2"])) if st.get("accent2") else None
    _fc.clear()

BUILDERS = {"type": scene_type, "hook": scene_type, "title": scene_title, "phone": scene_phone, "focus": scene_focus,
            "montage": scene_montage, "trio": scene_trio, "morph": scene_morph, "stat": scene_stat,
            "stack": scene_stack, "end": scene_end}
DEFAULT_IN = {"title": "cut", "montage": "cut", "end": "cut", "focus": "zoom", "morph": "whip"}

def main():
    spec_path = sys.argv[1]; frames_only = "--frames" in sys.argv
    spec = json.load(open(spec_path)); spec["_dir"] = os.path.dirname(os.path.abspath(spec_path))
    apply_style(spec)
    bpm = spec.get("bpm", 120); B = 60 / bpm
    slug = spec["slug"]; out = os.path.join(ROOT, "out", slug); os.makedirs(out, exist_ok=True)
    bg = BG(spec); scenes = []; dev_i = 0
    for s in spec["scenes"]:
        if s["type"] in ("phone", "focus"): d, fn = BUILDERS[s["type"]](spec, s, B, dev_i); dev_i += 1
        else: d, fn = BUILDERS[s["type"]](spec, s, B)
        scenes.append((s, d, fn))
    n = len(scenes)
    ins = ["none"] + [s.get("in", DEFAULT_IN.get(s["type"], "whip")) for s, _, _ in scenes[1:]]
    starts = np.cumsum([0] + [d for _, d, _ in scenes]).tolist(); total = starts[-1]
    def render(i, t):
        s, d, fn = scenes[i]; L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); fn(L, t)
        return compose(bg.frame(starts[i] + t), L, t, d, ins[i], ins[i + 1] if i + 1 < n else None, i == n - 1, getattr(fn, "push", 0.045))
    if frames_only:
        fd = os.path.join(out, "frames"); os.makedirs(fd, exist_ok=True)
        for f in os.listdir(fd): os.remove(os.path.join(fd, f))
        for i, (s, d, fn) in enumerate(scenes):
            for frac in (0.08, 0.5, 0.9):
                render(i, d * frac).convert("RGB").save(os.path.join(fd, f"{i:02d}_{s['type']}_{int(frac*100):02d}.jpg"), quality=88)
        print("frames:", fd, "total", round(total, 2), "s"); return
    parts = []
    for i, (s, d, fn) in enumerate(scenes):
        tmp, fin = os.path.join(out, f"s{i:02d}.tmp.mp4"), os.path.join(out, f"s{i:02d}.mp4")
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                               "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
        for k in range(int(round(d * FPS))): ff.stdin.write(render(i, k / FPS).convert("RGB").tobytes())
        ff.stdin.close()
        if ff.wait() != 0: sys.exit(f"ffmpeg failed on scene {i}")
        os.replace(tmp, fin); parts.append(fin); print(f"scene {i} {s['type']} {d:.2f}s in={ins[i]}", flush=True)
    lst = os.path.join(out, "list.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    joined = os.path.join(out, "joined.mp4")
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined])
    types = [s["type"] for s, _, _ in scenes]
    drop = starts[types.index("title")] if "title" in types else starts[1]
    outro = starts[types.index("end")] if "end" in types else total - 3
    whooshes = [starts[i] for i in range(1, n) if ins[i] in ("whip", "zoom")]
    ticks = [starts[i] + x for i, (_, _, fn) in enumerate(scenes) for x in getattr(fn, "ticks", [])]
    hits = [starts[i] + x for i, (_, _, fn) in enumerate(scenes) for x in getattr(fn, "hits", [])]
    wav = music.compose(total, drop, outro, bpm=bpm, seed=spec.get("music_seed", 0), path=os.path.join(out, "score.wav"),
                        whooshes=whooshes, ticks=ticks, hits=hits)
    final = os.path.join(ROOT, "reels", f"{slug}.mp4"); os.makedirs(os.path.dirname(final), exist_ok=True)
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", joined, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", final])
    print("final", final, round(total, 2), "s")

if __name__ == "__main__":
    main()
