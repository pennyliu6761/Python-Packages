# 模組 1-1：Pillow (PIL) — 影像處理基礎

## 📌 為什麼工管系要學影像處理？

在智慧製造中，AOI（自動光學檢測）是品質管制的第一道防線。當相機拍攝到零件後，電腦需要透過**影像前處理**強化瑕疵特徵，才能讓後續的 AI 辨識更準確。Pillow 就是 Python 中最直覺的影像處理工具。
> **學習目標**：理解影像作為「數字矩陣」的本質，掌握工業影像前處理的核心技術。

---

<img width="1814" height="901" alt="image" src="https://github.com/user-attachments/assets/d1a1030d-f033-40e1-bdc6-8cb572676351" />

---

<img width="1826" height="655" alt="image" src="https://github.com/user-attachments/assets/58146b1b-1919-4263-af1f-59772a856a76" />

---

## 🔧 安裝

```bash
pip install Pillow
```

---

## 準備圖片：模擬生成

```python
"""
gen_defect_image.py
====================
模擬 AOI 工業檢測場景的瑕疵零件影像產生器
輸出：defect_part.png（800×600 px）

需求套件：
    pip install pillow numpy
"""

import math
import random
import numpy as np
from PIL import Image, ImageDraw

random.seed(42)
np.random.seed(42)

W, H = 800, 600
cx, cy, R = 390, 295, 195   # 零件中心與半徑

img = Image.new("RGB", (W, H), (10, 12, 16))
draw = ImageDraw.Draw(img)

# ── 背景網格 ──────────────────────────────────────────────────
for x in range(0, W, 40):
    draw.line([(x, 0), (x, H)], fill=(22, 30, 45), width=1)
for y in range(0, H, 40):
    draw.line([(0, y), (W, y)], fill=(22, 30, 45), width=1)

# ── 十字準心線 ─────────────────────────────────────────────────
draw.line([(cx, 0), (cx, H)], fill=(25, 40, 60), width=1)
draw.line([(0, cy), (W, cy)], fill=(25, 40, 60), width=1)

# ── 金屬本體（漸層填充） ──────────────────────────────────────
draw.ellipse([cx-R-3, cy-R-3, cx+R+3, cy+R+3], fill=(40, 44, 52))   # 陰影
for i in range(R, 0, -1):
    t = i / R
    draw.ellipse([cx-i, cy-i, cx+i, cy+i],
                 fill=(int(90+75*t), int(95+72*t), int(100+70*t)))

# ── 金屬表面高光 ───────────────────────────────────────────────
for i in range(55, 0, -1):
    c = min(215 + i, 245)
    draw.ellipse([cx-85-i//3, cy-95-i//3, cx-35+i//3, cy-45+i//3],
                 fill=(c, c, c+3))

# ── 表面噪點紋理 ───────────────────────────────────────────────
arr = np.array(img)
yy, xx = np.ogrid[:H, :W]
inside = (xx - cx)**2 + (yy - cy)**2 <= (R - 2)**2
noise = np.random.randint(-14, 15, (H, W, 3))
arr[inside] = np.clip(arr[inside].astype(int) + noise[inside], 0, 255).astype(np.uint8)
img = Image.fromarray(arr)
draw = ImageDraw.Draw(img)

# ── 同心參考圓 ─────────────────────────────────────────────────
for r2 in [65, 130]:
    draw.ellipse([cx-r2, cy-r2, cx+r2, cy+r2], outline=(110, 118, 128), width=1)

# ── 螺栓孔（四個） ───────────────────────────────────────────
for deg in [45, 135, 225, 315]:
    a = math.radians(deg)
    bx, by = int(cx + 130*math.cos(a)), int(cy + 130*math.sin(a))
    for i in range(7, 0, -1):
        t = i / 7
        draw.ellipse([bx-i, by-i, bx+i, by+i],
                     fill=(int(20+10*t), int(22+10*t), int(25+10*t)))
    draw.ellipse([bx-7, by-7, bx+7, by+7], outline=(80, 85, 95), width=1)

# ── 中心孔 ────────────────────────────────────────────────────
for i in range(45, 0, -1):
    t = i / 45
    draw.ellipse([cx-i, cy-i, cx+i, cy+i],
                 fill=(int(15+8*t), int(17+8*t), int(20+8*t)))
draw.ellipse([cx-45, cy-45, cx+45, cy+45], outline=(55, 60, 70), width=2)
draw.ellipse([cx-12, cy-8, cx+5, cy+5], fill=(28, 30, 34))  # 內反光

# ─────────────────────────────────────────────────────────────
# 瑕疵繪製
# ─────────────────────────────────────────────────────────────

# 1. 裂縫 CRACK（左上）
crack_pts = [(248,195),(255,205),(245,215),(252,226),(244,238),(250,248)]
for i in range(len(crack_pts)-1):
    x1,y1 = crack_pts[i]; x2,y2 = crack_pts[i+1]
    draw.line([(x1,y1),(x2,y2)],   fill=(35, 37, 42), width=3)
    draw.line([(x1+1,y1),(x2+1,y2)], fill=(20, 22, 26), width=2)
    draw.line([(x1-1,y1-1),(x2-1,y2-1)], fill=(155,160,168), width=1)

# 2. 刮痕 SCRATCH（右上）
for dx, dy, col, w in [
    (0, 0, (45,48,55), 4), (1, 1, (25,27,32), 2), (-1,-1, (160,165,172), 1),
    (4, 2, (45,48,55), 2), (5, 2, (140,145,152), 1),
]:
    draw.line([(420+dx, 200+dy), (468+dx, 248+dy)], fill=col, width=w)

# 3. 油汙 OIL STAIN（左下、右下各一）
def draw_oil(ox, oy, rx, ry):
    for i in range(rx, 0, -1):
        t = 1 - i / rx
        ry_i = max(1, int(ry * i / rx))
        draw.ellipse([ox-i, oy-ry_i, ox+i, oy+ry_i],
                     fill=(int(55+10*t), int(48+8*t), int(28+5*t)))

draw_oil(300, 355, 32, 18)
draw_oil(355, 335, 20, 12)

# ─────────────────────────────────────────────────────────────
# 瑕疵標記框（虛線）
# ─────────────────────────────────────────────────────────────
'''
def dashed_rect(d, x1, y1, x2, y2, color, dash=8, gap=4):
    for start, end in [(x1, x2)]:
        x = start
        while x < end:
            d.line([(x, y1), (min(x+dash, end), y1)], fill=color, width=2)
            d.line([(x, y2), (min(x+dash, end), y2)], fill=color, width=2)
            x += dash + gap
    for start, end in [(y1, y2)]:
        y = start
        while y < end:
            d.line([(x1, y), (x1, min(y+dash, end))], fill=color, width=2)
            d.line([(x2, y), (x2, min(y+dash, end))], fill=color, width=2)
            y += dash + gap
    for bx, by in [(x1,y1),(x2,y1),(x1,y2),(x2,y2)]:
        d.rectangle([bx-3, by-3, bx+3, by+3], fill=color)

dashed_rect(draw, 228, 178, 278, 262, (220, 50,  50))   # CRACK
dashed_rect(draw, 408, 185, 488, 262, (245,158,  11))   # SCRATCH
dashed_rect(draw, 260, 328, 400, 382, (167,139, 250))   # OIL STAIN

# ── 標籤文字 ──────────────────────────────────────────────────
try:
    from PIL import ImageFont
    font_label = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 11)
    font_info  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 10)
    font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 10)
except Exception:
    font_label = font_info = font_title = ImageFont.load_default()

draw.text((228, 164), "CRACK",     font=font_label, fill=(220, 50,  50))
draw.text((408, 171), "SCRATCH",   font=font_label, fill=(245,158,  11))
draw.text((260, 314), "OIL STAIN", font=font_label, fill=(167,139, 250))

# ── 右側資訊面板 ───────────────────────────────────────────────

panel_x = 610
draw.line([(panel_x-10, 50), (panel_x-10, 550)], fill=(30, 40, 55), width=1)

info_lines = [
    ("AOI SYSTEM",    (70, 100, 140)),
    ("",              None),
    ("SIZE  φ85 mm",  (100,110,125)),
    ("MAT   SUS304",  (100,110,125)),
    ("LOT   B-2403",  (100,110,125)),
    ("SEQ   #00147",  (100,110,125)),
    ("",              None),
    ("DEFECTS",       (70, 100, 140)),
    ("CRACK     ×1",  (220, 50,  50)),
    ("SCRATCH   ×1",  (245,158,  11)),
    ("OIL STAIN ×2",  (167,139, 250)),
    ("",              None),
    ("TOTAL     4pt", (220, 80,  80)),
    ("",              None),
    ("VERDICT",       (70, 100, 140)),
    ("✕  NG/REJECT",  (220, 50,  50)),
]

y_cur = 60
for text, color in info_lines:
    if text and color:
        draw.text((panel_x, y_cur), text, font=font_info, fill=color)
    y_cur += 18 if text else 8

# ── 頂部狀態列 ────────────────────────────────────────────────
status = "AOI INSPECTION  |  CAM-01  |  LINE-B  |  LOT B-2403  |  SN#00147"
draw.text((10, 8), status, font=font_title, fill=(50, 65, 90))
draw.line([(0, 24), (W, 24)], fill=(22, 30, 45), width=1)

# ── 底部說明 ──────────────────────────────────────────────────
footer = "IEM VISION LAB — SIMULATED AOI DEFECT IMAGE — FOR EDUCATIONAL USE ONLY"
draw.text((10, H-18), footer, font=font_title, fill=(35, 48, 65))
'''
# ─────────────────────────────────────────────────────────────
# 輸出
# ─────────────────────────────────────────────────────────────
output_path = "defect_part.png"
img.save(output_path, "PNG")
print(f"✅ 已儲存：{output_path}  ({W}×{H} px)")
```


