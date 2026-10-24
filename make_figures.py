"""Buat gambar laporan dari keluaran evaluate.py (results/)."""
import json

import cv2
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

rows = json.load(open("results/metrics.json"))
rgb = lambda p: cv2.cvtColor(cv2.imread(p), cv2.COLOR_BGR2RGB)

# Gambar 2: tahapan pada sampel 05
items = [("samples/note_05.jpg", "(a) Foto masukan"), ("results/05_edges.png", "(b) Canny + closing"),
         ("results/05_detect.jpg", "(c) Sudut terdeteksi"), ("results/05_warped.png", "(d) Hasil warp"),
         ("results/05_gray.png", "(e) Iluminasi + CLAHE"), ("results/05_binary.png", "(f) Biner Otsu")]
fig, ax = plt.subplots(2, 3, figsize=(10, 7))
for a, (p, t) in zip(ax.ravel(), items):
    a.imshow(rgb(p)); a.set_title(t, fontsize=10); a.axis("off")
fig.tight_layout(); fig.savefig("fig2_tahapan_sampel05.png", dpi=170); plt.close(fig)

# Gambar 3: foto asli vs hasil, sampel 10 dan 04
by = {r["id"]: r for r in rows}
fig, ax = plt.subplots(2, 2, figsize=(9, 7.5))
for i, n in enumerate(["10", "04"]):
    ax[i, 0].imshow(rgb(f"samples/note_{n}.jpg"))
    ax[i, 0].set_title(f"Sampel {n}: foto asli (OCR {by[n]['ocr_raw']:.0f}%)", fontsize=10)
    ax[i, 1].imshow(rgb(f"results/{n}_binary.png"))
    ax[i, 1].set_title(f"Sampel {n}: hasil pipeline (OCR {by[n]['ocr_full']:.0f}%)", fontsize=10)
    ax[i, 0].axis("off"); ax[i, 1].axis("off")
fig.tight_layout(); fig.savefig("fig3_perbandingan_10_04.png", dpi=170); plt.close(fig)

# Gambar 4: OCR per sampel
x = np.arange(len(rows)); w = 0.27
fig, a = plt.subplots(figsize=(9, 3.6))
for k, (key, lab, col) in enumerate([("ocr_raw", "Foto asli", "#8a8f98"), ("ocr_warp", "Warp saja", "#e0a33a"),
                                     ("ocr_full", "Pipeline penuh", "#2f6db5")]):
    a.bar(x + (k - 1) * w, [r[key] for r in rows], w, label=lab, color=col)
a.set_xticks(x, [r["id"] for r in rows]); a.set_xlabel("Sampel"); a.set_ylabel("Akurasi OCR (%)")
a.set_ylim(0, 105); a.spines[["top", "right"]].set_visible(False)
a.legend(ncol=3, fontsize=9, frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.0))
fig.tight_layout(); fig.savefig("fig4_ocr_per_sampel.png", dpi=200); plt.close(fig)

# Gambar 5: kasus gagal sampel 09
fig, ax = plt.subplots(1, 3, figsize=(12, 4.2))
for a, (p, t) in zip(ax, [("results/09_detect.jpg", "(a) Sudut tetap terdeteksi benar"),
                          ("results/09_gray.png", f"(b) Grayscale (OCR {by['09']['ocr_gray']:.0f}%)"),
                          ("results/09_binary.png", f"(c) Biner (OCR {by['09']['ocr_full']:.0f}%)")]):
    a.imshow(rgb(p)); a.set_title(t, fontsize=10); a.axis("off")
fig.tight_layout(); fig.savefig("fig5_kasus_gagal_sampel09.png", dpi=170); plt.close(fig)
print("ok")
