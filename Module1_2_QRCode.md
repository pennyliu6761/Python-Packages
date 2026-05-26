# 模組 1-2：QR Code (qrcode) — 智慧倉儲標籤產生器

> **學習目標**：理解二維條碼的資訊編碼原理，實作物流追蹤的第一步。

---

## 📌 為什麼工管系要學 QR Code？

在智慧倉儲中，每個料件、棧板、儲位都需要**可機讀的識別標籤**。QR Code 能將「料號＋批次＋數量＋日期」等結構化資訊壓縮為一個二維矩陣，讓掃描槍、手機、工業相機都能快速讀取，是製造業 **MES（製造執行系統）** 與 **WMS（倉儲管理系統）** 的基礎元件。

---

## 🔧 安裝

```bash
pip install qrcode[pil]   # 需要 Pillow 支援影像輸出
pip install pillow        # 若尚未安裝
```

---

## 一、QR Code 的基本原理

```
文字資訊
  ↓ Reed-Solomon 錯誤更正編碼
二進位資料流
  ↓ 模組（黑白方格）映射
21×21 到 177×177 的方格矩陣
  ↓ 加上定位標記（三個角落的大方塊）
可辨識的 QR Code 圖片
```

**版本（Version）**：從 V1（21×21）到 V40（177×177），版本越高可存越多資料。  
**糾錯等級（Error Correction Level）**：
| 等級 | 可容許損毀比例 | 適用場景 |
|------|-------------|---------|
| L    | 7%          | 清潔、室內環境 |
| M    | 15%         | 一般用途（預設）|
| Q    | 25%         | 工廠輕微污染環境 |
| H    | 30%         | **工業首選**：可在油污、刮傷下仍可讀 |

---

## 二、基本生成

```python
import qrcode
from PIL import Image

# ===== 方法一：最簡潔的一行生成 =====
img = qrcode.make("P/N: M-2024-001 | Qty: 100 | Date: 2024-01-15")
img.save("simple_qr.png")

# ===== 方法二：客製化設定（工業標籤推薦）=====
qr = qrcode.QRCode(
    version=None,          # None = 自動選擇最小版本（推薦）
    error_correction=qrcode.constants.ERROR_CORRECT_H,  # H 級：工業環境首選
    box_size=10,           # 每個模組（小方格）的像素大小，10px 適合列印
    border=4,              # 四周的「靜區（Quiet Zone）」：標準要求至少 4 個模組
)

# 加入資料
qr.add_data("P/N: M-2024-001 | Batch: B001 | Qty: 100 | Date: 2024-01-15")
qr.make(fit=True)  # fit=True：自動決定版本大小

# 生成黑白圖片
img = qr.make_image(
    fill_color="black",   # 前景色（模組顏色）
    back_color="white"    # 背景色
)

img.save("industrial_qr.png")
print(f"✅ QR Code 已生成：{img.size}")  # 查看圖片尺寸
```

<img width="410" height="410" alt="simple_qr" src="https://github.com/user-attachments/assets/dbe50b49-578e-48bd-95e3-cc944664937d" />
<img width="530" height="530" alt="industrial_qr" src="https://github.com/user-attachments/assets/480522fc-b6d9-457a-a453-d052330de94d" />

---

## 三、結構化料件資訊編碼

