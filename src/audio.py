"""Synthesise the 118 BPM corporate-electronic bed, SFX, and mix under the voiceover.

Everything is generated procedurally (no third-party music), so the track is
royalty-free and locked to the scene timeline.
"""
import subprocess

import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

from config import BEAT, BUILD
from timeline import TRANS, build

SR = 48000
rng = np.random.default_rng(7)


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, "low", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, "high", fs=SR, output="sos"), x)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "band", fs=SR, output="sos"), x)


def saw(freq, n, harmonics=14, phase=0.0):
    t = np.arange(n) / SR
    out = np.zeros(n)
    for k in range(1, harmonics + 1):
        if freq * k > 16000:
            break
        out += np.sin(2 * np.pi * freq * k * t + phase * k) / k
    return out * 0.6


def reverb(x, secs=2.2, wet=0.25, predelay=0.02):
    n = int(secs * SR)
    ir = rng.standard_normal(n) * np.exp(-np.linspace(0, 7, n))
    ir = lp(ir, 6000)
    ir = np.concatenate([np.zeros(int(predelay * SR)), ir])
    ir /= np.sqrt(np.sum(ir ** 2))
    return x + wet * fftconvolve(x, ir)[: len(x)]


def place(buf, sig, t, gain=1.0):
    i = int(t * SR)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i] * gain


# ---------------------------------------------------------------- instruments
def kick():
    n = int(0.42 * SR)
    t = np.arange(n) / SR
    f = 46 + 110 * np.exp(-t / 0.035)
    ph = 2 * np.pi * np.cumsum(f) / SR
    k = np.sin(ph) * np.exp(-t / 0.16)
    click = hp(rng.standard_normal(n), 3000) * np.exp(-t / 0.004) * 0.25
    return np.tanh((k + click) * 1.6) * 0.9


def clap():
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    env = np.zeros(n)
    for d in (0.0, 0.011, 0.022):
        m = t >= d
        env[m] += np.exp(-(t[m] - d) / (0.010 if d < 0.02 else 0.09))
    return bp(rng.standard_normal(n), 900, 3500) * env * 0.55


def hat(open_=False):
    n = int((0.22 if open_ else 0.06) * SR)
    t = np.arange(n) / SR
    return hp(rng.standard_normal(n), 8000, 4) * np.exp(-t / (0.07 if open_ else 0.014)) * 0.35


def impact(big=True):
    n = int(2.0 * SR)
    t = np.arange(n) / SR
    boom = np.sin(2 * np.pi * np.cumsum(38 + 60 * np.exp(-t / 0.06)) / SR) * np.exp(-t / 0.45)
    crack = lp(rng.standard_normal(n), 2500) * np.exp(-t / 0.08) * 0.35
    s = (boom + crack) * (1.0 if big else 0.5)
    return reverb(s, 2.5, 0.35)


def whoosh(length=0.55, up=True):
    n = int(length * SR)
    t = np.linspace(0, 1, n)
    noise = rng.standard_normal(n)
    out = np.zeros(n)
    # sweep a band-pass through the noise in blocks
    blk = 512
    for b in range(0, n, blk):
        p = b / n if up else 1 - b / n
        fc = 300 + 5200 * p ** 1.6
        out[b:b + blk] = bp(noise[b:b + blk + 0], max(80, fc * 0.6), min(18000, fc * 1.6), 1)
    env = np.sin(np.pi * t) ** 1.5
    out = lp(out, 9000) * env
    return out / (np.abs(out).max() + 1e-9) * 0.5


def riser(length):
    n = int(length * SR)
    t = np.linspace(0, 1, n)
    noise = rng.standard_normal(n)
    out = np.zeros(n)
    blk = 1024
    for b in range(0, n, blk):
        fc = 400 + 7000 * (b / n) ** 2
        out[b:b + blk] = bp(noise[b:b + blk], fc * 0.7, min(18000, fc * 1.4), 1)
    tone = np.sin(2 * np.pi * np.cumsum(200 + 600 * t ** 2) / SR) * 0.15
    return (out / (np.abs(out).max() + 1e-9) * 0.4 + tone) * t ** 2


