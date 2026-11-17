"""Build the KL AUTO SB Proton X50 promo as a HyperFrames project.

    python3 tools/build.py          # voice + music + photos + index.html
    python3 tools/build.py --html   # only regenerate index.html (keeps audio)

Then:  ./hf.sh check  ->  ./hf.sh preview  ->  ./hf.sh render
Script (casual Malaysian Malay), prices and phone number live in SCRIPT / CTA below.
Token syntax:  word | DISPLAY|spoken-words | *red | ^silver
"""
import asyncio
import html
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

HF = Path(__file__).resolve().parents[1]
ROOT = HF.parent
sys.path.insert(0, str(ROOT / "src"))
import audio as A  # noqa: E402  (music + sfx synth, reused read-only)
import edge_tts  # noqa: E402
import tts as _tts  # noqa: E402
from tts import PROXY, norm, parse_tokens, tighten  # noqa: E402

_tts.MAX_GAP, _tts.KEEP_GAP = 0.40, 0.30   # snappier sentence pauses

ASSETS = HF / "assets"
AUD = ASSETS / "audio"
PH = ASSETS / "photos"

VOICE, RATE, PITCH = "ms-MY-OsmanNeural", "+6%", "-4Hz"   # "Suara B", calmer: slower, lower, no "!"
BPM = 118
BEAT = 60 / BPM
SR = 48000

# --------------------------------------------------------------------- script
SCRIPT = [
    dict(  # 1 HOOK
        vo="Ada satu unit ^Proton ^X50|X-fifty ^Executive ^Spec nak dijual secara *sambung *bayar *berdeposit.",
        head=[("SAMBUNG BAYAR", "hero", "pearl"), ("LEASE TO OWN", "label", "silver")],
        photos=["01_hitam_depan34.jpg"], move="push", trans=None, min_beats=0),
    dict(  # 2 MODEL
        vo="^Proton ^X50|X-fifty ^Executive ^Facelift ^2026.|dua-ribu-dua-puluh-enam. Kereta baru, puas hati kereta baru.",
        head=[("PROTON X50", "hero", "silver"), ("EXECUTIVE FACELIFT 2026", "label", "pearl")],
        photos=["02_hitam_depan.jpg"], move="rise", trans="whip-left", min_beats=8),
    dict(  # 3 DEPOSIT
        vo="*Deposit? *RM13,000.|tiga-belas-ribu-ringgit.",
        head=[("DEPOSIT", "label", "silver"), ("RM13,000", "price", "red")],
        photos=["03_hitam_belakang34.jpg"], move="pull", trans="flash", min_beats=6),
    dict(  # 4 BULANAN
        vo="*Bulanan pula, *RM1,300.|seribu-tiga-ratus-ringgit. *Loan *9|sembilan *tahun.",
        head=[("BULANAN", "label", "silver"), ("RM1,300", "price", "red"), ("LOAN 9 TAHUN", "tag", "pearl")],
        photos=["04_hitam_badge.jpg"], move="push", trans="whip-up", min_beats=6),
    dict(  # 5 AGREEMENT
        vo="Yang bestnya, ^agreement *terus *dengan *owner. Semua urusan kita bantu sampai selesai.",
        head=[("AGREEMENT", "label", "silver"), ("DIRECT OWNER", "hero", "pearl"), ("PROSES MUDAH & PANTAS", "tag", "pearl")],
        photos=["05_hitam_belakang.jpg"], move="track", trans="zoom", min_beats=8),
    dict(  # 6 INTERIOR MONTAGE
        vo="Tengoklah interior dia. ^Moden, ^selesa, ruang pun ^luas. Memang ngam untuk bawa ^family.",
        head=[("MODERN INTERIOR", "hero-s", "pearl"), ("COMFORTABLE FAMILY SUV", "label", "silver")],
        photos=["06_stereng.jpg", "07_tempat_duduk_depan.jpg", "08_tempat_duduk_belakang.jpg"],
        move="montage", trans="whip-left", min_beats=8),
    dict(  # 7 CLOSING & CTA
        vo="Berminat dengan kereta? *WhatsApp sekarang. *017-203|kosong-satu-tujuh,-dua-kosong-tiga, *6099.|enam-kosong-sembilan-sembilan. Jangan tunggu lama.",
        head="cta",
        photos=["01_hitam_depan34.jpg"], move="cta", trans="dip", min_beats=0),
]
CTA = dict(q="NAK VIEW KERETA?", sub="WHATSAPP SEKARANG", phone="017-203 6099")

