"""Render the 1080x1920 / 30fps video frames and mux with the audio mix.

Usage:  python3 render.py [--preview]     (--preview = 540x960 fast draft)
Photos: put the original car photos in ./photos (jpg/png/webp). They are used in
filename order; see config.SCENES[*]["photos"] for which slot goes where.
"""
import math
import subprocess
import sys
from functools import lru_cache
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

import config as C
from timeline import TRANS, build

W, H, FPS = C.W, C.H, C.FPS
EXTS = {".jpg", ".jpeg", ".png", ".webp"}

# safe-area layout (TikTok / Reels UI: top ~200px, bottom ~420px, right ~140px)
BUG_Y = 205
HEAD_Y = 330
SUB_Y = 1335
CARD_CY = 935
CTA_CAR_CY = 772
CTA_SUB_Y = 1448


# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_io(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out_back(x, s=1.4):
    x = clamp(x) - 1
    return x * x * ((s + 1) * x + s) + 1


# ---------------------------------------------------------------- fonts / text
def font(name, size):
    return ImageFont.truetype(str(C.FONTS / name), int(size))


def montserrat(size, weight=700):
    f = ImageFont.truetype(str(C.FONTS / "Montserrat.ttf"), int(size))
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


STYLES = {  # style -> (font factory(size), base size)
    "hero": (lambda z: font("Poppins-ExtraBold.ttf", z), 118),
    "price": (lambda z: font("Poppins-ExtraBold.ttf", z), 200),
    "label": (lambda z: montserrat(z, 700), 54),
    "sub": (lambda z: montserrat(z, 600), 44),
    "chip": (lambda z: font("Poppins-SemiBold.ttf", z), 38),
}
TRACK = {"hero": 2, "price": 0, "label": 14, "sub": 8, "chip": 2}


def text_mask(txt, fnt, track=0):
    """Render text to an L mask with letter-spacing; returns (mask, ascent-offset)."""
    asc, desc = fnt.getmetrics()
    widths = [fnt.getlength(ch) for ch in txt]
    total = sum(widths) + track * (len(txt) - 1)
    pad = 40
    m = Image.new("L", (int(total) + 2 * pad, asc + desc + 2 * pad), 0)
    d = ImageDraw.Draw(m)
    x = pad
    for ch, w in zip(txt, widths):
        d.text((x, pad), ch, font=fnt, fill=255)
        x += w + track
    return m.crop(m.getbbox()) if m.getbbox() else m


def gradient_fill(size, kind):
    w, h = size
    y = np.linspace(0, 1, h)[:, None]
    if kind == "silver":
        a, b = np.array(C.SILVER_LIGHT), np.array(C.SILVER_DARK)
        t = 0.5 - 0.5 * np.cos(np.pi * 2 * (y * 0.9 + 0.05))  # light-dark-light band
        col = a * (1 - t * 0.85) + b * (t * 0.85)
        col = col + 18 * np.exp(-((y - 0.32) / 0.07) ** 2)  # specular line
    elif kind == "red":
        a, b = np.array([240, 52, 60]), np.array([180, 18, 28])
        col = a * (1 - y) + b * y
    else:
        a, b = np.array([255, 255, 255]), np.array(C.PEARL) * 0.96
        col = a * (1 - y) + b * y
    arr = np.broadcast_to(np.clip(col, 0, 255)[:, None, :], (h, w, 3)).astype(np.uint8)
    return Image.fromarray(arr, "RGB")


@lru_cache(maxsize=256)
def styled_text(txt, style, color, max_w=940, size_scale=1.0):
    make, base = STYLES[style]
    size = base * size_scale
    m = text_mask(txt, make(size), TRACK[style] * size / base)
    while m.width > max_w:  # auto-fit to safe width
        size *= 0.95
        m = text_mask(txt, make(size), TRACK[style] * size / base)
    fill = gradient_fill(m.size, color).convert("RGBA")
    fill.putalpha(m)
    # soft shadow + (red) glow
    pad = 40
    out = Image.new("RGBA", (m.width + 2 * pad, m.height + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("L", out.size, 0)
    sh.paste(m, (pad, pad + 6))
    sh = sh.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.65))
    shadow = Image.new("RGBA", out.size, (0, 0, 0, 255))
    shadow.putalpha(sh)
    out.alpha_composite(shadow)
    if color == "red":
        g = Image.new("L", out.size, 0)
        g.paste(m, (pad, pad))
        g = g.filter(ImageFilter.GaussianBlur(22)).point(lambda v: int(v * 0.45))
        glow = Image.new("RGBA", out.size, C.RED + (255,))
        glow.putalpha(g)
        out.alpha_composite(glow)
    out.alpha_composite(fill, (pad, pad))
    return out