def shimmer_chord(notes, length=3.0):
    n = int(length * SR)
    t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * mtof(m) * t) + 0.3 * np.sin(4 * np.pi * mtof(m) * t) for m in notes)
    s *= np.exp(-t / 0.9) * (1 - np.exp(-t / 0.005))
    return reverb(s / len(notes), 3.0, 0.5) * 0.5


# ------------------------------------------------------------------- music
CHORDS = [  # (pad voicing, bass root) — Am9, Fmaj7, Cadd9, G6
    ([57, 60, 64, 67, 71], 33),
    ([53, 57, 60, 64, 69], 29),
    ([55, 60, 62, 64, 67], 36),
    ([55, 59, 62, 64, 67], 31),
]


def music(total, scenes):
    n = int(total * SR) + SR * 3
    drums, bass, pad, pluck = (np.zeros(n) for _ in range(4))
    nbeats = int(total / BEAT) + 1
    final_t = scenes[-1]["words"][-1]["t1"] + 0.35
    final_beat = int(np.ceil(final_t / BEAT))
    break_start = scenes[-1]["start"] - 2 * BEAT
    K, C = kick(), clap()

    for b in range(nbeats):
        t = b * BEAT
        if b >= final_beat:
            break
        in_break = break_start <= t < scenes[-1]["start"]
        bar = b // 4
        if not in_break:
            place(drums, K, t)
            if b % 2 == 1 and b >= 4:
                place(drums, C, t, 0.8)
            if b >= 2:
                place(drums, hat(), t + BEAT / 2, 0.9)
                place(drums, hat(), t + BEAT / 4, 0.25)
                place(drums, hat(), t + 3 * BEAT / 4, 0.25)
            if b % 8 == 7:
                place(drums, hat(True), t + BEAT / 2, 0.6)
        chord, root = CHORDS[bar % 4]
        # bass: off-beat eighths + root on the 1
        for off, g in ((0.0, 1.0), (0.5, 0.8)):
            if in_break and off == 0.0:
                continue
            ln = int(BEAT * 0.45 * SR)
            tt = np.arange(ln) / SR
            f = mtof(root + 12)
            s = np.sin(2 * np.pi * f * tt) + 0.35 * saw(f, ln, 6)
            s *= np.exp(-tt / 0.22) * (1 - np.exp(-tt / 0.003))
            place(bass, s, t + off * BEAT, 0.55 * g)
        # pluck arpeggio (16ths)
        arp = [chord[i] + 12 for i in (0, 2, 1, 3)]
        for k in range(4):
            ln = int(0.22 * SR)
            tt = np.arange(ln) / SR
            s = saw(mtof(arp[k]), ln, 8) * np.exp(-tt / 0.07)
            place(pluck, s, t + k * BEAT / 4, 0.16 if b >= 2 else 0.09)
        # pad: one chord per bar
        if b % 4 == 0:
            ln = int(4 * BEAT * SR) + int(0.3 * SR)
            tt = np.arange(ln) / SR
            s = sum(saw(mtof(m) * d, ln, 10, ph) for m in chord
                    for d, ph in ((1.0, 0), (1.004, 1.3), (0.996, 2.1)))
            s *= np.minimum(1, tt / 0.08) * np.minimum(1, (ln / SR - tt) / 0.3)
            place(pad, s / 15, t, 0.5)

    # sidechain pump on pad + bass
    sc = np.ones(n)
    for b in range(min(nbeats, final_beat)):
        if break_start <= b * BEAT < scenes[-1]["start"]:
            continue
        i = int(b * BEAT * SR)
        ln = int(BEAT * SR)
        tt = np.arange(ln) / SR
        seg = 1 - 0.65 * np.exp(-tt / 0.11)
        sc[i:i + ln] = seg[: max(0, min(ln, n - i))]
    pad = lp(pad, 3800) * sc
    bass = lp(bass, 900) * sc
    # pluck through a dotted-eighth ping-pong delay
    d = int(0.75 * BEAT * SR)
    pl_l, pl_r = pluck.copy(), pluck.copy()
    pl_l[d:] += 0.35 * pluck[:-d]
    pl_r[2 * d:] += 0.25 * pluck[:-2 * d]
    pl_l, pl_r = lp(pl_l, 5000), lp(pl_r, 5000)

    mid = drums + bass + reverb(pad, 2.4, 0.3)
    L = mid + pl_l + 0.1 * np.roll(pad, 300)
    R = mid + pl_r + 0.1 * np.roll(pad, 450)
    # final accent
    final = shimmer_chord([57, 64, 69, 72, 76, 81], 4.0)
    final[: int(2.0 * SR)] += impact(True) * 0.9
    place(L, final, final_beat * BEAT)
    place(R, final, final_beat * BEAT)
    return np.stack([L, R])[:, : int(total * SR)], final_beat * BEAT


