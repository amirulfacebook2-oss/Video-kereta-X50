#!/usr/bin/env bash
# Build "SAMBUNG BAYAR BERDEPOSIT" — KL AUTO SB / Proton X50 Executive Facelift 2026
# Usage: ./make_video.sh            -> final 1080x1920 30fps H.264 (build/KLAUTOSB_..._1080x1920.mp4)
#        ./make_video.sh --preview  -> fast 540x960 draft (build/preview.mp4)
set -euo pipefail
cd "$(dirname "$0")/src"
python3 tts.py        # Malay male voiceover + word timings (needs internet: speech.platform.bing.com)
python3 timeline.py   # beat-locked scene timeline (118 BPM)
python3 audio.py      # music bed + SFX + ducking + loudnorm -14 LUFS
python3 render.py "$@"
