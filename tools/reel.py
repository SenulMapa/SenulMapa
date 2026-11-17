#!/usr/bin/env python3
"""Launch-reel generator. Usage: python3 tools/reel.py projects/<slug>/spec.json [--frames]

Renders a 1080x1350 (4:5, LinkedIn feed) 30fps motion promo from a JSON spec.
Scene types: hook, title, phone, window, stat, stack, end.
--frames : only write key still frames to out/<slug>/frames/ for review (no video).
"""
import json, math, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1350, 30
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "fonts")
_fc = {}

def font(name, size):
    k = (name, size)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(os.path.join(FONTS, name + ".woff"), size)
    return _fc[k]

DISPLAY = "fraunces-latin-600-normal"
DISPLAY_L = "fraunces-latin-400-normal"
SANS = "schibsted-grotesk-latin-500-normal"
SANS_B = "schibsted-grotesk-latin-700-normal"
MONO = "jetbrains-mono-latin-600-normal"

def hexc(h, a=255):
    h = h.lstrip("#"); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4)) + (a,)

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out(t): t = clamp(t); return 1 - (1 - t) ** 4
def ease_inout(t): t = clamp(t); return 4*t*t*t if t < .5 else 1 - (-2*t + 2) ** 3 / 2
def back_out(t, s=1.4): t = clamp(t) - 1; return 1 + (s + 1) * t**3 + s * t**2
def prog(t, start, dur): return clamp((t - start) / dur)

# ---------- sprites ----------
def text_sprite(txt, fnt, color):
    l, t, r, b = fnt.getbbox(txt)
    asc, desc = fnt.getmetrics()
    im = Image.new("RGBA", (r - l + 4, asc + desc + 8), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((2 - l, 4), txt, font=fnt, fill=color)
    return im

def wrap(txt, fnt, maxw):
    words, lines, cur = txt.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if fnt.getlength(test) <= maxw or not cur: cur = test
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

class Words:
    """Word sprites laid out in wrapped lines, revealed with stagger (slide up + fade)."""
    def __init__(self, txt, fnt, color, maxw, x, y, align="left", lh=1.12, accent_words=(), accent=None):
        self.items = []
        lines = wrap(txt, fnt, maxw)
        space = fnt.getlength(" ")
        asc, desc = fnt.getmetrics(); lineh = int((asc + desc) * lh)
        for li, line in enumerate(lines):
            ws = line.split(); widths = [fnt.getlength(w) for w in ws]
            total = sum(widths) + space * (len(ws) - 1)
            cx = x if align == "left" else x - total / 2
            for w, wd in zip(ws, widths):
                col = accent if accent and w.strip(".,!?—:").lower() in accent_words else color
                self.items.append((text_sprite(w, fnt, col), int(cx), y + li * lineh))
                cx += wd + space
        self.height = len(lines) * lineh
    def draw(self, canvas, t, start=0, stagger=0.045, dur=0.5, rise=36, out_t=None, out_dur=0.3):
        for i, (spr, x, y) in enumerate(self.items):
            p = ease_out(prog(t, start + i * stagger, dur))
            a = p
            if out_t is not None: a *= 1 - ease_inout(prog(t, out_t, out_dur))
            if a <= 0.01: continue
            paste(canvas, spr, x, int(y + (1 - p) * rise), a)

def paste(canvas, spr, x, y, alpha=1.0):
    if alpha < 1:
        spr = spr.copy(); a = spr.getchannel("A").point(lambda v: int(v * alpha)); spr.putalpha(a)
    canvas.alpha_composite(spr, (int(x), int(y)))

def rounded(im, r):
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, *im.size), r, fill=255)
    out = im.convert("RGBA"); out.putalpha(m); return out

def phone(img_path, h, frame_col):
    shot = Image.open(img_path).convert("RGB")
    bez = int(h * 0.022); sh = h - 2 * bez; sw = int(shot.width * sh / shot.height)
    shot = rounded(shot.resize((sw, sh), Image.LANCZOS), int(sw * 0.11))
    body = Image.new("RGBA", (sw + 2 * bez, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(body)
    d.rounded_rectangle((0, 0, body.width - 1, h - 1), int(body.width * 0.14), fill=frame_col, outline=(255, 255, 255, 38), width=3)
    body.alpha_composite(shot, (bez, bez))
    return with_shadow(body)

def window(img_path, w, frame_col, title=""):
    shot = Image.open(img_path).convert("RGB")
    bar = int(w * 0.045); sh = int(shot.height * w / shot.width)
    shot = shot.resize((w, sh), Image.LANCZOS)
    body = Image.new("RGBA", (w, sh + bar), frame_col)
    d = ImageDraw.Draw(body)
    for i, c in enumerate([(255, 95, 87), (254, 188, 46), (40, 200, 64)]):
        cx = int(bar * 0.7 + i * bar * 0.55); cy = bar // 2; r = int(bar * 0.16)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=c)
    if title:
        f = font(MONO, int(bar * 0.38)); d.text((w / 2 - f.getlength(title) / 2, bar * 0.28), title, font=f, fill=(255, 255, 255, 120))
    body.paste(shot, (0, bar))
    return with_shadow(rounded(body, int(w * 0.018)))

def with_shadow(im, blur=40, off=30):
    pad = blur * 2
    out = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad + off), (0, 0, 0, 0))
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0))
    sh.paste((0, 0, 0, 150), (pad, pad + off, pad + im.width, pad + off + im.height), im.getchannel("A"))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    out.alpha_composite(sh); out.alpha_composite(im, (pad, pad))
    out.info["pad"] = pad
    return out