## 一、基礎概念：影像就是數字矩陣

```python
from PIL import Image
import numpy as np

# 開啟一張圖片
img = Image.open("part.jpg")

# 查看基本資訊
print(f"尺寸 (寬x高): {img.size}")       # e.g. (1920, 1080)
print(f"色彩模式: {img.mode}")             # RGB / RGBA / L (灰階)
print(f"圖片格式: {img.format}")           # JPEG / PNG

# 【關鍵概念】轉成 NumPy 陣列，就能看到「數字的真面目」
arr = np.array(img)
print(f"陣列形狀: {arr.shape}")            # (高, 寬, 色彩通道) e.g. (1080, 1920, 3)
print(f"左上角像素的 RGB 值: {arr[0, 0]}") # e.g. [230, 215, 200]

# 【工業意義】瑕疵區域的像素值，會與正常區域有顯著差異
# 這就是 AOI 偵測的數學基礎！
```

---

## 二、影像讀寫與格式轉換

```python
from PIL import Image

# === 讀取圖片 ===
img = Image.open("metal_part.jpg")

# === 轉換色彩模式 ===
# RGB → 灰階（減少計算量，AOI 常用）
img_gray = img.convert("L")

# RGB → RGBA（加入透明度通道）
img_rgba = img.convert("RGBA")

# === 調整尺寸 ===
# LANCZOS：高品質縮放演算法（保留細節，適合工業影像）
img_small = img.resize((640, 480), Image.LANCZOS)

# 等比例縮放（避免零件變形）
width, height = img.size
scale = 0.5  # 縮小為 50%
img_half = img.resize((int(width * scale), int(height * scale)), Image.LANCZOS)

# === 裁切 ROI（感興趣區域）===
# 假設零件主體在影像中央，裁切出檢測區域
# crop() 參數為 (左, 上, 右, 下) 的像素座標
roi = img.crop((200, 150, 800, 600))

# === 儲存圖片 ===
img_gray.save("part_gray.png")                        # PNG（無損壓縮）
img_small.save("part_small.jpg", quality=95)          # JPEG（有損壓縮，quality=95 為高品質）
roi.save("part_roi.png")

print("✅ 影像處理完成並儲存！")
```