```python
import qrcode
import json
from datetime import datetime

def generate_part_qr(part_no: str, batch: str, qty: int,
                     location: str, supplier: str) -> qrcode.image.base.BaseImage:
    """
    生成標準化的工廠料件 QR Code
    
    採用 JSON 格式儲存，讓掃描後的系統能直接解析
    """
    # 建立結構化的料件資訊（JSON 格式，易於系統解析）
    part_data = {
        "PN":  part_no,             # 料號 (Part Number)
        "BT":  batch,               # 批次號 (Batch)
        "QT":  qty,                 # 數量 (Quantity)
        "LC":  location,            # 儲位 (Location)
        "SP":  supplier,            # 供應商 (Supplier)
        "DT":  datetime.now().strftime("%Y%m%d"),   # 入庫日期（精簡格式節省空間）
        "VR":  "1.0"                # 標籤版本（方便未來格式升級）
    }
    
    # 序列化為 JSON 字串（縮減空格節省 QR Code 容量）
    data_str = json.dumps(part_data, separators=(',', ':'))
    print(f"編碼內容（{len(data_str)} 字元）：{data_str}")
    
    # 生成 QR Code
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=8,
        border=4
    )
    qr.add_data(data_str)
    qr.make(fit=True)
    
    return qr.make_image(fill_color="#1a1a2e", back_color="white")  # 深藍色更有質感


# 使用範例
img = generate_part_qr(
    part_no  = "M-BOLT-M8-316",
    batch    = "B2024-0115-01",
    qty      = 500,
    location = "A-03-02-04",     # 倉別-排-層-格
    supplier = "台灣緊固件股份有限公司"
)
img.save("part_label_qr.png")
```

<img width="616" height="616" alt="part_label_qr" src="https://github.com/user-attachments/assets/d2eb237c-590f-4f2d-b07f-daf13f13e88f" />

---

## 四、加入工廠 Logo（品牌化標籤）

```python
import qrcode
from PIL import Image

def generate_branded_qr(data: str, logo_path: str, output_path: str,
                         logo_ratio: float = 0.25) -> None:
    """
    生成帶有工廠 Logo 的品牌化 QR Code
    
    【技術要點】
    - 使用 H 級糾錯（30% 容錯），讓 Logo 遮住中央 25% 仍可讀
    - Logo 比例建議不超過 30%（否則可能無法掃描）
    """
    # 1. 生成基礎 QR Code（高解析度）
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # 必須用 H 級！
        box_size=12,   # 高解析度，方便 Logo 疊加
        border=4
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
    qr_w, qr_h = qr_img.size
    
    # 2. 載入並縮放 Logo
    logo = Image.open(logo_path).convert("RGBA")
    
    logo_size = int(qr_w * logo_ratio)            # Logo 邊長 = QR 邊長的 25%
    logo = logo.resize((logo_size, logo_size), Image.LANCZOS)
    
    # 3. 計算 Logo 貼上的位置（正中央）
    logo_x = (qr_w - logo_size) // 2
    logo_y = (qr_h - logo_size) // 2
    
    # 4. 加上白色圓角背景（讓 Logo 更清晰）
    padding = 8  # 背景比 Logo 多 8px 的 padding
    background = Image.new("RGBA",
                           (logo_size + padding * 2, logo_size + padding * 2),
                           (255, 255, 255, 255))
    qr_img.paste(background, (logo_x - padding, logo_y - padding), background)
    
    # 5. 疊加 Logo（使用 alpha 遮罩保留透明度）
    qr_img.paste(logo, (logo_x, logo_y), logo)
    
    # 6. 儲存最終圖片
    qr_img.convert("RGB").save(output_path)
    print(f"✅ 品牌 QR Code 已儲存：{output_path}")
    print(f"   圖片尺寸：{qr_img.size[0]} × {qr_img.size[1]} px")


# 使用（需要準備一張 logo.png 圖片）
generate_branded_qr(
    data="https://iem.nqu.edu.tw/",
    logo_path="company_logo.png",
    output_path="branded_label.png"
)
```

<img width="444" height="444" alt="branded_label" src="https://github.com/user-attachments/assets/ae629995-d056-4e19-b122-3f895e2cc812" />

---

## 五、完整標籤設計（QR Code + 文字資訊）

