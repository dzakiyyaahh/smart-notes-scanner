import cv2, numpy as np, glob, json, difflib, os, time, pytesseract
from skimage.metrics import structural_similarity as ssim
from scanner import scan, order_points
ref = cv2.imread("samples/reference.png"); refg = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY)
from make_samples import TEXT  # noqa (re-generates samples deterministically)
GT_TEXT = "\n".join(TEXT)
def norm(s): return " ".join(s.lower().split())
def ocr_acc(img):
    # autojunk=False: heuristik bawaan difflib membuang karakter yang sering muncul pada teks >200 karakter,
    # sehingga skor OCR anjlok pada keluaran yang tidak sempurna (mis. sampel 09: 45,5% -> 85,9%).
    txt = pytesseract.image_to_string(img, config="--psm 6")
    return difflib.SequenceMatcher(None, norm(GT_TEXT), norm(txt), autojunk=False).ratio()*100
def sharp(g): return cv2.Laplacian(g, cv2.CV_64F).var()
os.makedirs("results", exist_ok=True)
rows = []
for p in sorted(glob.glob("samples/note_??.jpg")):
    n = p[-6:-4]; img = cv2.imread(p); gt = order_points(np.load(p[:-4]+"_gt.npy"))
    t = time.time(); r = scan(img); dt = (time.time()-t)*1000
    err = float(np.mean(np.linalg.norm(r["corners"]-gt, axis=1)))
    ref_rs = cv2.resize(refg, (r["gray"].shape[1], r["gray"].shape[0]))
    s_bin = ssim(ref_rs, r["binary"]);
    # baseline: raw photo, grayscale, OCR
    base_ocr = ocr_acc(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
    warp_ocr = ocr_acc(cv2.cvtColor(r["warped"], cv2.COLOR_BGR2GRAY))
    full_ocr = ocr_acc(r["binary"]); gray_ocr = ocr_acc(r["gray"])
    rows.append(dict(id=n, found=bool(r["found"]), err=err, ssim=float(s_bin), ocr_raw=base_ocr,
                     ocr_warp=warp_ocr, ocr_full=full_ocr, ocr_gray=gray_ocr, ms=dt,
                     sharp_warp=sharp(cv2.cvtColor(r["warped"], cv2.COLOR_BGR2GRAY)), sharp_out=sharp(r["gray"])))
    cv2.imwrite(f"results/{n}_warped.png", r["warped"]); cv2.imwrite(f"results/{n}_gray.png", r["gray"])
    cv2.imwrite(f"results/{n}_binary.png", r["binary"]); cv2.imwrite(f"results/{n}_edges.png", r["edges"])
    vis = img.copy(); cv2.polylines(vis, [r["corners"].astype(np.int32)], True, (0,255,0), 6)
    for q in r["corners"]: cv2.circle(vis, tuple(int(v) for v in q), 14, (0,0,255), -1)
    cv2.imwrite(f"results/{n}_detect.jpg", vis)
    print(n, rows[-1])
json.dump(rows, open("results/metrics.json", "w"), indent=1)
m = lambda k: np.mean([r[k] for r in rows])
print("GRAY", m("ocr_gray")); print("MEAN err %.1f ssim %.3f raw %.1f warp %.1f full %.1f ms %.0f success %d/%d" % (m("err"), m("ssim"), m("ocr_raw"), m("ocr_warp"), m("ocr_full"), m("ms"), sum(r["err"]<25 for r in rows), len(rows)))
