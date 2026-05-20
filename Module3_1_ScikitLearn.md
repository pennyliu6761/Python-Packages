# 模組 3-1：Scikit-Learn — K-Means 供應商/顧客分群模擬

> **學習目標**：理解非監督式機器學習的核心概念，實作 K-Means 分群並以視覺化方式展示市場區隔的應用。

---

## 📌 為什麼工管系要學機器學習？

機器學習不只是 AI 工程師的工具，工業工程師可以用它來：
- **供應商分群**：依採購頻率與訂單金額評鑑供應商，制定差異化管理策略
- **客戶區隔（Market Segmentation）**：找出 A、B、C 類客戶，分配業務資源
- **異常偵測**：找出與群體行為明顯偏離的機台（預測性維保）
- **製程分類**：判斷當下的製程狀態屬於哪一種已知的「模式」

---

## 🔧 安裝

```bash
pip install scikit-learn matplotlib numpy pandas streamlit
```

---

## 一、機器學習基礎概念

```
監督式學習（Supervised Learning）
├── 有標籤資料（已知答案）
├── 分類（Classification）：判斷是/否、好/壞品
└── 迴歸（Regression）：預測數值（良率、設備壽命）

非監督式學習（Unsupervised Learning）
├── 無標籤資料（不知道答案，自己找規律）
├── 分群（Clustering）：K-Means、DBSCAN
└── 降維（Dimensionality Reduction）：PCA、t-SNE

本單元重點：K-Means 分群
├── 輸入：n 個數據點（如供應商的「採購頻率」和「訂單金額」）
├── 參數：K = 要分成幾群
└── 輸出：每個數據點的群組標籤 + 各群的中心點
```

---

## 二、K-Means 演算法原理

```
K-Means 執行步驟：
─────────────────────────────────────────
Step 1：隨機初始化 K 個「群心（Centroid）」
Step 2：計算每個點到各群心的距離，指定到最近的群心（形成 K 群）
Step 3：更新群心 = 各群內所有點的平均位置
Step 4：重複 Step 2~3，直到群心不再移動（收斂）

關鍵假設：
- 每個群的形狀接近「球形（圓形）」
- 資料需要先做「特徵標準化」，否則量綱不同的特徵會主導距離計算
─────────────────────────────────────────
```

---

## 三、特徵標準化（Feature Scaling）

```python
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler

# ===== 為什麼需要標準化？=====
# 假設供應商資料有兩個特徵：
# 採購頻率（次/月）：範圍 1~30
# 平均訂單金額（萬元）：範圍 50~5000

# 若不標準化，「訂單金額」的數值尺度遠大於「頻率」
# 距離計算會被金額主導，頻率幾乎沒有影響！

raw_data = np.array([
    [5,   100],   # 供應商 A
    [20, 3000],   # 供應商 B
    [10,  500],   # 供應商 C
])

# ===== StandardScaler：Z-score 標準化（均值0，標準差1）=====
# 適合：資料呈常態分配時
scaler_std = StandardScaler()
data_std   = scaler_std.fit_transform(raw_data)
print("StandardScaler 後：")
print(data_std.round(3))
print(f"  均值：{data_std.mean(axis=0).round(3)}")   # 應接近 [0, 0]
print(f"  標準差：{data_std.std(axis=0).round(3)}")  # 應接近 [1, 1]

# ===== MinMaxScaler：Min-Max 正規化（壓縮到 0~1）=====
# 適合：資料分佈不確定，或需要保留 0 的意義時
scaler_mm = MinMaxScaler()
data_mm   = scaler_mm.fit_transform(raw_data)
print("\nMinMaxScaler 後：")
print(data_mm.round(3))

# ===== 重要：fit 和 transform 的分別 =====
# fit()       → 「學習」訓練資料的均值和標準差（只對訓練集做！）
# transform() → 「應用」學到的參數進行縮放
# fit_transform() = fit() + transform() 合一（訓練集用）

# 新資料（測試集）只能 transform()，不能重新 fit()！
new_supplier = np.array([[8, 800]])
new_scaled   = scaler_std.transform(new_supplier)  # 只用 transform！
print(f"\n新供應商標準化後：{new_scaled.round(3)}")
```

