"""Evaluasi pada foto catatan NYATA (tanpa ground truth sudut).

Tahap 1 - jalankan:
    python evaluate_real.py --input foto_uji --output hasil_uji
  -> hasil_uji/hasil_uji.csv   (satu baris per foto, kolom label_manual masih kosong)
  -> hasil_uji/lembar_kontak_XX.jpg (deteksi + hasil scan per foto, untuk dinilai manual)

Tahap 2 - isi kolom label_manual di CSV dengan "benar" atau "salah"
  (benar = garis hijau mengikuti tepi kertas dan hasil scan tegak serta terbaca).

Tahap 3 - rekap:
    python evaluate_real.py --rekap hasil_uji/hasil_uji.csv
  -> ringkasan per latar dan per sudut, dan hasil_uji/rekap.md untuk laporan

Penamaan file foto: <latar>_<sudut>_<nomor>.jpg, contoh: seprai_miring_01.jpg, meja-gelap_tegak_02.jpg.
Opsional OCR: taruh teks asli halaman pada file .txt bernama sama (contoh: handout_tegak_01.txt).
"""
import argparse, csv, difflib, glob, os, time
from collections import defaultdict

import cv2
import numpy as np

from scanner import scan

EXT = (".jpg", ".jpeg", ".png")


def norm(s):
    return " ".join(s.lower().split())


def ocr_acc(img, truth):
    import pytesseract
    txt = pytesseract.image_to_string(img, config="--psm 6")
    return difflib.SequenceMatcher(None, norm(truth), norm(txt), autojunk=False).ratio() * 100


def thumb(img, h=420):
    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR) if img.ndim == 2 else img
    return cv2.resize(img, (max(1, int(img.shape[1] * h / img.shape[0])), h), interpolation=cv2.INTER_AREA)


