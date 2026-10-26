# Ringkasan Evaluasi Foto Nyata

## Data uji

- 15 foto dari satu halaman catatan tulisan tangan (PPPL, Domain Modeling), dipotret dengan iPhone.
- Variasi latar: alas meja bermotif garis kontur (7 foto, `mat`), seprai abu-abu (7 foto, `seprai`), seprai gelap (1 foto).
- Variasi sudut: tegak (7 foto) dan miring, yaitu diputar atau difoto dari samping (8 foto).
- Variasi cahaya terjadi secara alami, tidak dikontrol: lampu kamar, bayangan tangan, pantulan.
- Teks acuan OCR adalah transkripsi manual halaman tersebut, disimpan di `foto_uji/*.txt`.

## Kriteria

Satu foto dinilai **berhasil** jika keempat sudut deteksi berada pada sudut halaman, hasil scan tegak, dan seluruh teks terbaca. Penilaian dilakukan manual dengan melihat lembar kontak.

Akurasi OCR dihitung dengan Tesseract `--psm 6`, lalu kemiripan karakter terhadap teks acuan diukur dengan `difflib.SequenceMatcher` (`autojunk=False`).

## Hasil deteksi

| Kondisi | v1 (minAreaRect lalu segmentasi) | v2 (segmentasi lalu minAreaRect) |
|---|---|---|
| Semua | 12/15 (80%) | 13/15 (87%) |
| Sudut tegak | 7/7 (100%) | 7/7 (100%) |
| Sudut miring | 5/8 (62%) | 6/8 (75%) |
| Latar alas meja | 6/7 | 6/7 |
| Latar seprai | 5/7 | 6/7 |
| Latar seprai gelap | 1/1 | 1/1 |
| Waktu proses rata-rata | 130 ms | 105 ms |

Pada v1, metode `minAreaRect` gagal 2 dari 2 kasus. Kotak persegi panjangnya tidak bisa mengikuti bentuk trapesium halaman, dan pada satu kasus kotak itu mencakup seluruh bingkai foto. Metode segmentasi berhasil 5 dari 5. Karena itu, pada v2 urutan kedua metode cadangan ini ditukar.

**Catatan bias:** perbaikan v2 ditemukan dan diuji pada 15 foto yang sama. Angka 13/15 masih perlu dikonfirmasi dengan foto baru.

## Hasil OCR (v2, 15 foto)

| Sudut | n | Foto asli | Hasil scan gray | Hasil scan biner |
|---|---|---|---|---|
| Miring | 8 | 22,7% | 51,8% | 63,8% |
| Tegak | 7 | 67,3% | 59,5% | 70,8% |
| Semua | 15 | 43,5% | 55,4% | 67,0% |

Interpretasi:

- Manfaat terbesar muncul pada foto miring: akurasi OCR naik dari 22,7% menjadi 63,8%, karena koreksi perspektif menegakkan baris teks.
- Pada foto tegak, kenaikannya kecil (67,3% menjadi 70,8%).
- Keluaran *gray* (CLAHE dan *unsharp masking*) justru menurunkan OCR pada foto tegak. Untuk OCR, keluaran biner adalah yang terbaik.

## Kasus gagal (v2)

1. `mat_miring_02`: halaman berhasil terdeteksi, tetapi foto diambil menyamping, sehingga hasil scan juga menyamping dan OCR hanya sekitar 8%. Penyebabnya, pipeline tidak mengoreksi orientasi halaman.
2. `seprai_miring_09`: sisi kiri halaman terpotong oleh bingkai foto, dan sudut kanan bawah terdeteksi pada sampul buku. Akibatnya ada pita hitam di bagian bawah hasil scan, meskipun teksnya masih terbaca.

## Keterbatasan evaluasi

- Hanya satu halaman dan satu jenis tulisan tangan, sehingga hasil OCR belum mewakili tulisan orang lain.
- Foto dikirim melalui chat, sehingga resolusinya sudah turun (1125×2000 piksel). Foto asli dari kamera kemungkinan memberi hasil OCR yang berbeda.
- Label berhasil/gagal ditentukan oleh satu penilai.
- Jumlah sampel kecil (15 foto), jadi persentase di atas belum bisa digeneralisasi.

## Perbandingan dengan data sintetis (Tabel 1, metrik OCR yang sudah diperbaiki)

Pada 10 foto sintetis, OCR foto asli sudah mencapai 98,4% dan pipeline lengkap 98,1%. Data sintetis berhuruf cetak sehingga terlalu mudah untuk mengukur manfaat OCR. Data ini lebih tepat dipakai untuk mengukur ketepatan geometri (galat sudut rata-rata 2,3 piksel). Manfaat praktis pipeline terlihat pada foto nyata yang diambil dari sudut miring.
