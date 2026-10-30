"""EP4 透視檢查：船舷兩線的消失點 vs 遠方水岸線
EP4 perspective check: vanishing point of the two boat rails vs the far shoreline.
原理：水平的平行線應消失在地平線上；若交點明顯低於水岸線，透視可能不一致（僅為線索，非證據）。
Idea: level parallel lines vanish on the horizon; a VP far below the shoreline hints at inconsistent perspective (a clue, not proof).
適用：深色船身在亮色水面前方的畫面。Works for a dark hull in front of bright water.

用法 Usage: python perspective_vp.py images/your.jpg [--out out] [--bright 150] [--dark 110]
"""
import argparse, os, json, numpy as np, cv2

def boat_lines(bgr, bright=150, dark=110):
    """每欄由上往下找「亮水 → 暗船身」轉折，左右各擬合直線，求交點
    per column find first bright-water→dark-hull step, fit left/right lines, intersect"""
    v = cv2.GaussianBlur(cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)[..., 2], (5, 5), 0).astype(np.int32)
    h, w = v.shape; pts = {"L": [], "R": []}
    for x in range(w):
        if not (x < w * 0.22 or x > w * 0.80): continue
        col = v[h // 3:, x]
        for y in range(4, len(col) - 8):
            if col[y - 4] > bright and col[y + 6] < dark and col[y + 2:y + 8].max() < dark + 10:
                pts["L" if x < w / 2 else "R"].append((x, h // 3 + y)); break
    fit = {}
    for k, p in pts.items():
        if len(p) < 10: raise SystemExit(f"{k} 側邊緣點太少 too few edge points ({len(p)}); 調整 --bright/--dark")
        p = np.array(p, np.float32); vx, vy, x0, y0 = cv2.fitLine(p, cv2.DIST_HUBER, 0, .01, .01).ravel()
        resid = np.abs((p[:, 0] - x0) * vy - (p[:, 1] - y0) * vx)
        fit[k] = {"vx": float(vx), "vy": float(vy), "x0": float(x0), "y0": float(y0), "n": len(p),
                  "rms": float(np.sqrt((resid ** 2).mean())), "x_range": [int(p[:, 0].min()), int(p[:, 0].max())]}
    a, b = fit["L"], fit["R"]
    s, _ = np.linalg.solve(np.array([[a["vx"], -b["vx"]], [a["vy"], -b["vy"]]]), [b["x0"] - a["x0"], b["y0"] - a["y0"]])
    return fit, (a["x0"] + s * a["vx"], a["y0"] + s * a["vy"])

def water_line(bgr):
    """遠方水岸線：左側區域亮度沿 y 的最大正梯度（暗樹 → 亮水）/ shoreline: strongest dark-tree→bright-water step along y"""
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(np.float32); h, w = g.shape
    prof = np.median(g[: h // 2, int(w * .02): int(w * .30)], axis=1)
    d = np.convolve(np.diff(prof), np.ones(5) / 5, "same"); return int(np.argmax(d) + 1)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("image"); ap.add_argument("--out", default="out")
    ap.add_argument("--bright", type=int, default=150); ap.add_argument("--dark", type=int, default=110)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    img = cv2.imread(a.image)
    if img is None: raise SystemExit(f"讀不到圖片 cannot read image: {a.image}")
    fit, vp = boat_lines(img, a.bright, a.dark); shore = water_line(img)
    for k, name in (("L", "左舷 left"), ("R", "右舷 right")):
        f = fit[k]; print(f"[{name}] slope={f['vy'] / f['vx']:+.3f} n={f['n']} rms={f['rms']:.2f}px")
    print(f"消失點 vanishing point=({vp[0]:.0f}, {vp[1]:.0f}) | 水岸線 shoreline y={shore} → 差 diff {vp[1] - shore:+.0f}px（正=在水岸下方 positive = below shoreline）")
    vis = img.copy()
    for f in fit.values():
        cv2.line(vis, (int(f["x0"] - 2000 * f["vx"]), int(f["y0"] - 2000 * f["vy"])),
                 (int(f["x0"] + 2000 * f["vx"]), int(f["y0"] + 2000 * f["vy"])), (255, 240, 0), 3)
    cv2.line(vis, (0, shore), (img.shape[1], shore), (0, 230, 255), 2); cv2.circle(vis, (int(vp[0]), int(vp[1])), 12, (60, 50, 255), -1)
    cv2.imwrite(f"{a.out}/perspective.png", vis)
    json.dump({"left": fit["L"], "right": fit["R"], "vanishing_point": [round(vp[0], 1), round(vp[1], 1)], "shoreline_y": shore,
               "vp_below_shore_px": round(vp[1] - shore, 1), "image_h": img.shape[0]},
              open(f"{a.out}/results_perspective.json", "w"), indent=1); print("完成 Done →", a.out)

if __name__ == "__main__": main()