VO_LEAD = 0.12
TAIL_PAD = 0.12
CTA_HOLD = 1.1


# --------------------------------------------------------------------- voice
async def synth(i, line):
    toks = parse_tokens(line)
    text = " ".join(t["spoken"] for t in toks)
    comm = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH, boundary="WordBoundary", proxy=PROXY)
    audio, bounds = bytearray(), []
    async for ch in comm.stream():
        if ch["type"] == "audio":
            audio += ch["data"]
        elif ch["type"] == "WordBoundary":
            bounds.append(dict(t0=ch["offset"] / 1e7, t1=(ch["offset"] + ch["duration"]) / 1e7, text=ch["text"]))
    mp3 = AUD / f"vo_{i}.mp3"
    mp3.write_bytes(bytes(audio))
    words = [b for b in bounds if norm(b["text"])]
    wi = 0
    for k, t in enumerate(toks):
        target = "".join(norm(w) for w in t["spoken"].split())
        got, acc = [], ""
        while wi < len(words) and len(acc) < len(target):
            acc += norm(words[wi]["text"])
            got.append(words[wi])
            wi += 1
        if not got:
            t0 = toks[k - 1]["t1"] if k else 0.0
            got = [dict(t0=t0, t1=t0 + 0.2)]
        t["t0"], t["t1"] = got[0]["t0"], got[-1]["t1"]
    wav = AUD / f"vo_{i}.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp3), "-ar", str(SR), "-ac", "1", str(wav)], check=True)
    mp3.unlink()
    dur = tighten(wav, toks)
    return dict(tokens=toks, duration=dur)


def make_voice():
    AUD.mkdir(parents=True, exist_ok=True)

    async def run():
        return [await synth(i, s["vo"]) for i, s in enumerate(SCRIPT)]
    res = asyncio.run(run())
    (AUD / "vo_timings.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    return res


# --------------------------------------------------------------------- timeline
def timeline(vo):
    t, scenes = 0.0, []
    for i, (cfg, v) in enumerate(zip(SCRIPT, vo)):
        last = i == len(SCRIPT) - 1
        need = VO_LEAD + v["duration"] + (CTA_HOLD if last else TAIL_PAD)
        beats = max(cfg["min_beats"] if i in (0, len(SCRIPT) - 1) else 0, math.ceil(need / (BEAT / 2)) / 2)  # half-beat grid
        words = [dict(w, t0=round(w["t0"] + t + VO_LEAD, 3), t1=round(w["t1"] + t + VO_LEAD, 3)) for w in v["tokens"]]
        scenes.append(dict(i=i, start=round(t, 3), end=round(t + beats * BEAT, 3), beats=beats,
                           vo_start=t + VO_LEAD, words=words, cfg=cfg))
        t += beats * BEAT
    return scenes, round(t, 3)


# --------------------------------------------------------------------- audio stems
def make_audio(scenes, total):
    n = int(total * SR)
    vo = np.zeros(n)
    for s in scenes:
        raw = AUD / f"vo_{s['i']}.raw"
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(AUD / f"vo_{s['i']}.wav"), "-af",
            "highpass=f=85,equalizer=f=220:t=q:w=1:g=-1.5,equalizer=f=3200:t=q:w=1.2:g=2.5,"
            "acompressor=threshold=-20dB:ratio=3:attack=4:release=90:makeup=3,alimiter=limit=0.93",
            "-ar", str(SR), "-ac", "1", "-f", "f32le", str(raw)], check=True)
        A.place(vo, np.fromfile(raw, dtype=np.float32).astype(np.float64), s["vo_start"])
        raw.unlink()
    # audio.py expects cfg["head"] on scenes; give it our scenes as-is
    mus, _ = A.music(total, scenes)
    fx = A.sfx(total, scenes)
    from scipy.signal import lfilter
    rel = np.exp(-1 / (0.35 * SR))
    env = lfilter([1 - rel], [1, -rel], np.abs(vo))
    env = np.minimum(1, env / (np.percentile(env, 95) + 1e-9))
    duck = 1 - 0.5 * env
    mus = mus / (np.abs(mus).max() + 1e-9) * 0.30 * duck
    fx = fx * 0.55
    fade = int(0.6 * SR)
    mus[:, -fade:] *= np.linspace(1, 0, fade)
    # one gain for all stems so their sum lands at -14 LUFS
    mix = np.stack([mus[0] + fx + vo, mus[1] + fx + vo]).T.astype(np.float32)
    mix.tofile(AUD / "_mix.raw")
    out = subprocess.run(["ffmpeg", "-hide_banner", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", str(AUD / "_mix.raw"),
                          "-af", "loudnorm=I=-14:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
    (AUD / "_mix.raw").unlink()
    meas = json.loads(out[out.rindex("{"):])
    g = 10 ** ((-14 - float(meas["input_i"])) / 20)
    peak = np.abs(mix).max() * g
    if peak > 0.89:  # keep ~-1 dBTP headroom
        g *= 0.89 / peak
    for name, data in (("music", mus.T), ("sfx", np.stack([fx, fx]).T), ("vo", np.stack([vo, vo]).T)):
        p = AUD / f"{name}.raw"
        (data * g).astype(np.float32).tofile(p)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", str(p),
                        "-c:a", "pcm_s16le", str(AUD / f"{name}.wav")], check=True)
        p.unlink()
    print(f"audio stems: gain {20 * math.log10(g):+.1f} dB, mix in {float(meas['input_i']):.1f} LUFS")