---

## 三、對比度與亮度調整（品質檢測的關鍵前處理）

```python
from PIL import Image, ImageEnhance

img = Image.open("metal_part.jpg")

# === ImageEnhance：增強器模組 ===
# 增強因子 > 1.0 表示增強；< 1.0 表示降低；= 1.0 表示不變

# 1. 對比度調整（讓瑕疵更明顯）
enhancer_contrast = ImageEnhance.Contrast(img)
img_high_contrast = enhancer_contrast.enhance(2.5)  # 提高到 2.5 倍對比
img_low_contrast  = enhancer_contrast.enhance(0.5)  # 降低到 0.5 倍對比

# 2. 亮度調整（補償打光不均問題）
enhancer_bright = ImageEnhance.Brightness(img)
img_bright = enhancer_bright.enhance(1.5)   # 提亮 50%
img_dark   = enhancer_bright.enhance(0.7)   # 調暗 30%

# 3. 銳利度調整（強化邊緣讓刮痕更清晰）
enhancer_sharp = ImageEnhance.Sharpness(img)
img_sharp = enhancer_sharp.enhance(3.0)  # 大幅提高銳利度

# 4. 色彩飽和度調整
enhancer_color = ImageEnhance.Color(img)
img_vivid = enhancer_color.enhance(1.8)

# 儲存對比結果
img_high_contrast.save("high_contrast.png")
img_sharp.save("sharpened.png")
```

