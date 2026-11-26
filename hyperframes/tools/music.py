"""'Groove' music bed for style v2: upbeat major-key house, arranged to the scene timeline.

Sections (driven by the scenes):
  intro   hook scene       kick + shaker, chords/bass behind a filter that opens up
  drop A  model..agreement full groove: kick, clap, open hats, swung shaker, house bass,
                           offbeat chord stabs, bell motif (soft)
  break   interior montage no kick: pad + bell + shaker, riser and snare fill into...
  drop B  recap + end card full groove with the bell motif up front, final chord + hit

Everything is synthesised (royalty-free) and reuses the drum/FX voices in src/audio.py.
"""
import numpy as np

import audio as A  # src/audio.py (path is set up by build.py)

SR = A.SR
RNG = np.random.default_rng(11)

# Major-key I-V-vi-IV: (voicing, bass root)
CHORDS = [
    ([60, 64, 67, 71, 74], 36),   # Cmaj9
    ([59, 62, 67, 69, 74], 31),   # G6/9
    ([57, 60, 64, 67, 72], 33),   # Am7
    ([57, 60, 65, 69, 72], 29),   # Fmaj7
]
# bell motif per bar: (eighth position, index into the chord voicing, +12)
MOTIF = [
    [(0, 4), (2, 3), (3, 2), (5, 3), (6, 4)],
    [(0, 2), (1, 3), (3, 4), (4, 3), (6, 2), (7, 1)],
]


def bell(f, ln=0.6):
    n = int(ln * SR)
    t = np.arange(n) / SR
    mod = 1.3 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / 0.12)
    s = np.sin(2 * np.pi * f * t + mod) * np.exp(-t / 0.28) * (1 - np.exp(-t / 0.002))
    return s * 0.5


def stab(notes, ln=0.18):
    n = int(ln * SR)
    t = np.arange(n) / SR
    s = sum(A.saw(A.mtof(m), n, 8) for m in notes) / len(notes)
    return A.lp(s * np.exp(-t / 0.07) * (1 - np.exp(-t / 0.003)), 2600)


def bass(root, ln=0.24):
    n = int(ln * SR)
    t = np.arange(n) / SR
    f = A.mtof(root + 12)
    s = np.sin(2 * np.pi * f * t) + 0.3 * A.saw(f, n, 5)
    return np.tanh(1.4 * s * np.exp(-t / 0.16) * (1 - np.exp(-t / 0.004))) * 0.7


def shaker(accent):
    n = int(0.05 * SR)
    t = np.arange(n) / SR
    return A.bp(RNG.standard_normal(n), 5000, 11000) * np.exp(-t / 0.018) * (0.22 if accent else 0.12)


def pad(notes, ln):
    n = int(ln * SR)
    t = np.arange(n) / SR
    s = sum(A.saw(A.mtof(m) * d, n, 9, ph) for m in notes for d, ph in ((1.0, 0), (1.005, 1.1), (0.995, 2.3)))
    s *= np.minimum(1, t / 0.25) * np.minimum(1, (ln - t) / 0.4)
    return A.lp(s / (3 * len(notes)), 3200)


