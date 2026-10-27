"""EP04：颶風海倫「哭泣女孩與小狗」照片鑑識 / EP04: forensics on the Hurricane Helene "crying girl & puppy" image
圖片來源 Image sources（請自行下載到 src/ · download into src/ yourself）：
  girl_a.jpg  Snopes 事實查核文章中的轉存版本，取中央清晰區 / copy embedded in Snopes fact-check (centre sharp area)
              https://www.snopes.com/fact-check/little-girl-with-puppy-hurricane-helene/
              → media.snopes.com/2024/10/girl_puppy.jpg（1200×675，腳本自動裁切 script auto-crops）
  girl_b.png  同文章「不同小狗」版本截圖 / "different puppy" version screenshot from the same article
              → media.snopes.com/2024/10/girl_with_dog.png
  real.jpg    真實對照 real reference: Wikimedia Commons "French Broad Flooding - Hurricane Helene.jpg"（CC0, Mcmorrl, 2024-09-27）
說明 Note：社群轉存版已被縮放、重壓縮，原始檔不存在；結果只代表這些副本。
           Social copies are resized/recompressed; no original file exists. Results describe these copies only.
用法 Usage: python forensics_helene.py [src_dir] [out_dir]
"""
import sys, os, json, numpy as np, cv2
SRC = sys.argv[1] if len(sys.argv) > 1 else "src"; OUT = sys.argv[2] if len(sys.argv) > 2 else "out"
os.makedirs(OUT, exist_ok=True)
A_CROP = (285, 21, 916, 653)   # Snopes 版中央清晰區（兩側為模糊填充）/ sharp centre (sides are blurred padding)

def load_a():
    im = cv2.imread(f"{SRC}/girl_a.jpg"); x0, y0, x1, y1 = A_CROP; return im[y0:y1, x0:x1].copy()

def meta(path):
    """EXIF / XMP / C2PA 位元組掃描 / byte scan for EXIF, XMP, C2PA (JUMBF) markers"""
    raw = open(path, "rb").read()
    return {"exif": b"Exif\x00\x00" in raw, "xmp": b"http://ns.adobe.com/xap" in raw,
            "c2pa": any(m in raw for m in (b"c2pa", b"jumb")), "bytes": len(raw)}

def ela(bgr, q=90):
    """錯誤等級分析 ELA：重存 JPEG 後的差異 / Error Level Analysis: diff after re-saving as JPEG"""
    ok, enc = cv2.imencode(".jpg", bgr, [cv2.IMWRITE_JPEG_QUALITY, q]); re = cv2.imdecode(enc, 1)
    return np.abs(bgr.astype(np.float32) - re.astype(np.float32)).mean(2)

def noise_res(gray):
    """雜訊殘差 = 原圖 − 3×3 中值濾波 / noise residual = image − 3×3 median"""
    return np.abs(gray.astype(np.float32) - cv2.medianBlur(gray, 3).astype(np.float32))

def fft_peak(gray):
    """高通殘差 FFT 週期峰值分數（AI 上採樣常留格狀峰）/ periodic-peak score of high-pass FFT"""
    g = gray.astype(np.float32); res = g - cv2.GaussianBlur(g, (0, 0), 2); n = min(g.shape); res = res[:n, :n]
    spec = np.log1p(np.abs(np.fft.fftshift(np.fft.fft2(res * np.outer(np.hanning(n), np.hanning(n))))))
    yy, xx = np.mgrid[:n, :n] - n // 2; r = np.hypot(yy, xx)
    ring = spec[(r > n * 0.15) & (np.abs(yy) > 3) & (np.abs(xx) > 3)]
    v = (spec - np.percentile(spec, 1)) / (np.percentile(spec, 99.9) - np.percentile(spec, 1))
    return float(np.percentile(ring, 99.95) / np.median(ring)), cv2.applyColorMap(np.clip(v * 255, 0, 255).astype(np.uint8), cv2.COLORMAP_INFERNO)

