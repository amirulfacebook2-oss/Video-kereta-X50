"""Generate the Malay male voiceover per scene + word-level timings for subtitles."""
import asyncio
import json
import re
import subprocess

import os
import ssl

import edge_tts
import numpy as np
import edge_tts.communicate as _ec

# Route through the HTTPS proxy / CA bundle when present (cloud sandbox).
_CA = os.environ.get("SSL_CERT_FILE") or ("/root/.ccr/ca-bundle.crt" if os.path.exists("/root/.ccr/ca-bundle.crt") else None)
if _CA:
    _ec._SSL_CTX = ssl.create_default_context(cafile=_CA)
PROXY = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")

from config import BUILD, SCENES, VOICE, VOICE_PITCH, VOICE_RATE

OUT = BUILD / "vo"


def parse_tokens(line):
    """Return list of dicts: display, spoken, style ('red'|'silver'|None)."""
    toks = []
    for raw in line.split():
        style = None
        if raw[0] == "*":
            style, raw = "red", raw[1:]
        elif raw[0] == "^":
            style, raw = "silver", raw[1:]
        if "|" in raw:
            disp, spoken = raw.split("|", 1)
            # carry trailing punctuation of spoken part to the display
            m = re.search(r"[.,!?]+$", spoken)
            if m and not re.search(r"[.,!?]$", disp) and not re.search(r"\d", disp):
                disp += m.group(0)
            spoken = spoken.replace("-", " ")
        else:
            disp = spoken = raw
        toks.append(dict(display=disp, spoken=spoken, style=style))
    return toks


def norm(w):
    return re.sub(r"[^\w]", "", w.lower())


async def synth(i, scene):
    toks = parse_tokens(scene["vo"])
    text = " ".join(t["spoken"] for t in toks)
    comm = edge_tts.Communicate(text, VOICE, rate=VOICE_RATE, pitch=VOICE_PITCH,
                                boundary="WordBoundary", proxy=PROXY)
    audio = bytearray()
    bounds = []
    async for chunk in comm.stream():
        if chunk["type"] == "audio":
            audio += chunk["data"]
        elif chunk["type"] == "WordBoundary":
            bounds.append(dict(t0=chunk["offset"] / 1e7,
                               t1=(chunk["offset"] + chunk["duration"]) / 1e7,
                               text=chunk["text"]))
    mp3 = OUT / f"vo_{i}.mp3"
    mp3.write_bytes(bytes(audio))

    # Align boundaries (TTS words) to display tokens sequentially.
    words = [b for b in bounds if norm(b["text"])]
    wi = 0
    for t in toks:
        need = [norm(w) for w in t["spoken"].split() if norm(w)]
        got, acc = [], ""
        target = "".join(need)
        while wi < len(words) and len(acc) < len(target):
            acc += norm(words[wi]["text"])
            got.append(words[wi])
            wi += 1
        if not got:  # fallback: reuse previous end
            prev = toks[toks.index(t) - 1] if toks.index(t) else None
            t0 = prev["t1"] if prev else 0.0
            got = [dict(t0=t0, t1=t0 + 0.2)]
        t["t0"], t["t1"] = got[0]["t0"], got[-1]["t1"]
    # decode to wav for precise duration / mixing
    wav = OUT / f"vo_{i}.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp3), "-ar", "48000",
                    "-ac", "1", str(wav)], check=True)
    dur = tighten(wav, toks)
    return dict(tokens=toks, duration=dur, raw_bounds=bounds)


MAX_GAP, KEEP_GAP, LEAD, TAIL = 0.42, 0.30, 0.06, 0.22


def tighten(wav, toks):
    """Shorten long pauses between words and trim head/tail silence, shifting timings."""
    sr, x = read_wav(wav)
    segs, cursor, shift = [], max(0.0, toks[0]["t0"] - LEAD), 0.0
    shift = cursor
    start = cursor
    for a, b in zip(toks, toks[1:]):
        gap = b["t0"] - a["t1"]
        if gap > MAX_GAP:
            cut0 = a["t1"] + KEEP_GAP / 2
            cut1 = b["t0"] - KEEP_GAP / 2
            segs.append((start, cut0))
            for t in toks[toks.index(b):]:
                t["_s"] = t.get("_s", 0) + (cut1 - cut0)
            start = cut1
    end = toks[-1]["t1"] + TAIL
    segs.append((start, end))
    y = np.concatenate([x[int(s0 * sr):int(s1 * sr)] for s0, s1 in segs])
    # 4ms fades at the joins are implicit-safe since cuts land in silence
    for t in toks:
        d = t.pop("_s", 0) + shift
        t["t0"] -= d
        t["t1"] -= d
    write_wav(wav, sr, y)
    return len(y) / sr


def read_wav(p):
    import wave
    with wave.open(str(p)) as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return sr, x


def write_wav(p, sr, y):
    import wave
    with wave.open(str(p), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())


async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    res = []
    for i, s in enumerate(SCENES):
        r = await synth(i, s)
        print(f"scene {i}: {r['duration']:.2f}s  "
              + " ".join(f"{t['display']}[{t['t0']:.2f}]" for t in r["tokens"]))
        res.append(r)
    (OUT / "timings.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
