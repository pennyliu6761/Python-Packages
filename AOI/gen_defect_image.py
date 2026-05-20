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
'''
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
'''
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
#output_path = "defect_part.png"
output_path = "normal_part.png"
img.save(output_path, "PNG")
print(f"✅ 已儲存：{output_path}  ({W}×{H} px)")