def run(a):
    os.makedirs(a.output, exist_ok=True)
    files = sorted(f for f in glob.glob(os.path.join(a.input, "*")) if f.lower().endswith(EXT))
    skipped = sorted(f for f in glob.glob(os.path.join(a.input, "*"))
                     if not f.lower().endswith(EXT + (".txt",)) and not os.path.basename(f).startswith("."))
    for f in skipped:
        print(f"dilewati (bukan JPG/PNG, mungkin HEIC): {os.path.basename(f)}")
    rows, tiles = [], []
    for f in files:
        img = cv2.imread(f)
        if img is None:
            print(f"dilewati (tidak bisa dibaca): {os.path.basename(f)}")
            continue
        base = os.path.splitext(os.path.basename(f))[0]
        parts = base.split("_")
        t = time.time(); r = scan(img); ms = (time.time() - t) * 1000
        row = dict(file=os.path.basename(f), latar=parts[0] if len(parts) > 1 else "-",
                   sudut=parts[1] if len(parts) > 2 else "-", terdeteksi=int(r["found"]), metode=r["method"],
                   ms=round(ms), resolusi=f"{img.shape[1]}x{img.shape[0]}",
                   ocr_foto="", ocr_scan_gray="", ocr_scan_biner="", label_manual="")
        gt = os.path.join(a.input, base + ".txt")
        if os.path.exists(gt):
            truth = open(gt, encoding="utf-8").read()
            row["ocr_foto"] = round(ocr_acc(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), truth), 1)
            row["ocr_scan_gray"] = round(ocr_acc(r["gray"], truth), 1)
            row["ocr_scan_biner"] = round(ocr_acc(r["binary"], truth), 1)
        rows.append(row)
        vis = img.copy()
        lw = max(4, img.shape[0] // 250)
        cv2.polylines(vis, [r["corners"].astype(np.int32)], True, (0, 255, 0), lw)
        cv2.imwrite(os.path.join(a.output, f"{base}_detect.jpg"), vis)
        cv2.imwrite(os.path.join(a.output, f"{base}_binary.png"), r["binary"])
        tile = np.hstack([thumb(vis), np.full((420, 10, 3), 255, np.uint8), thumb(r["binary"])])
        bar = np.full((50, tile.shape[1], 3), 255, np.uint8)
        cv2.putText(bar, f"{base} | {r['method']} | {round(ms)} ms", (8, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2, cv2.LINE_AA)
        tiles.append(np.vstack([bar, tile]))
        print(f"{base}: {'terdeteksi' if r['found'] else 'TIDAK terdeteksi'} [metode: {r['method']}] {round(ms)} ms")
    if not rows:
        print("Tidak ada foto JPG/PNG di", a.input); return
    out_csv = os.path.join(a.output, "hasil_uji.csv")
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    # lembar kontak: 6 foto per halaman, 2 kolom
    for p in range(0, len(tiles), 6):
        page = tiles[p:p + 6]
        W = max(t.shape[1] for t in page)
        page = [cv2.copyMakeBorder(t, 10, 10, 10, W - t.shape[1] + 10, cv2.BORDER_CONSTANT, value=(255, 255, 255)) for t in page]
        while len(page) % 2: page.append(np.full_like(page[0], 255))
        sheet = np.vstack([np.hstack(page[i:i + 2]) for i in range(0, len(page), 2)])
        cv2.imwrite(os.path.join(a.output, f"lembar_kontak_{p // 6 + 1:02d}.jpg"), sheet, [cv2.IMWRITE_JPEG_QUALITY, 85])
    print(f"\n{len(rows)} foto diproses. Isi kolom label_manual (benar/salah) di {out_csv}, lalu jalankan:")
    print(f"python evaluate_real.py --rekap {out_csv}")


def rekap(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    lab = lambda r: r["label_manual"].strip().lower() in ("benar", "b", "1", "ya", "y")
    unlabeled = [r["file"] for r in rows if not r["label_manual"].strip()]
    if unlabeled:
        print("PERINGATAN: belum dilabeli:", ", ".join(unlabeled))
    rows = [r for r in rows if r["label_manual"].strip()]
    if not rows:
        print("Belum ada baris yang dilabeli."); return
    lines = ["| Kelompok | Nilai | Berhasil | Total | Persentase |", "|---|---|---|---|---|"]
    def add(name, key):
        g = defaultdict(list)
        for r in rows: g[r[key]].append(lab(r))
        for k in sorted(g):
            v = g[k]; lines.append(f"| {name} | {k} | {sum(v)} | {len(v)} | {100 * sum(v) / len(v):.0f}% |")
    ok = [lab(r) for r in rows]
    lines.append(f"| Semua | - | {sum(ok)} | {len(ok)} | {100 * sum(ok) / len(ok):.0f}% |")
    add("Latar", "latar"); add("Sudut", "sudut"); add("Metode deteksi", "metode")
    ms = [float(r["ms"]) for r in rows]
    extra = [f"\nWaktu proses rata-rata: {np.mean(ms):.0f} ms (min {min(ms):.0f}, maks {max(ms):.0f}) per foto."]
    o = [r for r in rows if r["ocr_foto"]]
    if o:
        m = lambda k: np.mean([float(r[k]) for r in o])
        extra.append(f"OCR pada {len(o)} foto ber-teks-acuan: foto asli {m('ocr_foto'):.1f}%, "
                     f"hasil scan gray {m('ocr_scan_gray'):.1f}%, hasil scan biner {m('ocr_scan_biner'):.1f}%.")
        extra += ["", "| OCR per sudut | n | Foto asli | Scan gray | Scan biner |", "|---|---|---|---|---|"]
        for sd in sorted({r["sudut"] for r in o}):
            g = [r for r in o if r["sudut"] == sd]
            mm = lambda k: np.mean([float(r[k]) for r in g])
            extra.append(f"| {sd} | {len(g)} | {mm('ocr_foto'):.1f}% | {mm('ocr_scan_gray'):.1f}% | {mm('ocr_scan_biner'):.1f}% |")
        extra.append("")
    gagal = [r["file"] for r in rows if not lab(r)]
    extra.append("Kasus gagal: " + (", ".join(gagal) if gagal else "tidak ada") + ".")
    txt = "\n".join(lines + extra)
    print(txt)
    out = os.path.join(os.path.dirname(path), "rekap.md")
    open(out, "w", encoding="utf-8").write(txt + "\n")
    print(f"\nTersimpan di {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Evaluasi Smart Notes Scanner pada foto nyata")
    ap.add_argument("--input", default="foto_uji", help="folder foto uji")
    ap.add_argument("--output", default="hasil_uji", help="folder hasil")
    ap.add_argument("--rekap", metavar="CSV", help="buat rekap dari CSV yang sudah dilabeli")
    a = ap.parse_args()
    rekap(a.rekap) if a.rekap else run(a)
