# 照妖鏡實驗室 PixelProbe — EP04：颶風海倫「哭泣女孩與小狗」照片是真的嗎？
# EP04: Is the Hurricane Helene "crying girl & puppy" photo real?

> ⚠️ 劇透提醒 Spoiler alert：本頁含影片結論，建議先看完影片。This page contains the video's verdict — watch the video first.
> 🎬 影片 Video: PixelProbe EP04 · 程式碼 Code: https://github.com/pixelprobe-lab/pixelprobe-ep04

2024 年 10 月颶風海倫過後，一張女孩抱著小狗坐在救難船上的照片在 X、Facebook、Threads 瘋傳。Snopes、PolitiFact、Full Fact 都判定它不是真照片（Full Fact：AI 生成）。這個腳本重現 EP04 影片裡的鑑識步驟與數字。
After Hurricane Helene (Oct 2024), an image of a crying girl holding a puppy in a rescue boat went viral on X, Facebook and Threads. Snopes, PolitiFact and Full Fact rated it not authentic (Full Fact: AI-generated). This script reproduces the forensic steps and numbers shown in the EP04 video.

## 準備圖片 Get the images（不附在 repo 內 · not included in this repo）
放到 `src/` · put them in `src/`:

| 檔名 File | 來源 Source |
|---|---|
| `girl_a.jpg` | Snopes 事實查核內的副本 copy in the Snopes fact-check: `https://mediaproxy.snopes.com/width/1200/https://media.snopes.com/2024/10/girl_puppy.jpg` (1200×675) |
| `girl_b.png` | 同文章「不同小狗」截圖 "different puppy" screenshot: `https://mediaproxy.snopes.com/width/600?url=https://media.snopes.com/2024/10/girl_with_dog.png` (600×554) |
| `real.jpg` | 真實對照 real reference: [French Broad Flooding - Hurricane Helene.jpg](https://commons.wikimedia.org/wiki/File:French_Broad_Flooding_-_Hurricane_Helene.jpg) — Mcmorrl, CC0（1920px 縮圖 thumbnail） |

## 執行 Run
```bash
pip install -r requirements.txt
python forensics_helene.py src out
```

## 預期結果 Expected results（EP04 影片中的數字 numbers shown in the EP04 video）
已於 2026-10-26 重新執行驗證，與影片數字一致。Re-run and verified on 2026-10-26: output matches the video.
| 步驟 Step | 結果 Result | 解讀 Reading |
|---|---|---|
| 1 中繼資料 Metadata | 三張都沒有 EXIF / XMP / C2PA · none in all three | 轉存會清掉，**不能當證據** · stripped on re-upload, **not proof** |
| 2 ELA (q90) | 臉 face 1.78、小狗 puppy 2.20、救生衣 jacket 1.50、水 water 0.71 | 跟著紋理走、沒有貼上熱點 → **判斷不出來** · follows texture, no paste hotspot → **inconclusive** |
| 3 雜訊殘差 Noise | 臉 skin 2.282 > 水 water 0.236 | 沒顯示「皮膚過度平滑」→ **判斷不出來** · no measurable "too smooth skin" → **inconclusive** |
| 4 FFT 峰值 peak | 假圖 fake 1.456 vs 真圖 real 1.308 | 沒有明顯週期峰 → **判斷不出來** · no clear periodic peak → **inconclusive** |
| 5 透視 Perspective | 左舷 left −0.368、右舷 right +0.625；消失點 y=287，水岸線 y=135 → 低 152 px | 水平平行線應消失在地平線（不會低於水岸）→ **可疑** · level parallel lines should vanish on the horizon (not below the shoreline) → **suspicious** |
| 6 版本比對 Versions | 同女孩、不同小狗 · same girl, different puppy | 真照片不會這樣 · real photos don't do this |

## 限制 Limits
- 社群副本已被縮放、重壓縮，原始檔不存在；數字只代表這些副本。 Social copies are resized/recompressed; no original exists — numbers describe these copies only.
- 透視法：船身前傾、船舷彎曲、鏡頭變形、裁切都可能影響。 Perspective: boat pitch, curved rails, lens distortion or cropping can skew it.
- 雜訊比較的真實對照是湍急河流，場景不同，所以只用來比 FFT。 The CC0 reference is a turbulent river, so it is used only for the FFT comparison.
- 單一方法都不是鐵證，要綜合來源查證。 No single test is proof; combine with source verification.

## 參考 References
- Snopes: https://www.snopes.com/fact-check/little-girl-with-puppy-hurricane-helene/
- PolitiFact (2024-10-11): https://politifact.com/factchecks/2024/oct/11/viral-image/recent-hurricanes-devastated-us-communities-but-th/
- Full Fact: https://fullfact.org/news/child-image-puppy-flooding-america-ai-generated/
- The Dispatch (Hive 99.5%, Hany Farid): https://thedispatch.com/article/viral-images-of-girl-and-puppy-in-hurricane-recovery-are-ai-generated/

## 授權 License
程式碼 MIT（見 LICENSE）；圖片版權屬原作者，不在本授權內。 Code is MIT (see LICENSE); images belong to their owners and are not covered.
