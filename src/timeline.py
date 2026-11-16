"""Beat-quantised scene timeline shared by audio + video renderers."""
import json
import math

from config import BEAT, BUILD, SCENES

VO_LEAD = [0.10, 0.22, 0.22, 0.22, 0.22, 0.22, 0.30]  # VO start offset inside each scene
TAIL_PAD = 0.30          # breathing room after each line
CTA_HOLD = 2.4           # end-card hold after the last word
TRANS = 0.32             # transition length (seconds), centred on the cut


def build():
    vo = json.loads((BUILD / "vo" / "timings.json").read_text())
    t, scenes = 0.0, []
    for i, (cfg, v) in enumerate(zip(SCENES, vo)):
        need = VO_LEAD[i] + v["duration"] + (CTA_HOLD if i == len(SCENES) - 1 else TAIL_PAD)
        beats = max(cfg["min_beats"], math.ceil(need / BEAT))
        if i < len(SCENES) - 1 and beats % 2:
            beats += 1  # keep cuts on strong beats
        dur = beats * BEAT
        words = [dict(w, t0=w["t0"] + t + VO_LEAD[i], t1=w["t1"] + t + VO_LEAD[i])
                 for w in v["tokens"]]
        scenes.append(dict(i=i, start=t, end=t + dur, beats=beats, vo_start=t + VO_LEAD[i],
                           vo_dur=v["duration"], words=words, cfg=cfg))
        t += dur
    return scenes, t


if __name__ == "__main__":
    sc, total = build()
    for s in sc:
        print(f"{s['i']}: {s['start']:6.2f} -> {s['end']:6.2f}  ({s['beats']} beats)")
    print("total", round(total, 2))