def boat_lines(bgr):
    """船舷透視：綠色船身遮罩 → 每欄最上緣 → 左右各擬合直線 → 求交點（消失點）
    Boat-rail perspective: green hull mask → top edge per column → fit left/right lines → intersection (vanishing point)"""
    # 船身在亮色洪水前方是深色：每欄由上往下找「亮 → 暗」的第一個轉折 / dark hull in front of bright water: first bright→dark step per column
    v = cv2.GaussianBlur(cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)[..., 2], (5, 5), 0).astype(np.int32)
    h, w = v.shape; pts = {"L": [], "R": []}; m = (v < 110).astype(np.uint8)
    for x in range(w):
        if not (x < w * 0.22 or x > w * 0.80): continue
        col = v[h // 3:, x]
        for y in range(4, len(col) - 8):
            if col[y - 4] > 150 and col[y + 6] < 110 and col[y + 2:y + 8].max() < 120:
                pts["L" if x < w / 2 else "R"].append((x, h // 3 + y)); break
    fit = {}
    for k, p in pts.items():
        p = np.array(p, np.float32); vx, vy, x0, y0 = cv2.fitLine(p, cv2.DIST_HUBER, 0, .01, .01).ravel()
        resid = np.abs((p[:, 0] - x0) * vy - (p[:, 1] - y0) * vx)
        fit[k] = {"vx": float(vx), "vy": float(vy), "x0": float(x0), "y0": float(y0), "n": len(p), "rms": float(np.sqrt((resid ** 2).mean())),
                  "x_range": [int(p[:, 0].min()), int(p[:, 0].max())]}
    a, b = fit["L"], fit["R"]   # 解 p_a + s*d_a = p_b + t*d_b / solve the intersection
    M = np.array([[a["vx"], -b["vx"]], [a["vy"], -b["vy"]]]); s, t = np.linalg.solve(M, [b["x0"] - a["x0"], b["y0"] - a["y0"]])
    vp = (a["x0"] + s * a["vx"], a["y0"] + s * a["vy"])
    return fit, vp, m

def water_line(bgr):
    """遠方水岸線：亮度沿 y 的最大負梯度（樹 → 水）/ far shoreline: strongest tree→water brightness step along y"""
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(np.float32); h, w = g.shape
    prof = np.median(g[: h // 2, int(w * .02): int(w * .30)], axis=1)   # 左側無人物區 left, no people
    d = np.convolve(np.diff(prof), np.ones(5) / 5, "same"); return int(np.argmax(d) + 1)

def save(name, bgr): cv2.imwrite(f"{OUT}/{name}.png", bgr)

R = {}
A = load_a(); cv2.imwrite(f"{OUT}/girl_a_crop.png", A); gA = cv2.cvtColor(A, cv2.COLOR_BGR2GRAY)
B = cv2.imread(f"{SRC}/girl_b.png")[105:517, 10:590];  # 只取照片區（去掉貼文文字）/ photo area only
REF = cv2.imread(f"{SRC}/real.jpg")
# 對照圖縮到同大小並以 q=75 重壓，模擬社群轉存 / resize reference to same size + recompress q75 to mimic social copies
REF = cv2.resize(REF, (int(REF.shape[1] * A.shape[0] / REF.shape[0]), A.shape[0]), interpolation=cv2.INTER_AREA)
REF = cv2.imdecode(cv2.imencode(".jpg", REF, [cv2.IMWRITE_JPEG_QUALITY, 75])[1], 1); gR = cv2.cvtColor(REF, cv2.COLOR_BGR2GRAY)

# 1) 中繼資料 metadata
R["meta"] = {k: meta(f"{SRC}/{f}") for k, f in (("girl_a", "girl_a.jpg"), ("girl_b", "girl_b.png"), ("real", "real.jpg"))}
for k, v in R["meta"].items(): print(f"[1 中繼資料 metadata] {k}: EXIF={v['exif']} XMP={v['xmp']} C2PA={v['c2pa']}")

# 2) ELA：區域平均 / regional means (A 座標 crop coords)
REG = {"face 臉": (215, 120, 300, 230), "jacket 救生衣": (430, 300, 480, 380), "water 水面": (20, 200, 140, 320), "puppy 小狗": (190, 240, 260, 330)}
e = ela(A); R["ela"] = {k: round(float(e[y0:y1, x0:x1].mean()), 2) for k, (x0, y0, x1, y1) in REG.items()}
R["ela"]["whole 全圖"] = round(float(e.mean()), 2); print("[2 ELA q90] 區域平均 regional mean:", R["ela"])
save("ela_a", cv2.applyColorMap(np.clip(e * 12, 0, 255).astype(np.uint8), cv2.COLORMAP_INFERNO))

# 3) 雜訊殘差：臉部皮膚 vs 水面 vs 真實照片水面 / noise residual: skin vs water vs real-photo water
nA = noise_res(gA)
x0, y0, x1, y1 = REG["face 臉"]; skin = float(nA[y0:y1, x0:x1].mean())
x0, y0, x1, y1 = REG["water 水面"]; water = float(nA[y0:y1, x0:x1].mean())
# 註：真實對照是湍急河流，場景不同，不拿來比雜訊 / note: the CC0 reference is a turbulent river — not compared for noise
R["noise"] = {"skin_A": round(skin, 3), "water_A": round(water, 3), "whole_A": round(float(nA.mean()), 3)}
print("[3 雜訊殘差 noise residual] 平均 mean:", R["noise"])
save("noise_a", cv2.applyColorMap(np.clip(nA * 14, 0, 255).astype(np.uint8), cv2.COLORMAP_VIRIDIS))

# 4) FFT 週期峰值 / periodic peaks
sA, vA = fft_peak(gA); sR, vR = fft_peak(gR); R["fft"] = {"girl_a": round(sA, 3), "real_ref": round(sR, 3)}
print("[4 FFT 峰值分數 peak score]", R["fft"]); save("fft_a", vA); save("fft_real", vR)

# 5) 船舷透視 vs 水岸線 / boat-rail vanishing point vs shoreline
fit, vp, mask = boat_lines(A); shore = water_line(A)
R["perspective"] = {"left": fit["L"], "right": fit["R"], "vanishing_point": [round(vp[0], 1), round(vp[1], 1)], "shoreline_y": shore,
                    "vp_below_shore_px": round(vp[1] - shore, 1), "image_h": A.shape[0]}
print(f"[5 透視 perspective] 左舷 L 斜率 slope={fit['L']['vy'] / fit['L']['vx']:+.3f} (n={fit['L']['n']}, rms={fit['L']['rms']:.2f}px) | "
      f"右舷 R 斜率 slope={fit['R']['vy'] / fit['R']['vx']:+.3f} (n={fit['R']['n']}, rms={fit['R']['rms']:.2f}px)")
print(f"    消失點 vanishing point=({vp[0]:.0f}, {vp[1]:.0f}) | 水岸線 shoreline y={shore} → 低於水岸 below shoreline by {vp[1] - shore:.0f}px")
vis = A.copy()
for k in ("L", "R"):
    f_ = fit[k]; p0 = (int(f_["x0"] - 2000 * f_["vx"]), int(f_["y0"] - 2000 * f_["vy"])); p1 = (int(f_["x0"] + 2000 * f_["vx"]), int(f_["y0"] + 2000 * f_["vy"]))
    cv2.line(vis, p0, p1, (255, 240, 0), 3)
cv2.line(vis, (0, shore), (A.shape[1], shore), (0, 230, 255), 2); cv2.circle(vis, (int(vp[0]), int(vp[1])), 12, (60, 50, 255), -1)
save("perspective_a", vis)

# 6) 兩個版本並排（同一女孩、不同小狗）/ two versions side by side (same girl, different puppy)
bh = A.shape[0]; Bs = cv2.resize(B, (int(B.shape[1] * bh / B.shape[0]), bh)); save("versions_ab", np.hstack([A, np.full((bh, 12, 3), 255, np.uint8), Bs]))
# 特寫（人工框選座標）/ close-ups (hand-picked boxes)
CROPS = {"hands": (120, 330, 340, 450), "background_men": (455, 30, 600, 170), "face": (200, 100, 360, 280)}
for k, (x0, y0, x1, y1) in CROPS.items(): cv2.imwrite(f"{OUT}/crop_{k}.png", cv2.resize(A[y0:y1, x0:x1], None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST))
R["regions"] = REG; R["crops"] = CROPS; R["a_crop"] = A_CROP
json.dump(R, open(f"{OUT}/results.json", "w"), indent=1, ensure_ascii=False); print("完成 Done →", OUT)
