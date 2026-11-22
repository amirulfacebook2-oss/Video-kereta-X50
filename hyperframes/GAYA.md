# Gaya KL AUTO SB (satu-satunya gaya, versi 20 Nov 2026)

Gaya rumah untuk video promosi kereta *sambung bayar / lease to own* KL AUTO SB. **Versi rasmi terkini ialah video
Proton S70 3 warna v4** (`renders/KLAUTOSB_S70_3_Warna_Syarat_v4.mp4`, `videos/s70v2.json`); templatnya `videos/contoh.json`.
Ia mengikut gaya X50 Jade Grey v4 di bawah, dengan **hook SYARAT UTAMA sebagai lalai** (untuk tapis penonton yang serius sahaja).
Semua unit seterusnya ikut gaya ini secara lalai:

- **Gambar:** gambar showroom yang disediakan pemilik (kereta atas lantai showroom gelap) dipakai **penuh, tidak dipotong** (`fit_width`).
  `"photo_top"` pada babak menurunkan gambar supaya tulisan, cop atau kad tidak menutup kereta. Gambar depan 3/4 yang lebar sesuai untuk babak deposit/agreement.
  Jika hanya ada gambar asal (luar), guna `"soft_bg"` untuk kaburkan latar. Latar showroom buatan (kereta dipotong) **tidak** digunakan.
- **Pembukaan lalai (baru): hook SYARAT UTAMA** (lihat di bawah). Pilihan lama: ayat hook berbeza + cop **WAJIB ADA DEPOSIT** dihentak bila disebut (`hook_curtain` + `"curtain": false`,
  `"stamp": ["WAJIB ADA DEPOSIT", "wajib"], "stamp_size": 60`). Suara: *"... Ingat ya, wajib ada deposit. Tiada deposit, tak perlu PM."*
  Satu cop sahaja (tiada kad kuning). Tulisan SAMBUNG BAYAR / LEASE TO OWN / tag model sejak frame 0. Tiada baris warna (COLOR).
- **Tanpa bunyi pembukaan** (`"intro_sfx": false`); hanya bunyi hentakan cop.
- **Kamera lembut** (`"zoom": "soft"`).
- **Deposit:** tag **BAWAH MARKET**, suara *"Deposit? RMx sahaja. Ini bawah market."*
- **Plate V:** tulis `plate V`, sebut "plate vi".
- **Agreement beranimasi**, **animasi 4 langkah** (semakan dokumen dahulu).
- **Penutup:** `docs` = IC, LESEN, BIL AIR/API, **DEPOSIT**; suara *"Sediakan IC, lesen, bil air atau api, dan deposit. Deposit wajib ya, tiada deposit tak perlu PM."*; `cta.meta` = model kereta.

- **Hook syarat utama (`"hook_checks"`):** panel SYARAT UTAMA dengan ✓ Deposit RMx, IC, Lesen (setiap baris menyala bila disebut) + cop **DEPOSIT WAJIB RMx**.
  Suara: *"Syarat utama sambung bayar kereta <MODEL> ni, cuma deposit RMx, IC dan lesen sahaja. Yang serius dan dah ada deposit, baru PM ya. Kalau tiada deposit, tak perlu PM dulu. Tengok video ni sampai habis, dan fahamkan dulu ya."*
  Penutup `docs` = IC, LESEN, DEPOSIT. Contoh: `videos/s70v2.json`.

- **Pilihan warna (`"color_cars": [[gambar, LABEL, cue], ...]`, `color_top`):** kereta kecil sebenar (dipotong) dalam kad muncul satu demi satu bila warna disebut, dengan bunyi pop.
- **Cop latar putih:** `"stamp_white": true` (tulisan dan bingkai merah atas latar putih).

- **Kad deposit profesional (`"badge": [LABEL, NILAI, ayat kecil]`, `badge_top`) — LALAI BARU untuk hook:** garisan merah melintas, panel kaca gelap terbuka dari tengah,
  label DEPOSIT WAJIB, angka dikira naik, ayat kecil (cth "Ready deposit & serius sahaja PM"), panel rapat bawah tag (badge_top ~545) dan kilauan; bunyi whoosh + ka-ching. Ganti cop (pemilik mahu nampak profesional)
  dan tiada panel SYARAT UTAMA (IC & lesen cukup disebut dalam suara). Contoh: `videos/x50warna.json`.

