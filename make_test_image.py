"""產生合成測試圖（非真實照片、無版權）/ Generate a synthetic test image (not a real photo, no copyright).
畫面：上方深色樹林、亮色水面、前景深色船身左右兩舷向內收斂。
Scene: dark treeline on top, bright water, dark boat hull whose two rails converge.
用法 Usage: python make_test_image.py [out_path]   (預設 default: images/test.jpg)
"""
import sys, os, numpy as np, cv2

def make(w=640, h=632, seed=0):
    rng = np.random.default_rng(seed)
    img = np.zeros((h, w, 3), np.float32)
    shore = 135
    img[:shore] = (40, 70, 45)                      # 樹林 trees (BGR)
    img[shore:] = (175, 185, 190)                   # 亮水面 bright water
    # 船身：兩條收斂直線以下為深色 / hull: dark below two converging rails
    vp = (w / 2, shore + 150)                       # 刻意把消失點放在水岸線下方 VP deliberately below shoreline
    yy, xx = np.mgrid[:h, :w]
    for x_edge, y_edge in ((0, h * 0.62), (w, h * 0.70)):
        slope = (vp[1] - y_edge) / (vp[0] - x_edge)
        rail_y = y_edge + slope * (xx - x_edge)
        side = (xx < w * 0.25) if x_edge == 0 else (xx > w * 0.75)
        img[side & (yy > rail_y)] = (40, 90, 50)    # 綠色深色船身 dark green hull
    # 中央人物塊（簡化）/ simple central "subject" blob
    cv2.ellipse(img, (w // 2, 260), (70, 90), 0, 0, 360, (120, 150, 200), -1)
    img += rng.normal(0, 4, img.shape)              # 感測器雜訊 sensor-like noise
    img[200:280, 260:340] = cv2.GaussianBlur(img[200:280, 260:340], (0, 0), 3)  # 局部平滑區（模擬過度平滑皮膚）smoothed patch
    return np.clip(img, 0, 255).astype(np.uint8)

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join("images", "test.jpg")
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    cv2.imwrite(out, make(), [cv2.IMWRITE_JPEG_QUALITY, 85]); print("寫入 wrote", out)