# ---------- background ----------
class BG:
    def __init__(self, spec):
        self.bg = hexc(spec["bg"]); self.acc = hexc(spec["accent"])
        import numpy as np
        yy, xx = np.mgrid[0:900, 0:900]; r2 = ((xx - 450) ** 2 + (yy - 450) ** 2) / (190.0 ** 2)
        g = Image.fromarray((np.exp(-r2) * 255).astype("uint8"), "L")
        self.glow = Image.new("RGBA", g.size, self.acc[:3] + (0,)); self.glow.putalpha(g.point(lambda v: int(v * 0.30)))
        self.glow2 = Image.new("RGBA", g.size, self.acc[:3] + (0,)); self.glow2.putalpha(g.point(lambda v: int(v * 0.16)))
        # subtle dot grid
        self.grid = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(self.grid)
        for x in range(30, W, 60):
            for y in range(30, H, 60): d.ellipse((x - 1.5, y - 1.5, x + 1.5, y + 1.5), fill=(255, 255, 255, 14))
    def frame(self, T):
        c = Image.new("RGBA", (W, H), self.bg)
        c.alpha_composite(self.grid)
        x = int(W * 0.62 + math.sin(T * 0.35) * 160 - 450); y = int(H * 0.12 + math.cos(T * 0.27) * 120 - 450)
        c.alpha_composite(self.glow, (x, y))
        x2 = int(W * 0.2 + math.cos(T * 0.3) * 140 - 450); y2 = int(H * 0.85 + math.sin(T * 0.4) * 100 - 450)
        c.alpha_composite(self.glow2, (x2, y2))
        return c

# ---------- scenes ----------
M = 96  # side margin

def kicker(spec, txt):
    return text_sprite(txt.upper(), font(MONO, 26), hexc(spec["accent"]))

def scene_hook(spec, s):
    fg, acc = hexc(spec["fg"]), hexc(spec["accent"])
    lines = s["lines"]; blocks = []; y = 380
    for i, ln in enumerate(lines):
        col = acc if i == len(lines) - 1 else fg
        b = Words(ln, font(DISPLAY, 92 if i == 0 else 84), col, W - 2 * M, M, y, lh=1.08)
        blocks.append(b); y += b.height + 50
    dur = s.get("dur", 3.8)
    def draw(c, t):
        for i, b in enumerate(blocks):
            b.draw(c, t, start=0.15 + i * 1.2, out_t=dur - 0.35)
    return dur, draw

