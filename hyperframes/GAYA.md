# Gaya KL AUTO SB (satu-satunya gaya, versi 17 Nov 2026)

Gaya rumah untuk video promosi kereta *sambung bayar / lease to own* KL AUTO SB. Versi rasmi ialah video
**Perodua Aruz Advance 2021 dengan suara Ashraf** (`renders/KLAUTOSB_Aruz_2021_Ashraf.mp4`, `videos/aruz2021.json`).
Gaya lama (v1 hitam, suara Microsoft) telah dipadam. Semua video baharu
guna gaya ini secara lalai (`DEFAULT_STYLE = "v2"` dalam `tools/build.py`). Templatnya ialah `videos/contoh.json`.

## Buat video kereta baharu

1. Letak gambar dalam `../photos/NAMA/` (gambar menegak atau melintang dari telefon pun boleh).
2. Salin `videos/contoh.json` kepada `videos/NAMA.json`. Tukar `src`, nama gambar, skrip dan butiran kereta.
3. Jana dan render:
   ```bash
   cd hyperframes
   python3 tools/build.py --video NAMA
   ./hf.sh check
   ./hf.sh render --quality delivery -o renders/NAMA.mp4
   ```
   Pratonton dan edit di pelayar: `./hf.sh preview`.

Butiran yang biasanya diberi untuk setiap kereta: model, tahun, deposit, bulanan, baki loan, due date, mileage,
owner, plate, roadtax/insurans, lokasi, warranty, agreement direct owner.

## Babak (9)

| # | Babak | Gambar | Gerakan kamera | Masuk dengan |
|---|---|---|---|---|
| 1 | Hook: tawaran utama (cth DEPOSIT BAWAH RM7K) + SAMBUNG BAYAR / LEASE TO OWN + tag (cth SUV 7 SEATER). Suara buka dengan ayat hook dahulu | depan 3/4 | *reveal*: tarik ke belakang, kemudian perlahan | (frame 0 = thumbnail, tajuk sudah ada) |
| 2 | MODEL / VARIAN TAHUN | depan | naik perlahan + kilauan cahaya | whip ke kiri |
| 3 | DEPOSIT RMx (dikira naik) | belakang 3/4 | *orbit*: pusing perlahan | kilat putih |
| 4 | BULANAN RMx + tag LOAN x TAHUN x BULAN | belakang / badge | tolak masuk | whip ke atas |
| 5 | AGREEMENT / DIRECT OWNER + tag (cth ROADTAX & INSURANS / SMART WARRANTY) | stereng / sisi | gerak sisi | zoom-through |
| 6 | BUTIRAN KERETA: senarai bertanda (tahun, mileage, owner, plate, due date, lokasi) | kabin / odometer | serong perlahan | whip ke kiri |
| 7 | INTERIOR KEMAS / 7 TEMPAT DUDUK | 2–5 gambar: dashboard, baris 2, baris 3, but | **tiada zoom**; gambar meluncur masuk ikut perkataan yang disebut | cahaya hangat (*light leak*) |
| 8 | NAK VIEW KERETA? + senarai 4 perkara | belakang 3/4 | serong perlahan | gelap sekejap |
| 9 | WHATSAPP SEKARANG / SAMBUNG BAYAR BERDEPOSIT + kad 017-203 6099 | depan 3/4 | tolak masuk perlahan + kilauan | zoom-through |

- **Kereta penuh dalam bingkai:** gambar dalam `fit_width` (depan 3/4, depan, belakang 3/4) dipapar penuh lebar, bermula y 110, dengan latar kabur.
- **Harga:** angka dikira naik dari RM0 (0.9 saat) hingga angka tepat, dengan sedikit hentakan kamera bila angka mendarat.
- **Senarai bertanda:** setiap baris muncul satu demi satu dengan tanda ✓ merah. Panel ikut lebar teks, dan baris tidak terbalut. Jika lebih 5 baris, baris dirapatkan.
- **Nombor WhatsApp:** muncul bahagian demi bahagian tepat bila disebut, dengan riak pada ikon dan kilauan di hujung.
- Gerakan laju menggunakan *motion blur* Hyperframes.

## Format

- 1080×1920 (9:16), 30 fps, H.264, audio AAC, kenyaringan sekitar −14 LUFS (standard TikTok/Reels).
- Panjang sekitar 60–65 saat, ikut suara. Potongan babak jatuh pada grid ketukan 118 BPM.

## Identiti visual

- **Tulisan:** semua putih. Merah `#E2232D` hanya untuk elemen hiasan: garisan, tag, tanda ✓, bar logo.
- **Ikon WhatsApp:** hijau WhatsApp `#25D366`.
- **Fon:** Poppins ExtraBold untuk tajuk dan harga, Montserrat Bold untuk label berjarak, Poppins Bold untuk sarikata.
- **Logo:** "KL AUTO SB" di penjuru kiri atas, dengan bar merah di sebelahnya, sepanjang video.
- **Cerah:** gambar dicerahkan 7%, dan latar kabur hanya sedikit gelap. Lapisan gelap tipis di atas dan ringan di bawah. Tulisan putih bergantung pada bayangnya sendiri (drop-shadow) untuk kekal jelas.
- **Kedudukan:** tajuk di bahagian atas (y 290), dalam zon selamat TikTok/Reels.