---

## 四、K-Means 分群實作

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

plt.rcParams['font.family'] = ['Microsoft JhengHei', 'PingFang TC', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# ============================================================
# 第一步：生成模擬供應商資料
# ============================================================
np.random.seed(42)

# 模擬三種供應商的採購行為（三個天然群體）
# 群 1：頻繁小額（60 家）→ 小型零件供應商
freq_small = np.random.multivariate_normal(
    mean=[25, 80],           # 平均 25 次/月，80 萬/單
    cov=[[16, 0], [0, 400]], # 變異數：頻率較集中，金額略有分散
    size=60
)

# 群 2：中頻中額（50 家）→ 一般零組件供應商
freq_medium = np.random.multivariate_normal(
    mean=[12, 500],
    cov=[[9, 100], [100, 10000]],
    size=50
)

# 群 3：低頻大額（30 家）→ 關鍵原材料供應商
freq_large = np.random.multivariate_normal(
    mean=[3, 2500],
    cov=[[1, 0], [0, 250000]],
    size=30
)

# 合併並建立 DataFrame
all_data = np.vstack([freq_small, freq_medium, freq_large])
all_data = np.clip(all_data, [0, 0], [50, 5000])  # 限制在合理範圍

df = pd.DataFrame(all_data, columns=['採購頻率（次/月）', '平均訂單金額（萬元）'])
df.index.name = '供應商ID'
print(f"供應商總數：{len(df)}")
print(df.describe().round(1))

# ============================================================
# 第二步：特徵標準化
# ============================================================
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df)

# ============================================================
# 第三步：決定最佳 K 值（手肘法）
# ============================================================
inertias = []
K_range  = range(1, 11)

for k in K_range:
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    km.fit(X_scaled)
    inertias.append(km.inertia_)   # inertia = 各點到群心的距離平方和

fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(K_range, inertias, 'bD-', markersize=8)
ax.set_title('手肘法（Elbow Method）：選擇最佳 K 值', fontsize=13)
ax.set_xlabel('K（分群數）')
ax.set_ylabel('Inertia（群內距離平方和）')
ax.axvline(3, color='red', linestyle='--', alpha=0.7, label='建議 K=3（手肘點）')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('elbow.png', dpi=150)
plt.show()
print("💡 手肘點（Elbow Point）：曲線斜率突然變緩的地方，即最佳 K 值")

# ============================================================
# 第四步：執行 K-Means 分群（K=3）
# ============================================================
K = 3
kmeans = KMeans(
    n_clusters  = K,
    random_state= 42,   # 固定種子，結果可重現
    n_init      = 10,   # 重複執行 10 次，取最佳結果（避免局部最優）
    max_iter    = 300   # 最大迭代次數
)
kmeans.fit(X_scaled)

# 取得結果
df['群組']  = kmeans.labels_           # 每個供應商的群組標籤（0, 1, 2）
df['群組名稱'] = ''

# 根據群組特徵命名（業務意義的詮釋）
# 先找各群的中心點（反標準化回原始尺度）
centers_original = scaler.inverse_transform(kmeans.cluster_centers_)
print("\n各群心的原始特徵值：")
for i, center in enumerate(centers_original):
    print(f"  群 {i}：採購頻率={center[0]:.1f} 次/月，訂單金額={center[1]:.1f} 萬元")

# 手動標記群組名稱（根據中心點特徵判斷）
label_map = {}
sorted_by_freq = np.argsort(centers_original[:, 0])[::-1]  # 依頻率由高到低排序
cluster_names  = ['頻繁小額型', '中頻中額型', '低頻大額型']
for rank, cluster_id in enumerate(sorted_by_freq):
    label_map[cluster_id] = cluster_names[rank]

df['群組名稱'] = df['群組'].map(label_map)

print("\n各群供應商數量：")
print(df['群組名稱'].value_counts())

# ============================================================
# 第五步：視覺化分群結果
# ============================================================
colors  = ['#e74c3c', '#3498db', '#2ecc71']
markers = ['o', 's', '^']

fig, ax = plt.subplots(figsize=(11, 8))