def paste_anim(frame, img, cx, y, t, delay=0.0, dur=0.5, rise=46, out_t=None):
    """Slide-up + mask reveal; returns bottom y of the element."""
    p = ease_out((t - delay) / dur)
    if p <= 0:
        return y + img.height
    a = p
    if out_t is not None:
        a *= 1 - ease_io((t - out_t) / 0.22)
    if a <= 0:
        return y + img.height
    dy = int(rise * (1 - p))
    # mask reveal: element rises out from behind a line at its own baseline
    vis_h = int(img.height * clamp(0.25 + 0.75 * p))
    crop = img.crop((0, 0, img.width, vis_h))
    if a < 1:
        al = crop.getchannel("A").point(lambda v: int(v * a))
        crop = crop.copy()
        crop.putalpha(al)
    frame.alpha_composite(crop, (int(cx - img.width / 2), int(y + dy)))
    return y + img.height


# ---------------------------------------------------------------- photos
def load_photos():
    files = sorted(p for p in C.PHOTOS.iterdir() if p.suffix.lower() in EXTS) if C.PHOTOS.exists() else []
    if not files:
        files = placeholder_photos()
    return files


def placeholder_photos():
    """Neutral labelled frames used ONLY for layout previews when no photos are supplied."""
    out = C.BUILD / "placeholders"
    out.mkdir(parents=True, exist_ok=True)
    labels = ["FOTO 1 - DEPAN 3/4", "FOTO 2 - SISI", "FOTO 3 - BELAKANG 3/4", "FOTO 4 - DEPAN",
              "FOTO 5 - RIM / LAMPU", "FOTO 6 - DASHBOARD", "FOTO 7 - TEMPAT DUDUK", "FOTO 8 - BUT"]
    files = []
    for i, lab in enumerate(labels):
        w, h = (1600, 1200) if i != 5 else (1200, 1600)
        y = np.linspace(0, 1, h)[:, None, None]
        x = np.linspace(0, 1, w)[None, :, None]
        base = np.array([40, 44, 52]) * (1 - y) + np.array([90, 96, 108]) * y
        base = base + 25 * np.exp(-((x - 0.5) ** 2 + (y - 0.45) ** 2) / 0.08)
        im = Image.fromarray(np.clip(np.broadcast_to(base, (h, w, 3)), 0, 255).astype(np.uint8))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((w * .18, h * .45, w * .82, h * .72), radius=60, outline=(200, 205, 212), width=6)
        for cx in (w * .32, w * .68):
            d.ellipse((cx - 90, h * .64, cx + 90, h * .64 + 180), outline=(200, 205, 212), width=6)
        f = font("Poppins-SemiBold.ttf", 64)
        d.text((w / 2, h * .25), lab, font=f, fill=(230, 232, 236), anchor="mm")
        d.text((w / 2, h * .33), "(placeholder - letak foto asal dalam /photos)", font=font("Poppins-Medium.ttf", 36),
               fill=(170, 175, 182), anchor="mm")
        p = out / f"{i:02d}.jpg"
        im.save(p, quality=92)
        files.append(p)
    return files


