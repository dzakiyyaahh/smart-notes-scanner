"""Smart Notes Scanner - core pipeline (OpenCV)."""
import cv2
import numpy as np

def order_points(pts):
    pts = np.array(pts, dtype="float32")
    s, d = pts.sum(axis=1), np.diff(pts, axis=1).ravel()
    return np.array([pts[np.argmin(s)], pts[np.argmin(d)],
                     pts[np.argmax(s)], pts[np.argmax(d)]], dtype="float32")  # TL,TR,BR,BL

def detect_paper_region(small):
    """[Tambahan] Fallback untuk foto nyata yang tepi kertasnya tidak tertutup
    (mis. sisi spiral buku, lipatan kain di latar). Kertas lebih terang dari latar:
    Otsu pada kanal L (LAB), lalu area terang dipotong di sepanjang tepi Canny agar
    kertas terpisah dari benda terang lain, ambil komponen terbesar, convex hull -> 4 titik."""
    gray = cv2.GaussianBlur(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY), (7, 7), 0)
    L = cv2.GaussianBlur(cv2.cvtColor(small, cv2.COLOR_BGR2LAB)[:, :, 0], (7, 7), 0)
    _, m = cv2.threshold(L, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    m[cv2.dilate(cv2.Canny(gray, 40, 120), np.ones((3, 3), np.uint8)) > 0] = 0
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    if n < 2:
        return None
    m = np.uint8(lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
    c = max(cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0], key=cv2.contourArea)
    if cv2.contourArea(c) < 0.20 * small.shape[0] * small.shape[1]:
        return None
    hull = cv2.convexHull(c)
    for eps in (0.02, 0.03, 0.04, 0.05, 0.06, 0.08):
        ap = cv2.approxPolyDP(hull, eps * cv2.arcLength(hull, True), True)
        if len(ap) == 4:
            return ap.reshape(4, 2).astype("float32")
    return cv2.boxPoints(cv2.minAreaRect(hull))

def detect_document(img, work_h=700):
    """Return 4 corners (in original image coordinates) and a debug edge map."""
    scale = work_h / img.shape[0]
    small = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    gray = cv2.GaussianBlur(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY), (7, 7), 0)
    edges = cv2.Canny(gray, 40, 120)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8), iterations=2)
    cnts, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:8]
    min_area = 0.20 * small.shape[0] * small.shape[1]
    for c in cnts:
        approx = cv2.approxPolyDP(c, 0.02 * cv2.arcLength(c, True), True)
        if len(approx) == 4 and cv2.contourArea(approx) > min_area and cv2.isContourConvex(approx):
            return order_points(approx.reshape(4, 2) / scale), edges, True
    if cnts and cv2.contourArea(cnts[0]) > min_area:           # fallback: min-area rectangle
        box = cv2.boxPoints(cv2.minAreaRect(cnts[0]))
        return order_points(box / scale), edges, True
    q = detect_paper_region(small)                              # [tambahan] fallback 2: segmentasi kertas terang
    if q is not None:
        return order_points(q / scale), edges, True
    h, w = img.shape[:2]                                        # last resort: whole image
    return order_points([[0, 0], [w, 0], [w, h], [0, h]]), edges, False

def warp(img, corners):
    tl, tr, br, bl = corners
    W = int(max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl)))
    H = int(max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl)))
    dst = np.array([[0, 0], [W - 1, 0], [W - 1, H - 1], [0, H - 1]], dtype="float32")
    M = cv2.getPerspectiveTransform(corners, dst)
    return cv2.warpPerspective(img, M, (W, H), flags=cv2.INTER_CUBIC)

def enhance(warped):
    """Illumination correction -> CLAHE+unsharp (gray) and Otsu on flattened image (binary)."""
    gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    k = max(31, (min(gray.shape) // 8) | 1)
    bg = cv2.medianBlur(cv2.dilate(gray, np.ones((7, 7), np.uint8)), k)   # estimate paper/shadow
    flat = cv2.divide(gray, bg, scale=255)                                 # remove shadow
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(flat)
    sharp = cv2.addWeighted(clahe, 1.5, cv2.GaussianBlur(clahe, (0, 0), 3), -0.5, 0)
    smooth = cv2.GaussianBlur(flat, (3, 3), 0)
    _, binary = cv2.threshold(smooth, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return sharp, binary

def scan(img):
    corners, edges, found = detect_document(img)
    warped = warp(img, corners)
    gray_out, bin_out = enhance(warped)
    return dict(corners=corners, edges=edges, found=found, warped=warped, gray=gray_out, binary=bin_out)
