"""CLI: python main.py --input foto.jpg --output hasil/   (atau --input folder/)"""
import argparse, glob, os, cv2, numpy as np
from scanner import scan


def side_by_side(img, out, h=1000):
    """[Tambahan] Gabungkan foto asli dan hasil scan berdampingan untuk perbandingan."""
    out = cv2.cvtColor(out, cv2.COLOR_GRAY2BGR) if out.ndim == 2 else out
    rs = lambda x: cv2.resize(x, (int(x.shape[1] * h / x.shape[0]), h), interpolation=cv2.INTER_AREA)
    a, b = rs(img), rs(out)
    gap = np.full((h, 20, 3), 255, np.uint8)
    row = np.hstack([a, gap, b])
    bar = np.full((70, row.shape[1], 3), 255, np.uint8)
    for x, t in ((10, "SEBELUM (foto asli)"), (a.shape[1] + 30, "SESUDAH (hasil scan)")):
        cv2.putText(bar, t, (x, 48), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 0, 0), 3, cv2.LINE_AA)
    return np.vstack([bar, row])


def main():
    ap = argparse.ArgumentParser(description="Smart Notes Scanner")
    ap.add_argument("--input", required=True, help="path gambar atau folder gambar")
    ap.add_argument("--output", default="output", help="folder hasil")
    ap.add_argument("--debug", action="store_true", help="simpan edge map & visualisasi sudut")
    ap.add_argument("--compare", action="store_true", help="[tambahan] simpan gambar sebelum/sesudah berdampingan")
    a = ap.parse_args()
    os.makedirs(a.output, exist_ok=True)
    files = sorted(glob.glob(os.path.join(a.input, "*"))) if os.path.isdir(a.input) else [a.input]
    for f in files:
        img = cv2.imread(f)
        if img is None: continue
        r = scan(img); base = os.path.splitext(os.path.basename(f))[0]
        cv2.imwrite(f"{a.output}/{base}_gray.png", r["gray"])
        cv2.imwrite(f"{a.output}/{base}_binary.png", r["binary"])
        if a.debug:
            vis = img.copy(); cv2.polylines(vis, [r["corners"].astype(int)], True, (0, 255, 0), 6)
            cv2.imwrite(f"{a.output}/{base}_detect.jpg", vis); cv2.imwrite(f"{a.output}/{base}_edges.png", r["edges"])
        if a.compare:
            cv2.imwrite(f"{a.output}/{base}_compare.jpg", side_by_side(img, r["binary"]))
        print(f"{base}: dokumen {'terdeteksi' if r['found'] else 'TIDAK terdeteksi (fallback)'}")
if __name__ == "__main__": main()