def sfx(total, scenes):
    n = int(total * SR) + SR * 3
    out = np.zeros(n)
    place(out, impact(True), 0.0, 0.8)                     # hook hit
    for s in scenes[1:]:                                    # whoosh into every cut
        w = whoosh(0.6, up=s["i"] % 2 == 1)
        place(out, w, s["start"] - 0.38, 0.55)
    for s in scenes:                                        # soft hits on price/key reveals
        if s["cfg"]["head"] and s["cfg"]["head"] != "cta" and s["i"] in (2, 3, 4):
            place(out, impact(False), s["start"] + BEAT, 0.5)
    last = scenes[-1]
    place(out, riser(2 * BEAT), last["start"] - 2 * BEAT, 0.45)
    place(out, impact(True), last["start"], 0.7)
    # phone number reveal accent
    ph = [w for w in last["words"] if w["display"].startswith("017")][0]
    place(out, impact(False), ph["t0"], 0.45)
    return out[: int(total * SR)]


def voice(total, scenes):
    n = int(total * SR)
    out = np.zeros(n)
    for s in scenes:
        src = BUILD / "vo" / f"vo_{s['i']}.wav"
        proc = BUILD / "vo" / f"vo_{s['i']}_fx.wav"
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-af",
            "highpass=f=85,equalizer=f=220:t=q:w=1:g=-1.5,equalizer=f=3200:t=q:w=1.2:g=2.5,"
            "acompressor=threshold=-20dB:ratio=3:attack=4:release=90:makeup=3,"
            "alimiter=limit=0.93", "-ar", str(SR), "-ac", "1", "-f", "f32le", str(proc.with_suffix(".raw"))
        ], check=True)
        x = np.fromfile(proc.with_suffix(".raw"), dtype=np.float32).astype(np.float64)
        place(out, x, s["vo_start"])
    return out


def main():
    scenes, total = build()
    mus, final_t = music(total, scenes)
    fx = sfx(total, scenes)
    vo = voice(total, scenes)

    # ducking: smooth VO envelope
    env = np.abs(vo)
    att, rel = np.exp(-1 / (0.01 * SR)), np.exp(-1 / (0.35 * SR))
    from scipy.signal import lfilter
    env = lfilter([1 - rel], [1, -rel], env)
    env = np.minimum(1, env / (np.percentile(env, 95) + 1e-9))
    duck = 1 - 0.5 * env

    mus = mus / (np.abs(mus).max() + 1e-9)
    music_gain = 0.30  # ~ -10.5 dB under VO before ducking
    L = mus[0] * music_gain * duck + fx * 0.55 + vo
    R = mus[1] * music_gain * duck + fx * 0.55 + vo
    # fade the very end
    fade = int(0.6 * SR)
    for ch in (L, R):
        ch[-fade:] *= np.linspace(1, 0, fade)
    mix = np.stack([L, R]).T.astype(np.float32)
    raw = BUILD / "mix.raw"
    mix.tofile(raw)
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", str(raw),
        "-af", "loudnorm=I=-14:TP=-1.0:LRA=9", "-ar", str(SR), str(BUILD / "mix.wav")
    ], check=True)
    # stems for re-editing
    np.stack([mus[0] * music_gain, mus[1] * music_gain]).T.astype(np.float32).tofile(BUILD / "music.raw")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2",
                    "-i", str(BUILD / "music.raw"), str(BUILD / "music_stem.wav")], check=True)
    print(f"mix written: {total:.2f}s, final accent at {final_t:.2f}s")


if __name__ == "__main__":
    main()