for i, name in enumerate(cluster_names):
    mask = df['群組名稱'] == name
    ax.scatter(
        df.loc[mask, '採購頻率（次/月）'],
        df.loc[mask, '平均訂單金額（萬元）'],
        c=colors[i], marker=markers[i], s=60, alpha=0.7,
        label=f'{name}（{mask.sum()} 家）', edgecolors='white', linewidth=0.5
    )

# 繪製群心
for i, (center, name) in enumerate(zip(centers_original, cluster_names)):
    cluster_id = [k for k, v in label_map.items() if v == name][0]
    ax.scatter(
        centers_original[cluster_id, 0],
        centers_original[cluster_id, 1],
        c=colors[i], s=400, marker='*',
        edgecolors='black', linewidth=2, zorder=5
    )
    ax.annotate(f'中心\n({centers_original[cluster_id, 0]:.0f}, {centers_original[cluster_id, 1]:.0f})',
                xy=(centers_original[cluster_id, 0], centers_original[cluster_id, 1]),
                xytext=(10, 10), textcoords='offset points',
                fontsize=9, color=colors[i])

ax.set_title('供應商 K-Means 分群（K=3）', fontsize=15, fontweight='bold')
ax.set_xlabel('採購頻率（次/月）', fontsize=13)
ax.set_ylabel('平均訂單金額（萬元）', fontsize=13)
ax.legend(fontsize=11, loc='upper right')
ax.grid(True, alpha=0.25, linestyle=':')
plt.tight_layout()
plt.savefig('kmeans_clusters.png', dpi=150, bbox_inches='tight')
plt.show()
print("✅ 分群結果已儲存！")
```

---

## 五、分群品質評估

```python
from sklearn.metrics import silhouette_score, calinski_harabasz_score
import numpy as np

# ===== 輪廓係數（Silhouette Score）=====
# 衡量「群內緊密度」與「群間分離度」的綜合指標
# 範圍 -1 到 1，越接近 1 代表分群越好

sil_score = silhouette_score(X_scaled, kmeans.labels_)
print(f"輪廓係數（Silhouette Score）：{sil_score:.3f}")
print("解讀：> 0.5 良好；> 0.7 優秀；< 0.25 可能分群不合適")

# ===== 比較不同 K 值的輪廓係數 =====
sil_scores = []
for k in range(2, 9):
    km_temp = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels  = km_temp.fit_predict(X_scaled)
    sil     = silhouette_score(X_scaled, labels)
    sil_scores.append((k, sil))
    print(f"  K={k}：輪廓係數 = {sil:.3f}")

best_k = max(sil_scores, key=lambda x: x[1])
print(f"\n最佳 K 值：{best_k[0]}（輪廓係數 = {best_k[1]:.3f}）")

# ===== Calinski-Harabasz 指數（CH 指數）=====
# 群間變異 / 群內變異的比值，越大越好
ch_score = calinski_harabasz_score(X_scaled, kmeans.labels_)
print(f"\nCH 指數：{ch_score:.1f}")
```

---

## 六、🖥️ Streamlit 應用：分群互動儀表板

```python
# 檔案名稱：app_kmeans.py
# 執行方式：streamlit run app_kmeans.py

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

plt.rcParams['font.family'] = ['Microsoft JhengHei', 'PingFang TC', 'sans-serif']

st.set_page_config(page_title="供應商分群分析", page_icon="🔬", layout="wide")
st.title("🔬 K-Means 供應商分群分析儀表板")
st.markdown("調整分群數 K，觀察分群結果的變化，找出最佳市場區隔。")

# ===== 生成資料（或上傳）=====
@st.cache_data  # 快取：避免每次互動都重新生成資料
def generate_data(seed=42):
    np.random.seed(seed)
    g1 = np.random.multivariate_normal([25, 80],   [[16, 0], [0, 400]],   60)
    g2 = np.random.multivariate_normal([12, 500],  [[9, 100], [100, 10000]], 50)
    g3 = np.random.multivariate_normal([3, 2500],  [[1, 0], [0, 250000]], 30)
    data = np.clip(np.vstack([g1, g2, g3]), [0, 0], [50, 5000])
    return pd.DataFrame(data, columns=['採購頻率（次/月）', '平均訂單金額（萬元）'])