---

## 四、濾鏡與邊緣強化（特徵提取的核心）

```python
from PIL import Image, ImageFilter

img = Image.open("metal_part.jpg")
img_gray = img.convert("L")  # 轉灰階更能突顯邊緣

# === ImageFilter：各種卷積濾鏡 ===

# 1. 模糊（去除雜訊 Noise，避免干擾）
img_blur = img.filter(ImageFilter.GaussianBlur(radius=3))
img_smooth = img.filter(ImageFilter.SMOOTH_MORE)

# 2. 銳化（強化特徵邊緣）
img_sharpen = img.filter(ImageFilter.SHARPEN)
img_edge_enhance = img.filter(ImageFilter.EDGE_ENHANCE_MORE)

# 3. 【AOI 核心】邊緣偵測（找出瑕疵輪廓！）
# CONTOUR 濾鏡：提取輪廓線條，瑕疵區域會有明顯的封閉輪廓
img_contour = img_gray.filter(ImageFilter.CONTOUR)

# FIND_EDGES 濾鏡：找出所有邊緣，比 CONTOUR 更細緻
img_edges = img_gray.filter(ImageFilter.FIND_EDGES)

# EMBOSS 浮雕效果：讓表面紋理的高低起伏更明顯
img_emboss = img_gray.filter(ImageFilter.EMBOSS)

# 4. 自訂卷積核（Convolution Kernel）
# 水平邊緣偵測（Sobel 濾波器變形）
horizontal_kernel = ImageFilter.Kernel(
    size=3,                                  # 3x3 的卷積核
    kernel=[
        -1, -2, -1,   # 第一列
         0,  0,  0,   # 第二列（中心）
         1,  2,  1    # 第三列
    ],
    scale=1,
    offset=128  # 偏移量，讓負值也能顯示
)
img_horizontal_edge = img_gray.filter(horizontal_kernel)

# 儲存結果
img_contour.save("contour.png")
img_edges.save("edges.png")
img_emboss.save("emboss.png")
print("✅ 濾鏡處理完成！")
```

---

## 五、像素級操作（進階：手動操控每個像素）

