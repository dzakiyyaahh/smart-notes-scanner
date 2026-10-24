# Smart Notes Scanner

**Digitalisasi Foto Catatan Kuliah dengan Koreksi Perspektif dan Peningkatan Kualitas Citra**
Kelompok 4 · Teknologi Berkembang (Computer Vision) · OpenCV klasik, tanpa deep learning

Program ini mengubah foto catatan kuliah dari ponsel (miring, ada latar meja, pencahayaan tidak merata) menjadi citra dokumen yang tegak, bersih, dan mudah dibaca.

**Pipeline:** resize → Gaussian blur → Canny → morphological closing → kontur 4 titik (`approxPolyDP`, cadangan `minAreaRect`) → transformasi perspektif → koreksi iluminasi (dilate + median, lalu divide) → CLAHE + unsharp masking (keluaran *gray*) → Otsu (keluaran *binary*).

## Struktur repo

```
smart-notes-scanner/
├── scanner.py         # inti pipeline: detect_document, warp, enhance, scan
├── main.py            # CLI untuk foto sendiri
├── make_samples.py    # pembuat 10 foto sintetis + ground truth
├── evaluate.py        # evaluasi: galat sudut, SSIM, OCR, waktu proses
├── make_figures.py    # gambar 2–5 untuk laporan
├── requirements.txt   # versi library dikunci
├── fonts/             # font DejaVu Sans, dipakai make_samples.py
├── samples/           # 10 foto sintetis (sudah dibuat)
├── results/           # metrics.json hasil evaluasi
└── foto_asli/         # taruh foto catatan asli tim di sini
```

---

## 1. Persiapan (macOS, termasuk Apple Silicon M1/M2/M3)

Buka **Terminal** dan jalankan perintah berikut satu kali saja.

```bash
# Homebrew (lewati kalau sudah terpasang)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Python 3.12 dan Tesseract OCR (Tesseract hanya dibutuhkan untuk evaluate.py)
brew install python@3.12 tesseract
```

Untuk memeriksa hasilnya, jalankan `python3.12 --version` dan `tesseract --version`.

> Pengguna Windows: pasang Python 3.12 dari python.org dan Tesseract dari UB-Mannheim. Ganti `source .venv/bin/activate` dengan `.venv\Scripts\activate`.

## 2. Buka di Visual Studio Code

1. Ekstrak zip. Di VS Code, pilih **File → Open Folder…** lalu pilih folder `smart-notes-scanner`.
2. Pasang ekstensi **Python** (dari Microsoft) kalau belum ada.
3. Buka terminal VS Code dengan **Terminal → New Terminal**, lalu jalankan:

   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

4. Tekan `Cmd+Shift+P`, ketik **Python: Select Interpreter**, lalu pilih `./.venv/bin/python`.
   Mulai sekarang, setiap terminal baru di VS Code otomatis memakai `.venv` (ditandai `(.venv)` di awal baris).

Untuk memastikan versi yang terpasang sudah benar:

```bash
python -c "import cv2; print(cv2.__version__)"   # harus 4.13.0
```

## 3. Menjalankan program

```bash
# satu foto
python main.py --input foto_asli/catatan1.jpg --output hasil

# satu folder sekaligus, plus visualisasi sudut dan perbandingan sebelum/sesudah
python main.py --input foto_asli/ --output hasil --debug --compare
```

| Opsi | File yang dihasilkan di `hasil/` |
|---|---|
| (selalu) | `<nama>_gray.png` (hasil scan grayscale), `<nama>_binary.png` (hasil scan hitam-putih) |
| `--debug` | `<nama>_detect.jpg` (garis hijau pada 4 sudut dokumen), `<nama>_edges.png` (peta tepi Canny) |
| `--compare` | `<nama>_compare.jpg` (foto asli dan hasil scan berdampingan) |

> **Foto dari iPhone:** format HEIC **tidak bisa** dibaca OpenCV. Ubah ke JPG dulu, misalnya lewat Preview → File → Export → JPEG, atau dari Terminal: `sips -s format jpeg IMG_1234.HEIC --out foto_asli/catatan1.jpg`.

**Tips foto:** letakkan kertas di atas permukaan yang rata dan gelap, pastikan keempat sudut kertas terlihat, dan hindari bayangan yang terlalu pekat.
Untuk buku spiral, lipat buku ke belakang supaya hanya satu halaman yang tampak. Kalau halaman sebelahnya ikut terfoto (apalagi saat difoto dari sudut miring), halaman itu bisa ikut terdeteksi sebagai bagian dari kertas.

## 4. Evaluasi pada data sintetis (Tabel 1 laporan)

