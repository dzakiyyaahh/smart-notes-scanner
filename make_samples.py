"""Generate synthetic note photos with known ground truth (for controlled testing)."""
import cv2, numpy as np, random, os
from PIL import Image, ImageDraw, ImageFont
random.seed(7); np.random.seed(7)
# Font disertakan di repo (fonts/) supaya sampel identik di macOS, Windows, dan Linux.
FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "DejaVuSans.ttf")
TEXT = ["Sistem Informasi - Teknologi Berkembang","Computer Vision adalah bidang yang","memungkinkan komputer memahami citra.",
"1. Grayscale dan Gaussian Blur","2. Deteksi tepi (Canny)","3. Contour dan approxPolyDP","4. Transformasi perspektif 4 titik",
"5. Adaptive thresholding","Rumus: M = getPerspectiveTransform(src, dst)","Output = warpPerspective(img, M, (W, H))",
"Catatan: pencahayaan tidak merata akan","mempengaruhi hasil binarisasi global.","Solusi: koreksi iluminasi + CLAHE.",
"Evaluasi: akurasi OCR, SSIM, error sudut.","Tugas: baca bab 3 dan siapkan ringkasan."]
def page(w=850, h=1100):
    im = Image.new("RGB", (w, h), (250, 249, 244)); d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT_PATH, 30)
    for y in range(110, h, 52): d.line([(40, y+10), (w-40, y+10)], fill=(200, 215, 235), width=1)
    for i, t in enumerate(TEXT): d.text((60, 70+i*52), t, fill=(25, 25, 60), font=f)
    return np.array(im)[:, :, ::-1].copy()
def desk(W, H):
    base = np.full((H, W, 3), (60, 90, 120), np.uint8)
    noise = np.random.randint(-12, 12, (H, W, 1)).astype(np.int16)
    return np.clip(base.astype(np.int16)+noise, 0, 255).astype(np.uint8)
def make(idx, tilt, light, blur, noise):
    pg = page(); h, w = pg.shape[:2]; W, H = 1600, 1200
    src = np.float32([[0,0],[w,0],[w,h],[0,h]])
    cx, cy, s = W/2, H/2, 0.80
    base = np.float32([[cx-w*s*.43, cy-h*s*.43],[cx+w*s*.43, cy-h*s*.43],[cx+w*s*.43, cy+h*s*.43],[cx-w*s*.43, cy+h*s*.43]])
    base = np.float32([[cx-420,cy-540],[cx+420,cy-540],[cx+420,cy+540],[cx-420,cy+540]]) * 1.0
    base[:, 1] = np.clip(base[:, 1], 40, H-40)
    j = np.float32([[random.uniform(-tilt, tilt), random.uniform(-tilt, tilt)] for _ in range(4)]) * 1.0
    dst = base * np.float32([1, 0.92]) + np.float32([0, H*0.04]) + j * np.float32([1.6, 0.6])
    dst += np.float32([[ tilt*0.9, 0],[-tilt*0.9, 0],[ -tilt*0.2, 0],[ tilt*0.2, 0]])
    M = cv2.getPerspectiveTransform(src, dst.astype(np.float32))
    bg = desk(W, H)
    mask = cv2.warpPerspective(np.full((h, w), 255, np.uint8), M, (W, H))
    wp = cv2.warpPerspective(pg, M, (W, H), flags=cv2.INTER_LINEAR)
    out = np.where(mask[..., None] > 0, wp, bg)
    if light:  # uneven illumination / shadow gradient
        gx = np.linspace(1.0, light, W)[None, :, None]; gy = np.linspace(1.0, 0.85, H)[:, None, None]
        out = np.clip(out * gx * gy, 0, 255).astype(np.uint8)
    if blur: out = cv2.GaussianBlur(out, (0, 0), blur)
    if noise: out = np.clip(out.astype(np.int16)+np.random.normal(0, noise, out.shape), 0, 255).astype(np.uint8)
    cv2.imwrite(f"samples/note_{idx:02d}.jpg", out, [cv2.IMWRITE_JPEG_QUALITY, 90])
    np.save(f"samples/note_{idx:02d}_gt.npy", dst.astype(np.float32))
    cv2.imwrite("samples/reference.png", pg)
configs = [ # (tilt, light-right-factor, blur, noise)
 (20,1.0,0,0),(60,1.0,0,0),(110,1.0,0,3),(40,0.55,0,3),(80,0.45,0.8,4),(130,0.6,1.2,5),
 (30,0.7,1.8,6),(100,0.35,0.6,3),(60,0.5,2.2,8),(140,0.5,1.0,6)]
if __name__ == "__main__":
    os.makedirs("samples", exist_ok=True)
    for i, c in enumerate(configs, 1): make(i, *c)
    print("ok")

