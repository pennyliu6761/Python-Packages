"""
aoi_app.py
===========
AOI 瑕疵零件自動檢測系統 — Streamlit UI 版

需求套件：
    pip install pillow numpy streamlit

執行方式：
    streamlit run aoi_app.py
"""

import os, math, random, json, io, time
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import streamlit as st

# ══════════════════════════════════════════════
# 頁面設定
# ══════════════════════════════════════════════
st.set_page_config(
    page_title="AOI 瑕疵檢測系統",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════
# 自訂 CSS（工業風深色主題）
# ══════════════════════════════════════════════
st.markdown("""
<style>
/* ── 全域字體與背景 ── */
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}
.stApp {
    background-color: #0e1117;
    color: #c9d1d9;
}

/* ── 側邊欄 ── */
[data-testid="stSidebar"] {
    background-color: #0d1117;
    border-right: 1px solid #21262d;
}
[data-testid="stSidebar"] .stMarkdown h1,
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 {
    color: #58a6ff;
}

/* ── 標題區塊 ── */
.aoi-header {
    background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
    border: 1px solid #21262d;
    border-left: 4px solid #58a6ff;
    border-radius: 8px;
    padding: 18px 24px;
    margin-bottom: 24px;
    font-family: 'IBM Plex Mono', monospace;
}
.aoi-header .sys-title {
    font-size: 22px;
    font-weight: 600;
    color: #e6edf3;
    letter-spacing: 2px;
    text-transform: uppercase;
}
.aoi-header .sys-sub {
    font-size: 11px;
    color: #58a6ff;
    letter-spacing: 4px;
    margin-top: 4px;
}

/* ── 指標卡片 ── */
.metric-card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 16px 20px;
    text-align: center;
    font-family: 'IBM Plex Mono', monospace;
}
.metric-card .label {
    font-size: 10px;
    letter-spacing: 3px;
    color: #8b949e;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.metric-card .value {
    font-size: 28px;
    font-weight: 600;
    color: #e6edf3;
}
.metric-card .unit {
    font-size: 12px;
    color: #58a6ff;
    margin-top: 4px;
}

/* ── 判定結果大字 ── */
.verdict-ok {
    background: #0d2818;
    border: 1px solid #238636;
    border-left: 5px solid #3fb950;
    border-radius: 8px;
    padding: 20px 28px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 28px;
    font-weight: 600;
    color: #3fb950;
    letter-spacing: 4px;
    text-align: center;
}
.verdict-ng {
    background: #2d0f10;
    border: 1px solid #6e1a1a;
    border-left: 5px solid #f85149;
    border-radius: 8px;
    padding: 20px 28px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 28px;
    font-weight: 600;
    color: #f85149;
    letter-spacing: 4px;
    text-align: center;
}

/* ── 特徵列 ── */
.feat-row {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 6px;
    padding: 10px 16px;
    margin-bottom: 8px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 13px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.feat-name { color: #8b949e; }
.feat-val  { color: #e6edf3; font-weight: 600; }
.feat-flag { color: #f85149; font-size: 11px; letter-spacing: 2px; }
.feat-ok   { color: #3fb950; font-size: 11px; letter-spacing: 2px; }

/* ── 進度條 ── */
.prog-wrap {
    background: #21262d;
    border-radius: 4px;
    height: 6px;
    margin-top: 6px;
    overflow: hidden;
}
.prog-bar {
    height: 6px;
    border-radius: 4px;
    transition: width 0.4s ease;
}

/* ── 圖片格線 ── */
.img-cell {
    border: 2px solid #21262d;
    border-radius: 6px;
    overflow: hidden;
    position: relative;
    cursor: pointer;
    transition: border-color 0.2s;
}
.img-cell:hover { border-color: #58a6ff; }
.img-cell.selected { border-color: #58a6ff; border-width: 2px; }
.img-label {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    background: rgba(13,17,23,0.85);
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    padding: 4px 6px;
    color: #8b949e;
}

/* ── section 標題 ── */
.section-head {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    letter-spacing: 4px;
    color: #58a6ff;
    text-transform: uppercase;
    border-bottom: 1px solid #21262d;
    padding-bottom: 8px;
    margin-bottom: 16px;
}

/* ── Streamlit 元件微調 ── */
div[data-testid="stButton"] button {
    background: #21262d;
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 6px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    letter-spacing: 1px;
    padding: 8px 20px;
    width: 100%;
}
div[data-testid="stButton"] button:hover {
    background: #30363d;
    border-color: #58a6ff;
    color: #58a6ff;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════
# 常數
# ══════════════════════════════════════════════
W_IMG, H_IMG = 640, 480
CX, CY  = 300, 235
R       = 165
HOLE_R  = 44
DATASET = "dataset"

# ══════════════════════════════════════════════
# 核心函式（來自 aoi_defect_detector.py）
# ══════════════════════════════════════════════

@st.cache_data
def build_mask():
    yy, xx = np.ogrid[:H_IMG, :W_IMG]
    return ((xx-CX)**2+(yy-CY)**2 <= (R-5)**2) & ~((xx-CX)**2+(yy-CY)**2 <= HOLE_R**2)

MASK = build_mask()


def radial_gradient(draw, cx, cy, r, c_in, c_out):
    for i in range(r, 0, -3):
        t = i / r
        c = tuple(int(c_in[j]*t + c_out[j]*(1-t)) for j in range(3))
        draw.ellipse([cx-i, cy-i, cx+i, cy+i], fill=c)


def build_base(seed=0):
    rng = random.Random(seed)
    np.random.seed(seed)
    img  = Image.new("RGB", (W_IMG, H_IMG), (16,12,9))
    draw = ImageDraw.Draw(img)
    for y in range(H_IMG):
        t = y/H_IMG
        draw.line([(0,y),(W_IMG,y)], fill=(int(10+8*t),int(8+6*t),int(6+4*t)))
    for x in range(0,W_IMG,32): draw.line([(x,0),(x,H_IMG)], fill=(20,16,11))
    for y in range(0,H_IMG,32): draw.line([(0,y),(W_IMG,y)], fill=(20,16,11))
    draw.ellipse([CX-R-5,CY-R-5,CX+R+5,CY+R+5], fill=(8,6,4))
    ci = (rng.randint(198,218),rng.randint(185,200),rng.randint(148,165))
    co = (rng.randint(58,72),rng.randint(48,60),rng.randint(32,45))
    radial_gradient(draw,CX,CY,R,ci,co)
    for i in range(48,0,-1):
        lum=min(228+i,248)
        draw.ellipse([CX-78-i//3,CY-90-i//3,CX-30+i//3,CY-42+i//3],
                     fill=(lum,int(lum*0.95),int(lum*0.82)))
    for r2 in range(R-4,12,-14):
        sh=(max(0,88-r2//3),max(0,75-r2//3),max(0,52-r2//3))
        draw.ellipse([CX-r2,CY-r2,CX+r2,CY+r2],outline=sh,width=1)
    arr=np.array(img)
    noise=np.random.randint(-16,17,(H_IMG,W_IMG,3))
    arr[MASK]=np.clip(arr[MASK].astype(int)+noise[MASK],0,255).astype(np.uint8)
    img=Image.fromarray(arr); draw=ImageDraw.Draw(img)
    for deg in [45,135,225,315]:
        a=math.radians(deg)
        bx,by=int(CX+108*math.cos(a)),int(CY+108*math.sin(a))
        radial_gradient(draw,bx,by,12,(185,168,125),(48,38,24))
        radial_gradient(draw,bx,by,9,(28,20,12),(10,7,4))
        draw.ellipse([bx-9,by-9,bx+9,by+9],outline=(52,42,26),width=1)
    radial_gradient(draw,CX,CY,42,(32,24,14),(10,7,4))
    draw.ellipse([CX-42,CY-42,CX+42,CY+42],outline=(58,46,28),width=2)
    draw.ellipse([CX-R,CY-R,CX+R,CY+R],outline=(85,72,48),width=2)
    return img


def add_rust(draw,rng,cx,cy,rx,ry):
    for i in range(rx,0,-1):
        t=1-i/rx; ry_i=max(1,int(ry*i/rx))
        draw.ellipse([cx-i,cy-ry_i,cx+i,cy+ry_i],fill=(int(180+28*t),int(72-22*t),int(16-6*t)))
    for _ in range(20):
        px=cx+int(rng.uniform(-rx*0.8,rx*0.8)); py=cy+int(rng.uniform(-ry*0.7,ry*0.7))
        pr=rng.randint(1,4)
        draw.ellipse([px-pr,py-pr,px+pr,py+pr],fill=(rng.randint(120,185),rng.randint(35,75),rng.randint(4,18)))

def add_crack(draw,rng,sx,sy):
    pts=[(sx,sy)]; x,y=sx,sy
    for _ in range(6):
        x+=rng.randint(6,12); y+=rng.randint(-6,8); pts.append((x,y))
    for i in range(len(pts)-1):
        x1,y1=pts[i]; x2,y2=pts[i+1]
        draw.line([(x1-1,y1),(x2-1,y2)],fill=(18,11,5),width=4)
        draw.line([(x1,y1),(x2,y2)],fill=(8,5,2),width=2)
        draw.line([(x1+1,y1-1),(x2+1,y2-1)],fill=(165,145,100),width=1)

def add_scratch(draw,rng,sx,sy):
    ang=rng.uniform(20,70)
    ex=sx+int(rng.randint(45,80)*math.cos(math.radians(ang)))
    ey=sy+int(rng.randint(45,80)*math.sin(math.radians(ang)))
    draw.line([(sx,sy),(ex,ey)],fill=(14,9,4),width=5)
    draw.line([(sx,sy),(ex,ey)],fill=(6,4,2),width=3)
    draw.line([(sx-1,sy-1),(ex-1,ey-1)],fill=(215,200,148),width=1)

def add_oil(draw,rng,cx,cy,rx,ry):
    for i in range(rx,0,-1):
        t=i/rx; ry_i=max(1,int(ry*i/rx))
        draw.ellipse([cx-i,cy-ry_i,cx+i,cy+ry_i],fill=(int(16+8*t),int(28+16*t),int(12+6*t)))
    for _ in range(5):
        px=cx+int(rng.uniform(-rx*0.5,rx*0.5)); py=cy+int(rng.uniform(-ry*0.4,ry*0.4))
        pr=rng.randint(2,5)
        draw.ellipse([px-pr,py-pr,px+pr,py+pr],fill=(rng.randint(18,42),rng.randint(52,78),rng.randint(36,55)))

DEFECT_DRAW = {
    "rust":    lambda draw,rng,ox,oy: add_rust(draw,rng,ox,oy,rng.randint(22,38),rng.randint(14,24)),
    "crack":   lambda draw,rng,ox,oy: add_crack(draw,rng,ox,oy),
    "scratch": lambda draw,rng,ox,oy: add_scratch(draw,rng,ox,oy),
    "oil":     lambda draw,rng,ox,oy: add_oil(draw,rng,ox,oy,rng.randint(20,34),rng.randint(12,20)),
}

DEFECT_ZH = {"rust":"生鏽","crack":"裂縫","scratch":"刮痕","oil":"油汙"}

def _valid_pos(rng):
    bolt_pos=[(int(CX+108*math.cos(math.radians(d))),int(CY+108*math.sin(math.radians(d)))) for d in [45,135,225,315]]
    for _ in range(50):
        ang=rng.uniform(0,2*math.pi); dist=rng.uniform(55,R-35)
        ox,oy=int(CX+dist*math.cos(ang)),int(CY+dist*math.sin(ang))
        if (ox-CX)**2+(oy-CY)**2<55**2: continue
        if any((ox-bx)**2+(oy-by)**2<22**2 for bx,by in bolt_pos): continue
        return ox,oy
    return CX+80,CY+60


def generate_dataset(n_each=10):
    os.makedirs(DATASET, exist_ok=True)
    records = []
    for i in range(n_each):
        img=build_base(seed=i)
        path=os.path.join(DATASET,f"normal_{i:02d}.png")
        img.save(path)
        records.append({"path":path,"label":"OK","defects":[]})
    for i in range(n_each):
        rng=random.Random(i+100); img=build_base(seed=i+100)
        draw=ImageDraw.Draw(img)
        types=rng.sample(list(DEFECT_DRAW.keys()),k=rng.randint(1,2))
        applied=[]
        for dtype in types:
            ox,oy=_valid_pos(rng)
            DEFECT_DRAW[dtype](draw,rng,ox,oy); applied.append(dtype)
        path=os.path.join(DATASET,f"defect_{i:02d}.png")
        img.save(path)
        records.append({"path":path,"label":"NG","defects":applied})
    return records


def build_template(records):
    normal_paths=[r["path"] for r in records if r["label"]=="OK"]
    stack=np.stack([np.array(Image.open(p),dtype=np.float32) for p in normal_paths])
    template=stack.mean(axis=0)
    # compute thresholds from normal imgs
    scores_mean,scores_hot=[],[]
    for p in normal_paths:
        arr=np.array(Image.open(p),dtype=np.float32)
        diff=np.abs(arr-template).mean(axis=2)
        scores_mean.append(diff[MASK].mean())
        scores_hot.append((diff[MASK]>30).sum()/MASK.sum())
    thr_mean=float(np.mean(scores_mean)+3*np.std(scores_mean))
    thr_hot =float(np.mean(scores_hot) +3*np.std(scores_hot)+1e-6)
    return template,{"thr_mean_diff":round(thr_mean,4),"thr_hot_frac":round(thr_hot,6)}


def detect_image(img: Image.Image, template, thresholds):
    arr=np.array(img.convert("RGB"),dtype=np.float32)
    diff=np.abs(arr-template).mean(axis=2)
    mean_diff=float(diff[MASK].mean())
    hot_frac =float((diff[MASK]>30).sum()/MASK.sum())
    features={"mean_diff":round(mean_diff,4),"hot_frac":round(hot_frac,6)}
    flags={"mean_diff":mean_diff>thresholds["thr_mean_diff"],
           "hot_frac": hot_frac >thresholds["thr_hot_frac"]}
    verdict="NG" if any(flags.values()) else "OK"
    # diff heatmap (normalise to 0-255)
    diff_vis=np.clip(diff*4,0,255).astype(np.uint8)
    diff_rgb=np.zeros((H_IMG,W_IMG,3),dtype=np.uint8)
    diff_rgb[:,:,0]=diff_vis          # R channel = hot
    diff_rgb[:,:,2]=255-diff_vis      # B channel = cold
    heatmap=Image.fromarray(diff_rgb)
    # blend with original
    overlay=Image.blend(img.convert("RGB"), heatmap, alpha=0.45)
    return verdict,features,flags,overlay


# ══════════════════════════════════════════════
# Session State 初始化
# ══════════════════════════════════════════════
if "records"   not in st.session_state: st.session_state.records   = []
if "template"  not in st.session_state: st.session_state.template  = None
if "thresholds"not in st.session_state: st.session_state.thresholds= None
if "selected"  not in st.session_state: st.session_state.selected  = None
if "result"    not in st.session_state: st.session_state.result    = None


# ══════════════════════════════════════════════
# 側邊欄
# ══════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 🏭 系統控制台")
    st.markdown("---")

    # Step 1
    st.markdown("**① 資料集**")
    n_each = st.slider("每類張數", 5, 20, 10, key="n_each")
    if st.button("⚙ 產生資料集 + 建立樣板"):
        with st.spinner("產生圖片中..."):
            records = generate_dataset(n_each=n_each)
            template, thresholds = build_template(records)
            st.session_state.records    = records
            st.session_state.template   = template
            st.session_state.thresholds = thresholds
            st.session_state.selected   = None
            st.session_state.result     = None
        st.success(f"完成！共 {n_each*2} 張圖片")

    st.markdown("---")

    # Step 2
    st.markdown("**② 上傳自訂圖片**")
    uploaded = st.file_uploader("選擇 PNG / JPG", type=["png","jpg","jpeg"])
    if uploaded and st.session_state.template is not None:
        img = Image.open(uploaded).resize((W_IMG, H_IMG))
        verdict, features, flags, overlay = detect_image(img, st.session_state.template, st.session_state.thresholds)
        st.session_state.selected = {"img":img,"name":uploaded.name,"label":None}
        st.session_state.result   = (verdict,features,flags,overlay)

    st.markdown("---")

    # 統計摘要
    if st.session_state.records:
        total = len(st.session_state.records)
        ok_n  = sum(1 for r in st.session_state.records if r["label"]=="OK")
        ng_n  = total - ok_n
        st.markdown("**資料集摘要**")
        st.markdown(f"""
<div class='metric-card' style='margin-bottom:8px'>
  <div class='label'>TOTAL</div>
  <div class='value'>{total}</div>
  <div class='unit'>張圖片</div>
</div>
<div style='display:flex;gap:8px'>
  <div class='metric-card' style='flex:1'>
    <div class='label'>OK</div>
    <div class='value' style='color:#3fb950'>{ok_n}</div>
  </div>
  <div class='metric-card' style='flex:1'>
    <div class='label'>NG</div>
    <div class='value' style='color:#f85149'>{ng_n}</div>
  </div>
</div>
""", unsafe_allow_html=True)

        st.markdown("")
        thr = st.session_state.thresholds
        st.markdown(f"""
**自動計算閾值**
```
mean_diff  ≤ {thr['thr_mean_diff']:.4f}
hot_frac   ≤ {thr['thr_hot_frac']:.6f}
```
""")


# ══════════════════════════════════════════════
# 主頁面
# ══════════════════════════════════════════════

# 頁首
st.markdown("""
<div class='aoi-header'>
  <div class='sys-title'>🔬 AOI 瑕疵自動檢測系統</div>
  <div class='sys-sub'>Automated Optical Inspection · Golden Template Method · IEM Vision Lab</div>
</div>
""", unsafe_allow_html=True)

if not st.session_state.records:
    # 尚未產生資料集 — 說明畫面
    st.info("👈 請先在左側點擊「產生資料集 + 建立樣板」開始使用")
    c1, c2, c3 = st.columns(3)
    for col, icon, title, desc in [
        (c1,"⚙","Step 1：產生資料集","自動生成 10 張正常零件圖與 10 張含生鏽、裂縫、刮痕、油汙的瑕疵圖"),
        (c2,"📐","Step 2：建立黃金樣板","從正常圖取像素平均，自動計算 mean+3σ 判定閾值"),
        (c3,"🎯","Step 3：點選或上傳圖片","計算差異熱力圖，輸出 OK / NG 判定結果與特徵數值"),
    ]:
        col.markdown(f"""
<div class='metric-card' style='text-align:left;padding:20px'>
  <div style='font-size:28px;margin-bottom:12px'>{icon}</div>
  <div style='font-size:14px;font-weight:600;color:#e6edf3;margin-bottom:8px'>{title}</div>
  <div style='font-size:13px;color:#8b949e;line-height:1.6'>{desc}</div>
</div>
""", unsafe_allow_html=True)
    st.stop()


# ── 圖片選擇格線 ─────────────────────────────
st.markdown("<div class='section-head'>選擇圖片</div>", unsafe_allow_html=True)

records = st.session_state.records
cols_per_row = 5
rows = [records[i:i+cols_per_row] for i in range(0, len(records), cols_per_row)]

for row in rows:
    cols = st.columns(cols_per_row)
    for col, rec in zip(cols, row):
        with col:
            thumb = Image.open(rec["path"]).resize((160,120))
            is_sel = (st.session_state.selected is not None and
                      st.session_state.selected.get("path") == rec["path"])

            border = "2px solid #58a6ff" if is_sel else "2px solid #21262d"
            label_color = "#3fb950" if rec["label"]=="OK" else "#f85149"
            defect_str  = " / ".join(DEFECT_ZH.get(d,d) for d in rec["defects"]) if rec["defects"] else "—"

            st.image(thumb, use_container_width=True)
            name = os.path.basename(rec["path"])
            st.markdown(f"""
<div style='font-family:IBM Plex Mono,monospace;font-size:10px;text-align:center;margin-top:-8px;margin-bottom:4px'>
  <span style='color:{label_color};font-weight:600'>{rec["label"]}</span>
  <span style='color:#8b949e'> · {name}</span>
</div>
""", unsafe_allow_html=True)
            if st.button("選取", key=f"sel_{rec['path']}"):
                img = Image.open(rec["path"])
                verdict, features, flags, overlay = detect_image(
                    img, st.session_state.template, st.session_state.thresholds)
                st.session_state.selected = {"img":img,"path":rec["path"],"name":name,"label":rec["label"]}
                st.session_state.result   = (verdict,features,flags,overlay)
                st.rerun()


# ── 檢測結果 ─────────────────────────────────
if st.session_state.result:
    st.markdown("---")
    st.markdown("<div class='section-head'>檢測結果</div>", unsafe_allow_html=True)

    verdict, features, flags, overlay = st.session_state.result
    sel = st.session_state.selected

    left, right = st.columns([1.1, 0.9])

    with left:
        # 原圖 + 差異熱力圖
        tab1, tab2 = st.tabs(["📷 原始影像", "🌡 差異熱力圖"])
        with tab1:
            st.image(sel["img"], use_container_width=True)
        with tab2:
            st.image(overlay, use_container_width=True)
            st.caption("紅色 = 與黃金樣板差異大（疑似瑕疵區域），藍色 = 正常區域")

    with right:
        # 判定結果
        label = sel.get("label")
        correct_str = ""
        if label:
            correct_str = " ✓ 正確" if label==verdict else " ✗ 誤判"

        verdict_cls = "verdict-ok" if verdict=="OK" else "verdict-ng"
        verdict_txt = "✓  OK  正常品" if verdict=="OK" else "✕  NG  瑕疵品"
        st.markdown(f"""
<div class='{verdict_cls}'>
  {verdict_txt}
  <div style='font-size:14px;margin-top:8px;letter-spacing:2px'>{sel['name']}{correct_str}</div>
</div>
""", unsafe_allow_html=True)

        st.markdown("")

        # 特徵明細
        st.markdown("<div class='section-head' style='font-size:10px'>特徵明細</div>", unsafe_allow_html=True)

        thr = st.session_state.thresholds
        feat_info = [
            ("均差 mean_diff", features["mean_diff"], thr["thr_mean_diff"], flags["mean_diff"]),
            ("熱點比例 hot_frac", features["hot_frac"],  thr["thr_hot_frac"],  flags["hot_frac"]),
        ]
        for fname, fval, fthr, flag in feat_info:
            flag_html = "<span class='feat-flag'>● ABNORMAL</span>" if flag else "<span class='feat-ok'>● NORMAL</span>"
            ratio = min(fval/fthr, 2.0) if fthr > 0 else 0
            bar_w  = min(int(ratio*50), 100)
            bar_col= "#f85149" if flag else "#3fb950"
            st.markdown(f"""
<div class='feat-row'>
  <span class='feat-name'>{fname}</span>
  <span>
    <span class='feat-val'>{fval:.5f}</span>
    <span style='color:#8b949e;font-size:11px'> / {fthr:.5f}</span>
  </span>
  {flag_html}
</div>
<div class='prog-wrap'>
  <div class='prog-bar' style='width:{bar_w}%;background:{bar_col}'></div>
</div>
""", unsafe_allow_html=True)

        # 真實標籤（如有）
        if label:
            st.markdown("")
            match = label == verdict
            color = "#3fb950" if match else "#f85149"
            icon  = "✓" if match else "✗"
            st.markdown(f"""
<div style='font-family:IBM Plex Mono,monospace;font-size:12px;
     border:1px solid #21262d;border-radius:6px;padding:10px 16px;
     background:#161b22;margin-top:8px'>
  <span style='color:#8b949e'>真實標籤：</span>
  <span style='color:{"#3fb950" if label=="OK" else "#f85149"};font-weight:600'>{label}</span>
  　
  <span style='color:#8b949e'>判定：</span>
  <span style='color:{"#3fb950" if verdict=="OK" else "#f85149"};font-weight:600'>{verdict}</span>
  　
  <span style='color:{color};font-weight:600'>{icon} {"正確" if match else "誤判"}</span>
</div>
""", unsafe_allow_html=True)


# ── 批次績效統計 ────────────────────────────
if st.session_state.records and st.session_state.template is not None:
    st.markdown("---")
    st.markdown("<div class='section-head'>批次績效統計</div>", unsafe_allow_html=True)

    if st.button("▶ 執行全部批次檢測"):
        results = []
        prog = st.progress(0)
        for i, rec in enumerate(st.session_state.records):
            img = Image.open(rec["path"])
            verdict, features, flags, _ = detect_image(img, st.session_state.template, st.session_state.thresholds)
            results.append({"name": os.path.basename(rec["path"]),
                             "true":rec["label"], "pred":verdict,
                             "mean_diff":features["mean_diff"], "hot_frac":features["hot_frac"]})
            prog.progress((i+1)/len(st.session_state.records))
        st.session_state["batch_results"] = results

    if "batch_results" in st.session_state:
        results = st.session_state["batch_results"]
        tp=sum(1 for r in results if r["true"]=="NG" and r["pred"]=="NG")
        tn=sum(1 for r in results if r["true"]=="OK" and r["pred"]=="OK")
        fp=sum(1 for r in results if r["true"]=="OK" and r["pred"]=="NG")
        fn=sum(1 for r in results if r["true"]=="NG" and r["pred"]=="OK")
        total=len(results)
        acc  = (tp+tn)/total*100
        prec = tp/(tp+fp)*100 if (tp+fp)>0 else 0
        rec_ = tp/(tp+fn)*100 if (tp+fn)>0 else 0
        f1   = 2*prec*rec_/(prec+rec_) if (prec+rec_)>0 else 0

        m1,m2,m3,m4 = st.columns(4)
        for col,label,val,unit in [
            (m1,"正確率",acc,"%"),
            (m2,"精確率",prec,"%"),
            (m3,"召回率",rec_,"%"),
            (m4,"F1 分數",f1,"%"),
        ]:
            col.markdown(f"""
<div class='metric-card'>
  <div class='label'>{label}</div>
  <div class='value' style='color:{"#3fb950" if val>=90 else "#f0a03a"}'>{val:.1f}</div>
  <div class='unit'>{unit}</div>
</div>
""", unsafe_allow_html=True)

        st.markdown("")
        # 混淆矩陣
        c1,c2 = st.columns([1,2])
        with c1:
            st.markdown(f"""
<div style='font-family:IBM Plex Mono,monospace;font-size:12px;
     border:1px solid #21262d;border-radius:8px;padding:16px;background:#161b22;text-align:center'>
  <div style='color:#8b949e;letter-spacing:3px;font-size:10px;margin-bottom:12px'>CONFUSION MATRIX</div>
  <table style='width:100%;border-collapse:collapse'>
    <tr>
      <td></td>
      <td style='color:#8b949e;font-size:10px;padding:4px'>預測 OK</td>
      <td style='color:#8b949e;font-size:10px;padding:4px'>預測 NG</td>
    </tr>
    <tr>
      <td style='color:#8b949e;font-size:10px;padding:4px'>真實 OK</td>
      <td style='background:#0d2818;color:#3fb950;font-size:20px;padding:12px;border-radius:4px'>{tn}</td>
      <td style='background:#2d0f10;color:#f85149;font-size:20px;padding:12px;border-radius:4px'>{fp}</td>
    </tr>
    <tr>
      <td style='color:#8b949e;font-size:10px;padding:4px'>真實 NG</td>
      <td style='background:#2d0f10;color:#f85149;font-size:20px;padding:12px;border-radius:4px'>{fn}</td>
      <td style='background:#0d2818;color:#3fb950;font-size:20px;padding:12px;border-radius:4px'>{tp}</td>
    </tr>
  </table>
</div>
""", unsafe_allow_html=True)

        with c2:
            # 逐張結果表格
            import pandas as pd
            df = pd.DataFrame([{
                "圖片":r["name"],
                "真實":r["true"],
                "判定":r["pred"],
                "正誤":"✓" if r["true"]==r["pred"] else "✗",
                "mean_diff":r["mean_diff"],
                "hot_frac":r["hot_frac"],
            } for r in results])
            st.dataframe(df, use_container_width=True, height=300)
