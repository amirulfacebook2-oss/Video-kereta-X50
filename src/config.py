"""Creative config for "SAMBUNG BAYAR BERDEPOSIT" — KL AUTO SB, Proton X50 Executive Facelift 2026.

Voiceover token syntax (one token per spoken unit):
    word                  -> shown and spoken as-is
    DISPLAY|spoken words  -> subtitle shows DISPLAY, TTS speaks "spoken words"
    *token                -> subtitle highlight in RED
    ^token                -> subtitle highlight in METALLIC SILVER
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PHOTOS = ROOT / "photos"
FONTS = ROOT / "assets" / "fonts"
BUILD = ROOT / "build"

W, H, FPS = 1080, 1920, 30
BPM = 118
BEAT = 60.0 / BPM

VOICE = "ms-MY-OsmanNeural"   # natural Malaysian Malay male
VOICE_RATE = "+10%"            # medium-fast, still relaxed
VOICE_PITCH = "-2Hz"

# Palette — Midnight Black x Pearl White x Metallic Silver, red accents
BLACK = (11, 13, 18)
PEARL = (246, 245, 241)
SILVER_LIGHT = (232, 236, 240)
SILVER_DARK = (150, 156, 165)
RED = (226, 35, 45)

# Each scene: voiceover line, headline layers, photo slot(s), camera move.
# photo: index into the sorted photo list (wraps if fewer photos are supplied).
SCENES = [
    dict(  # 1 — HOOK (first 2s)
        vo="Jangan scroll dulu! Nak SUV premium tanpa pening ^loan ^bank?",
        head=[("SAMBUNG BAYAR", "hero", "pearl"), ("LEASE TO OWN", "sub", "silver")],
        photos=[0], move="dolly_in", min_beats=8,
    ),
    dict(  # 2 — MODEL
        vo="^Proton ^X50|X-fifty ^Executive ^Facelift ^2026|dua-ribu-dua-puluh-enam, kini boleh *sambung *bayar!",
        head=[("PROTON X50", "hero", "silver"), ("EXECUTIVE FACELIFT 2026", "sub", "pearl")],
        photos=[1], move="track_lr", min_beats=8,
    ),
    dict(  # 3 — DEPOSIT
        vo="^Lease ^to ^own, *deposit cuma *RM13,000|tiga-belas-ribu-ringgit sahaja.",
        head=[("DEPOSIT", "label", "silver"), ("RM13,000", "price", "red")],
        photos=[2], move="zoom_out", min_beats=8,
    ),
    dict(  # 4 — MONTHLY
        vo="*Bulanan pula, *RM1,300|seribu-tiga-ratus-ringgit je!",
        head=[("BULANAN", "label", "silver"), ("RM1,300", "price", "red")],
        photos=[3], move="dolly_in", min_beats=6,
    ),
    dict(  # 5 — AGREEMENT
        vo="^Agreement *direct *owner, urusan telus dan mudah.",
        head=[("AGREEMENT", "label", "silver"), ("DIRECT OWNER", "hero", "pearl")],
        photos=[4], move="track_rl", min_beats=8,
    ),
    dict(  # 6 — LIFESTYLE / DETAIL MONTAGE (no headline, let the car breathe)
        vo="Rekaan bergaya, kabin selesa, padan untuk keluarga.",
        head=[],
        photos=[5, 6, 7], move="montage", min_beats=8,
    ),
    dict(  # 7 — CTA END CARD
        vo="Berminat? *WhatsApp ^KL|K-L ^Auto ^SB|S-B sekarang, *017-203|kosong-satu-tujuh,-dua-kosong-tiga, *6099|enam-kosong-sembilan-sembilan.",
        head="cta",
        photos=[0], move="cta", min_beats=14,
    ),
]

CTA = dict(
    brand="KL AUTO SB",
    title="SAMBUNG BAYAR BERDEPOSIT",
    model="PROTON X50 EXECUTIVE FACELIFT 2026",
    deposit="DEPOSIT RM13,000",
    monthly="BULANAN RM1,300",
    phone="017-203 6099",
)