```python
from PIL import Image
import numpy as np

img = Image.open("metal_part.jpg")
arr = np.array(img, dtype=np.float64)  # 轉換成 NumPy 陣列，方便矩陣運算

# === 直方圖均衡化（Histogram Equalization）===
# 用途：讓影像的灰階分佈更均勻，提升對比度
# 在打光不均勻的廠房環境中特別有效！

img_gray = img.convert("L")
arr_gray = np.array(img_gray)

# 計算並正規化直方圖
hist, bins = np.histogram(arr_gray.flatten(), bins=256, range=[0, 256])
cdf = hist.cumsum()                                       # 累積分佈函數
cdf_normalized = (cdf - cdf.min()) * 255 / (cdf.max() - cdf.min())

# 套用均衡化映射
arr_equalized = cdf_normalized[arr_gray].astype(np.uint8)
img_equalized = Image.fromarray(arr_equalized)
img_equalized.save("equalized.png")

# === 閾值化（Thresholding）===
# 用途：將灰階圖轉換為二值圖（黑/白），分離瑕疵與背景
threshold = 128  # 低於此值視為瑕疵（暗區），高於此值視為正常（亮區）
arr_binary = np.where(arr_gray < threshold, 0, 255).astype(np.uint8)
img_binary = Image.fromarray(arr_binary)
img_binary.save("binary.png")

# === 影像合成（疊加比較）===
# 將原圖與邊緣圖疊合，直覺展示檢測位置
from PIL import ImageFilter
img_edge = img_gray.filter(ImageFilter.FIND_EDGES)
img_edge_rgb = img_edge.convert("RGB")

# blend()：兩張圖片的加權平均
# alpha=0.7 表示 70% 原圖 + 30% 邊緣圖
img_overlay = Image.blend(img.convert("RGB"), img_edge_rgb, alpha=0.3)
img_overlay.save("overlay.png")

print("✅ 像素操作完成！")
```

---

## 六、🖥️ Streamlit 應用：AOI 瑕疵影像前處理器

> 將以上所學整合成一個互動式網頁工具，讓學生**拖拉滑桿**即時看到影像特徵被提取的過程。