# --------------------------------------------------------------------- photos
def make_photos():
    PH.mkdir(parents=True, exist_ok=True)
    for name in sorted({p for s in SCRIPT for p in s["photos"]}):
        im = ImageOps.exif_transpose(Image.open(ROOT / "photos" / name)).convert("RGB")
        im = ImageEnhance.Contrast(im).enhance(1.05)
        fg = im.copy()
        fg.thumbnail((2400, 2400), Image.LANCZOS)
        fg.save(PH / name, quality=90)
        sc = max(1080 / im.width, 1920 / im.height) * 1.2
        bg = im.resize((int(im.width * sc / 4), int(im.height * sc / 4)), Image.BILINEAR)
        bg = bg.filter(ImageFilter.GaussianBlur(14))
        bg = ImageEnhance.Color(ImageEnhance.Brightness(bg).enhance(0.45)).enhance(0.8)
        bg.resize((int(im.width * sc / 2), int(im.height * sc / 2)), Image.BILINEAR).save(PH / f"bg_{name}", quality=85)


def is_portrait(name):
    w, h = Image.open(PH / name).size
    return w / h < 0.8


# --------------------------------------------------------------------- html
def esc(s):
    return html.escape(s, quote=True)


def head_html(i, head):
    out = []
    for j, (txt, style, color) in enumerate(head):
        out.append(f'<div class="line {style}"><span id="h{i}_{j}" class="{color}">{esc(txt)}</span></div>')
    return f'<div class="heads">{"".join(out)}</div>'


def chunks(words, max_n=5, max_chars=24):
    """Phrase-based groups: break at sentence ends, at commas once a group has 2+ words,
    or at the size limit, so every caption reads as a tidy phrase (max 2 short lines)."""
    out, cur = [], []
    for w in words:
        if cur and (len(cur) >= max_n or len(" ".join(x["display"] for x in cur + [w])) > max_chars):
            out.append(cur)
            cur = []
        cur.append(w)
        end = w["display"][-1]
        if end in ".!?" or (end == "," and len(cur) >= 2):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    # never leave a lonely single word if it can join the previous phrase
    merged = []
    for g in out:
        if merged and len(g) == 1 and len(merged[-1]) < max_n and merged[-1][-1]["display"][-1] not in ".!?":
            merged[-1] = merged[-1] + g
        else:
            merged.append(g)
    return merged


PRE = {"whip-left": 0.18, "whip-up": 0.18, "zoom": 0.2, "flash": 0.0, "dip": 0.0, None: 0.0}
POST = {"whip-left": 0.18, "whip-up": 0.18, "zoom": 0.2, "flash": 0.0, "dip": 0.0, None: 0.0}