```python
import qrcode
from PIL import Image, ImageDraw, ImageFont
import textwrap

def generate_warehouse_label(part_no: str, description: str,
                              qty: int, location: str,
                              batch: str) -> Image.Image:
    """
    生成完整的倉儲實體標籤
    包含：QR Code + 可讀文字 + 邊框
    
    模擬實際貼在棧板上的 A6 大小標籤（105×148mm）
    """
    # ===== 標籤尺寸（300 DPI 下的像素數）=====
    # 105mm × 148mm (A6) @ 300DPI = 1240 × 1748 px
    # 這裡用縮小版示範
    LABEL_W, LABEL_H = 600, 400
    MARGIN = 20

    # ===== 建立白色畫布 =====
    label = Image.new("RGB", (LABEL_W, LABEL_H), "white")
    draw  = ImageDraw.Draw(label)

    # ===== 畫外框 =====
    draw.rectangle(
        [(2, 2), (LABEL_W - 3, LABEL_H - 3)],
        outline="#2c3e50", width=3
    )

    # ===== 標題區（深色背景）=====
    draw.rectangle([(2, 2), (LABEL_W - 3, 50)], fill="#2c3e50")
    # 注意：實際環境中需要提供字型檔路徑
    # font_title = ImageFont.truetype("NotoSansCJK.ttf", 22)
    # 若無字型檔，使用預設字型（不支援中文）
    font_default = ImageFont.load_default()
    draw.text((MARGIN, 15), "WAREHOUSE LABEL", fill="white", font=font_default)

    # ===== 生成小尺寸 QR Code（嵌入標籤右側）=====
    qr_data = f"PN:{part_no}|QT:{qty}|BT:{batch}|LC:{location}"
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H,
                        box_size=4, border=3)
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_img = qr_img.resize((200, 200), Image.LANCZOS)

    # 將 QR Code 貼在標籤右側
    label.paste(qr_img, (LABEL_W - 220, 70))

    # ===== 文字資訊區（標籤左側）=====
    text_x = MARGIN
    lines = [
        ("料號 (P/N)",     part_no),
        ("品名",           description),
        ("數量 (Qty)",     str(qty)),
        ("儲位",           location),
        ("批次",           batch),
    ]

    y_pos = 65
    for label_text, value in lines:
        draw.text((text_x, y_pos),      label_text + ":",  fill="#7f8c8d", font=font_default)
        draw.text((text_x, y_pos + 16), value,             fill="#2c3e50", font=font_default)
        draw.line([(text_x, y_pos + 34), (350, y_pos + 34)],
                  fill="#ecf0f1", width=1)  # 分隔線
        y_pos += 50

    # ===== 掃描提示 =====
    draw.text((LABEL_W - 220, 275), "SCAN TO VERIFY",
              fill="#95a5a6", font=font_default)

    return label


# 生成標籤
label_img = generate_warehouse_label(
    part_no     = "M-BOLT-M8-316L",
    description = "Bolt M8x20 SUS316L",
    qty         = 500,
    location    = "A-03-02-04",
    batch       = "B2024011501"
)
label_img.save("warehouse_label.png", dpi=(300, 300))
print("✅ 倉儲標籤已生成！")
```

<img width="600" height="400" alt="warehouse_label" src="https://github.com/user-attachments/assets/16ea9420-f76a-42cc-bedc-8b75bfa2aa01" />

---

## 六、🖥️ Streamlit 應用：智慧倉儲標籤產生器