```python
# 檔案名稱：app_aoi.py
# 執行方式：streamlit run app_aoi.py

import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np

# ===== 頁面設定 =====
st.set_page_config(
    page_title="AOI 瑕疵影像前處理器",
    page_icon="🔍",
    layout="wide"  # 使用寬版佈局，左右並排比較
)

st.title("🔍 AOI 瑕疵影像前處理器")
st.markdown("上傳金屬零件圖片，調整參數，即時看到影像特徵提取的過程。")

# ===== 側邊欄：參數控制 =====
with st.sidebar:
    st.header("⚙️ 調整參數")

    st.subheader("1. 基本調整")
    contrast   = st.slider("對比度",   0.5, 4.0, 1.0, 0.1,
                            help="增加對比度可讓瑕疵更明顯")
    brightness = st.slider("亮度",     0.5, 2.0, 1.0, 0.1,
                            help="補償廠房打光不均的問題")
    sharpness  = st.slider("銳利度",   0.0, 5.0, 1.0, 0.5,
                            help="提高銳利度讓刮痕輪廓更清晰")

    st.subheader("2. 影像模式")
    color_mode = st.radio(
        "色彩模式",
        ["彩色 (RGB)", "灰階 (Grayscale)"],
        index=1,  # 預設灰階（AOI 常用）
        help="灰階模式計算量更少，適合工業即時檢測"
    )

    st.subheader("3. 特徵提取濾鏡")
    filter_choice = st.selectbox(
        "選擇濾鏡",
        ["無濾鏡", "邊緣強化 (Edge Enhance)", "邊緣偵測 (Find Edges)",
         "輪廓提取 (Contour)", "浮雕效果 (Emboss)", "高斯模糊 (去雜訊)"],
        help="Contour / Find Edges 最常用於 AOI 輪廓偵測"
    )

    st.subheader("4. 二值化")
    apply_threshold = st.checkbox("套用閾值化（二值圖）")
    if apply_threshold:
        threshold_val = st.slider("閾值", 0, 255, 128, 5,
                                  help="低於閾值的像素變黑（視為瑕疵區域）")

# ===== 主畫面：上傳與顯示 =====
uploaded_file = st.file_uploader(
    "📤 上傳零件圖片",
    type=["jpg", "jpeg", "png", "bmp"],
    help="支援 JPG / PNG / BMP 格式"
)

# 若沒有上傳，使用預設範例圖（方便展示）
if uploaded_file is None:
    st.info("💡 尚未上傳圖片，使用範例圖片展示效果。")
    # 建立一張模擬的「金屬零件」圖（灰色底+隨機深色斑點模擬瑕疵）
    sample_arr = np.random.randint(180, 220, (400, 600, 3), dtype=np.uint8)
    # 模擬幾個瑕疵點（暗斑）
    sample_arr[100:130, 150:200] = 50   # 瑕疵 1
    sample_arr[250:280, 350:420] = 30   # 瑕疵 2
    sample_arr[180:200, 480:510] = 60   # 瑕疵 3
    img_original = Image.fromarray(sample_arr)
else:
    img_original = Image.open(uploaded_file)

# ===== 影像處理流程 =====
img_processed = img_original.copy()

# 步驟 1：色彩模式轉換
if color_mode == "灰階 (Grayscale)":
    img_processed = img_processed.convert("L").convert("RGB")  # 轉回 RGB 才能統一顯示

# 步驟 2：套用增強器
img_processed = ImageEnhance.Contrast(img_processed).enhance(contrast)
img_processed = ImageEnhance.Brightness(img_processed).enhance(brightness)
img_processed = ImageEnhance.Sharpness(img_processed).enhance(sharpness)

# 步驟 3：套用濾鏡
filter_map = {
    "邊緣強化 (Edge Enhance)": ImageFilter.EDGE_ENHANCE_MORE,
    "邊緣偵測 (Find Edges)":   ImageFilter.FIND_EDGES,
    "輪廓提取 (Contour)":      ImageFilter.CONTOUR,
    "浮雕效果 (Emboss)":       ImageFilter.EMBOSS,
    "高斯模糊 (去雜訊)":      ImageFilter.GaussianBlur(radius=3),
}
if filter_choice != "無濾鏡":
    img_processed = img_processed.filter(filter_map[filter_choice])

# 步驟 4：二值化
if apply_threshold:
    arr = np.array(img_processed.convert("L"))
    arr_binary = np.where(arr < threshold_val, 0, 255).astype(np.uint8)
    img_processed = Image.fromarray(arr_binary).convert("RGB")

# ===== 並排顯示：原始圖 vs 處理後 =====
col1, col2 = st.columns(2)

with col1:
    st.subheader("📷 原始影像")
    st.image(img_original, use_column_width=True)
    arr_orig = np.array(img_original.convert("L"))
    st.caption(f"尺寸：{img_original.size[0]} × {img_original.size[1]} px｜"
               f"平均亮度：{arr_orig.mean():.1f}")

with col2:
    st.subheader("🔬 處理後影像")
    st.image(img_processed, use_column_width=True)
    arr_proc = np.array(img_processed.convert("L"))
    st.caption(f"尺寸：{img_processed.size[0]} × {img_processed.size[1]} px｜"
               f"平均亮度：{arr_proc.mean():.1f}")

# ===== 像素分佈直方圖 =====
st.subheader("📊 灰階像素分佈對比")
import pandas as pd

hist_orig, _ = np.histogram(np.array(img_original.convert("L")).flatten(), bins=50, range=[0, 256])
hist_proc, _ = np.histogram(arr_proc.flatten(), bins=50, range=[0, 256])
bins_center = np.arange(0, 256, 256 / 50)

chart_data = pd.DataFrame({
    "灰階值": bins_center,
    "原始影像像素數": hist_orig,
    "處理後像素數": hist_proc
}).set_index("灰階值")

st.line_chart(chart_data)
st.caption("💡 瑕疵會使深色（低灰階值）的像素增加；套用邊緣偵測後，高對比邊緣像素也會增多。")

# ===== 下載按鈕 =====
import io
buf = io.BytesIO()
img_processed.save(buf, format="PNG")
st.download_button(
    label="⬇️ 下載處理後影像",
    data=buf.getvalue(),
    file_name="processed_part.png",
    mime="image/png"
)

# ===== 學習筆記 =====
with st.expander("📚 學習筆記：各濾鏡的工業應用場景"):
    st.markdown("""
    | 濾鏡 | 原理 | AOI 應用場景 |
    |------|------|------------|
    | **CONTOUR** | 偵測像素梯度的閉合輪廓 | 偵測零件上的裂縫、凹陷 |
    | **FIND_EDGES** | 計算像素梯度差異 | 偵測刮痕、銲接邊緣缺陷 |
    | **EMBOSS** | 模擬光線側打的浮雕效果 | 強化表面紋理的起伏特徵 |
    | **SHARPEN** | 強化高頻細節 | 讓細微刮痕更清晰 |
    | **GaussianBlur** | 平均周遭像素值 | 去除相機感測器雜訊 |

    **實際 AOI 系統流程：**
    ```
    原始影像 → 灰階化 → 高斯模糊（去雜訊）→ 邊緣偵測 → 閾值化 → 輪廓分析 → 判定良/不良品
    ```
    """)
```

