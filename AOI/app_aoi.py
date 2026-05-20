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
    st.image(img_original, use_container_width=True)
    arr_orig = np.array(img_original.convert("L"))
    st.caption(f"尺寸：{img_original.size[0]} × {img_original.size[1]} px｜"
               f"平均亮度：{arr_orig.mean():.1f}")

with col2:
    st.subheader("🔬 處理後影像")
    st.image(img_processed, use_container_width=True)
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