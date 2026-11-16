# SAMBUNG BAYAR BERDEPOSIT — KL AUTO SB

Iklan video menegak 9:16 (1080×1920, 30 fps, H.264) untuk **Proton X50 Executive Facelift 2026**, ~38 saat.

## Cara guna

1. Letak foto asal kereta dalam folder `photos/` (jpg/png/webp). Foto digunakan ikut **susunan nama fail**:

   | Fail | Babak |
   |---|---|
   | 1st | Hook (0–5s) + end card CTA — terbaik: depan 3/4 |
   | 2nd | PROTON X50 / EXECUTIVE FACELIFT 2026 — sisi |
   | 3rd | DEPOSIT RM13,000 — belakang 3/4 |
   | 4th | BULANAN RM1,300 — depan |
   | 5th | AGREEMENT DIRECT OWNER — detail (rim/lampu) |
   | 6th–8th | Montaj interior (dashboard, tempat duduk, but) |

   Kurang dari 8 foto pun boleh — slot akan berulang. Tiada foto = placeholder untuk semakan susun atur sahaja.
2. `pip install -r requirements.txt` (perlukan `ffmpeg`).
3. `./make_video.sh` → `build/KLAUTOSB_ProtonX50_SambungBayar_1080x1920.mp4`
   (`./make_video.sh --preview` untuk draf pantas 540×960).

## Apa yang ada

- **Voiceover**: suara lelaki Bahasa Melayu Malaysia (`ms-MY-OsmanNeural`), jeda dipendekkan automatik.
- **Sarikata**: disegerakkan perkataan demi perkataan dari masa sebenar TTS; kata kunci merah / perak.
- **Muzik**: elektronik korporat 118 BPM dijana sendiri (bebas royalti), sidechain, ducking bawah suara, −14 LUFS.
- **SFX**: impact pembuka, whoosh setiap transisi, soft hit pada harga, riser + aksen penutup.
- **Visual**: Ken Burns / dolly-in / tracking kiri-kanan, parallax latar kabur, light sweep, transisi push dengan motion blur, tipografi Poppins + Montserrat, zon selamat TikTok/Reels.

Teks skrip, harga dan nombor telefon: `src/config.py`.