### Pilihan babak pembukaan (sedia ada)

| Pilihan | Kunci | Bila guna |
|---|---|---|
| Cop WAJIB ADA DEPOSIT tanpa tirai (**lalai**) | `"hook_curtain": "depan34.jpg", "curtain": false, "stamp": ["WAJIB ADA DEPOSIT", "wajib"]` | semua unit |
| Tirai + cop 1 UNIT SAHAJA | `"hook_curtain": "depan34.jpg", "stamp": ["1 UNIT SAHAJA", "sahaja"]` | unit tunggal; teks cop boleh ditukar (cth "DEPOSIT RENDAH") |
| Kad foto | `"hook_card": "depan34.jpg"` | gambar penuh dalam bingkai putih yang mendarat |
| Studio | `"studio": "depan34.jpg"` | kereta dipotong atas pentas studio |
| Studio 3 warna | `"studio_trio": [[gambar, LABEL, cue], ...]` | beberapa warna/unit sekali gus |

Idea pembukaan yang belum dibina (boleh diminta bila-bila): lampu depan menyala, kilat kamera, harga dulu, skrin telefon (chat),
kad foto berganda, koyak plastik. Contoh visual: `docs/idea_pembukaan_1.jpg` dan `docs/idea_pembukaan_2.jpg`.

Versi lama (Corolla Cross, Aruz 2021) masih boleh dirujuk.

## Struktur rasmi (ikut video X50 Jade Grey v4)

| # | Babak | Isi |
|---|---|---|
| 1 | Hook (lalai: tirai + cop; lihat pilihan di atas) | Tirai terbuka menunjukkan gambar penuh, cop dihentak bila disebut. Tulisan **SAMBUNG BAYAR / LEASE TO OWN** + tag model sejak frame 0. Suara: ayat hook yang **berbeza setiap video** (cth *"Satu unit sahaja!"*, *"Siapa cari sedan turbo?"*, *"Jangan scroll dulu!"*) + *"<Model> untuk dijual secara sambung bayar."* Tanpa bunyi pembukaan. |
| 2 | Model | nama model, warna, keadaan (cth koyak plastik) |
| 3 | Deposit | RMx dikira naik + tag **BAWAH MARKET**. Suara: *"Deposit? RMx sahaja. Ini bawah market."* |
| 4 | Bulanan | RMx + tag LOAN x TAHUN |
| 5 | Agreement (animasi) | `"head": "agreement"`: ANDA ↔ dokumen AGREEMENT ↔ OWNER (garisan tersambung, ✓, "🤝 TERUS DENGAN OWNER"), kemudian chip ✓ muncul ikut perkataan (`steps`: insurans, roadtax, plat, warranty) |
| 6 | Spesifikasi | `"head": "specs"`, 5–7 baris ✓ (hanya ciri yang ada pada unit) |
| 7 | Interior | 2–5 gambar ikut cue, tiada zoom |
| 8 | 4 Langkah Mudah (lalai) | `"head": "journey"`: semakan dokumen → tandatangan → bayar cash/transfer → bawa balik kereta. 4 langkah = langkah pertama semakan dokumen (MYKAD, LESEN, BIL ditanda ✓ + LULUS). `car_flip: true` jika kereta dalam gambar menghadap kanan |
| 9 | Penutup | `"head": "cta2"`: deposit promo, dokumen, WhatsApp 017-203 6099. **Tukar `cta.meta` kepada model kereta** (teks di bawah nombor telefon) |

Jadual 9 babak di bawah ialah susunan asas yang lama; untuk video baharu ikut struktur di atas.
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

- **Kamera lembut (`"zoom": "soft"`):** zoom dan gerakan dikurangkan kira-kira 1/3 supaya gambar tidak nampak terlalu dekat. Guna bersama `fit_width` untuk semua gambar luar kereta. Contoh: `videos/s70warna.json`.
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

- **Studio (`"studio": "gambar.jpg"`, lalai pada hook):** kereta sebenar dipotong (rembg, piksel kereta tidak diubah) dan diletak atas pentas studio gelap: lampu sorot, lantai berkilat, pantulan, bayang, kilauan cahaya. Kereta masuk dari kanan.
- **Animasi 3 langkah (`"head": "journey"`):** (1) pen menulis tandatangan + cop SAH, (2) CASH atau TRANSFER online + ✓ BERJAYA, (3) kereta sebenar (`car_side`) bergerak pulang ke rumah + TAHNIAH. Setiap langkah menyala ikut perkataan yang disebut; bunyi pop, ka-ching dan whoosh. Contoh: `videos/ccross.json`.