def groove(total, scenes, beat):
    n = int(total * SR) + 4 * SR
    drums, inst, lead, padbuf, intro_buf = (np.zeros(n) for _ in range(5))
    shk_l, shk_r = np.zeros(n), np.zeros(n)

    hook_end = scenes[1]["start"]
    mont = next(s for s in scenes if s["cfg"]["move"] == "montage")
    recap = next((s for s in scenes if s["cfg"]["head"] in ("recap", "process")), scenes[-1])  # second drop starts at the ending
    bd_start, bd_end = mont["start"], recap["start"]
    final_t = scenes[-1]["words"][-1]["t1"] + 0.35
    final_beat = int(np.ceil(final_t / beat))
    K, C = A.kick(), A.clap()
    six = beat / 4

    def section(t):
        if t < hook_end:
            return "intro"
        if bd_start <= t < bd_end:
            return "break"
        return "dropB" if t >= bd_end else "dropA"

    for b in range(final_beat):
        t = b * beat
        sec = section(t)
        bar = b // 4
        chord, root = CHORDS[bar % 4]
        fill = (hook_end - beat <= t < hook_end) or (bd_end - 2 * beat <= t < bd_end)
        # --- drums
        if sec in ("intro", "dropA", "dropB") and not (fill and sec != "intro"):
            A.place(drums, K, t, 0.95 if sec != "intro" else 0.8)
        if sec in ("dropA", "dropB") and b % 2 == 1:
            A.place(drums, C, t, 0.75)
        if sec in ("dropA", "dropB"):
            A.place(drums, A.hat(True), t + beat / 2, 0.45)
        if fill:  # snare/clap roll into the drop
            for k in range(4):
                A.place(drums, C, t + k * six, 0.25 + 0.15 * k)
        for k in range(4):  # swung 16th shaker everywhere
            sw = 0.18 * six if k % 2 else 0.0
            sh = shaker(k % 2 == 0)
            g = 0.6 if sec == "break" else 1.0
            A.place(shk_l, sh, t + k * six + sw, g * (1.0 if k % 2 else 0.6))
            A.place(shk_r, sh, t + k * six + sw, g * (0.6 if k % 2 else 1.0))
        # --- harmony
        target = intro_buf if sec == "intro" else inst
        if sec != "break":
            A.place(target, stab(chord), t + beat / 2, 0.55)              # offbeat stab
            for pos, oct_ in ((1.0, 0), (1.5, 12) if b % 2 else (1.75, 0)):  # house bass (eighths)
                A.place(target, bass(root + oct_), t + pos * beat / 2, 0.8)
        if b % 4 == 0:
            ln = 4 * beat + 0.3
            A.place(padbuf, pad(chord, ln), t, 0.9 if sec == "break" else 0.45)
        # --- bell motif (2 eighths per beat; place this beat's share)
        if sec in ("dropA", "dropB", "break"):
            motif = MOTIF[bar % 2]
            for pos, idx in motif:
                if pos // 2 == b % 4:
                    gl = {"dropA": 0.35, "break": 0.5, "dropB": 0.6}[sec]
                    A.place(lead, bell(A.mtof(chord[idx] + 12)), bar * 4 * beat + pos * beat / 2, gl)

    # intro: the filter opens across the hook
    ramp = np.clip(np.arange(n) / SR / max(hook_end, 0.1), 0, 1) ** 2
    intro_mix = A.lp(intro_buf, 700) * (1 - ramp) + intro_buf * ramp

    # sidechain pump from the kick (not in the break)
    sc = np.ones(n)
    for b in range(final_beat):
        t = b * beat
        if section(t) == "break":
            continue
        i0 = int(t * SR)
        ln = int(beat * SR)
        seg = 1 - 0.6 * np.exp(-np.arange(ln) / SR / 0.1)
        sc[i0:i0 + ln] = seg[: max(0, min(ln, n - i0))]

    body = (inst + intro_mix) * sc + A.reverb(padbuf, 2.2, 0.3) * sc
    # ping-pong delay on the bell
    d = int(0.75 * beat * SR)
    lead_l, lead_r = lead.copy(), lead.copy()
    lead_l[d:] += 0.35 * lead[:-d]
    lead_r[2 * d:] += 0.25 * lead[:-2 * d]
    lead_l, lead_r = A.reverb(lead_l, 1.8, 0.25), A.reverb(lead_r, 1.8, 0.25)

    # riser into drop B, ending chord + hit
    A.place(body, A.riser(2 * beat) * 0.8, bd_end - 2 * beat)
    end = A.shimmer_chord([60, 64, 67, 72, 76, 79], 4.0)
    end[: int(2.0 * SR)] += A.impact(True) * 0.8
    A.place(body, end, final_beat * beat)

    L = drums + body + lead_l + shk_l
    R = drums + body + lead_r + shk_r
    return np.stack([L, R])[:, : int(total * SR)]


# ---------------------------------------------------------------- "night" style
# Moody trap / future-bass bed in A minor (Am F C G): half-time clap, 808 sub glides, rolling hats,
# airy pad and a soft pluck arpeggio. Same sections as groove (intro filter, drop, break, drop B, end hit).
NIGHT_CHORDS = [
    ([57, 60, 64, 67], 33),   # Am7
    ([53, 57, 60, 64], 29),   # Fmaj7
    ([48, 55, 60, 64], 36),   # C
    ([55, 59, 62, 67], 31),   # G
]


def sub808(root, ln):
    n = int(ln * SR)
    t = np.arange(n) / SR
    f = A.mtof(root) * (1 + 0.9 * np.exp(-t / 0.03))
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.tanh(2.2 * np.sin(ph) * np.exp(-t / (ln * 0.55))) * 0.8