class Shot:
    """A graded photo prepared as blurred background + feathered foreground."""

    def __init__(self, path):
        im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
        im = ImageEnhance.Contrast(im).enhance(1.06)   # gentle grade; paint colour untouched
        self.portrait = im.width / im.height < 0.8
        # foreground source (keep extra resolution for zooms)
        self.s0 = max(W / im.width, H / im.height) if self.portrait else W * 1.04 / im.width
        maxsrc = 1.35
        if self.s0 * maxsrc < 1:
            im = im.resize((int(im.width * self.s0 * maxsrc), int(im.height * self.s0 * maxsrc)), Image.LANCZOS)
            self.s0 = 1 / maxsrc
        self.fg = im.convert("RGBA")
        if not self.portrait:
            a = np.ones((im.height, im.width), np.float32)
            f = int(im.height * 0.11)
            ramp = np.linspace(0, 1, f) ** 1.5
            a[:f] *= ramp[:, None]
            a[-f:] *= ramp[::-1][:, None]
            fs = int(im.width * 0.03)
            r2 = np.linspace(0, 1, fs)
            a[:, :fs] *= r2[None]
            a[:, -fs:] *= r2[::-1][None]
            self.fg.putalpha(Image.fromarray((a * 255).astype(np.uint8)))
        # background: cover + heavy blur + darken
        sc = max(W / im.width, H / im.height) * 1.15
        bg = im.resize((int(im.width * sc / 3), int(im.height * sc / 3)), Image.BILINEAR)
        bg = bg.filter(ImageFilter.GaussianBlur(18))
        bg = ImageEnhance.Brightness(bg).enhance(0.42)
        bg = ImageEnhance.Color(bg).enhance(0.8)
        self.bg = bg.resize((int(im.width * sc), int(im.height * sc)), Image.BILINEAR)

    def render(self, zoom, ox, oy, sweep=None, scale=1.0, cy=None):
        frame = affine(self.bg, 1.0 + (zoom - 1) * 0.4, -ox * 0.35, -oy * 0.35, W / 2, H / 2, "RGB")
        cy = cy if cy is not None else (H / 2 if self.portrait else CARD_CY)
        fg = affine(self.fg, self.s0 * zoom * scale, ox, oy, W / 2, cy, "RGBA")
        if sweep is not None:
            fg = light_sweep(fg, sweep)
        frame = frame.convert("RGBA")
        frame.alpha_composite(fg)
        return frame


def affine(src, s, ox, oy, cx_out, cy_out, mode):
    cx_in, cy_in = src.width / 2, src.height / 2
    cx_out += ox
    cy_out += oy
    a = 1 / s
    data = (a, 0, cx_in - (cx_out) * a, 0, a, cy_in - (cy_out) * a)
    fill = (0, 0, 0, 0) if mode == "RGBA" else C.BLACK
    return src.transform((W, H), Image.AFFINE, data, resample=Image.BICUBIC, fillcolor=fill)