```python
# 檔案名稱：app_qr.py
# 執行方式：streamlit run app_qr.py

import streamlit as st
import qrcode
from PIL import Image, ImageDraw, ImageFont
import json
import io
from datetime import datetime, date

st.set_page_config(page_title="智慧倉儲標籤產生器", page_icon="🏭", layout="wide")

st.title("🏭 智慧倉儲 QR Code 標籤產生器")
st.markdown("填寫料件資訊，即時生成帶有完整資訊的 QR Code 標籤。")

# ===== 輸入表單 =====
with st.form("label_form"):
    st.subheader("📋 料件資訊")

    col1, col2 = st.columns(2)

    with col1:
        part_no     = st.text_input("料號 (Part Number) *", value="M-BOLT-M8-316L",
                                     help="例：M-BOLT-M8-316L")
        description = st.text_input("品名 *", value="Bolt M8x20 SUS316L")
        supplier    = st.text_input("供應商", value="台灣緊固件")
        qty         = st.number_input("數量 *", min_value=1, value=500)

    with col2:
        batch       = st.text_input("批次號 *", value="B2024011501")
        location    = st.text_input("儲位", value="A-03-02-04",
                                     help="格式建議：倉別-排-層-格")
        inbound_date = st.date_input("入庫日期", value=date.today())
        unit        = st.selectbox("單位", ["PCS", "KG", "BOX", "ROLL", "M"])

    st.subheader("⚙️ QR Code 設定")
    col3, col4 = st.columns(2)
    with col3:
        error_level = st.select_slider(
            "糾錯等級",
            options=["L (7%)", "M (15%)", "Q (25%)", "H (30%)"],
            value="H (30%)",
            help="工廠環境建議選 H，可容忍 30% 的污損"
        )
        qr_color = st.color_picker("QR Code 顏色", "#000000")
    with col4:
        include_json = st.checkbox("編碼為 JSON 格式", value=True,
                                    help="JSON 格式讓系統掃描後能自動解析各欄位")
        add_url      = st.text_input("系統連結 URL（選填）",
                                      placeholder="https://wms.company.com/part/",
                                      help="若填入，QR Code 掃描後會開啟此頁面")

    submitted = st.form_submit_button("🔨 生成標籤", type="primary")

# ===== 生成結果 =====
if submitted:
    # 組合 QR Code 內容
    ec_map = {"L (7%)": qrcode.constants.ERROR_CORRECT_L,
              "M (15%)": qrcode.constants.ERROR_CORRECT_M,
              "Q (25%)": qrcode.constants.ERROR_CORRECT_Q,
              "H (30%)": qrcode.constants.ERROR_CORRECT_H}

    if add_url:
        qr_content = f"{add_url}{part_no}"
    elif include_json:
        data_dict = {
            "PN": part_no, "DS": description, "QT": qty, "UT": unit,
            "BT": batch, "LC": location, "SP": supplier,
            "DT": inbound_date.strftime("%Y%m%d"), "VR": "1.0"
        }
        qr_content = json.dumps(data_dict, ensure_ascii=False, separators=(',', ':'))
    else:
        qr_content = f"PN:{part_no} QT:{qty}{unit} BT:{batch} LC:{location}"

    # 生成 QR Code
    qr = qrcode.QRCode(
        error_correction=ec_map[error_level],
        box_size=10, border=4
    )
    qr.add_data(qr_content)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color=qr_color, back_color="white").convert("RGB")

    # 顯示結果
    col_a, col_b = st.columns([1, 2])

    with col_a:
        st.subheader("📲 生成的 QR Code")
        st.image(qr_img, width=300)

        # 下載 QR Code 圖片
        buf = io.BytesIO()
        qr_img.save(buf, format="PNG")
        buf.seek(0)
        st.download_button(
            "⬇️ 下載 QR Code",
            data=buf.getvalue(),
            file_name=f"qr_{part_no}.png",
            mime="image/png"
        )

    with col_b:
        st.subheader("📋 標籤預覽")
        st.markdown(f"""
        | 欄位 | 內容 |
        |------|------|
        | **料號** | `{part_no}` |
        | **品名** | {description} |
        | **數量** | {qty} {unit} |
        | **批次** | {batch} |
        | **儲位** | {location} |
        | **供應商** | {supplier} |
        | **入庫日期** | {inbound_date} |
        """)

        st.subheader("🔍 QR Code 編碼內容")
        st.code(qr_content, language="json" if include_json else "text")
        st.caption(f"資料長度：{len(qr_content)} 字元 | QR Code 版本：自動選擇")

    st.success("✅ 標籤生成成功！掃描上方 QR Code 驗證內容。")

    # ===== 學習補充 =====
    with st.expander("💡 這個 QR Code 在工廠系統中如何被使用？"):
        st.markdown("""
        ```
        實體流程
        ─────────────────────────────────────────────────────
        ① 倉管人員在電腦系統輸入入庫資料（就是這個頁面的功能）
        ② 系統列印標籤，貼在棧板或料箱上
        ③ 叉車司機掃描 QR Code，確認放置儲位
        ④ 生產線作業員掃描 QR Code，系統自動扣料
        ⑤ 出貨時再掃一次，完成批次追蹤記錄
        
        QR Code 解碼後的 JSON 範例
        ─────────────────────────────────────────────────────
        {"PN":"M-BOLT-M8-316L","QT":500,"UT":"PCS","BT":"B2024011501"}
                                          ↓
                        WMS/MES 系統直接 json.loads() 解析
                        不需要人工鍵入，零錯誤率
        ```
        """)
```