def make_html(scenes, total):
    body, js = [], []
    J = js.append
    for s in scenes:
        i, cfg = s["i"], s["cfg"]
        nxt = scenes[i + 1]["cfg"]["trans"] if i + 1 < len(scenes) else None
        c0 = max(0.0, s["start"] - PRE[cfg["trans"]])
        c1 = min(total, s["end"] + POST[nxt])
        dur = round(c1 - c0, 3)
        s["clip"] = (round(c0, 3), dur)
        inner = []
        if cfg["move"] == "montage":
            n = len(cfg["photos"])
            cuts = [0, 3, 6, s["beats"]]
            for k, ph in enumerate(cfg["photos"]):
                a, b = s["start"] + cuts[k] * BEAT, s["start"] + cuts[k + 1] * BEAT
                if k == 0:
                    a = c0
                if k == n - 1:
                    b = c0 + dur
                inner.append(
                    f'<div id="s{i}m{k}" class="sub clip" data-start="{a:.3f}" data-duration="{b - a:.3f}" data-track-index="{10 + k}">'
                    f'<div id="s{i}m{k}kb" class="kb"><img class="full" src="assets/photos/{ph}" alt="" /></div></div>')
                J(f'tl.fromTo("#s{i}m{k}kb",{{scale:1.12,x:{-30 if k % 2 else 30}}},{{scale:1.03,x:{30 if k % 2 else -30},duration:{b - a:.3f},ease:"none"}},{a:.3f});')
        else:
            ph = cfg["photos"][0]
            portrait = is_portrait(ph)
            card_cls = "full" if portrait else ("card cta-card" if cfg["move"] == "cta" else "card")
            inner.append(f'<img id="s{i}bg" class="bg" src="assets/photos/bg_{ph}" alt="" />')
            inner.append(f'<div id="s{i}kb" class="kb"><img class="{card_cls}" src="assets/photos/{ph}" alt="" /></div>')
            if cfg["move"] in ("rise", "cta"):
                inner.append(f'<div id="s{i}sw" class="sweep"></div>')
            d = s["end"] - s["start"] + POST[nxt]
            t0 = c0
            mv = {
                "push": ("{scale:1.0}", "{scale:1.12}", "power1.out"),
                "pull": ("{scale:1.16}", "{scale:1.03}", "sine.inOut"),
                "rise": ("{scale:1.08,y:40}", "{scale:1.08,y:-40}", "sine.inOut"),
                "track": ("{scale:1.1,x:60}", "{scale:1.1,x:-60}", "sine.inOut"),
                "cta": ("{scale:1.0}", "{scale:1.05}", "sine.inOut"),
            }[cfg["move"]]
            J(f'tl.fromTo("#s{i}kb",{mv[0]},{{...{mv[1]},duration:{d + PRE[cfg["trans"]]:.3f},ease:"{mv[2]}"}},{t0:.3f});')
            J(f'tl.fromTo("#s{i}bg",{{scale:1.0}},{{scale:1.05,duration:{d + PRE[cfg["trans"]]:.3f},ease:"none"}},{t0:.3f});')
            if cfg["move"] in ("rise", "cta"):
                sw = s["start"] + (0.4 if cfg["move"] == "rise" else 1.4)
                J(f'tl.fromTo("#s{i}sw",{{x:-1300}},{{x:1300,duration:1.3,ease:"power1.inOut"}},{sw:.3f});')
        inner.append('<div class="shade"></div>')
        if cfg["head"] == "cta":
            inner.append(cta_html(i))
            cta_js(J, s)
        elif cfg["head"]:
            inner.append(head_html(i, cfg["head"]))
            pidx = next((k for k, h in enumerate(cfg["head"]) if h[1] == "price"), None)
            for j, (txt, style, color) in enumerate(cfg["head"]):
                at = s["start"] + (0.0 if i == 0 else 0.15) + (BEAT if style == "price" else 0.14 * j)
                if pidx is not None and j > pidx:
                    at = s["start"] + 0.15 + BEAT + 0.35
                elif style == "tag":
                    at = s["start"] + 0.15 + 0.14 * j + 0.2
                if i == 0:  # frame 0 is the thumbnail: hook title already on screen
                    J(f'tl.fromTo("#h{i}_{j}",{{scale:1.08}},{{scale:1,duration:0.35,ease:"power3.out"}},0);')
                elif style == "tag":
                    J(f'tl.fromTo("#h{i}_{j}",{{opacity:0,y:18}},{{opacity:1,y:0,duration:0.4,ease:"power3.out"}},{at:.3f});')
                elif style == "price":
                    J(f'tl.fromTo("#h{i}_{j}",{{yPercent:110,scale:0.9}},{{yPercent:0,scale:1,duration:0.5,ease:"back.out(1.5)"}},{at:.3f});')
                else:
                    J(f'tl.fromTo("#h{i}_{j}",{{yPercent:110}},{{yPercent:0,duration:0.5,ease:"power3.out"}},{at:.3f});')
        body.append(
            f'<div id="s{i}" class="scene clip" data-start="{c0:.3f}" data-duration="{dur:.3f}" data-track-index="{1 + i % 2}" '
            f'data-track-kind="graphics" style="z-index:{10 + i}"><div id="s{i}cam" class="cam">{"".join(inner)}</div></div>')
        transition_js(J, scenes, s)

    # captions
    words = [w for s in scenes for w in s["words"]]
    groups = chunks(words)
    caps = []
    cta_start = scenes[-1]["start"]
    for g_i, g in enumerate(groups):
        start = g[0]["t0"] - 0.08
        end = (groups[g_i + 1][0]["t0"] - 0.1) if g_i + 1 < len(groups) else min(total, g[-1]["t1"] + 0.8)
        end = min(end, g[-1]["t1"] + 0.9)
        cls = "grp cta-pos" if start >= cta_start - 0.05 else "grp"
        spans = " ".join(f'<span class="w {w["style"] or ""}">{esc(w["display"])}</span>' for w in g)
        caps.append(f'<div id="c{g_i}" class="{cls}"><span id="c{g_i}p" class="pill">{spans}</span></div>')
        J(f'tl.set("#c{g_i}",{{opacity:1,visibility:"visible"}},{start:.3f});')
        J(f'tl.fromTo("#c{g_i}p",{{opacity:0}},{{opacity:1,duration:0.14,ease:"power2.out"}},{start:.3f});')
        J(f'tl.to("#c{g_i}",{{opacity:0,duration:0.1,ease:"power2.in"}},{end - 0.1:.3f});')
        J(f'tl.set("#c{g_i}",{{opacity:0,visibility:"hidden"}},{end:.3f});')
    body.append(f'<div id="captions" class="clip" data-start="0" data-duration="{total}" data-track-index="5" '
                f'data-track-kind="captions" style="z-index:40">{"".join(caps)}</div>')
    # brand bug (hidden on the end card, which carries the brand itself)
    body.append(f'<div id="bug" class="clip" data-start="0" data-duration="{total}" data-track-index="6" '
                f'data-track-kind="graphics" data-layout-allow-safe-zone style="z-index:41"><span class="bar"></span><span class="bt">KL AUTO SB</span></div>')
    body.append(f'<div id="fx" class="clip" data-start="0" data-duration="{total}" data-track-index="7" data-track-kind="graphics" style="z-index:42">'
                f'<div id="flash"></div><div id="dip"></div></div>')
    for k, (name, idx) in enumerate((("music", 8), ("sfx", 9), ("vo", 4))):
        body.append(f'<audio id="{name}" class="clip" src="assets/audio/{name}.wav" data-start="0" data-duration="{total}" data-track-index="{idx}"></audio>')

    page = TEMPLATE.replace("%%TOTAL%%", f"{total}").replace("%%BODY%%", "\n      ".join(body)).replace("%%JS%%", "\n      ".join(js))
    (HF / "index.html").write_text(page)
    print(f"index.html: {len(scenes)} scenes, {len(groups)} caption groups, {total:.2f}s")