def light_sweep(fg, p):
    """Soft diagonal specular band passing over the car (p: 0..1)."""
    if not 0 < p < 1:
        return fg
    arr = np.asarray(fg).astype(np.float32)
    yy, xx = np.mgrid[0:H:4, 0:W:4]
    pos = -400 + p * (W + 800)
    d = (xx + yy * 0.35 - pos - H * 0.15)
    band = np.exp(-(d / 70.0) ** 2) * 0.16 * math.sin(math.pi * p)
    band = np.asarray(Image.fromarray((band * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR),
                      np.float32) / 255
    arr[..., :3] = arr[..., :3] + (255 - arr[..., :3]) * band[..., None] * (arr[..., 3:] / 255)
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


# ---------------------------------------------------------------- overlays
def overlays():
    y = np.linspace(0, 1, H)[:, None]
    x = np.linspace(-1, 1, W)[None, :]
    top = np.clip(1 - y / 0.36, 0, 1) ** 1.6 * 0.78
    bot = np.clip((y - 0.5) / 0.32, 0, 1) ** 1.2 * 0.9
    vig = np.clip((np.sqrt(x ** 2 * 0.6 + ((y - 0.5) * 2) ** 2 * 0.5) - 0.55) / 0.7, 0, 1) ** 2 * 0.55
    a = 1 - (1 - top) * (1 - bot) * (1 - vig)
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., :3] = C.BLACK
    arr[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def brand_bug():
    fnt = font("Poppins-Bold.ttf", 34)
    m = text_mask("KL AUTO SB", fnt, 4)
    im = Image.new("RGBA", (m.width + 40, m.height + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 4, 8, m.height + 4), fill=C.RED + (255,))
    fill = Image.new("RGBA", m.size, C.PEARL + (255,))
    fill.putalpha(m)
    im.alpha_composite(fill, (22, 4))
    return im


# ---------------------------------------------------------------- subtitles
SUB_FONT = None


def sub_font():
    global SUB_FONT
    if SUB_FONT is None:
        SUB_FONT = font("Poppins-Bold.ttf", 62)
    return SUB_FONT


def chunk_words(words, max_w=820, max_n=4):
    f = sub_font()
    chunks, cur = [], []
    for w in words:
        trial = cur + [w]
        width = f.getlength(" ".join(x["display"] for x in trial))
        if cur and (width > max_w or len(cur) >= max_n):
            chunks.append(cur)
            cur = [w]
        else:
            cur = trial
        if w["display"][-1] in ".!?":
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    return chunks


def draw_subs(frame, t, chunks, layer, sub_y=SUB_Y):
    active = None
    for i, ch in enumerate(chunks):
        start = ch[0]["t0"] - 0.06
        end = chunks[i + 1][0]["t0"] - 0.06 if i + 1 < len(chunks) else ch[-1]["t1"] + 0.5
        end = min(end, ch[-1]["t1"] + 0.9)
        if start <= t < end:
            active = (ch, start, end)
    if not active:
        return
    ch, start, end = active
    f = sub_font()
    space = f.getlength(" ")
    widths = [f.getlength(w["display"]) for w in ch]
    total = sum(widths) + space * (len(ch) - 1)
    x = 540 - total / 2
    fade = clamp((end - t) / 0.12)
    for w, wd in zip(ch, widths):
        spoken = t >= w["t0"] - 0.03
        p = ease_out((t - (w["t0"] - 0.03)) / 0.14)
        col = {"red": C.RED, "silver": (214, 220, 228)}.get(w["style"], (255, 255, 255))
        alpha = (1.0 if spoken else 0.55) * fade
        lift = int(10 * (1 - p)) if spoken else 0
        img = sub_word(w["display"], col)
        if alpha < 1:
            img = img.copy()
            img.putalpha(img.getchannel("A").point(lambda v: int(v * alpha)))
        layer.alpha_composite(img, (int(x - 20), int(sub_y - 20 + lift)))
        x += wd + space


@lru_cache(maxsize=256)
def sub_word(txt, col):
    f = sub_font()
    asc, desc = f.getmetrics()
    w = int(f.getlength(txt)) + 40
    h = asc + desc + 40
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).text((20, 20), txt, font=f, fill=255)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sh = Image.new("L", (w, h), 0)
    sh.paste(m, (0, 4))
    sh = sh.filter(ImageFilter.GaussianBlur(6)).point(lambda v: int(v * 0.85))
    s = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    s.putalpha(sh)
    out.alpha_composite(s)
    ImageDraw.Draw(out).text((20, 20), txt, font=f, fill=col + (255,),
                             stroke_width=2, stroke_fill=(0, 0, 0, 90))
    return out