df = generate_data()
scaler  = StandardScaler()
X_scaled = scaler.fit_transform(df)

# ===== 側邊欄 =====
with st.sidebar:
    st.header("⚙️ 參數設定")
    K = st.slider("分群數 K", 2, 8, 3)
    show_centers = st.checkbox("顯示群心（⭐）", value=True)
    show_elbow   = st.checkbox("顯示手肘法圖", value=True)

    st.divider()
    st.header("💡 商業策略建議")
    st.markdown("""
    **K=3 的分群策略建議：**
    - 🔴 **頻繁小額**：自動化採購、長期框架合約
    - 🔵 **中頻中額**：定期供應商稽核、穩定合作
    - 🟢 **低頻大額**：高層關係維護、備貨策略
    """)

# ===== 執行 K-Means =====
kmeans = KMeans(n_clusters=K, random_state=42, n_init=10)
labels  = kmeans.fit_predict(X_scaled)
df['群組'] = labels

sil = silhouette_score(X_scaled, labels)
centers = scaler.inverse_transform(kmeans.cluster_centers_)

# ===== KPI 卡片 =====
col1, col2, col3 = st.columns(3)
col1.metric("供應商總數", len(df))
col2.metric("分群數 K", K)
col3.metric("輪廓係數", f"{sil:.3f}",
            delta="分群品質良好" if sil > 0.5 else "分群品質一般")

col_a, col_b = st.columns([2, 1])

with col_a:
    # ===== 分群散佈圖 =====
    st.subheader(f"📊 分群結果（K={K}）")
    cmap = plt.cm.get_cmap('tab10', K)

    fig, ax = plt.subplots(figsize=(8, 6))
    for k in range(K):
        mask = df['群組'] == k
        ax.scatter(df.loc[mask, '採購頻率（次/月）'],
                   df.loc[mask, '平均訂單金額（萬元）'],
                   color=cmap(k), s=50, alpha=0.7, label=f'群組 {k+1}（{mask.sum()} 家）',
                   edgecolors='white', linewidth=0.5)
        if show_centers:
            ax.scatter(centers[k, 0], centers[k, 1],
                       color=cmap(k), s=350, marker='*',
                       edgecolors='black', linewidth=1.5, zorder=6)

    ax.set_xlabel('採購頻率（次/月）', fontsize=12)
    ax.set_ylabel('平均訂單金額（萬元）', fontsize=12)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.25, linestyle=':')
    st.pyplot(fig)

with col_b:
    # ===== 各群統計 =====
    st.subheader("📋 各群特徵摘要")
    for k in range(K):
        mask = df['群組'] == k
        st.markdown(f"**群組 {k+1}**（{mask.sum()} 家）")
        st.markdown(f"- 平均頻率：{df.loc[mask, '採購頻率（次/月）'].mean():.1f} 次/月")
        st.markdown(f"- 平均金額：{df.loc[mask, '平均訂單金額（萬元）'].mean():.0f} 萬元")
        st.divider()

# ===== 手肘法圖 =====
if show_elbow:
    st.subheader("🔍 手肘法：選擇最佳 K")
    inertias = []
    sil_vals = []
    k_range = range(2, 9)
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        lb = km.fit_predict(X_scaled)
        inertias.append(km.inertia_)
        sil_vals.append(silhouette_score(X_scaled, lb))

    fig2, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    ax1.plot(k_range, inertias, 'bD-', markersize=7)
    ax1.axvline(K, color='red', linestyle='--', alpha=0.7, label=f'當前 K={K}')
    ax1.set_title('Inertia（越小越好）')
    ax1.set_xlabel('K'); ax1.legend(); ax1.grid(True, alpha=0.3)

    ax2.plot(k_range, sil_vals, 'rs-', markersize=7)
    ax2.axvline(K, color='blue', linestyle='--', alpha=0.7, label=f'當前 K={K}')
    ax2.set_title('輪廓係數（越大越好）')
    ax2.set_xlabel('K'); ax2.legend(); ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    st.pyplot(fig2)