def transition_js(J, scenes, s):
    """Animate the seam INTO scene s (the outgoing scene is the previous one)."""
    i, kind = s["i"], s["cfg"]["trans"]
    if not kind:
        return
    b = s["start"]
    prev = f"#s{i - 1}cam"
    cur = f"#s{i}cam"
    if kind in ("whip-left", "whip-up"):
        ax, size = ("x", 1080) if kind == "whip-left" else ("y", 1920)
        J(f'tl.fromTo("{prev}",{{{ax}:0}},{{{ax}:{-size},duration:0.36,ease:"power2.inOut"}},{b - 0.18:.3f});')
        J(f'tl.fromTo("{cur}",{{{ax}:{size}}},{{{ax}:0,duration:0.36,ease:"power2.inOut"}},{b - 0.18:.3f});')
    elif kind == "zoom":
        J(f'tl.fromTo("{prev}",{{scale:1,opacity:1}},{{scale:1.6,opacity:0,duration:0.4,ease:"power2.in"}},{b - 0.2:.3f});')
        J(f'tl.fromTo("{cur}",{{scale:1.18,opacity:0}},{{scale:1,opacity:1,duration:0.45,ease:"power2.out"}},{b - 0.2:.3f});')
        J(f'tl.set("{prev}",{{zIndex:2}},{b - 0.2:.3f});')
    elif kind == "flash":
        J(f'tl.fromTo("#flash",{{opacity:0}},{{opacity:0.85,duration:0.1,ease:"power2.in"}},{b - 0.1:.3f});')
        J(f'tl.to("#flash",{{opacity:0,duration:0.3,ease:"power2.out"}},{b:.3f});')
        J(f'tl.fromTo("{cur}",{{scale:1.06}},{{scale:1,duration:0.4,ease:"power3.out"}},{b:.3f});')
    elif kind == "dip":
        J(f'tl.fromTo("#dip",{{opacity:0}},{{opacity:1,duration:0.25,ease:"power2.in"}},{b - 0.25:.3f});')
        J(f'tl.to("#dip",{{opacity:0,duration:0.4,ease:"power2.out"}},{b:.3f});')