# ---------------------------------------------------------------- scenes
class Renderer:
    def __init__(self):
        self.scenes, self.total = build()
        self.files = load_photos()
        self.shots = {}
        self.ov = overlays()
        self.bug = brand_bug()
        words = [w for s in self.scenes for w in s["words"]]
        self.chunks = chunk_words(words)

    def shot(self, slot):
        idx = slot % len(self.files)
        if idx not in self.shots:
            self.shots[idx] = Shot(self.files[idx])
        return self.shots[idx]

    # -- camera move per scene
    def plate(self, s, lt):
        cfg, dur = s["cfg"], s["end"] - s["start"]
        p = lt / dur
        mv = cfg["move"]
        if mv == "montage":
            n = len(cfg["photos"])
            cuts = [0, 3, 6, s["beats"]][: n + 1] if n == 3 else [s["beats"] * k / n for k in range(n + 1)]
            b = max(0.0, lt) / C.BEAT
            k = max(i for i in range(n) if b >= cuts[i])
            t0, t1 = cuts[k] * C.BEAT, cuts[k + 1] * C.BEAT
            q = (lt - t0) / (t1 - t0)
            zoom = 1.02 + 0.08 * ease_io(q)
            ox = (30 - 60 * ease_io(q)) * (1 if k % 2 else -1)
            img = self.shot(cfg["photos"][k]).render(zoom, ox, 0)
            # quick dissolve into the next sub-shot
            if k + 1 < n and lt > t1 - 0.18:
                nxt = self.shot(cfg["photos"][k + 1]).render(1.02, 30 * (1 if (k + 1) % 2 else -1), 0)
                img = Image.blend(img, nxt, ease_io((lt - (t1 - 0.18)) / 0.18))
            return img
        sweep = None
        if mv == "dolly_in":
            zoom, ox, oy = 1.0 + 0.12 * ease_out(p * 0.9) if s["i"] == 0 else 1.0 + 0.10 * ease_io(p), 0, -12 * p
        elif mv == "zoom_out":
            zoom, ox, oy = 1.14 - 0.11 * ease_io(p), 0, 0
        elif mv == "track_lr":
            zoom, ox, oy = 1.07, 50 - 100 * ease_io(p), 0
            sweep = (lt - 0.35) / 1.3
        elif mv == "track_rl":
            zoom, ox, oy = 1.07, -50 + 100 * ease_io(p), 0
        else:  # cta
            zoom = 1.0 + 0.05 * ease_io(p)
            sweep = (lt - 1.2) / 1.4
            sh = self.shot(cfg["photos"][0])
            return sh.render(zoom, 0, 0, sweep, scale=0.62 if sh.portrait else 0.8, cy=CTA_CAR_CY)
        return self.shot(cfg["photos"][0]).render(zoom, ox, oy, sweep)

    # -- headline layer per scene
    def headline(self, frame, s, lt):
        head = s["cfg"]["head"]
        if head == "cta":
            return self.cta(frame, s, lt)
        dur = s["end"] - s["start"]
        y = HEAD_Y
        hook = s["i"] == 0
        for j, (txt, style, color) in enumerate(head):
            img = styled_text(txt, style, color)
            delay = (0.05 if hook else 0.12) + j * (C.BEAT if style == "price" else 0.16)
            if style == "price":
                delay = C.BEAT
            if hook and j == 0:  # punchy slam-in for the opening hook
                p = ease_out_back((lt - 0.04) / 0.38)
                if p > 0:
                    sc = 1.25 - 0.25 * p
                    im2 = img.resize((int(img.width * sc), int(img.height * sc)), Image.BICUBIC)
                    im2.putalpha(im2.getchannel("A").point(lambda v: int(v * clamp(p * 1.4))))
                    frame.alpha_composite(im2, (int(540 - im2.width / 2), int(y - (im2.height - img.height) / 2)))
                y_next = y + img.height
            else:
                y_next = paste_anim(frame, img, 540, y, lt, delay, 0.48)
            if style == "label":  # thin red accent rule under labels
                p = ease_out((lt - delay - 0.1) / 0.4)
                if p > 0:
                    d = ImageDraw.Draw(frame)
                    wline = int(90 * p)
                    d.rectangle((540 - wline // 2, y_next - 34, 540 + wline // 2, y_next - 28), fill=C.RED + (255,))
            y = y_next - (40 if style != "price" else 70)

    def cta(self, frame, s, lt):
        cta = C.CTA
        d = ImageDraw.Draw(frame)
        y = 262
        brand = styled_text(cta["brand"], "hero", "silver", 900, 1.0)
        paste_anim(frame, brand, 540, y, lt, 0.05, 0.5)
        y += brand.height - 18
        p = ease_out((lt - 0.35) / 0.45)
        if p > 0:
            wl = int(200 * p)
            d.rectangle((540 - wl // 2, y, 540 + wl // 2, y + 6), fill=C.RED + (255,))
        y -= 4
        paste_anim(frame, styled_text(cta["title"], "sub", "pearl", 940, 0.95), 540, y, lt, 0.3, 0.5)
        # lower info block (below the car card)
        y = 1040
        model = styled_text(cta["model"], "chip", "silver", 940, 1.0)
        paste_anim(frame, model, 540, y, lt, 0.55, 0.5)
        y += model.height - 22
        pc = ease_out((lt - 0.75) / 0.45)
        if pc > 0:
            for cx, txt, col in ((290, cta["deposit"], "pearl"), (790, cta["monthly"], "pearl")):
                chip = styled_text(txt, "chip", col, 420, 0.95)
                bw, bh = chip.width - 80 + 56, chip.height - 80 + 34
                yy = y + int(30 * (1 - pc))
                box = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
                ImageDraw.Draw(box).rounded_rectangle((0, 0, bw - 1, bh - 1), radius=bh // 2,
                                                      fill=(11, 13, 18, int(150 * pc)),
                                                      outline=(205, 210, 218, int(200 * pc)), width=2)
                frame.alpha_composite(box, (int(cx - bw / 2), int(yy)))
                c2 = chip.copy()
                c2.putalpha(c2.getchannel("A").point(lambda v: int(v * pc)))
                frame.alpha_composite(c2, (int(cx - chip.width / 2), int(yy + bh / 2 - chip.height / 2)))
        y += 104
        ag = styled_text("AGREEMENT DIRECT OWNER", "label", "silver", 900, 0.66)
        paste_anim(frame, ag, 540, y, lt, 0.95, 0.45)
        y += ag.height - 62
        # WhatsApp button — pops in as the number is spoken, pulses, glint on final accent
        phone_t = [w for w in s["words"] if w["display"].startswith("017")][0]["t0"] - s["start"]
        pb = ease_out_back((lt - min(1.2, phone_t - 0.6)) / 0.5, 1.2)
        if pb > 0:
            self.whatsapp_button(frame, 540, y, lt, pb, phone_t)

    def whatsapp_button(self, frame, cx, y, lt, pb, phone_t):
        label = styled_text("WHATSAPP  " + C.CTA["phone"], "hero", "pearl", 760, 0.52)
        icon_r = 34
        bw = label.width - 80 + icon_r * 2 + 50 + 70
        bh = 124
        pulse = 1 + 0.025 * math.sin(2 * math.pi * max(0, lt - phone_t) / (2 * C.BEAT)) * (lt > phone_t)
        sc = pb * pulse
        btn = Image.new("RGBA", (bw + 80, bh + 80), (0, 0, 0, 0))
        g = Image.new("L", btn.size, 0)
        ImageDraw.Draw(g).rounded_rectangle((40, 48, 40 + bw, 48 + bh), radius=bh // 2, fill=170)
        g = g.filter(ImageFilter.GaussianBlur(20))
        glow = Image.new("RGBA", btn.size, C.RED + (255,))
        glow.putalpha(g)
        btn.alpha_composite(glow)
        body = Image.new("RGBA", btn.size, (0, 0, 0, 0))
        bd = ImageDraw.Draw(body)
        bd.rounded_rectangle((40, 40, 40 + bw, 40 + bh), radius=bh // 2, fill=C.RED + (255,))
        # chat-bubble glyph (generic, not a brand logo)
        ix, iy = 40 + 34 + icon_r, 40 + bh // 2
        bd.ellipse((ix - icon_r, iy - icon_r, ix + icon_r, iy + icon_r), outline=(255, 255, 255, 255), width=6)
        bd.polygon([(ix - icon_r + 4, iy + icon_r - 14), (ix - icon_r - 6, iy + icon_r + 6),
                    (ix - icon_r + 22, iy + icon_r - 2)], fill=(255, 255, 255, 255))
        bd.rounded_rectangle((ix - 13, iy - 15, ix + 13, iy + 15), radius=8, outline=(255, 255, 255, 255), width=5)
        btn.alpha_composite(body)
        btn.alpha_composite(label, (ix + icon_r + 4, 40 + bh // 2 - label.height // 2 + 4))
        # glint
        gp = (lt - (phone_t + 1.6)) / 0.6
        if 0 < gp < 1:
            arr = np.asarray(btn).astype(np.float32)
            xx = np.arange(btn.width)[None, :] + np.arange(btn.height)[:, None] * 0.5
            band = np.exp(-((xx - gp * (btn.width + 200)) / 40) ** 2) * 0.55
            arr[..., :3] += (255 - arr[..., :3]) * band[..., None] * (arr[..., 3:] / 255)
            btn = Image.fromarray(arr.astype(np.uint8), "RGBA")
        if sc != 1:
            btn = btn.resize((max(1, int(btn.width * sc)), max(1, int(btn.height * sc))), Image.BICUBIC)
        frame.alpha_composite(btn, (int(cx - btn.width / 2), int(y + (bh + 80) * (1 - sc) / 2)))

    # -- full scene frame (plate + headline), before global overlays
    def scene_frame(self, s, lt):
        f = self.plate(s, lt)
        f.alpha_composite(self.ov)
        self.headline(f, s, lt)
        return f

    def frame(self, n):
        t = n / FPS
        idx = max(i for i, s in enumerate(self.scenes) if t >= s["start"] or i == 0)
        s = self.scenes[idx]
        half = TRANS / 2
        nxt = self.scenes[idx + 1] if idx + 1 < len(self.scenes) else None
        if nxt and t > nxt["start"] - half:
            idx, s = idx, s
        cur_f = None
        # transition window around each cut
        if idx > 0 and t < s["start"] + half:
            prev = self.scenes[idx - 1]
            q = (t - (s["start"] - half)) / TRANS
            cur_f = self.transition(self.scene_frame(prev, t - prev["start"]),
                                    self.scene_frame(s, t - s["start"]), q, idx)
        elif nxt and t >= nxt["start"] - half:
            q = (t - (nxt["start"] - half)) / TRANS
            cur_f = self.transition(self.scene_frame(s, t - s["start"]),
                                    self.scene_frame(nxt, t - nxt["start"]), q, idx + 1)
        else:
            cur_f = self.scene_frame(s, t - s["start"])
        # hook: flash in from black
        if t < 0.18:
            k = ease_out(t / 0.18)
            cur_f = Image.blend(Image.new("RGBA", (W, H), C.BLACK + (255,)), cur_f, k)
        # global layers
        last = self.scenes[-1]
        if t < last["start"] + 0.3:
            cur_f.alpha_composite(self.bug, (64, BUG_Y))
        draw_subs(cur_f, t, self.chunks, cur_f, CTA_SUB_Y if t >= last["start"] else SUB_Y)
        # final fade
        if t > self.total - 0.5:
            k = ease_io((t - (self.total - 0.5)) / 0.5)
            cur_f = Image.blend(cur_f, Image.new("RGBA", (W, H), C.BLACK + (255,)), k)
        return cur_f.convert("RGB")

    def transition(self, a, b, q, k):
        """Directional push with controlled motion blur (alternating direction)."""
        q = clamp(q)
        e = ease_io(q)
        dirn = 1 if k % 2 else -1
        A = np.asarray(a.convert("RGB"), np.float32)
        B = np.asarray(b.convert("RGB"), np.float32)
        shift = int(W * 0.18 * e) * dirn
        shift_b = int(-W * 0.18 * (1 - e)) * dirn
        blur = int(60 * math.sin(math.pi * q))
        A2 = mblur(hshift(A, -shift), blur)
        B2 = mblur(hshift(B, -shift_b), blur)
        out = A2 * (1 - e) + B2 * e
        return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).convert("RGBA")


def hshift(arr, dx):
    """Shift horizontally by dx px (positive = content moves left), clamping edges."""
    dx = int(dx)
    if dx == 0:
        return arr
    if dx > 0:
        return np.concatenate([arr[:, dx:], np.repeat(arr[:, -1:], dx, axis=1)], axis=1)
    return np.concatenate([np.repeat(arr[:, :1], -dx, axis=1), arr[:, :dx]], axis=1)


def mblur(arr, px):
    if px < 2:
        return arr
    acc = np.zeros_like(arr)
    taps = 6
    for i in range(taps):
        acc += hshift(arr, (i / (taps - 1) - 0.5) * px)
    return acc / taps


# ---------------------------------------------------------------- driver
R = None


def _init():
    global R
    R = Renderer()


def _render(n):
    return R.frame(n).tobytes()


def main():
    preview = "--preview" in sys.argv
    only = [a for a in sys.argv[1:] if a.startswith("--frames=")]
    scenes, total = build()
    nframes = int(round(total * FPS))
    out = C.BUILD / ("preview.mp4" if preview else "KLAUTOSB_ProtonX50_SambungBayar_1080x1920.mp4")
    if only:  # stills for QA: --frames=0,45,300
        _init()
        for n in map(int, only[0].split("=")[1].split(",")):
            R.frame(n).save(C.BUILD / f"still_{n:04d}.jpg", quality=90)
        return
    vf = ["-vf", "scale=540:960:flags=lanczos"] if preview else []
    enc = ["-c:v", "libx264", "-preset", "veryfast" if preview else "slow", "-crf", "23" if preview else "14",
           "-maxrate", "30M", "-bufsize", "40M", "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", str(FPS)]
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", str(C.BUILD / "mix.wav"), *vf, *enc,
           "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-movflags", "+faststart", "-shortest", str(out)]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(processes=max(1, __import__("os").cpu_count()), initializer=_init) as pool:
        for i, buf in enumerate(pool.imap(_render, range(nframes), chunksize=4)):
            ff.stdin.write(buf)
            if i % 60 == 0:
                print(f"frame {i}/{nframes}", flush=True)
    ff.stdin.close()
    ff.wait()
    print("wrote", out)


if __name__ == "__main__":
    main()