- **Hook 3 warna (`"studio_trio"`):** 3 kereta sebenar (dipotong) atas satu pentas studio, satu baris label warna yang muncul bila setiap warna disebut. Format: `[[gambar, LABEL, perkataan cue], ...]` (kiri, kanan, tengah depan). Contoh: `videos/s70warna.json`.

- **Hook kad foto (`"hook_card": "gambar.jpg"`):** gambar asal penuh (tidak dipotong) dalam bingkai putih yang jatuh dan mendarat, atas latar kabur gambar sama, dengan kilauan cahaya. `card_top`, `card_w` laras kedudukan. Pilihan jika tidak mahu studio.
- **Hook tirai + cop (`"hook_curtain": "gambar.jpg"`, `"stamp": ["1 UNIT SAHAJA", "sahaja"]`):** skrin gelap dengan garis cahaya, tirai terbuka ke kiri dan kanan menunjukkan gambar penuh, kemudian cop merah dihentak (dengan gegaran dan bunyi hentakan) tepat bila perkataan cue disebut. `stamp_top` laras kedudukan cop. Contoh: `videos/x50putih3.json`.
- **Tanpa bunyi pembukaan:** `"intro_sfx": false` dalam fail video.
- **Deposit:** tag ringkas **BAWAH MARKET**, suara *"Ini bawah market."* (tanpa sebut kereta second hand).

## Video yang sudah dibuat

| Video | Fail |
|---|---|
| Perodua Aruz Advance 2021 | `videos/aruz2021.json` (versi rasmi lama) |
| Perodua Aruz Advance 2019 | `videos/aruz.json` |
| Proton X50 Executive Facelift 2026 (putih) | `videos/x50.json` |
| Proton S70 Premium Facelift 2026 (merah) | `videos/s70.json` (penutup PROSES + Deposit Promo) |
| Perodua Aruz Advance 2019 (biru) | `videos/aruzbiru.json` |
| Toyota Vios G 2026 (putih) | `videos/vios.json` |
| Toyota Corolla Cross 1.8 V (putih) | `videos/ccross.json` (**versi rasmi templat**: hook studio, deposit bawah harga pasaran, 3 langkah mudah) |
| Proton X50 Executive Facelift 2026 (3 warna, syarat utama) | `videos/x50warna.json` |
| Proton S70 Premium Facelift 2026 (3 warna, syarat utama) | `videos/s70v2.json` |
| Proton X50 Executive Facelift 2026 (Jade Grey) | `videos/x50grey.json` (**versi rasmi templat**: gambar showroom, cop WAJIB ADA DEPOSIT, deposit dalam dokumen) |
| Proton X50 Executive Facelift 2026 (Snow White, tirai + cop) | `videos/x50putih3.json` |
| Proton X50 Executive Facelift 2026 (Snow White, gaya baharu) | `videos/x50putih2.json` (hook kad foto, tanpa bunyi pembukaan) |
| Proton X50 Executive Facelift 2026 (Quartz Black) | `videos/x50hitam.json` (hook "Jangan scroll dulu!", 4 langkah dengan semakan dokumen) |
| Proton S70 Premium Facelift 2026 (3 warna: merah, silver, putih) | `videos/s70warna.json` (hook 3 warna, bulanan bawah RM1,100) |
| Proton S70 Premium Facelift 2026 (silver, gaya baharu) | `videos/s70silver2.json` (hook "Siapa cari sedan turbo?", kamera lembut) |
| Proton S70 Premium Facelift 2026 (silver, lama) | `videos/s70silver.json` (hook SAMBUNG BAYAR / LEASE TO OWN di permulaan) |

### Sebutan tambahan

  | model | tulis `model|mo-del` (sebut "mo-del", bukan "modal") |
  | Nombor WhatsApp | `"cta": {"phone": "012-297 9744"}` dan dalam skrip `*012-297|kosong-satu-dua,-dua-sembilan-tujuh, *9744.|sembilan-tujuh-empat-empat.` |
  | Plate V | tulis `plate V`, sebut **"plate vi"** (`*plate *V,|vi,`); bukan "huruf vi" atau "lima" |
  | boot (but kereta) | tulis `boot`, bukan `but` |