---

## 七、課後練習

### 練習 1：批次影像處理腳本

```python
# 【情境】工廠相機每小時拍攝 100 張圖片，需要自動批次前處理
import os
from PIL import Image, ImageFilter, ImageEnhance

def preprocess_aoi_image(input_path: str, output_path: str) -> dict:
    """
    AOI 標準前處理流程函式
    
    Parameters:
        input_path:  原始影像路徑
        output_path: 輸出影像路徑
    
    Returns:
        dict: 包含處理結果統計的字典
    """
    img = Image.open(input_path)
    
    # 1. 灰階化（減少計算量）
    img = img.convert("L")
    
    # 2. 對比度增強（提高瑕疵可見度）
    img = ImageEnhance.Contrast(img).enhance(2.0)
    
    # 3. 輕度模糊（去除感測器雜訊）
    img = img.filter(ImageFilter.GaussianBlur(radius=1))
    
    # 4. 邊緣偵測（特徵提取）
    img_edge = img.filter(ImageFilter.FIND_EDGES)
    
    # 5. 計算瑕疵指標（邊緣強度均值）
    import numpy as np
    arr = np.array(img_edge)
    defect_score = arr.mean()  # 分數越高，代表邊緣越多，可能有瑕疵
    
    # 6. 儲存
    img_edge.save(output_path)
    
    return {
        "file": os.path.basename(input_path),
        "defect_score": round(defect_score, 2),
        "判定": "⚠️ 疑似瑕疵" if defect_score > 30 else "✅ 正常"
    }


# 批次處理資料夾內所有圖片
input_folder  = "raw_images/"
output_folder = "processed_images/"
os.makedirs(output_folder, exist_ok=True)

results = []
for filename in os.listdir(input_folder):
    if filename.lower().endswith((".jpg", ".jpeg", ".png")):
        in_path  = os.path.join(input_folder, filename)
        out_path = os.path.join(output_folder, f"edge_{filename}")
        result   = preprocess_aoi_image(in_path, out_path)
        results.append(result)
        print(f"處理完成：{result}")

print(f"\n共處理 {len(results)} 張圖片")
```

### 練習 2：思考題

1. 為什麼 AOI 系統通常先轉成**灰階**再做邊緣偵測，而不直接用彩色圖片？
2. `GaussianBlur` 的 `radius` 值調太大有什麼壞處？調太小有什麼問題？
3. 閾值化的「閾值」要怎麼決定？有什麼方法可以**自動**計算最佳閾值？（提示：查詢 Otsu's Method）

---

## 📎 重點整理

```
Pillow 核心模組
├── Image          → 開啟、儲存、轉換、裁切、縮放
├── ImageEnhance   → 對比度、亮度、銳利度調整
├── ImageFilter    → 卷積濾鏡（模糊、邊緣、輪廓）
└── NumPy 整合     → 轉為陣列進行像素級數學操作

AOI 前處理標準流程
原始圖 → 灰階 → 去雜訊 → 增強對比 → 邊緣偵測 → 閾值化 → 特徵擷取
```

---

*下一單元：[模組 1-2：QR Code — 智慧倉儲標籤產生器](./Module1_2_QRCode.md)*