<img width="1768" height="840" alt="image" src="https://github.com/user-attachments/assets/023101ac-9091-4124-9062-8a4de03575c1" />
<img width="1773" height="890" alt="image" src="https://github.com/user-attachments/assets/42669651-f3ad-4bce-a906-acd370f3024d" />

---

## 七、課後練習

### 練習 1：批次生成多張標籤

```python
# 檔案名稱：app_qr.py
# 執行方式：streamlit run app_qr.py

import streamlit as st
import qrcode
from PIL import Image, ImageDraw, ImageFont
import json
import io
import csv
from datetime import datetime, date

st.set_page_config(page_title="智慧倉儲標籤產生器", page_icon="🏭", layout="wide")

st.title("🏭 智慧倉儲 QR Code 標籤產生器")
st.markdown("填寫料件資訊，即時生成帶有完整資訊的 QR Code 標籤。")

# ── 虛擬資料 ──────────────────────────────────────────────────────────────────
MOCK_ROWS = [
    {"part_no": "M-BOLT-M8-316L",    "description": "Bolt M8x20 SUS316L",     "qty": 500,  "unit": "PCS", "batch": "B20240115", "location": "A-01-02-03", "supplier": "台灣緊固件",  "inbound_date": "20240115"},
    {"part_no": "M-NUT-M8-304",      "description": "Nut M8 SUS304",          "qty": 500,  "unit": "PCS", "batch": "B20240115", "location": "A-01-02-04", "supplier": "台灣緊固件",  "inbound_date": "20240115"},
    {"part_no": "P-PIPE-DN50-SS",    "description": "Pipe DN50 Stainless",    "qty": 20,   "unit": "M",   "batch": "B20240117", "location": "B-02-01-01", "supplier": "聯鋼管材",    "inbound_date": "20240117"},
    {"part_no": "V-VALVE-DN50-CF8",  "description": "Gate Valve DN50 CF8",   "qty": 5,    "unit": "PCS", "batch": "B20240117", "location": "B-02-01-02", "supplier": "金門閥件",    "inbound_date": "20240117"},
    {"part_no": "B-BEARING-6204-ZZ", "description": "Deep Groove Bearing ZZ", "qty": 30,  "unit": "PCS", "batch": "B20240119", "location": "C-03-02-01", "supplier": "NSK 代理商",  "inbound_date": "20240119"},
]
CSV_COLUMNS = ["part_no", "description", "qty", "unit", "batch", "location", "supplier", "inbound_date"]


def make_csv_bytes(rows: list[dict]) -> bytes:
    """把 dict 列表序列化為 CSV bytes（UTF-8 BOM，Excel 可直接開啟）"""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=CSV_COLUMNS)
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8-sig")   # BOM 讓 Excel 正確顯示中文


def parse_csv_bytes(raw: bytes) -> list[dict]:
    """把上傳的 CSV bytes 解析為 dict 列表，自動處理 BOM"""
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for r in reader:
        r["qty"] = int(r.get("qty", 0))
        rows.append(r)
    return rows


def build_qr_content(row: dict, include_json: bool, url_prefix: str) -> str:
    if url_prefix:
        return f"{url_prefix}{row['part_no']}"
    if include_json:
        return json.dumps({
            "PN": row["part_no"], "DS": row["description"],
            "QT": row["qty"],     "UT": row["unit"],
            "BT": row["batch"],   "LC": row["location"],
            "SP": row["supplier"],"DT": row["inbound_date"], "VR": "1.0"
        }, ensure_ascii=False, separators=(',', ':'))
    return (f"PN:{row['part_no']}|QT:{row['qty']}{row['unit']}|"
            f"BT:{row['batch']}|LC:{row['location']}")


def make_qr_image(content: str, ec_const, color: str) -> Image.Image:
    qr = qrcode.QRCode(error_correction=ec_const, box_size=10, border=4)
    qr.add_data(content)
    qr.make(fit=True)
    return qr.make_image(fill_color=color, back_color="white").convert("RGB")


def img_to_png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# 頁籤：① 單筆手動輸入  ② 批次 CSV
# ─────────────────────────────────────────────────────────────────────────────
tab_manual, tab_batch = st.tabs(["✏️ 單筆輸入", "📂 批次 CSV"])


# ══════════════════════════════════════════════════════════════════════════════
# 頁籤 ①：單筆手動輸入（原有功能，完整保留）
# ══════════════════════════════════════════════════════════════════════════════
with tab_manual:
    with st.form("label_form"):
        st.subheader("📋 料件資訊")
        col1, col2 = st.columns(2)
        with col1:
            part_no     = st.text_input("料號 (Part Number) *", value="M-BOLT-M8-316L")
            description = st.text_input("品名 *", value="Bolt M8x20 SUS316L")
            supplier    = st.text_input("供應商", value="台灣緊固件")
            qty         = st.number_input("數量 *", min_value=1, value=500)
        with col2:
            batch        = st.text_input("批次號 *", value="B2024011501")
            location     = st.text_input("儲位", value="A-03-02-04")
            inbound_date = st.date_input("入庫日期", value=date.today())
            unit         = st.selectbox("單位", ["PCS", "KG", "BOX", "ROLL", "M"])

        st.subheader("⚙️ QR Code 設定")
        col3, col4 = st.columns(2)
        with col3:
            error_level = st.select_slider("糾錯等級",
                options=["L (7%)", "M (15%)", "Q (25%)", "H (30%)"], value="H (30%)")
            qr_color = st.color_picker("QR Code 顏色", "#000000")
        with col4:
            include_json = st.checkbox("編碼為 JSON 格式", value=True)
            add_url      = st.text_input("系統連結 URL（選填）",
                placeholder="https://wms.company.com/part/")

        submitted = st.form_submit_button("🔨 生成標籤", type="primary")

    if submitted:
        ec_map = {"L (7%)": qrcode.constants.ERROR_CORRECT_L,
                  "M (15%)": qrcode.constants.ERROR_CORRECT_M,
                  "Q (25%)": qrcode.constants.ERROR_CORRECT_Q,
                  "H (30%)": qrcode.constants.ERROR_CORRECT_H}
        row = {"part_no": part_no, "description": description,
               "qty": qty, "unit": unit, "batch": batch,
               "location": location, "supplier": supplier,
               "inbound_date": inbound_date.strftime("%Y%m%d")}
        qr_content = build_qr_content(row, include_json, add_url)
        qr_img = make_qr_image(qr_content, ec_map[error_level], qr_color)

        col_a, col_b = st.columns([1, 2])
        with col_a:
            st.subheader("📲 生成的 QR Code")
            st.image(qr_img, width=300)
            st.download_button("⬇️ 下載 QR Code", data=img_to_png_bytes(qr_img),
                               file_name=f"qr_{part_no}.png", mime="image/png")
        with col_b:
            st.subheader("📋 標籤預覽")
            st.markdown(f"""
| 欄位 | 內容 |
|------|------|
| **料號** | `{part_no}` |
| **品名** | {description} |
| **數量** | {qty} {unit} |
| **批次** | {batch} |
| **儲位** | {location} |
| **供應商** | {supplier} |
| **入庫日期** | {inbound_date} |
""")
            st.subheader("🔍 QR Code 編碼內容")
            st.code(qr_content, language="json" if include_json else "text")
        st.success("✅ 標籤生成成功！")


# ══════════════════════════════════════════════════════════════════════════════
# 頁籤 ②：批次 CSV
# ══════════════════════════════════════════════════════════════════════════════
with tab_batch:

    # ── A. 產生虛擬 CSV ───────────────────────────────────────────────────────
    st.subheader("① 取得 CSV 範本")
    st.caption("下載後可直接用 Excel 編輯，再上傳到下方。")
    st.download_button(
        label="⬇️ 下載 5 筆虛擬資料 CSV",
        data=make_csv_bytes(MOCK_ROWS),
        file_name="inventory_sample.csv",
        mime="text/csv",
    )

    st.divider()

    # ── B. 上傳 CSV ───────────────────────────────────────────────────────────
    st.subheader("② 上傳 CSV 檔案")
    uploaded = st.file_uploader("選擇 CSV 檔（欄位：" + "、".join(CSV_COLUMNS) + "）",
                                 type=["csv"])

    # 若沒有上傳，預設用虛擬資料讓介面可以操作
    if uploaded is not None:
        raw_bytes = uploaded.read()
        try:
            rows = parse_csv_bytes(raw_bytes)
            st.success(f"✅ 已載入 {len(rows)} 筆資料")
        except Exception as e:
            st.error(f"CSV 解析失敗：{e}")
            rows = []
    else:
        rows = MOCK_ROWS.copy()
        st.info("尚未上傳 CSV，目前顯示 5 筆虛擬資料供預覽。")

    if not rows:
        st.stop()

    st.divider()

    # ── C. 選取品項 ───────────────────────────────────────────────────────────
    st.subheader("③ 選取要製作 QR Code 的品項")

    # 顯示資料表，讓使用者勾選
    import pandas as pd
    df = pd.DataFrame(rows)

    # 多選：用 multiselect 讓使用者挑選 part_no + batch 組合
    options = [f"{r['part_no']}  ▸  批次 {r['batch']}" for r in rows]
    selected = st.multiselect(
        "選擇品項（可多選）",
        options=options,
        default=options,          # 預設全選
        help="按住 Ctrl 可多選，或直接點選清單中的項目"
    )

    # 顯示對應資料表（選到哪些就顯示哪些）
    selected_idx = [i for i, o in enumerate(options) if o in selected]
    selected_rows = [rows[i] for i in selected_idx]

    if selected_rows:
        st.dataframe(
            pd.DataFrame(selected_rows),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.warning("請至少選擇一個品項。")
        st.stop()

    st.divider()

    # ── D. QR Code 設定 ───────────────────────────────────────────────────────
    st.subheader("④ QR Code 設定")
    bc1, bc2, bc3 = st.columns(3)
    with bc1:
        b_error = st.select_slider("糾錯等級",
            options=["L (7%)", "M (15%)", "Q (25%)", "H (30%)"], value="H (30%)",
            key="batch_ec")
    with bc2:
        b_color = st.color_picker("QR Code 顏色", "#000000", key="batch_color")
    with bc3:
        b_json  = st.checkbox("編碼為 JSON 格式", value=True, key="batch_json")
    b_url = st.text_input("系統連結 URL（選填）", placeholder="https://wms.company.com/part/",
                           key="batch_url")

    st.divider()

    # ── E. 生成並下載 ─────────────────────────────────────────────────────────
    st.subheader("⑤ 生成 QR Code")

    ec_map = {"L (7%)": qrcode.constants.ERROR_CORRECT_L,
              "M (15%)": qrcode.constants.ERROR_CORRECT_M,
              "Q (25%)": qrcode.constants.ERROR_CORRECT_Q,
              "H (30%)": qrcode.constants.ERROR_CORRECT_H}

    if st.button("🔨 批次生成所有選取品項", type="primary"):
        progress = st.progress(0, text="生成中…")
        results = []   # list of (filename, png_bytes)

        for idx, row in enumerate(selected_rows):
            content = build_qr_content(row, b_json, b_url)
            img     = make_qr_image(content, ec_map[b_error], b_color)
            fname   = f"qr_{row['part_no']}_{row['batch']}.png"
            results.append((fname, img_to_png_bytes(img), img, row, content))
            progress.progress((idx + 1) / len(selected_rows),
                              text=f"已生成 {idx+1}/{len(selected_rows)}：{row['part_no']}")

        progress.empty()
        st.success(f"✅ 共生成 {len(results)} 張 QR Code")

        # 個別預覽 + 下載
        cols_per_row = 3
        for chunk_start in range(0, len(results), cols_per_row):
            chunk = results[chunk_start:chunk_start + cols_per_row]
            cols  = st.columns(cols_per_row)
            for col, (fname, png_bytes, img, row, content) in zip(cols, chunk):
                with col:
                    st.image(img, width=160)
                    st.caption(f"**{row['part_no']}**  \n批次 {row['batch']}")
                    st.download_button(
                        label="⬇️ 下載",
                        data=png_bytes,
                        file_name=fname,
                        mime="image/png",
                        key=fname,         # 每個按鈕需要唯一 key
                    )

        # 打包成 ZIP 一次下載全部
        import zipfile
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for fname, png_bytes, *_ in results:
                zf.writestr(fname, png_bytes)
        zip_buf.seek(0)
        st.download_button(
            label=f"📦 下載全部 {len(results)} 張（ZIP）",
            data=zip_buf.getvalue(),
            file_name="qr_labels.zip",
            mime="application/zip",
        )

    with st.expander("💡 CSV 欄位說明"):
        st.markdown("""
| 欄位 | 說明 | 範例 |
|------|------|------|
| `part_no` | 料號 | M-BOLT-M8-316L |
| `description` | 品名 | Bolt M8x20 SUS316L |
| `qty` | 數量（整數） | 500 |
| `unit` | 單位 | PCS / KG / BOX / M |
| `batch` | 批次號 | B20240115 |
| `location` | 儲位 | A-01-02-03 |
| `supplier` | 供應商 | 台灣緊固件 |
| `inbound_date` | 入庫日期（YYYYMMDD） | 20240115 |
""")
```