def cta_html(i):
    c = CTA
    q = "".join(f'<span id="ct_q{k}" class="qw">{esc(w)}</span> ' for k, w in enumerate(c["q"].split()))
    return f'''<div class="cta">
          <div class="ctaq">{q.strip()}</div>
          <div id="ct_rule" class="rule"></div>
          <div class="line label ctas"><span id="ct_sub" class="pearl">{esc(c["sub"])}</span></div>
          <div id="ct_card" class="ccard">
            <div id="ct_icon" class="cicon"><svg viewBox="0 0 48 48" width="62" height="62" aria-hidden="true"><circle cx="24" cy="23" r="16" fill="none" stroke="#fff" stroke-width="3.6"/><path d="M11 39 L13.5 31 L19 35.5 Z" fill="#fff"/><path d="M18.5 16.5c1.2-1 2.4-.9 3 .4l1.2 2.6c.4.9.1 1.7-.7 2.3l-.9.7c.9 2 2.5 3.6 4.5 4.6l.7-.9c.6-.8 1.4-1.1 2.3-.7l2.6 1.2c1.3.6 1.4 1.8.4 3-1.4 1.6-3.4 2-5.6 1-4.3-2-7.6-5.3-9.6-9.6-1-2.2-.6-4.2 1-5.6z" fill="#fff"/></svg><div id="ct_ring" class="ring"></div></div>
            <div class="ctext">
              <div class="cnum"><span id="ct_n1" class="nw">017-203</span> <span id="ct_n2" class="nw">6099</span></div>
              <div id="ct_meta" class="cmeta">Deposit RM13,000 &nbsp;·&nbsp; Bulanan RM1,300</div>
            </div>
            <div id="ct_glint" class="glint"></div>
          </div>
        </div>'''


def cta_js(J, s):
    b = s["start"]
    w = {x["display"].rstrip(".,"): x["t0"] for x in s["words"]}
    n1, n2 = w["017-203"], w["6099"]
    for k in range(len(CTA["q"].split())):
        J(f'tl.fromTo("#ct_q{k}",{{opacity:0,y:40,scale:1.1}},{{opacity:1,y:0,scale:1,duration:0.45,ease:"power3.out"}},{b + 0.15 + 0.12 * k:.3f});')
    J(f'tl.fromTo("#ct_rule",{{scaleX:0}},{{scaleX:1,duration:0.5,ease:"power3.out"}},{b + 0.55:.3f});')
    J(f'tl.fromTo("#ct_sub",{{yPercent:110}},{{yPercent:0,duration:0.5,ease:"power3.out"}},{b + 0.65:.3f});')
    J(f'tl.fromTo("#ct_card",{{opacity:0,y:60}},{{opacity:1,y:0,duration:0.6,ease:"power3.out"}},{min(b + 1.3, n1 - 0.6):.3f});')
    # the number lands as it is spoken
    J(f'tl.fromTo("#ct_n1",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.3,ease:"power3.out"}},{n1 - 0.05:.3f});')
    J(f'tl.fromTo("#ct_n2",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.3,ease:"power3.out"}},{n2 - 0.05:.3f});')
    J(f'tl.fromTo("#ct_ring",{{scale:1,opacity:0.8}},{{scale:1.9,opacity:0,duration:0.9,ease:"power2.out"}},{n1 - 0.05:.3f});')
    J(f'tl.fromTo("#ct_meta",{{opacity:0}},{{opacity:1,duration:0.5,ease:"power2.out"}},{n2 + 0.6:.3f});')
    J(f'tl.fromTo("#ct_glint",{{x:-220}},{{x:860,duration:0.8,ease:"power2.inOut"}},{n2 + 1.2:.3f});')


