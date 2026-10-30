# pixelprobe-ep04

PixelProbe EP4 示範程式碼 · Companion code for PixelProbe EP4
**全網瘋傳的颶風女孩照片，分享前先看這 4 個疑點**
影片連結 Video：即將公開 / coming soon

---

## 中文

本 repo 收錄影片中使用的 Python / OpenCV 分析：

| 腳本 | 功能 |
|---|---|
| `make_test_image.py` | 產生一張合成測試圖（樹林、水面、收斂的船舷），無版權，可直接測試其他腳本 |
| `forensics_basic.py` | 線索一中繼資料（EXIF / XMP / C2PA 位元組掃描）＋ ELA、雜訊殘差、FFT 週期峰值；可指定區域比較、可加真實對照圖 |
| `perspective_vp.py` | 線索三透視：抓出左右船舷 → `cv2.fitLine` 擬合 → 求消失點，與遠方水岸線比較 |

### 安裝與執行
```bash
pip install -r requirements.txt
python make_test_image.py                 # 產生 images/test.jpg
python forensics_basic.py images/test.jpg --region face=260,200,340,280 --region water=20,200,140,320
python perspective_vp.py images/test.jpg
```
分析自己的圖：把圖片放進 `images/`（例如 `images/your.jpg`），把上面路徑換掉即可；可用 `--ref images/real.jpg` 加入一張真實照片做 FFT 對照。輸出圖與 JSON 會寫到 `out/`。

### 聲明
- 本 repo 為**教育性影像鑑識示範**。**沒有任何單一方法能證明圖像是 AI 生成**；影片中 ELA、雜訊、FFT 在這張圖上都無法判斷，結論需結合查核報導與多項線索。
- **不內含瘋傳原圖**或任何第三方圖片，請自行放入圖片並遵守其授權。
- 座標與閾值（`--region`、`--bright`、`--dark`）需依你的圖片調整。

聯絡：pixelprobe.studio2026@gmail.com

---

## English

Python / OpenCV analysis used in the video.

| Script | What it does |
|---|---|
| `make_test_image.py` | Generates a synthetic, copyright-free test image (treeline, water, converging boat rails) |
| `forensics_basic.py` | Clue 1 metadata (EXIF / XMP / C2PA byte scan) plus ELA, noise residual and FFT periodic-peak score; optional regions and real reference image |
| `perspective_vp.py` | Clue 3 perspective: trace both boat rails, fit with `cv2.fitLine`, intersect to get the vanishing point and compare with the far shoreline |

### Install & run
```bash
pip install -r requirements.txt
python make_test_image.py
python forensics_basic.py images/test.jpg --region face=260,200,340,280 --region water=20,200,140,320
python perspective_vp.py images/test.jpg
```
To analyse your own image, put it in `images/` and pass its path; add `--ref images/real.jpg` for an FFT comparison. Outputs go to `out/`.

### Disclaimer
- This is an **educational image-forensics demo**. **No single method can prove an image is AI-generated.**
- The viral image and any third-party images are **not included**; supply your own images and respect their licences.
- Regions and thresholds must be tuned for your image.

Contact: pixelprobe.studio2026@gmail.com

License: MIT