## Sarikata

- **Kedudukan:** di bawah tengah, **di bawah kereta**, bukan di tengah gambar. Baris terakhir berakhir pada y 1540.
- **Rupa:** saiz 48 px, semua putih, latar gelap lembut mengikut setiap baris.
- **Frasa:** maksimum 5 perkataan dan 2 baris seimbang, muncul sekali gus. Pecah ikut ayat dan koma, dan tiada perkataan tinggal seorang.

## Suara

**Lalai baharu: ElevenLabs "Ashraf - Smooth, Casual and Expressive"** (voice id `NHFTLozDZneDWyQjRGAO`, model `eleven_v4`).
Jana satu klip bagi setiap babak (teks = bahagian sebutan skrip, nombor dieja penuh), simpan sebagai
`assets/audio/NAMA_el/el_<babak>.mp3`, kemudian dalam `videos/NAMA.json` letak `"voice": "elevenlabs", "voice_dir": "NAMA_el"`.
Masa sarikata dianggar daripada jeda dalam audio. Contoh: `videos/aruz2021.json`.

Sebutan tetap: nombor, harga, tahun dan nombor telefon dieja penuh dalam bahagian sebutan skrip. `X50|X-fifty`.
Skrip guna "." (bukan "!") kecuali ayat hook; elakkan "je".

## Muzik (groove, `tools/music.py`)

- House ceria dalam nada major (C, G, Am, F), 118 BPM. Disintesis sendiri, jadi bebas royalti.
- **Bahagian ikut babak:**
  - Hook: intro yang "terbuka" perlahan.
  - Model hingga butiran: drop penuh.
  - Interior: rehat tanpa kick.
  - Recap dan penutup: riser dan snare roll, kemudian drop kedua.
  - Akhir: kord penutup dengan hentakan.
- Muzik direndahkan setiap kali suara bercakap.
- **Bunyi pembukaan (semua video):** rev enjin + hentakan + shutter kamera + kilauan pada saat 0.
- **Bunyi kesan:** whoosh pada setiap potongan, hentakan pada pembukaan, *ka-ching* bila harga mendarat, *pop* pada setiap tanda ✓ dan tag, *ding* notifikasi bila nombor WhatsApp disebut, kilauan di hujung, riser sebelum penutup.

## Penutup alternatif (supaya setiap video berbeza)

- **`"head": "process"`**: langkah PROSES bernombor (`steps`: [teks, perkataan cue]); setiap langkah menyala bila disebut, garisan merah mengisi, langkah terakhir hijau. Bunyi *pop* pada setiap langkah.
- **`"head": "cta2"`**: DEPOSIT PROMO (`promo_label`, `promo_price` dikira naik + *ka-ching*), chip DOKUMEN (`docs`), kemudian kad WhatsApp.
- Hook boleh mula dengan harga bulanan, deposit, atau ciri utama (cth "SEDAN TURBO"). Contoh: `videos/s70.json`.
- Jangan sebut atau paparkan bangsa pemilik ("Owner Melayu") dalam video.

## Babak khas (pilihan)

- **Studio (`"studio": "gambar.jpg"` pada babak deposit):** kereta sebenar dipotong (rembg, piksel kereta tidak diubah) dan diletak atas pentas studio gelap: lampu sorot, lantai berkilat, pantulan, bayang, kilauan cahaya. Kereta masuk dari kanan.
- **Animasi 3 langkah (`"head": "journey"`):** (1) pen menulis tandatangan + cop SAH, (2) CASH atau TRANSFER online + ✓ BERJAYA, (3) kereta sebenar (`car_side`) bergerak pulang ke rumah + TAHNIAH. Setiap langkah menyala ikut perkataan yang disebut; bunyi pop, ka-ching dan whoosh. Contoh: `videos/ccross.json`.

## Video yang sudah dibuat

| Video | Fail |
|---|---|
| Perodua Aruz Advance 2021 | `videos/aruz2021.json` (**versi rasmi templat**) |
| Perodua Aruz Advance 2019 | `videos/aruz.json` |
| Proton X50 Executive Facelift 2026 (putih) | `videos/x50.json` |
| Proton S70 Premium Facelift 2026 (merah) | `videos/s70.json` (penutup PROSES + Deposit Promo) |
| Perodua Aruz Advance 2019 (biru) | `videos/aruzbiru.json` |
| Toyota Vios G 2026 (putih) | `videos/vios.json` |
| Toyota Corolla Cross 1.8 V (putih) | `videos/ccross.json` (hook soalan + bunyi pembukaan) |
| Proton S70 Premium Facelift 2026 (silver) | `videos/s70silver.json` (hook SAMBUNG BAYAR / LEASE TO OWN di permulaan) |

### Sebutan tambahan

  | Plat V | `V,|huruf-vi,` (bukan "lima") |
  | boot (but kereta) | tulis `boot`, bukan `but` |