TEMPLATE = r"""<!doctype html>
<html lang="ms" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>KL AUTO SB - Proton X50 Sambung Bayar</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      @font-face { font-family: "Poppins"; src: url("assets/fonts/Poppins-SemiBold.ttf"); font-weight: 600; }
      @font-face { font-family: "Poppins"; src: url("assets/fonts/Poppins-Bold.ttf"); font-weight: 700; }
      @font-face { font-family: "Poppins"; src: url("assets/fonts/Poppins-ExtraBold.ttf"); font-weight: 800; }
      @font-face { font-family: "Montserrat"; src: url("assets/fonts/Montserrat.ttf"); font-weight: 100 900; }
      :root {
        --ground: #0b0d12; --pearl: #f6f5f1; --red: #e2232d;
        --silver-grad: linear-gradient(180deg, #f6f8fa 0%, #d9dde2 38%, #9aa0a9 52%, #c9ced5 70%, #eef1f4 100%);
        --font-display: "Poppins"; --font-label: "Montserrat";
      }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1080px; height: 1920px; overflow: hidden; background: var(--ground); }
      #root { position: relative; width: 1080px; height: 1920px; overflow: hidden; background: var(--ground); font-family: var(--font-display); }
      .scene, .cam, .kb, .sub { position: absolute; inset: 0; }
      .scene { overflow: hidden; }
      .bg { position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; object-fit: cover; }
      .full { position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; object-fit: cover; }
      .card { position: absolute; left: -22px; top: 430px; width: 1124px; height: 843px; object-fit: cover;
              -webkit-mask-image: linear-gradient(180deg, transparent 0, #000 12%, #000 86%, transparent 100%);
                      mask-image: linear-gradient(180deg, transparent 0, #000 12%, #000 86%, transparent 100%); }
      .cta-card { left: 20px; top: 640px; width: 1040px; height: 780px; }
      .shade { position: absolute; inset: 0;
               background: linear-gradient(180deg, rgba(11,13,18,.9) 0%, rgba(11,13,18,.78) 16%, rgba(11,13,18,.5) 26%, rgba(11,13,18,0) 36%,
                           rgba(11,13,18,0) 54%, rgba(11,13,18,.62) 63%, rgba(11,13,18,.72) 72%, rgba(11,13,18,.45) 100%); }
      .sweep { position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; mix-blend-mode: screen;
               background: linear-gradient(105deg, transparent 42%, rgba(255,255,255,.16) 50%, transparent 58%); }
      .heads { position: absolute; left: 120px; top: 290px; width: 840px; text-align: center; }
      .line { overflow: hidden; line-height: 1.12; }
      .line span { display: inline-block; filter: drop-shadow(0 6px 14px rgba(0,0,0,.6)); }
      .hero { font-weight: 800; font-size: 90px; letter-spacing: -0.01em; white-space: nowrap; }
      .hero-s { font-weight: 800; font-size: 66px; letter-spacing: -0.01em; white-space: nowrap; }
      .line.tag { margin-top: 16px; overflow: visible; }
      .tag span { font-weight: 700; font-size: 38px; letter-spacing: .06em; padding: 8px 26px; border-radius: 40px; background: var(--red); color: #fff; filter: none; box-shadow: 0 6px 18px rgba(0,0,0,.45); }
      .price { font-weight: 800; font-size: 176px; letter-spacing: -0.01em; line-height: 1.05; }
      .label { font-family: var(--font-label); font-weight: 700; font-size: 38px; letter-spacing: 0.1em; margin: 6px 0; }
      .pearl { color: #fff; }
      .silver, .red { color: #fff; }
      .price .red { text-shadow: 0 6px 30px rgba(0,0,0,.55); }
      #captions { position: absolute; inset: 0; pointer-events: none; }
      .grp { position: absolute; left: 120px; top: 1096px; width: 660px; text-align: center;
             font-weight: 700; font-size: 48px; line-height: 1.42; color: #fff; opacity: 0; visibility: hidden; }
      .grp.cta-pos { top: 1140px; }
      .grp { text-wrap: balance; }
      .pill { display: inline; padding: 4px 20px 8px; border-radius: 16px; background: rgba(11,13,18,.62);
              -webkit-box-decoration-break: clone; box-decoration-break: clone;
              text-shadow: 0 2px 6px rgba(0,0,0,.6); }
      .grp .w { display: inline; }
      .grp .red, .grp .silver { color: #fff; }
      #bug { position: absolute; left: 64px; top: 186px; display: flex; align-items: center; gap: 14px; }
      #bug .bar { width: 8px; height: 38px; background: var(--red); }
      #bug .bt { font-weight: 700; font-size: 34px; letter-spacing: .12em; color: var(--pearl); }
      #fx { position: absolute; inset: 0; pointer-events: none; }
      #flash, #dip { position: absolute; inset: 0; opacity: 0; }
      #flash { background: #fff; }
      #dip { background: var(--ground); }
      .cta { position: absolute; inset: 0; text-align: center; }
      .ctaq { position: absolute; top: 290px; left: 120px; width: 840px; font-weight: 800; font-size: 84px; line-height: 1.1; color: #fff; white-space: nowrap; }
      .qw { display: inline-block; filter: drop-shadow(0 6px 14px rgba(0,0,0,.6)); }
      .rule { position: absolute; top: 396px; left: 470px; width: 140px; height: 6px; background: var(--red); }
      .ctas { position: absolute; top: 412px; left: 120px; width: 840px; }
      .ctas.label { font-size: 38px; letter-spacing: .2em; }
      .ccard { position: absolute; overflow: hidden; left: 120px; top: 488px; width: 840px; height: 180px; border-radius: 30px;
               display: flex; align-items: center; gap: 26px; padding: 0 30px; text-align: left;
               background: rgba(11,13,18,.78); border: 2px solid rgba(255,255,255,.18);
               box-shadow: 0 18px 40px rgba(0,0,0,.55), inset 0 1px 0 rgba(255,255,255,.12); }
      .cicon { position: relative; flex: 0 0 104px; height: 104px; border-radius: 52px; background: var(--red);
               display: flex; align-items: center; justify-content: center; box-shadow: 0 0 30px rgba(226,35,45,.5); }
      .ring { position: absolute; inset: 0; border-radius: 52px; border: 4px solid rgba(226,35,45,.9); }
      .nw { display: inline-block; }
      .cnum { font-weight: 800; font-size: 72px; line-height: 1.05; color: #fff; letter-spacing: .01em; white-space: nowrap; }
      .cmeta { margin-top: 8px; font-weight: 600; font-size: 30px; color: #fff; opacity: .85; white-space: nowrap; }
      .glint { position: absolute; left: 0; top: -40px; width: 90px; height: 260px; transform: rotate(18deg);
               background: linear-gradient(90deg, transparent, rgba(255,255,255,.55), transparent); }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="%%TOTAL%%" data-width="1080" data-height="1920" data-fps="30" data-motion-blur="on">
      %%BODY%%
    </div>
    <script>
      const tl = gsap.timeline({ paused: true });
      %%JS%%
      window.__timelines["main"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>
"""


def main():
    html_only = "--html" in sys.argv
    if html_only:
        vo = json.loads((AUD / "vo_timings.json").read_text())
    else:
        make_photos()
        vo = make_voice()
    scenes, total = timeline(vo)
    for s in scenes:
        print(f"  scene {s['i']}: {s['start']:6.2f}-{s['end']:6.2f}  " + " ".join(w["display"] for w in s["words"]))
    if not html_only:
        make_audio(scenes, total)
    make_html(scenes, total)


if __name__ == "__main__":
    main()