<img width="1775" height="658" alt="image" src="https://github.com/user-attachments/assets/eaf803ab-a9c9-43f4-b289-3755b49bdd38" />
<img width="1753" height="734" alt="image" src="https://github.com/user-attachments/assets/5967c4d8-3cb3-4466-be39-642ad857c7cc" />
<img width="1755" height="813" alt="image" src="https://github.com/user-attachments/assets/98beac85-433c-4e66-a2e2-25e89762c0d6" />

### 練習 2：思考題

1. QR Code 使用 **JSON** 格式而非純文字的優缺點各是什麼？
2. 如果料件資訊非常多（例如 50 個欄位），應該把所有資訊存進 QR Code，還是只存「料號+批次」再讓系統去資料庫查詢？為什麼？
3. QR Code 和傳統**一維條碼（Barcode）**相比，在工廠應用上各有什麼優缺點？

---

## 📎 重點整理

```
qrcode 核心設定
├── error_correction  → 選 H（工廠髒污環境的必要設定）
├── box_size          → 每格像素數（越大解析度越高）
├── border            → 靜區寬度（標準最少 4 格）
└── version=None      → 自動選最小版本

工廠 QR Code 最佳實踐
├── 資料格式：JSON（易解析、易擴展）
├── 糾錯等級：H（30% 容錯，應對油污/刮傷）
├── 編碼內容：核心識別碼 + 系統連結（二擇一）
└── 標籤設計：QR Code + 人類可讀文字（雙保險）
```

---

*上一單元：[模組 1-1：Pillow](./Module1_1_Pillow.md) ｜ 下一單元：[模組 1-3：NumPy](./Module1_3_NumPy.md)*
