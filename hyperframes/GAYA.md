# Gaya KL AUTO SB (v2)

Gaya rumah untuk video promosi kereta *sambung bayar* KL AUTO SB, seperti dalam video Proton X50 putih
(`renders/KLAUTOSB_X50_Putih_v1.mp4`). Semua video baharu guna gaya ini secara lalai (`DEFAULT_STYLE = "v2"`
dalam `tools/build.py`).

## Buat video unit baharu

1. Letak gambar dalam `../photos/NAMA/` (gambar menegak dari telefon pun boleh).
2. Salin `videos/contoh.json` kepada `videos/NAMA.json`, kemudian isi nama gambar mengikut babak.
3. Jana dan render:
   ```bash
   cd hyperframes
   python3 tools/build.py --video NAMA
   ./hf.sh check
   ./hf.sh render --quality delivery -o renders/NAMA.mp4
   ```
   Pratonton dan edit di pelayar: `./hf.sh preview`.

Skrip, suara, harga dan nombor telefon dikongsi oleh semua video (`SCRIPT` dan `CTA` dalam `tools/build.py`).
`voice_from: "hitam"` guna semula suara yang sudah diluluskan. Buang medan itu untuk jana suara baharu
selepas skrip diubah.

## Format

- 1080×1920 (9:16), 30 fps, H.264, audio AAC, kenyaringan sekitar −14 LUFS (standard TikTok/Reels).
- Panjang sekitar 54 saat, ikut suara. Potongan babak jatuh pada grid ketukan 118 BPM.

## Identiti visual

- **Tulisan:** semua putih. Merah `#E2232D` hanya untuk elemen hiasan: garisan, tag, ikon WhatsApp, bar logo.
- **Fon:** Poppins ExtraBold untuk tajuk dan harga, Montserrat Bold untuk label berjarak, Poppins Bold untuk sarikata.
- **Logo:** "KL AUTO SB" di penjuru kiri atas, dengan bar merah di sebelahnya, sepanjang video.
- **Cerah:** gambar dicerahkan 7%, dan latar kabur hanya sedikit gelap. Lapisan gelap tipis di atas dan ringan di bawah, jadi tulisan putih bergantung pada bayangnya sendiri (drop-shadow) untuk kekal jelas.
- **Zon selamat:** semua teks antara y 269 dan 1248 (TikTok/Reels). Tajuk di bahagian atas (y 290).

## Babak (8)

| # | Babak | Gambar | Gerakan kamera | Masuk dengan |
|---|---|---|---|---|
| 1 | Hook: SAMBUNG BAYAR / LEASE TO OWN | depan 3/4 | *reveal*: tarik ke belakang laju, kemudian perlahan | (frame 0 = thumbnail, tajuk sudah ada) |
| 2 | PROTON X50 / EXECUTIVE FACELIFT 2026 | depan | naik perlahan + kilauan cahaya | whip ke kiri |
| 3 | DEPOSIT RM13,000 | belakang 3/4 | *orbit*: pusing perlahan | kilat putih |
| 4 | BULANAN RM1,300 + tag LOAN 9 TAHUN | close-up badge | tolak masuk | whip ke atas |
| 5 | AGREEMENT / DIRECT OWNER + tag PROSES MUDAH & PANTAS | belakang | gerak sisi | zoom-through |
| 6 | MODERN INTERIOR / COMFORTABLE FAMILY SUV | 2–5 gambar interior/but | **tiada zoom**; gambar meluncur masuk ikut perkataan yang disebut | cahaya hangat (*light leak*) |
| 7 | NAK VIEW KERETA? + senarai bertanda (4 perkara) | mana-mana gambar luar | serong perlahan | gelap sekejap |
| 8 | WHATSAPP SEKARANG + kad nombor | depan 3/4 | tolak masuk perlahan + kilauan | zoom-through |

- **Kereta penuh dalam bingkai:** gambar dalam `fit_width` dipapar penuh lebar, dengan latar kabur di atas dan bawah, supaya kereta tak terpotong.
- **Harga:** angka dikira naik dari RM0 (0.9 saat), dengan sedikit hentakan kamera bila angka mendarat.
- **Senarai bertanda:** setiap baris muncul satu demi satu, dengan tanda ✓ merah yang melantun.
- **Nombor WhatsApp:** muncul bahagian demi bahagian tepat bila disebut, dengan riak pada ikon dan kilauan di hujung.
- Gerakan laju menggunakan *motion blur* Hyperframes.

## Sarikata

- Di bawah tengah: baris terakhir berakhir pada y 1320 (jalur sarikata TikTok). Saiz 48 px. Frasa penuh (maksimum 5 perkataan, 2 baris seimbang), muncul sekali gus.
- Latar gelap lembut mengikut setiap baris. Pecah ikut ayat dan koma, dan tiada perkataan tinggal seorang.
- Di TikTok, butang di sebelah kanan mungkin menindih sedikit hujung baris yang panjang. Kedudukan bawah tengah adalah pilihan klien.

## Suara

- Microsoft `ms-MY-OsmanNeural`, kelajuan −4%, nada −1 Hz. Gaya rileks dan santai.
- Skrip guna tanda "." (bukan "!") supaya intonasi tenang. Elakkan "je".
- Jeda antara ayat sekitar 0.45 saat.

## Muzik (groove, `tools/music.py`)

- House ceria dalam nada major (C, G, Am, F), 118 BPM. Disintesis sendiri, jadi bebas royalti.
- **Bahagian ikut babak:**
  - Hook: intro yang "terbuka" perlahan.
  - Model hingga agreement: drop penuh (kick, clap, hi-hat, shaker swing, bass house, stab kord, motif loceng).
  - Interior: rehat tanpa kick.
  - Senarai dan penutup: riser dan snare roll, kemudian drop kedua.
  - Akhir: kord penutup dengan hentakan.
- Muzik direndahkan setiap kali suara bercakap.
- **Bunyi kesan:** whoosh pada setiap potongan, hentakan lembut pada harga, riser sebelum kad WhatsApp.

## Gaya lain yang disimpan

- **v1** (`--video hitam`): rupa v6 unit hitam. Interior bertukar dengan crossfade, muzik minor yang lebih ringkas, harga muncul tanpa kiraan naik.
