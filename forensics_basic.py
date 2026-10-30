"""EP4 基本影像鑑識：中繼資料、ELA、雜訊殘差、FFT 週期峰值
EP4 basic image forensics: metadata, ELA, noise residual, FFT periodic peaks.
⚠ 教育示範，任何單一指標都不能證明圖片是 AI 生成。Educational demo; no single metric proves an image is AI-generated.

用法 Usage:
  python forensics_basic.py images/your.jpg [--ref images/real_reference.jpg] [--out out]
       [--region face=215,120,300,230 --region water=20,200,140,320 ...]
"""
import argparse, os, json, numpy as np, cv2

def meta(path):
    """EXIF / XMP / C2PA 位元組掃描 / byte scan for EXIF, XMP, C2PA (JUMBF) markers"""
    raw = open(path, "rb").read()
    return {"exif": b"Exif\x00\x00" in raw, "xmp": b"http://ns.adobe.com/xap" in raw,
            "c2pa": any(m in raw for m in (b"c2pa", b"jumb")), "bytes": len(raw)}

def ela(bgr, q=90):
    """錯誤等級分析：重存 JPEG 後的差異 / Error Level Analysis: diff after re-saving as JPEG"""
    re = cv2.imdecode(cv2.imencode(".jpg", bgr, [cv2.IMWRITE_JPEG_QUALITY, q])[1], 1)
    return np.abs(bgr.astype(np.float32) - re.astype(np.float32)).mean(2)

def noise_res(gray):
    """雜訊殘差 = 原圖 − 3×3 中值濾波 / noise residual = image − 3×3 median"""
    return np.abs(gray.astype(np.float32) - cv2.medianBlur(gray, 3).astype(np.float32))

def fft_peak(gray):
    """高通殘差 FFT 週期峰值分數（上採樣常留格狀峰）/ periodic-peak score of high-pass FFT"""
    g = gray.astype(np.float32); res = g - cv2.GaussianBlur(g, (0, 0), 2); n = min(g.shape); res = res[:n, :n]
    spec = np.log1p(np.abs(np.fft.fftshift(np.fft.fft2(res * np.outer(np.hanning(n), np.hanning(n))))))
    yy, xx = np.mgrid[:n, :n] - n // 2; r = np.hypot(yy, xx)
    ring = spec[(r > n * 0.15) & (np.abs(yy) > 3) & (np.abs(xx) > 3)]
    v = (spec - np.percentile(spec, 1)) / (np.percentile(spec, 99.9) - np.percentile(spec, 1) + 1e-9)
    return float(np.percentile(ring, 99.95) / np.median(ring)), cv2.applyColorMap(np.clip(v * 255, 0, 255).astype(np.uint8), cv2.COLORMAP_INFERNO)

def region_means(arr, regions):
    return {k: round(float(arr[y0:y1, x0:x1].mean()), 3) for k, (x0, y0, x1, y1) in regions.items()}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("image"); ap.add_argument("--ref"); ap.add_argument("--out", default="out")
    ap.add_argument("--region", action="append", default=[], help="name=x0,y0,x1,y1")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    img = cv2.imread(a.image)
    if img is None: raise SystemExit(f"讀不到圖片 cannot read image: {a.image}")
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    regions = {}
    for s in a.region:
        k, v = s.split("="); regions[k] = tuple(int(t) for t in v.split(","))
    R = {"meta": meta(a.image)}
    print(f"[1 中繼資料 metadata] EXIF={R['meta']['exif']} XMP={R['meta']['xmp']} C2PA={R['meta']['c2pa']} "
          "（缺少不代表造假：社群轉存會清除 missing ≠ fake, re-uploads strip it）")
    e = ela(img); R["ela"] = {"whole": round(float(e.mean()), 3), **region_means(e, regions)}
    print("[2 ELA q90] 平均 mean:", R["ela"])
    cv2.imwrite(f"{a.out}/ela.png", cv2.applyColorMap(np.clip(e * 12, 0, 255).astype(np.uint8), cv2.COLORMAP_INFERNO))
    n = noise_res(g); R["noise"] = {"whole": round(float(n.mean()), 3), **region_means(n, regions)}
    print("[3 雜訊殘差 noise residual] 平均 mean:", R["noise"])
    cv2.imwrite(f"{a.out}/noise.png", cv2.applyColorMap(np.clip(n * 14, 0, 255).astype(np.uint8), cv2.COLORMAP_VIRIDIS))
    s, vis = fft_peak(g); R["fft"] = {"image": round(s, 3)}; cv2.imwrite(f"{a.out}/fft.png", vis)
    if a.ref:
        ref = cv2.imread(a.ref)
        if ref is None: raise SystemExit(f"讀不到對照圖 cannot read ref: {a.ref}")
        # 對照圖縮到同高並以 q75 重壓，模擬社群轉存 / resize + recompress q75 to mimic social copies
        ref = cv2.resize(ref, (int(ref.shape[1] * img.shape[0] / ref.shape[0]), img.shape[0]), interpolation=cv2.INTER_AREA)
        ref = cv2.imdecode(cv2.imencode(".jpg", ref, [cv2.IMWRITE_JPEG_QUALITY, 75])[1], 1)
        sr, vr = fft_peak(cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY)); R["fft"]["reference"] = round(sr, 3)
        cv2.imwrite(f"{a.out}/fft_ref.png", vr); R["meta_ref"] = meta(a.ref)
    print("[4 FFT 峰值分數 peak score]", R["fft"])
    json.dump(R, open(f"{a.out}/results_basic.json", "w"), indent=1, ensure_ascii=False); print("完成 Done →", a.out)

if __name__ == "__main__": main()