```

---

## 七、延伸：監督式學習快速預覽

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import numpy as np

# ===== 情境：用機台感測器數據，預測產品是否為不良品 =====
# 特徵（X）：溫度、轉速、振動值、電流
# 標籤（y）：0=良品，1=不良品

np.random.seed(42)
n = 500

# 生成模擬感測器數據
X = np.column_stack([
    np.random.normal(200, 10, n),   # 溫度（°C）
    np.random.normal(1500, 50, n),  # 轉速（RPM）
    np.random.normal(0.5,  0.1, n), # 振動（mm/s）
    np.random.normal(5.0,  0.5, n), # 電流（A）
])

# 模擬規則：溫度>215 或 振動>0.7 → 不良品
y = ((X[:, 0] > 215) | (X[:, 2] > 0.7)).astype(int)
print(f"不良品比例：{y.mean():.1%}")

# ===== 訓練與評估 =====
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y  # stratify 確保訓練/測試集比例一致
)

rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)

y_pred = rf.predict(X_test)
print(f"\n測試集準確率：{accuracy_score(y_test, y_pred):.3f}")
print(classification_report(y_test, y_pred, target_names=['良品', '不良品']))

# ===== 特徵重要性（哪個感測器最關鍵？）=====
feature_names = ['溫度', '轉速', '振動', '電流']
importances   = rf.feature_importances_
for name, imp in sorted(zip(feature_names, importances), key=lambda x: -x[1]):
    print(f"  {name}：{imp:.3f} {'█' * int(imp * 30)}")
```

---

## 八、課後練習

### 練習 1：RFM 客戶分群

```python
import numpy as np
import pandas as pd

# RFM 分析是電商與製造業客戶管理的經典模型
# R = Recency    （最近購買距今幾天，越小越好）
# F = Frequency  （過去 6 個月購買次數，越大越好）
# M = Monetary   （過去 6 個月消費金額，越大越好）

np.random.seed(0)
n_customers = 200
rfm_data = pd.DataFrame({
    '客戶ID':     range(1, n_customers + 1),
    'Recency':   np.random.randint(1, 365, n_customers),
    'Frequency': np.random.randint(1, 50, n_customers),
    'Monetary':  np.random.exponential(10000, n_customers).round(0)
})

# 請你：
# 1. 對 RFM 三個特徵做 StandardScaler 標準化
# 2. 注意 Recency 的意義相反（越小越好），標準化後需要取負值或反轉
# 3. 用手肘法找最佳 K（建議試試 K=4，對應黃金/白銀/銅/休眠客戶）
# 4. 繪製 3D 散佈圖（from mpl_toolkits.mplot3d import Axes3D）
```

### 練習 2：思考題

1. K-Means 的分群結果每次執行可能不同，為什麼？設定 `random_state` 有什麼作用？
2. K-Means 在哪些情況下**表現不佳**？（提示：考慮群的形狀、密度不均、離群值）
3. 「頻繁小額供應商」和「低頻大額供應商」在**採購風險管理**上，各有什麼不同的特點？

---

## 📎 重點整理

```
Scikit-Learn 的 API 設計原則（非常一致！）
├── scaler.fit(X_train)      → 學習訓練集的統計量
├── scaler.transform(X)      → 套用轉換
├── model.fit(X, y)          → 訓練模型
├── model.predict(X)         → 預測
└── model.score(X, y)        → 評估準確率

K-Means 分群流程
├── 1. 標準化（StandardScaler）
├── 2. 手肘法選 K（inertia + 輪廓係數）
├── 3. KMeans(n_clusters=K).fit(X_scaled)
├── 4. labels_ 取得群組標籤
└── 5. 詮釋各群的業務意義（最重要！）

工業工程的分群應用
├── 供應商管理：RFM 採購分析
├── 客戶分群：市場區隔、精準行銷
├── 製程分群：找出相似的生產批次
└── 異常偵測：偏離群體的機台/產品
```

---

*上一單元：[模組 2-2：Pandas](./Module2_2_Pandas.md) ｜ 下一單元：[模組 4-1：網路爬蟲](./Module4_1_WebScraping.md)*