```bash
python evaluate.py        # membaca samples/, menulis results/ dan results/metrics.json
python make_figures.py    # opsional: membuat fig2–fig5 untuk laporan
```

Baris terakhir keluaran yang diharapkan:

```
MEAN err 2.3 ssim 0.816 raw 92.4 warp 86.3 full 93.3 ms ~60 success 10/10
```

Nilai `ms` (waktu proses) bisa berbeda tergantung laptop. Nilai lainnya harus sama persis.
Kalau ingin membuat ulang sampel dari awal, jalankan `python make_samples.py`; hasilnya identik karena seed-nya tetap.

---

## Cara mengambil Screenshot 1–3 untuk Bab 6

Siapkan dulu foto asli tim (JPG) di folder `foto_asli/`.

| Screenshot | Yang dilakukan |
|---|---|
| **1. Menjalankan `main.py` pada foto asli** | Di terminal VS Code, jalankan `python main.py --input foto_asli/ --output hasil --debug --compare`. Ambil screenshot jendela VS Code (`Cmd+Shift+4`, lalu tekan Spasi dan klik jendelanya). Pastikan terlihat perintahnya, keluaran `...: dokumen terdeteksi`, dan folder `hasil/` di panel Explorer. |
| **2. Visualisasi sudut (`--debug`)** | Buka `hasil/<nama>_detect.jpg` di VS Code atau Preview, lalu screenshot. Garis hijau harus mengikuti tepi kertas. |
| **3. Perbandingan sebelum/sesudah** | Buka `hasil/<nama>_compare.jpg`, lalu screenshot (atau langsung sisipkan file JPG-nya ke laporan). |

Kalau keluarannya `TIDAK terdeteksi (fallback)`, foto ulang dengan latar yang lebih kontras dan keempat sudut kertas terlihat. Kasus gagal seperti ini juga bisa dibahas di bagian keterbatasan.

---

## Upload ke GitHub

**Cara A: lewat VS Code (tanpa mengetik git)**
1. Klik ikon **Source Control** di sidebar kiri, lalu klik **Publish to GitHub**.
2. Login ke GitHub kalau diminta, lalu pilih *public* atau *private* (sesuaikan dengan aturan dosen).
3. Selesai. Folder `.venv/` dan `hasil/` otomatis tidak ikut ter-upload karena tercantum di `.gitignore`.

**Cara B: lewat terminal**
```bash
git init
git add .
git commit -m "Smart Notes Scanner - Kelompok 4"
git branch -M main
git remote add origin https://github.com/<username>/smart-notes-scanner.git   # buat repo kosong dulu di github.com/new
git push -u origin main
```

Setelah itu, masukkan URL repo ke laporan di bagian **[URL GitHub]** dan Lampiran C.

## Masalah yang sering muncul

| Gejala | Solusi |
|---|---|
| `TesseractNotFoundError` | Jalankan `brew install tesseract`, lalu buka terminal baru |
| `command not found: python` | Aktifkan venv dulu: `source .venv/bin/activate` |
| Foto dilewati tanpa pesan apa pun | Formatnya HEIC atau file tersebut bukan gambar. Ubah ke JPG |
| Angka evaluasi berbeda dari Tabel 1 | Cek `cv2.__version__`. Harus 4.13.0, **bukan** 5.x |

## Catatan versi

- Versi library dikunci di `requirements.txt`. Dengan OpenCV 5.0, deteksi sudut sampel 09 gagal (galat sekitar 395 px) sehingga rata-rata OCR turun ke 88,4%.
- Tambahan dibanding versi awal: opsi `--compare` di `main.py`, folder `samples/`/`results/` dibuat otomatis, dan font disertakan di `fonts/` supaya sampel identik di semua OS.
- **Fallback baru di `scanner.py` (`detect_paper_region`)**: dipakai hanya jika deteksi kontur Canny **dan** `minAreaRect` sama-sama gagal. Alasannya, pada foto nyata (buku spiral di atas seprai) tepi kertas tidak membentuk segi empat tertutup, karena satu sisi berupa spiral dan lipatan kain ikut terdeteksi sebagai tepi. Fallback ini mencari area kertas yang terang dengan Otsu pada kanal L (LAB), lalu memotong area itu di sepanjang tepi Canny agar terpisah dari benda terang lain, dan mengambil convex hull dari komponen terbesar sebagai 4 titik. Hasil evaluasi pada data sintetis (Tabel 1) **tidak berubah**, karena fallback ini tidak pernah terpicu di sana.
- Font DejaVu Sans memakai lisensi Bitstream Vera (bebas didistribusikan). Lihat `fonts/LICENSE-DejaVu.txt`.
