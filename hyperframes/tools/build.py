"""Build a KL AUTO SB Proton X50 promo as a HyperFrames project.

    python3 tools/build.py --video NAMA           # photos + voice + music + index.html for videos/NAMA.json
    python3 tools/build.py --video NAMA --html    # only regenerate index.html (keeps audio)

One house style (STYLES["v2"], see GAYA.md): ElevenLabs "Ashraf" voice, hook, ka-ching/pop/ding SFX,
green WhatsApp icon, captions under the car. To make another unit: copy videos/contoh.json.

Then:  ./hf.sh check  ->  ./hf.sh preview  ->  ./hf.sh render -o renders/<name>.mp4
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

# Brighter, "happening" bed: major-key I-V-vi-IV (Cadd9, G6, Am7, Fmaj7) instead of the minor default.
A.CHORDS = [
    ([60, 64, 67, 69, 74], 36),
    ([59, 62, 67, 69, 71], 31),
    ([57, 60, 64, 67, 72], 33),
    ([57, 60, 64, 65, 69], 29),
]
import edge_tts  # noqa: E402
import tts as _tts  # noqa: E402
from tts import PROXY, norm, parse_tokens, tighten  # noqa: E402

_tts.MAX_GAP, _tts.KEEP_GAP = 0.60, 0.45   # snappier sentence pauses

ASSETS = HF / "assets"
AUD = ASSETS / "audio" / "hitam"
PH = ASSETS / "photos"
PHOTO_SRC = ROOT / "photos"


def configure(name):
    """Point the build at one video: its photos, audio folder, style and per-scene overrides."""
    global VIDEO, STYLE, AUD, PHOTO_SRC, CUES, FIT_W, SCRIPT, CTA
    v = VIDEOS[name] = load_video(name)
    if "script" in v:  # a different car: its own lines, headlines, moves and transitions
        SCRIPT = [dict(sc, photos=sc.get("photos", []), base_move=sc["move"], base_trans=sc.get("trans"),
                       trans=sc.get("trans"), min_beats=sc.get("min_beats", 0)) for sc in v["script"]]
        CTA = dict(CTA, **v.get("cta", {}))
    VIDEO, STYLE, CUES, FIT_W = name, STYLES[v["style"]], v.get("cues"), set(v.get("fit_width", []))
    AUD = ASSETS / "audio" / name
    PHOTO_SRC = ROOT / "photos" / v["src"] if v["src"] else ROOT / "photos"
    custom = "script" in v
    for i, sc in enumerate(SCRIPT):
        sc["photos"] = v["photos"][i]
        sc["move"] = sc["base_move"] if custom else STYLE["moves"].get(i, sc["base_move"])
        sc["trans"] = sc["base_trans"] if custom else STYLE["trans"].get(i, sc["base_trans"])

VOICE, RATE, PITCH = "ms-MY-OsmanNeural", "-4%", "-1Hz"   # "Suara B", calmer: slower, lower, no "!"
BPM = 118
BEAT = 60 / BPM
SR = 48000

# --------------------------------------------------------------------- videos & styles
VIDEOS = {}   # every video lives in videos/<name>.json (template: videos/contoh.json)
STYLES = {
    "v2": dict(music="groove", countup=True, bump=True, montage="slide", shade="v2",
               photo_bright=1.07, bg_bright=0.72, captions="bottom",   # brighter look, captions bottom-centre
               sfx_plus=True, wa_green=True,                           # ka-ching / pops / ding; green WhatsApp icon
               trans={5: "leak"},                       # light-leak into the interior
               moves={0: "reveal", 2: "orbit", 4: "track", 6: "drift"}),
}
DEFAULT_STYLE = "v2"   # "Gaya KL AUTO SB" - the saved house style for every new video (see GAYA.md)
VIDEO, STYLE, CUES, FIT_W = None, STYLES["v2"], None, set()


def load_video(name):
    """A video is either built in (VIDEOS) or a JSON file in videos/<name>.json (see videos/contoh.json)."""
    if name in VIDEOS:
        return VIDEOS[name]
    f = HF / "videos" / f"{name}.json"
    if not f.exists():
        raise SystemExit(f"Tiada video '{name}': tambah videos/{name}.json (salin videos/contoh.json)")
    v = json.loads(f.read_text())
    v = {k: val for k, val in v.items() if not k.startswith("_")}
    v.setdefault("style", DEFAULT_STYLE)
    return v

# --------------------------------------------------------------------- script
SCRIPT = [
    dict(  # 1 HOOK
        vo="Ada satu unit ^Proton ^X50|X-fifty ^Executive ^Spec nak dijual secara *sambung *bayar *berdeposit.",
        head=[("SAMBUNG BAYAR", "hero", "pearl"), ("LEASE TO OWN", "label", "silver")],
        photos=["01_hitam_depan34.jpg"], move="push", trans=None, min_beats=0),
    dict(  # 2 MODEL
        vo="^Proton ^X50|X-fifty ^Executive ^Facelift ^2026.|dua-ribu-dua-puluh-enam. Kereta baru, jualan koyak plastik.",
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
        vo="Yang bestnya,|besnya, ^agreement *terus *dengan *owner. Semua urusan kita bantu sampai selesai.",
        head=[("AGREEMENT", "label", "silver"), ("DIRECT OWNER", "hero", "pearl"), ("PROSES MUDAH & PANTAS", "tag", "pearl")],
        photos=["05_hitam_belakang.jpg"], move="track", trans="zoom", min_beats=8),
    dict(  # 6 INTERIOR MONTAGE
        vo="Tengoklah interior dia. ^Moden, ^selesa, ruang pun ^luas. Memang ngam untuk bawa ^family.",
        head=[("MODERN INTERIOR", "hero-s", "pearl"), ("COMFORTABLE FAMILY SUV", "label", "silver")],
        photos=["06_stereng.jpg", "07_tempat_duduk_depan.jpg", "08_tempat_duduk_belakang.jpg"],
        move="montage", trans="whip-left", min_beats=8),
    dict(  # 7a RECAP
        vo="Berminat dengan kereta?",
        head="recap",
        photos=["03_hitam_belakang34.jpg"], move="recap", trans="dip", min_beats=8),
    dict(  # 7b CONTACT END CARD
        vo="*WhatsApp sekarang. *017-203|kosong-satu-tujuh,-dua-kosong-tiga, *6099.|enam-kosong-sembilan-sembilan. Jangan tunggu lama.",
        head="cta",
        photos=["01_hitam_depan34.jpg"], move="cta", trans="zoom", min_beats=0),
]
for _s in SCRIPT:
    _s["base_move"], _s["base_trans"] = _s["move"], _s["trans"]
CTA = dict(q="NAK VIEW KERETA?", sub="WHATSAPP SEKARANG", phone="017-203 6099",
           title="SAMBUNG BAYAR BERDEPOSIT", meta="Proton X50 Executive Facelift 2026",
           checks=["Deposit RM13,000", "Bulanan RM1,300", "Loan 9 tahun", "Agreement direct owner"])

VO_LEAD = 0.25
TAIL_PAD = 0.45
CTA_HOLD = 2.8


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


def make_voice_files(src_dir):
    """Use pre-generated per-scene voice files (e.g. ElevenLabs el_<i>.mp3). Word timings are estimated:
    speech regions are found from the audio energy and each token gets a share of the speech time
    proportional to its length, so captions follow the real pauses."""
    AUD.mkdir(parents=True, exist_ok=True)
    res = []
    for i, sc in enumerate(SCRIPT):
        toks = parse_tokens(sc["vo"])
        wav = AUD / f"vo_{i}.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src_dir / f"el_{i}.mp3"), "-ar", str(SR), "-ac", "1", str(wav)], check=True)
        sr, x = _tts.read_wav(wav)
        hop = int(0.01 * sr)
        rms = np.array([np.sqrt(np.mean(x[k:k + hop] ** 2) + 1e-12) for k in range(0, len(x) - hop, hop)])
        db = 20 * np.log10(rms / (rms.max() + 1e-12))
        on = db > -38
        regions, k = [], 0
        while k < len(on):
            if on[k]:
                j = k
                while j < len(on) and on[j]:
                    j += 1
                regions.append([k * 0.01, j * 0.01])
                k = j
            else:
                k += 1
        merged = []
        for r in regions:  # bridge gaps shorter than 0.12 s (consonants, breaths)
            if merged and r[0] - merged[-1][1] < 0.12:
                merged[-1][1] = r[1]
            else:
                merged.append(r)
        regions = [r for r in merged if r[1] - r[0] > 0.04]
        t_start, t_end = regions[0][0], regions[-1][1]
        lead = max(0.0, t_start - 0.05)
        y = x[int(lead * sr):int(min(len(x) / sr, t_end + 0.2) * sr)]
        _tts.write_wav(wav, sr, y)
        speech = sum(r[1] - r[0] for r in regions)
        w = [len(t["spoken"].replace(" ", "")) + 1.5 for t in toks]
        tot, acc = sum(w), 0.0

        def to_time(u):  # position along concatenated speech -> real time
            for r in regions:
                d = r[1] - r[0]
                if u <= d:
                    return r[0] + u
                u -= d
            return regions[-1][1]
        for t, wt in zip(toks, w):
            t["t0"] = round(to_time(acc / tot * speech) - lead, 3)
            acc += wt
            t["t1"] = round(to_time(acc / tot * speech) - lead, 3)
        res.append(dict(tokens=toks, duration=len(y) / sr))
    (AUD / "vo_timings.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    return res


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
        beats = max(cfg["min_beats"] if (i in (0, len(SCRIPT) - 1) or cfg["head"] in ("recap", "specs", "process")) else 0, math.ceil(need / (BEAT / 2)) / 2)  # half-beat grid
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
    if STYLE["music"] == "groove":
        import music as M
        mus = M.groove(total, scenes, BEAT)
    else:
        mus, _ = A.music(total, scenes)
    fx = A.sfx(total, scenes)
    if STYLE.get("sfx_plus"):
        fx = fx + extra_sfx(total, scenes)
    from scipy.signal import lfilter
    rel = np.exp(-1 / (0.35 * SR))
    env = lfilter([1 - rel], [1, -rel], np.abs(vo))
    env = np.minimum(1, env / (np.percentile(env, 95) + 1e-9))
    duck = 1 - 0.5 * env
    mus = mus / (np.abs(mus).max() + 1e-9) * 0.34 * duck
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


# --------------------------------------------------------------------- extra sound design (style v2)
def _env(n, a, d):
    t = np.arange(n) / SR
    return (1 - np.exp(-t / a)) * np.exp(-t / d)


def sfx_ching():
    """Cash-register style 'ka-ching' for prices: short click then two bright bell partials."""
    n = int(0.9 * SR)
    t = np.arange(n) / SR
    click = A.hp(np.random.default_rng(3).standard_normal(n), 3000) * np.exp(-t / 0.006) * 0.4
    bell = np.zeros(n)
    for f0, dl, g in ((2093, 0.06, 0.5), (2637, 0.11, 0.45), (3136, 0.11, 0.3)):
        k = int(dl * SR)
        tt = t[: n - k]
        bell[k:] += g * np.sin(2 * np.pi * f0 * tt) * np.exp(-tt / 0.28) * (1 + 0.3 * np.sin(2 * np.pi * 6 * tt))
    return A.reverb(click + bell, 1.2, 0.25) * 0.55


def sfx_pop(pitch=1.0):
    """Bubbly UI pop for checklist ticks."""
    n = int(0.12 * SR)
    t = np.arange(n) / SR
    f = (900 + 1600 * np.exp(-t / 0.02)) * pitch
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, 0.002, 0.035) * 0.45


def sfx_ding():
    """Message-notification ding for the WhatsApp number."""
    n = int(1.0 * SR)
    t = np.arange(n) / SR
    s = 0.6 * np.sin(2 * np.pi * 1568 * t) + 0.35 * np.sin(2 * np.pi * 2349 * t) * (t > 0.09)
    return A.reverb(s * _env(n, 0.003, 0.25), 1.0, 0.2) * 0.5


def sfx_sweep(length=0.5):
    """Airy shimmer swoosh used under the end-card glint."""
    n = int(length * SR)
    t = np.linspace(0, 1, n)
    s = A.hp(np.random.default_rng(5).standard_normal(n), 6000) * np.sin(np.pi * t) ** 2
    return s / (np.abs(s).max() + 1e-9) * 0.25


def extra_sfx(total, scenes):
    out = np.zeros(int(total * SR) + 3 * SR)
    for s in scenes:
        cfg, b = s["cfg"], s["start"]
        if isinstance(cfg["head"], list):
            for j, h in enumerate(cfg["head"]):
                if h[1] == "price":  # count-up lands -> ka-ching
                    A.place(out, sfx_ching(), b + 0.15 + BEAT + 0.85, 0.9)
                if h[1] == "tag" and s["i"] > 0:
                    A.place(out, sfx_pop(1.3), b + 0.15 + 0.14 * j + 0.2 + (BEAT + 0.2 if any(x[1] == "price" for x in cfg["head"]) else 0), 0.6)
        if cfg["head"] in ("recap", "specs"):
            rows = cfg.get("checks", CTA["checks"])
            step = min(0.42, (s["end"] - b - 1.6) / max(1, len(rows)))
            for k in range(len(rows)):
                A.place(out, sfx_pop(1 + 0.08 * k), b + 0.8 + step * k + 0.12, 0.7)
        if cfg["head"] == "process":
            for t in step_times(s, cfg):
                A.place(out, sfx_pop(1.1), t + 0.12, 0.75)
        if cfg["head"] == "cta2":
            A.place(out, sfx_ching(), b + 0.45 + 0.85, 0.9)
        if cfg["head"] in ("cta", "cta2"):
            w = {x["display"].rstrip(".,"): x["t0"] for x in s["words"]}
            A.place(out, sfx_ding(), w["017-203"] - 0.05, 0.8)
            A.place(out, sfx_ding(), w["6099"] - 0.05, 0.6)
            A.place(out, sfx_sweep(0.8), w["6099"] + 1.2, 0.8)
    return out[: int(total * SR)]


# --------------------------------------------------------------------- photos
def make_photos():
    PH.mkdir(parents=True, exist_ok=True)
    for name in sorted({p for s in SCRIPT for p in s["photos"]}):
        im = ImageOps.exif_transpose(Image.open(PHOTO_SRC / name)).convert("RGB")
        im = ImageEnhance.Contrast(im).enhance(1.05)
        if STYLE["photo_bright"] != 1.0:
            im = ImageEnhance.Brightness(im).enhance(STYLE["photo_bright"])
        fg = im.copy()
        fg.thumbnail((2400, 2400), Image.LANCZOS)
        fg.save(PH / name, quality=90)
        sc = max(1080 / im.width, 1920 / im.height) * 1.2
        bg = im.resize((int(im.width * sc / 4), int(im.height * sc / 4)), Image.BILINEAR)
        bg = bg.filter(ImageFilter.GaussianBlur(14))
        bg = ImageEnhance.Color(ImageEnhance.Brightness(bg).enhance(STYLE["bg_bright"])).enhance(0.85)
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
        if (merged and len(g) == 1 and len(merged[-1]) <= max_n and merged[-1][-1]["display"][-1] not in ".!?"
                and len(" ".join(x["display"] for x in merged[-1] + g)) <= max_chars + 4):
            merged[-1] = merged[-1] + g
        else:
            merged.append(g)
    return merged


PRE = {"whip-left": 0.18, "whip-up": 0.18, "zoom": 0.2, "flash": 0.0, "dip": 0.0, "leak": 0.35, None: 0.0}
POST = {"whip-left": 0.18, "whip-up": 0.18, "zoom": 0.2, "flash": 0.0, "dip": 0.0, "leak": 0.35, None: 0.0}


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
            seg = (s["end"] - s["start"]) / n
            slide = STYLE["montage"] == "slide"
            XF = 0.55 if slide else 0.45  # slide / crossfade between interior shots
            cuts = [s["start"] + k * seg for k in range(n)]
            if CUES:  # cut on the spoken word
                wt = {w["display"].strip(".,?!"): w["t0"] for w in s["words"]}
                cuts = [s["start"] if c is None else wt[c] - 0.12 for c in CUES]
            cuts.append(s["end"])
            for k, ph in enumerate(cfg["photos"]):
                a = c0 if k == 0 else cuts[k] - XF
                b = c0 + dur if k == n - 1 else cuts[k + 1]
                inner.append(
                    f'<div id="s{i}m{k}" class="sub clip" data-start="{a:.3f}" data-duration="{b - a:.3f}" data-track-index="{10 + k}" style="z-index:{k + 1}">'
                    f'<div id="s{i}m{k}kb" class="kb"><img class="bg" src="assets/photos/bg_{ph}" alt="" />'
                    f'<img class="contain" src="assets/photos/{ph}" alt="" /></div></div>')
                if k and slide:  # no zoom: the next shot slides in, the last one drifts back (parallax)
                    J(f'tl.fromTo("#s{i}m{k}kb",{{x:1080}},{{x:0,duration:{XF},ease:"power3.inOut"}},{a:.3f});')
                    J(f'tl.fromTo("#s{i}m{k - 1}kb",{{x:0,opacity:1}},{{x:-320,opacity:0.4,duration:{XF},ease:"power3.inOut"}},{a:.3f});')
                elif k:
                    J(f'tl.fromTo("#s{i}m{k}kb",{{opacity:0}},{{opacity:1,duration:{XF},ease:"sine.inOut"}},{a:.3f});')
        else:
            ph = cfg["photos"][0]
            portrait = is_portrait(ph)
            card_cls = "full" if portrait else {"cta": "card cta-card", "recap": "card card-low"}.get(cfg["move"], "card")
            if ph in FIT_W:
                card_cls = "contain hi"
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
                "recap": ("{scale:1.02,x:30}", "{scale:1.08,x:-30}", "sine.inOut"),
                "reveal": ("{scale:1.08}", "{scale:1.0}", "expo.out"),            # fast pull-back, then settle
                "orbit": ("{scale:1.14,x:80,rotation:0.8}", "{scale:1.14,x:-80,rotation:-0.8}", "sine.inOut"),
                "drift": ("{scale:1.1,x:-50,y:30}", "{scale:1.16,x:40,y:-20}", "sine.inOut"),
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
        elif cfg["head"] == "process":
            inner.append(process_html(i, cfg))
            process_js(J, s, cfg)
        elif cfg["head"] == "cta2":
            inner.append(cta2_html(i, cfg))
            cta2_js(J, s, cfg)
        elif cfg["head"] in ("recap", "specs"):
            inner.append(recap_html(i, cfg))
            recap_js(J, s, cfg)
        elif cfg["head"]:
            inner.append(head_html(i, cfg["head"]))
            pidx = next((k for k, h in enumerate(cfg["head"]) if h[1] == "price"), None)
            for j, (txt, style, color) in enumerate(cfg["head"]):
                at = s["start"] + (0.0 if i == 0 else 0.15) + (BEAT if style == "price" else 0.14 * j)
                if pidx is not None and j > pidx:
                    at = s["start"] + 0.15 + BEAT + 0.35
                elif style == "tag":
                    at = s["start"] + 0.15 + 0.14 * j + 0.2
                if i == 0:  # frame 0 is the thumbnail: hook title already on screen (only the big line punches in)
                    if style.startswith("hero"):
                        J(f'tl.fromTo("#h{i}_{j}",{{scale:1.08}},{{scale:1,duration:0.35,ease:"power3.out"}},0);')
                elif style == "tag":
                    J(f'tl.fromTo("#h{i}_{j}",{{opacity:0,y:18}},{{opacity:1,y:0,duration:0.4,ease:"power3.out"}},{at:.3f});')
                elif style == "price":
                    J(f'tl.fromTo("#h{i}_{j}",{{yPercent:110,scale:0.9,opacity:0}},{{yPercent:0,scale:1,opacity:1,duration:0.5,ease:"back.out(1.5)"}},{at:.3f});')
                    if STYLE["countup"]:
                        val = int("".join(ch for ch in txt if ch.isdigit()))
                        J(f'(()=>{{const el=document.getElementById("h{i}_{j}"),o={{v:0}};'
                          f'tl.fromTo(o,{{v:0}},{{v:{val},duration:0.9,ease:"power2.out",onUpdate:()=>{{'
                          f'el.textContent="RM"+Math.round(o.v).toLocaleString("en-US");}}}},{at:.3f});}})();')
                    if STYLE["bump"]:
                        J(f'tl.fromTo("#s{i}cam",{{scale:1.035}},{{scale:1,duration:0.4,ease:"power3.out"}},{at + 0.9:.3f});')
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
                f'data-track-kind="captions" data-layout-allow-safe-zone style="z-index:40">{"".join(caps)}</div>')
    # brand bug (hidden on the end card, which carries the brand itself)
    body.append(f'<div id="bug" class="clip" data-start="0" data-duration="{total}" data-track-index="6" '
                f'data-track-kind="graphics" data-layout-allow-safe-zone style="z-index:41"><span class="bar"></span><span class="bt">KL AUTO SB</span></div>')
    body.append(f'<div id="fx" class="clip" data-start="0" data-duration="{total}" data-track-index="7" data-track-kind="graphics" style="z-index:42">'
                f'<div id="flash"></div><div id="dip"></div><div id="leak"></div></div>')
    for k, (name, idx) in enumerate((("music", 8), ("sfx", 9), ("vo", 4))):
        body.append(f'<audio id="{name}" class="clip" src="assets/audio/{VIDEO}/{name}.wav" data-start="0" data-duration="{total}" data-track-index="{idx}"></audio>')

    page = TEMPLATE
    if STYLE["shade"] == "v2":  # lighter overall: thin top shade, light bottom; text carries its own shadow
        page = page.replace("background: linear-gradient(180deg, rgba(11,13,18,.9) 0%, rgba(11,13,18,.78) 16%, rgba(11,13,18,.5) 26%, rgba(11,13,18,0) 36%,",
                            "background: linear-gradient(180deg, rgba(11,13,18,.62) 0%, rgba(11,13,18,.46) 15%, rgba(11,13,18,.2) 27%, rgba(11,13,18,0) 35%,")
        page = page.replace("rgba(11,13,18,0) 54%, rgba(11,13,18,.62) 63%, rgba(11,13,18,.72) 72%, rgba(11,13,18,.45) 100%",
                            "rgba(11,13,18,0) 58%, rgba(11,13,18,.16) 66%, rgba(11,13,18,.2) 72%, rgba(11,13,18,.32) 100%")
        page = page.replace("</style>", """      .line span, .qw { filter: drop-shadow(0 2px 3px rgba(0,0,0,.6)) drop-shadow(0 4px 10px rgba(0,0,0,.45)); }
      .line { padding: 0 24px 14px; margin-bottom: -14px; }
      .tag span { filter: none; }
      #s0 .line { overflow: visible; }
      .cta::before { content: ""; position: absolute; left: 0; right: 0; top: 150px; height: 620px; z-index: -1;
                     background: radial-gradient(ellipse 60% 50% at 50% 45%, rgba(11,13,18,.6), rgba(11,13,18,0) 80%); }
      .dlab { background: rgba(11,13,18,.72); padding: 8px 16px; border-radius: 30px; }
      .heads::before { content: ""; position: absolute; left: -200px; right: -200px; top: -70px; bottom: -60px; z-index: -1;
                       background: radial-gradient(ellipse 55% 60% at 50% 50%, rgba(11,13,18,.55), rgba(11,13,18,0) 75%); }
      #bug { filter: drop-shadow(0 2px 8px rgba(0,0,0,.6)); }
    </style>""", 1)
    if STYLE.get("wa_green"):
        page = page.replace("</style>", """      .cicon { background: #25D366; box-shadow: 0 0 30px rgba(37,211,102,.55); }
      .ring { border-color: rgba(37,211,102,.9); }
    </style>""", 1)
    if STYLE["captions"] == "bottom":  # bottom-centre: last line ends at y 1520, below the car
        page = page.replace("</style>", """      .grp, .grp.cta-pos { top: auto; bottom: 380px; }
    </style>""", 1)
    page = page.replace("%%TOTAL%%", f"{total}").replace("%%BODY%%", "\n      ".join(body)).replace("%%JS%%", "\n      ".join(js))
    (HF / "index.html").write_text(page)
    print(f"index.html [{VIDEO}, style {VIDEOS[VIDEO]['style']}]: {len(scenes)} scenes, {len(groups)} caption groups, {total:.2f}s")


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
        J(f'tl.fromTo("#flash",{{opacity:0}},{{opacity:0.85,duration:0.12,ease:"power2.in"}},{b - 0.2:.3f});')
        J(f'tl.to("#flash",{{opacity:0,duration:0.22,ease:"power2.out"}},{b - 0.08:.3f});')
        J(f'tl.fromTo("{cur}",{{scale:1.06}},{{scale:1,duration:0.4,ease:"power3.out"}},{b:.3f});')
    elif kind == "leak":  # warm light leak sweeps across while the scenes cross-dissolve
        J(f'tl.fromTo("{cur}",{{opacity:0}},{{opacity:1,duration:0.6,ease:"sine.inOut"}},{b - 0.3:.3f});')
        J(f'tl.fromTo("#leak",{{opacity:0,x:-900}},{{opacity:0.95,x:-100,duration:0.4,ease:"power2.out"}},{b - 0.4:.3f});')
        J(f'tl.to("#leak",{{opacity:0,x:600,duration:0.55,ease:"power2.in"}},{b:.3f});')
    elif kind == "dip":
        J(f'tl.fromTo("#dip",{{opacity:0}},{{opacity:1,duration:0.25,ease:"power2.in"}},{b - 0.25:.3f});')
        J(f'tl.to("#dip",{{opacity:0,duration:0.4,ease:"power2.out"}},{b:.3f});')


CHECK_SVG = ('<svg viewBox="0 0 24 24" width="30" height="30" aria-hidden="true"><path d="M5 12.5l4.2 4.2L19 7" '
             'fill="none" stroke="#fff" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/></svg>')


def recap_html(i, cfg):
    """Checklist card: 'recap' (NAK VIEW KERETA?) or 'specs' (car details) - title + ticked rows."""
    title = cfg.get("title", CTA["q"])
    rows_txt = cfg.get("checks", CTA["checks"])
    q = "".join(f'<span id="r{i}q{k}" class="qw">{esc(w)}</span> ' for k, w in enumerate(title.split()))
    rows = "".join(f'<div id="r{i}c{k}" class="crow"><span id="r{i}k{k}" class="ck">{CHECK_SVG}</span><span>{esc(t)}</span></div>'
                   for k, t in enumerate(rows_txt))
    return f'''<div class="cta">
          <div class="ctaq">{q.strip()}</div>
          <div id="r{i}rule" class="rule"></div>
          <div id="r{i}panel" class="checks{' many' if len(rows_txt) > 5 else ''}">{rows}</div>
        </div>'''


def recap_js(J, s, cfg):
    b, i = s["start"], s["i"]
    title = cfg.get("title", CTA["q"])
    rows_txt = cfg.get("checks", CTA["checks"])
    for k in range(len(title.split())):
        J(f'tl.fromTo("#r{i}q{k}",{{opacity:0,y:40,scale:1.1}},{{opacity:1,y:0,scale:1,duration:0.45,ease:"power3.out"}},{b + 0.1 + 0.12 * k:.3f});')
    J(f'tl.fromTo("#r{i}rule",{{scaleX:0}},{{scaleX:1,duration:0.5,ease:"power3.out"}},{b + 0.5:.3f});')
    J(f'tl.fromTo("#r{i}panel",{{opacity:0}},{{opacity:1,duration:0.35,ease:"power2.out"}},{b + 0.55:.3f});')
    step = min(0.42, (s["end"] - b - 1.6) / max(1, len(rows_txt)))
    for k in range(len(rows_txt)):
        t = b + 0.8 + step * k
        J(f'tl.fromTo("#r{i}c{k}",{{opacity:0,x:-40}},{{opacity:1,x:0,duration:0.4,ease:"power3.out"}},{t:.3f});')
        J(f'tl.fromTo("#r{i}k{k}",{{scale:0}},{{scale:1,duration:0.35,ease:"back.out(2.2)"}},{t + 0.12:.3f});')


def step_times(s, cfg):
    """Each process step lands on its cue word (falls back to an even spread)."""
    wt = {}
    for w in s["words"]:
        wt.setdefault(w["display"].strip(".,?!").lower(), w["t0"])
    out = []
    for k, (_, cue) in enumerate(cfg["steps"]):
        t = wt.get((cue or "").lower())
        out.append(t - 0.1 if t is not None else s["start"] + 0.9 + 0.6 * k)
    return out


def process_html(i, cfg):
    """Ending variant A: numbered process steps, joined by a line that fills as each step is spoken."""
    title = cfg.get("title", "PROSES MUDAH")
    q = "".join(f'<span id="p{i}q{k}" class="qw">{esc(w)}</span> ' for k, w in enumerate(title.split()))
    rows = "".join(f'<div id="p{i}r{k}" class="srow"><span id="p{i}n{k}" class="sn">{k + 1}</span><span class="st">{esc(t)}</span></div>'
                   for k, (t, _) in enumerate(cfg["steps"]))
    return f'''<div class="cta">
          <div class="ctaq">{q.strip()}</div>
          <div id="p{i}rule" class="rule"></div>
          <div id="p{i}panel" class="steps"><div class="sline"><div id="p{i}fill" class="sfill"></div></div>{rows}</div>
        </div>'''


def process_js(J, s, cfg):
    b, i = s["start"], s["i"]
    title = cfg.get("title", "PROSES MUDAH")
    for k in range(len(title.split())):
        J(f'tl.fromTo("#p{i}q{k}",{{opacity:0,y:40,scale:1.1}},{{opacity:1,y:0,scale:1,duration:0.45,ease:"power3.out"}},{b + 0.1 + 0.12 * k:.3f});')
    J(f'tl.fromTo("#p{i}rule",{{scaleX:0}},{{scaleX:1,duration:0.5,ease:"power3.out"}},{b + 0.5:.3f});')
    J(f'tl.fromTo("#p{i}panel",{{opacity:0}},{{opacity:1,duration:0.4,ease:"power2.out"}},{b + 0.4:.3f});')
    ts = step_times(s, cfg)
    n = len(ts)
    for k, t in enumerate(ts):
        J(f'tl.fromTo("#p{i}r{k}",{{opacity:0.25,x:-30}},{{opacity:1,x:0,duration:0.35,ease:"power3.out"}},{t:.3f});')
        J(f'tl.fromTo("#p{i}n{k}",{{scale:0.6,backgroundColor:"rgba(255,255,255,.15)"}},{{scale:1,backgroundColor:"{"#25D366" if k == n - 1 else "#e2232d"}",duration:0.35,ease:"back.out(2.2)"}},{t + 0.05:.3f});')
        if k:
            J(f'tl.to("#p{i}fill",{{scaleY:{k / (n - 1):.3f},duration:0.3,ease:"power2.out"}},{t - 0.05:.3f});')
    J(f'tl.set("#p{i}fill",{{scaleY:0}},{b:.3f});')


def cta2_html(i, cfg):
    """Ending variant B: promo deposit + documents + WhatsApp card."""
    docs = "".join(f'<span id="d{i}c{k}" class="dchip">{esc(d)}</span>' for k, d in enumerate(cfg["docs"]))
    return f'''<div class="cta">
          <div class="line label c2lab"><span id="c2lab" class="pearl">{esc(cfg["promo_label"])}</span></div>
          <div class="line price c2price"><span id="c2price" class="red">{esc(cfg["promo_price"])}</span></div>
          <div id="c2docs" class="c2docs"><span class="dlab">DOKUMEN:</span>{docs}</div>
          <div id="ct_card" class="ccard c2card">
            <div id="ct_icon" class="cicon"><svg viewBox="0 0 48 48" width="62" height="62" aria-hidden="true"><circle cx="24" cy="23" r="16" fill="none" stroke="#fff" stroke-width="3.6"/><path d="M11 39 L13.5 31 L19 35.5 Z" fill="#fff"/><path d="M18.5 16.5c1.2-1 2.4-.9 3 .4l1.2 2.6c.4.9.1 1.7-.7 2.3l-.9.7c.9 2 2.5 3.6 4.5 4.6l.7-.9c.6-.8 1.4-1.1 2.3-.7l2.6 1.2c1.3.6 1.4 1.8.4 3-1.4 1.6-3.4 2-5.6 1-4.3-2-7.6-5.3-9.6-9.6-1-2.2-.6-4.2 1-5.6z" fill="#fff"/></svg><div id="ct_ring" class="ring"></div><div id="ct_ring2" class="ring"></div></div>
            <div class="ctext">
              <div class="cnum"><span id="ct_n1" class="nw">017-203</span> <span id="ct_n2" class="nw">6099</span></div>
              <div id="ct_meta" class="cmeta">{esc(CTA["meta"])}</div>
            </div>
            <div id="ct_glint" class="glint"></div>
          </div>
        </div>'''


def cta2_js(J, s, cfg):
    b = s["start"]
    w = {x["display"].rstrip(".,"): x["t0"] for x in s["words"]}
    n1, n2 = w["017-203"], w["6099"]
    val = int("".join(ch for ch in cfg["promo_price"] if ch.isdigit()))
    J(f'tl.fromTo("#c2lab",{{yPercent:110}},{{yPercent:0,duration:0.5,ease:"power3.out"}},{b + 0.1:.3f});')
    J(f'tl.fromTo("#c2price",{{yPercent:110,scale:0.9,opacity:0}},{{yPercent:0,scale:1,opacity:1,duration:0.5,ease:"back.out(1.5)"}},{b + 0.45:.3f});')
    J(f'(()=>{{const el=document.getElementById("c2price"),o={{v:0}};tl.fromTo(o,{{v:0}},{{v:{val},duration:0.9,ease:"power2.out",onUpdate:()=>{{el.textContent="RM"+Math.round(o.v).toLocaleString("en-US");}}}},{b + 0.45:.3f});}})();')
    J(f'tl.fromTo("#s{s["i"]}cam",{{scale:1.035}},{{scale:1,duration:0.4,ease:"power3.out"}},{b + 1.35:.3f});')
    J(f'tl.fromTo("#c2docs",{{opacity:0}},{{opacity:1,duration:0.3}},{b + 1.4:.3f});')
    for k in range(len(cfg["docs"])):
        J(f'tl.fromTo("#d{s["i"]}c{k}",{{opacity:0,y:20,scale:0.8}},{{opacity:1,y:0,scale:1,duration:0.35,ease:"back.out(2)"}},{b + 1.5 + 0.25 * k:.3f});')
    J(f'tl.fromTo("#ct_card",{{opacity:0,y:50,scale:0.94}},{{opacity:1,y:0,scale:1,duration:0.6,ease:"back.out(1.4)"}},{min(b + 2.2, n1 - 0.6):.3f});')
    J(f'tl.fromTo("#ct_n1",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.3,ease:"power3.out"}},{n1 - 0.05:.3f});')
    J(f'tl.fromTo("#ct_n2",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.3,ease:"power3.out"}},{n2 - 0.05:.3f});')
    J(f'tl.fromTo("#ct_ring",{{scale:1,opacity:0.85}},{{scale:1.9,opacity:0,duration:0.9,ease:"power2.out"}},{n1 - 0.05:.3f});')
    J(f'tl.fromTo("#ct_ring2",{{scale:1,opacity:0.85}},{{scale:1.9,opacity:0,duration:0.9,ease:"power2.out"}},{n2 - 0.05:.3f});')
    J(f'tl.fromTo("#ct_meta",{{opacity:0}},{{opacity:1,duration:0.5,ease:"power2.out"}},{n2 + 0.6:.3f});')
    J(f'tl.fromTo("#ct_glint",{{x:-220}},{{x:1000,duration:0.8,ease:"power2.inOut"}},{n2 + 1.2:.3f});')


def cta_html(i):
    c = CTA
    return f'''<div class="cta">
          <div class="line hero-s ctaq2"><span id="ct_q" class="pearl">{esc(c["sub"])}</span></div>
          <div id="ct_rule" class="rule"></div>
          <div class="line label ctas"><span id="ct_sub" class="pearl">{esc(c["title"])}</span></div>
          <div id="ct_card" class="ccard">
            <div id="ct_icon" class="cicon"><svg viewBox="0 0 48 48" width="62" height="62" aria-hidden="true"><circle cx="24" cy="23" r="16" fill="none" stroke="#fff" stroke-width="3.6"/><path d="M11 39 L13.5 31 L19 35.5 Z" fill="#fff"/><path d="M18.5 16.5c1.2-1 2.4-.9 3 .4l1.2 2.6c.4.9.1 1.7-.7 2.3l-.9.7c.9 2 2.5 3.6 4.5 4.6l.7-.9c.6-.8 1.4-1.1 2.3-.7l2.6 1.2c1.3.6 1.4 1.8.4 3-1.4 1.6-3.4 2-5.6 1-4.3-2-7.6-5.3-9.6-9.6-1-2.2-.6-4.2 1-5.6z" fill="#fff"/></svg><div id="ct_ring" class="ring"></div><div id="ct_ring2" class="ring"></div></div>
            <div class="ctext">
              <div class="cnum"><span id="ct_n1" class="nw">017-203</span> <span id="ct_n2" class="nw">6099</span></div>
              <div id="ct_meta" class="cmeta">{esc(c["meta"])}</div>
            </div>
            <div id="ct_glint" class="glint"></div>
          </div>
        </div>'''


def cta_js(J, s):
    b = s["start"]
    w = {x["display"].rstrip(".,"): x["t0"] for x in s["words"]}
    n1, n2 = w["017-203"], w["6099"]
    J(f'tl.fromTo("#ct_q",{{yPercent:110}},{{yPercent:0,duration:0.55,ease:"power3.out"}},{b + 0.1:.3f});')
    J(f'tl.fromTo("#ct_rule",{{scaleX:0}},{{scaleX:1,duration:0.5,ease:"power3.out"}},{b + 0.4:.3f});')
    J(f'tl.fromTo("#ct_sub",{{yPercent:110}},{{yPercent:0,duration:0.5,ease:"power3.out"}},{b + 0.5:.3f});')
    J(f'tl.fromTo("#ct_card",{{opacity:0,y:50,scale:0.94}},{{opacity:1,y:0,scale:1,duration:0.6,ease:"back.out(1.4)"}},{min(b + 0.8, n1 - 0.6):.3f});')
    J(f'tl.fromTo("#ct_n1",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.3,ease:"power3.out"}},{n1 - 0.05:.3f});')
    J(f'tl.fromTo("#ct_n2",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.3,ease:"power3.out"}},{n2 - 0.05:.3f});')
    J(f'tl.fromTo("#ct_ring",{{scale:1,opacity:0.85}},{{scale:1.9,opacity:0,duration:0.9,ease:"power2.out"}},{n1 - 0.05:.3f});')
    J(f'tl.fromTo("#ct_ring2",{{scale:1,opacity:0.85}},{{scale:1.9,opacity:0,duration:0.9,ease:"power2.out"}},{n2 - 0.05:.3f});')
    J(f'tl.fromTo("#ct_meta",{{opacity:0}},{{opacity:1,duration:0.5,ease:"power2.out"}},{n2 + 0.6:.3f});')
    J(f'tl.fromTo("#ct_glint",{{x:-220}},{{x:1000,duration:0.8,ease:"power2.inOut"}},{n2 + 1.2:.3f});')
    J(f'tl.fromTo("#ct_icon",{{scale:1}},{{scale:1.12,duration:0.18,ease:"power2.out",yoyo:true,repeat:1}},{n2 + 1.2:.3f});')


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
      .card-low { top: 640px; }
      .contain { position: absolute; left: 0; top: 240px; width: 1080px; height: 1440px; object-fit: contain; }
      .contain.hi { top: 110px; }
      .shade { position: absolute; inset: 0; z-index: 5;
               background: linear-gradient(180deg, rgba(11,13,18,.9) 0%, rgba(11,13,18,.78) 16%, rgba(11,13,18,.5) 26%, rgba(11,13,18,0) 36%,
                           rgba(11,13,18,0) 54%, rgba(11,13,18,.62) 63%, rgba(11,13,18,.72) 72%, rgba(11,13,18,.45) 100%); }
      .sweep { position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; mix-blend-mode: screen;
               background: linear-gradient(105deg, transparent 42%, rgba(255,255,255,.16) 50%, transparent 58%); }
      .heads { position: absolute; left: 120px; top: 290px; width: 840px; text-align: center; z-index: 6; }
      .line { overflow: hidden; line-height: 1.12; }
      .line span { display: inline-block; filter: drop-shadow(0 6px 14px rgba(0,0,0,.6)); }
      .hero { font-weight: 800; font-size: 90px; letter-spacing: -0.01em; white-space: nowrap; }
      .hero-s { font-weight: 800; font-size: 66px; letter-spacing: -0.01em; white-space: nowrap; }
      .line.tag { margin-top: 16px; overflow: visible; }
      .tag span { font-weight: 700; font-size: 38px; letter-spacing: .06em; padding: 8px 26px; border-radius: 40px; background: var(--red); color: #fff; filter: none; box-shadow: 0 6px 18px rgba(0,0,0,.45); }
      .price { font-variant-numeric: tabular-nums; font-weight: 800; font-size: 176px; letter-spacing: -0.01em; line-height: 1.05; }
      .label { font-family: var(--font-label); font-weight: 700; font-size: 38px; letter-spacing: 0.1em; margin: 6px 0; }
      .pearl { color: #fff; }
      .silver, .red { color: #fff; }
      .price .red { text-shadow: 0 6px 30px rgba(0,0,0,.55); }
      #captions { position: absolute; inset: 0; pointer-events: none; }
      .grp { position: absolute; left: 0; top: 1096px; width: 1080px; padding: 0 170px; text-align: center;
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
      #leak { position: absolute; left: -500px; top: 0; width: 2080px; height: 1920px; opacity: 0; mix-blend-mode: screen;
              background: radial-gradient(ellipse 520px 900px at 40% 45%, rgba(255,176,96,.85), transparent 70%),
                          radial-gradient(ellipse 420px 700px at 62% 60%, rgba(255,96,120,.55), transparent 70%); }
      #dip { background: var(--ground); }
      .cta { position: absolute; inset: 0; text-align: center; z-index: 6; }
      .ctaq { position: absolute; top: 290px; left: 120px; width: 840px; font-weight: 800; font-size: 84px; line-height: 1.1; color: #fff; white-space: nowrap; }
      .qw { display: inline-block; filter: drop-shadow(0 6px 14px rgba(0,0,0,.6)); }
      .rule { position: absolute; top: 396px; left: 470px; width: 140px; height: 6px; background: var(--red); }
      .ctas { position: absolute; top: 412px; left: 120px; width: 840px; }
      .ctas.label { font-size: 38px; letter-spacing: .2em; }
      .ctaq2 { position: absolute; top: 296px; left: 120px; width: 840px; }
      .checks { position: absolute; left: 50%; transform: translateX(-50%); top: 418px; width: max-content; max-width: 840px; white-space: nowrap; text-align: left; padding: 16px 34px; border-radius: 28px;
                background: rgba(11,13,18,.74); border: 2px solid rgba(255,255,255,.14); box-shadow: 0 16px 36px rgba(0,0,0,.5); }
      .crow { display: flex; align-items: center; gap: 22px; height: 70px; font-weight: 700; font-size: 42px; color: #fff;
              filter: drop-shadow(0 4px 12px rgba(0,0,0,.7)); }
      .checks.many .crow { height: 60px; font-size: 38px; }
      .ck { flex: 0 0 48px; height: 48px; border-radius: 24px; background: var(--red); display: flex; align-items: center; justify-content: center; }
      .steps { position: absolute; left: 50%; transform: translateX(-50%); top: 420px; width: max-content; max-width: 840px; white-space: nowrap;
               text-align: left; padding: 18px 36px 18px 30px; border-radius: 28px; background: rgba(11,13,18,.78);
               border: 2px solid rgba(255,255,255,.14); box-shadow: 0 16px 36px rgba(0,0,0,.5); }
      .sline { position: absolute; left: 55px; top: 52px; bottom: 52px; width: 4px; background: rgba(255,255,255,.18); border-radius: 2px; }
      .sfill { position: absolute; inset: 0; background: #e2232d; transform-origin: 50% 0; }
      .srow { position: relative; display: flex; align-items: center; gap: 22px; height: 74px; font-weight: 700; font-size: 38px; color: #fff; }
      .sn { flex: 0 0 52px; height: 52px; border-radius: 26px; display: flex; align-items: center; justify-content: center;
            font-weight: 800; font-size: 28px; color: #fff; background: rgba(255,255,255,.15); }
      .c2lab { position: absolute; top: 280px; left: 120px; width: 840px; }
      .c2lab.label { font-size: 42px; letter-spacing: .2em; }
      .c2price { position: absolute; top: 330px; left: 120px; width: 840px; }
      .c2price.price { font-size: 150px; }
      .c2docs { position: absolute; top: 548px; left: 120px; width: 840px; display: flex; gap: 14px; justify-content: center; align-items: center; }
      .dlab { font-family: var(--font-label); font-weight: 700; font-size: 26px; letter-spacing: .12em; color: #fff; filter: drop-shadow(0 2px 6px rgba(0,0,0,.7)); }
      .dchip { font-weight: 700; font-size: 30px; color: #fff; padding: 8px 22px; border-radius: 30px; background: rgba(11,13,18,.72); border: 2px solid rgba(255,255,255,.3); }
      .ccard.c2card { top: 640px; }
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
    name = sys.argv[sys.argv.index("--video") + 1]
    configure(name)
    src = VIDEOS[name].get("voice_from")
    if html_only:
        vo = json.loads((AUD / "vo_timings.json").read_text())
    else:
        make_photos()
        if VIDEOS[name].get("voice") == "elevenlabs":
            vo = make_voice_files(ASSETS / "audio" / VIDEOS[name]["voice_dir"])
        elif src:  # same script: reuse the approved voice take
            import shutil
            AUD.mkdir(parents=True, exist_ok=True)
            for f in (ASSETS / "audio" / src).glob("vo_*"):
                shutil.copy(f, AUD / f.name)
            vo = json.loads((AUD / "vo_timings.json").read_text())
        else:
            vo = make_voice()
    scenes, total = timeline(vo)
    for s in scenes:
        print(f"  scene {s['i']}: {s['start']:6.2f}-{s['end']:6.2f}  " + " ".join(w["display"] for w in s["words"]))
    if not html_only:
        make_audio(scenes, total)
    make_html(scenes, total)


if __name__ == "__main__":
    main()