def scene_title(spec, s):
    fg, acc = hexc(spec["fg"]), hexc(spec["accent"])
    name = text_sprite(spec["name"], font(DISPLAY, 230), fg)
    tag = Words(spec["tagline"], font(SANS, 44), hexc(spec["fg"], 190), W - 2 * M, W // 2, 820, align="center", lh=1.25)
    kk = kicker(spec, spec.get("kicker", "Jedach · case file"))
    dur = s.get("dur", 3.0)
    def draw(c, t):
        out = 1 - ease_inout(prog(t, dur - 0.35, 0.35))
        p = back_out(prog(t, 0.05, 0.75), 1.2)
        sc = 0.8 + 0.2 * p
        nm = name.resize((max(1, int(name.width * sc)), max(1, int(name.height * sc))), Image.LANCZOS)
        paste(c, nm, W / 2 - nm.width / 2, 520 - nm.height / 2, clamp(prog(t, 0.05, 0.4)) * out)
        lw = int(ease_out(prog(t, 0.45, 0.6)) * 220)
        if lw > 2:
            d = ImageDraw.Draw(c); d.rounded_rectangle((W / 2 - lw / 2, 715, W / 2 + lw / 2, 721), 3, fill=acc[:3] + (int(255 * out),))
        paste(c, kk, W / 2 - kk.width / 2, 330, ease_out(prog(t, 0.3, 0.5)) * out)
        tag.draw(c, t, start=0.6, stagger=0.03, out_t=dur - 0.35)
    return dur, draw

def head_block(spec, s, y0=110):
    kk = kicker(spec, s.get("kicker", ""))
    title = Words(s["title"], font(DISPLAY, 66), hexc(spec["fg"]), W - 2 * M, M, y0 + 50, lh=1.06,
                  accent_words=set(w.lower() for w in s.get("accent_words", [])), accent=hexc(spec["accent"]))
    sub = Words(s.get("sub", ""), font(SANS, 34), hexc(spec["fg"], 170), W - 2 * M, M, y0 + 70 + title.height, lh=1.3) if s.get("sub") else None
    bottom = y0 + 70 + title.height + (sub.height if sub else 0)
    def draw(c, t, dur):
        out = 1 - ease_inout(prog(t, dur - 0.35, 0.35))
        paste(c, kk, M, y0, ease_out(prog(t, 0.05, 0.4)) * out)
        title.draw(c, t, start=0.12, stagger=0.04, out_t=dur - 0.35)
        if sub: sub.draw(c, t, start=0.45, stagger=0.02, rise=20, out_t=dur - 0.35)
    return draw, bottom

def scene_device(spec, s, kind):
    dur = s.get("dur", 3.6)
    head, bottom = head_block(spec, s)
    if kind == "phone":
        avail = H - bottom - 30
        dev = phone(os.path.join(spec["_dir"], s["image"]), min(860, avail + 60), hexc("#0b0b0d"))
    else:
        dev = window(os.path.join(spec["_dir"], s["image"]), W - 2 * M + 20, hexc("#16161a"), s.get("window_title", ""))
    pad = dev.info["pad"]
    base_y = bottom + 30 - pad
    def draw(c, t):
        head(c, t, dur)
        p = ease_out(prog(t, 0.2, 0.9)); out = ease_inout(prog(t, dur - 0.35, 0.35))
        drift = -t * 10  # slow parallax drift
        y = base_y + (1 - p) * 260 + drift + out * 80
        a = clamp(prog(t, 0.2, 0.35)) * (1 - out)
        paste(c, dev, W / 2 - dev.width / 2, y, a)
    return dur, draw

def scene_stat(spec, s):
    dur = s.get("dur", 3.2)
    fg, acc = hexc(spec["fg"]), hexc(spec["accent"])
    big = s["value"]; f = font(DISPLAY, 260)
    lbl = Words(s["label"], font(SANS, 46), hexc(spec["fg"], 200), W - 2 * M, W // 2, 820, align="center", lh=1.25)
    kk = kicker(spec, s.get("kicker", ""))
    # count-up if numeric
    import re
    m = re.match(r"^([^\d]*)([\d,\.]+)(.*)$", big)
    def draw(c, t):
        out = 1 - ease_inout(prog(t, dur - 0.35, 0.35))
        p = ease_out(prog(t, 0.1, 1.1))
        if m:
            num = float(m.group(2).replace(",", "")); dec = "." in m.group(2)
            v = num * p; txt = m.group(1) + (f"{v:,.1f}" if dec else f"{int(round(v)):,}") + m.group(3)
        else: txt = big
        spr = text_sprite(txt, f, acc)
        paste(c, spr, W / 2 - spr.width / 2, 470, clamp(prog(t, 0.05, 0.3)) * out)
        paste(c, kk, W / 2 - kk.width / 2, 380, ease_out(prog(t, 0.1, 0.4)) * out)
        lbl.draw(c, t, start=0.5, stagger=0.03, out_t=dur - 0.35)
    return dur, draw

def scene_stack(spec, s):
    dur = s.get("dur", 3.0)
    fg, acc = hexc(spec["fg"]), hexc(spec["accent"])
    f = font(MONO, 40)
    chips = []
    for it in s["items"]:
        tw = f.getlength(it); w = int(tw + 64); h = 86
        ch = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(ch)
        d.rounded_rectangle((0, 0, w - 1, h - 1), 37, fill=hexc(spec["fg"], 14), outline=acc[:3] + (150,), width=2)
        d.text((32, 17), it, font=f, fill=fg); chips.append(ch)
    rows, cur, cw = [], [], 0
    for ch in chips:
        if cw + ch.width > W - 2 * M and cur: rows.append(cur); cur, cw = [], 0
        cur.append(ch); cw += ch.width + 18
    rows.append(cur)
    head, bottom = head_block(spec, {"kicker": s.get("kicker", "Built with"), "title": s.get("title", "The stack.")}, y0=300)
    placed, y = [], bottom + 60
    for r in rows:
        x = M
        for ch in r: placed.append((ch, x, y)); x += ch.width + 18
        y += 104
    def draw(c, t):
        head(c, t, dur)
        out = ease_inout(prog(t, dur - 0.35, 0.35))
        for i, (ch, x, y) in enumerate(placed):
            p = back_out(prog(t, 0.35 + i * 0.07, 0.45))
            a = clamp(prog(t, 0.35 + i * 0.07, 0.2)) * (1 - out)
            if a <= 0.01: continue
            sc = 0.6 + 0.4 * p
            sp = ch.resize((max(1, int(ch.width * sc)), max(1, int(ch.height * sc))), Image.BILINEAR)
            paste(c, sp, x + (ch.width - sp.width) / 2, y + (ch.height - sp.height) / 2, a)
    return dur, draw

def scene_end(spec, s):
    dur = s.get("dur", 3.4)
    fg, acc = hexc(spec["fg"]), hexc(spec["accent"])
    name = text_sprite(spec["name"], font(DISPLAY, 150), fg)
    line = Words(s.get("line", "Built by Senul Mapa"), font(SANS_B, 44), fg, W - 2 * M, W // 2, 760, align="center")
    sub = Words(s.get("sub", "Jedach · Colombo"), font(SANS, 34), hexc(spec["fg"], 150), W - 2 * M, W // 2, 770 + line.height, align="center")
    cta_y = 800 + line.height + sub.height
    cta = text_sprite(s.get("cta", ""), font(MONO, 34), acc) if s.get("cta") else None
    def draw(c, t):
        paste(c, name, W / 2 - name.width / 2, 470 + (1 - ease_out(prog(t, 0, 0.7))) * 40, ease_out(prog(t, 0, 0.5)))
        line.draw(c, t, start=0.35, stagger=0.04)
        sub.draw(c, t, start=0.6, stagger=0.03, rise=16)
        if cta:
            p = ease_out(prog(t, 0.9, 0.5)); d = ImageDraw.Draw(c)
            bw, bh = cta.width + 60, 80; bx, by = W / 2 - bw / 2, cta_y + (1 - p) * 20
            d.rounded_rectangle((bx, by, bx + bw, by + bh), 40, outline=acc[:3] + (int(255 * p),), width=3)
            paste(c, cta, W / 2 - cta.width / 2, by + 16, p)
    return dur, draw

BUILDERS = {"hook": scene_hook, "title": scene_title, "stat": scene_stat, "stack": scene_stack, "end": scene_end,
            "phone": lambda sp, s: scene_device(sp, s, "phone"), "window": lambda sp, s: scene_device(sp, s, "window")}

def main():
    spec_path = sys.argv[1]; frames_only = "--frames" in sys.argv
    spec = json.load(open(spec_path)); spec["_dir"] = os.path.dirname(os.path.abspath(spec_path))
    slug = spec["slug"]; out = os.path.join(ROOT, "out", slug); os.makedirs(out, exist_ok=True)
    bg = BG(spec); T0 = 0.0; parts = []
    for i, s in enumerate(spec["scenes"]):
        dur, draw = BUILDERS[s["type"]](spec, s)
        if frames_only:
            os.makedirs(os.path.join(out, "frames"), exist_ok=True)
            for frac in (0.55, 0.85):
                c = bg.frame(T0 + dur * frac); draw(c, dur * frac)
                c.convert("RGB").save(os.path.join(out, "frames", f"{i:02d}_{s['type']}_{int(frac*100)}.jpg"), quality=90)
            T0 += dur; continue
        tmp = os.path.join(out, f"scene{i:02d}.tmp.mp4"); fin = os.path.join(out, f"scene{i:02d}.mp4")
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                               "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                               "-pix_fmt", "yuv420p", "-r", str(FPS), tmp], stdin=subprocess.PIPE)
        n = int(round(dur * FPS))
        for k in range(n):
            t = k / FPS; c = bg.frame(T0 + t); draw(c, t)
            ff.stdin.write(c.convert("RGB").tobytes())
        ff.stdin.close()
        if ff.wait() != 0: sys.exit(f"ffmpeg failed on scene {i}")
        os.replace(tmp, fin); parts.append(fin); T0 += dur
        print(f"scene {i} {s['type']} {dur}s ok", flush=True)
    if frames_only: print("frames in", os.path.join(out, "frames")); return
    lst = os.path.join(out, "list.txt")
    open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    silent = os.path.join(out, "joined.mp4")
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent])
    final = os.path.join(ROOT, "reels", f"{slug}.mp4"); os.makedirs(os.path.dirname(final), exist_ok=True)
    # silent AAC track: some platforms choke on video with no audio stream
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                           "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-shortest", "-movflags", "+faststart", final])
    print("final", final)

if __name__ == "__main__":
    main()