def pluck(f, ln=0.35):
    n = int(ln * SR)
    t = np.arange(n) / SR
    s = A.saw(f, n, 6) * np.exp(-t / 0.09) * (1 - np.exp(-t / 0.002))
    return A.lp(s, 3000) * 0.5


def night(total, scenes, beat):
    n = int(total * SR) + 4 * SR
    drums, sub, padbuf, lead, intro_buf = (np.zeros(n) for _ in range(5))
    hl, hr = np.zeros(n), np.zeros(n)
    hook_end = scenes[1]["start"]
    mont = next((s for s in scenes if s["cfg"]["move"] == "montage"), None)
    bd_start = mont["start"] if mont else total
    bd_end = mont["end"] if mont else total
    final_t = scenes[-1]["words"][-1]["t1"] + 0.35
    final_beat = int(np.ceil(final_t / beat))
    K, C = A.kick(), A.clap()
    six = beat / 4

    def section(t):
        if t < hook_end:
            return "intro"
        if bd_start <= t < bd_end:
            return "break"
        return "dropB" if t >= bd_end else "dropA"

    for b in range(final_beat):
        t = b * beat
        sec = section(t)
        bar, pos = b // 4, b % 4
        chord, root = NIGHT_CHORDS[bar % 4]
        drop = sec in ("dropA", "dropB")
        # kick + 808 pattern (half-time trap): beat 1, the "and" of 2 (even bars) or beat 3.5 (odd bars)
        hits = {0: 0.0} if pos == 0 else {}
        if pos == 1 and bar % 2 == 0:
            hits[1] = 0.5
        if pos == 2 and bar % 2 == 1:
            hits[2] = 0.5
        for _, off in hits.items():
            if sec != "break":
                A.place(drums, K, t + off * beat, 0.9 if drop else 0.6)
                A.place(sub, sub808(root - 12, beat * 1.6), t + off * beat, 0.9 if drop else 0.5)
        # half-time clap on beat 3
        if drop and pos == 2:
            A.place(drums, C, t, 0.8)
        # hats: 8ths, rolling 16th/32nd at bar end
        if sec != "intro" or t > hook_end * 0.5:
            roll = drop and pos == 3 and bar % 2 == 1
            steps = 8 if roll else 2
            for k in range(steps):
                tk = t + k * beat / steps
                g = (0.32 if k % 2 == 0 else 0.22) * (0.6 if sec == "break" else 1.0)
                h = A.hat(False)
                A.place(hl, h, tk, g * (1.0 if k % 2 else 0.7))
                A.place(hr, h, tk, g * (0.7 if k % 2 else 1.0))
        # pad every bar, pluck arpeggio in eighths
        if pos == 0:
            A.place(padbuf if sec != "intro" else intro_buf, A.lp(sum(A.saw(A.mtof(m) * d, int((4 * beat + 0.4) * SR), 7)
                     for m in chord for d in (1.0, 1.006)) / 8 * np.minimum(1, np.arange(int((4 * beat + 0.4) * SR)) / SR / 0.3), 2400), t, 0.6)
        if sec in ("dropA", "dropB", "break"):
            for k in range(2):
                note = chord[(b * 2 + k) % len(chord)] + 12
                A.place(lead, pluck(A.mtof(note)), t + k * beat / 2, 0.45 if sec != "dropA" else 0.3)
    ramp = np.clip(np.arange(n) / SR / max(hook_end, 0.1), 0, 1) ** 2
    intro_mix = A.lp(intro_buf, 600) * (1 - ramp) + intro_buf * ramp
    body = A.reverb(padbuf + intro_mix, 2.6, 0.35) + sub
    d = int(0.75 * beat * SR)
    ll, lr = lead.copy(), lead.copy()
    ll[d:] += 0.35 * lead[:-d]
    lr[2 * d:] += 0.25 * lead[:-2 * d]
    ll, lr = A.reverb(ll, 2.0, 0.3), A.reverb(lr, 2.0, 0.3)
    if bd_end < total:
        A.place(body, A.riser(2 * beat) * 0.7, bd_end - 2 * beat)
    end = A.shimmer_chord([57, 60, 64, 69, 72, 76], 4.0)
    end[: int(2.0 * SR)] += A.impact(True) * 0.8
    A.place(body, end, final_beat * beat)
    L = drums + body + ll + hl
    R = drums + body + lr + hr
    return np.stack([L, R])[:, : int(total * SR)]
