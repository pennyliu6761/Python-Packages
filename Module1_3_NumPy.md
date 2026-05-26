# 模組 1-3：NumPy — 品質管制圖模擬

> **學習目標**：掌握陣列向量化運算，取代低效的 Python 迴圈；並以「品管圖」為載體，理解統計製程管制的核心概念。

---

## 📌 為什麼工管系要學 NumPy？

工業工程的核心是「用數字說話」。NumPy 是 Python 科學計算的基石：
- **速度快**：向量化運算比 Python 迴圈快 10~100 倍，能即時處理感測器數據流
- **品管基礎**：SPC（統計製程管制）、可靠度分析、良率計算都仰賴矩陣運算
- **AI 基礎**：所有機器學習框架（sklearn, TensorFlow, PyTorch）底層都是 NumPy

---

## 🔧 安裝

```bash
pip install numpy matplotlib
```

---

## 一、陣列基礎：取代 Python List

```python
import numpy as np

# ===== Python List 的問題 =====
# 若要對 100 個量測值乘以校正係數 1.02，用 List 需要迴圈：
measurements_list = [10.1, 9.8, 10.3, 10.0, 9.9]  # ... 100 個值
corrected_list = [x * 1.02 for x in measurements_list]  # 慢！

# ===== NumPy 的解法：向量化（一次全算）=====
measurements = np.array([10.1, 9.8, 10.3, 10.0, 9.9])
corrected    = measurements * 1.02   # 直接對整個陣列操作！

# ===== 建立陣列的各種方法 =====

# 1. 等差數列（常用於建立時間軸或規格序列）
time_axis = np.arange(0, 100, 0.1)   # 從 0 到 99.9，每隔 0.1
spec_vals  = np.linspace(9.5, 10.5, 100)  # 從 9.5 到 10.5，均勻分成 100 點

# 2. 全零 / 全一矩陣（初始化用）
zero_matrix = np.zeros((5, 3))       # 5 列 3 行的零矩陣
ones_vector = np.ones(10)            # 長度 10 的全 1 向量

# 3. 【品管常用】正態分配亂數（模擬製程量測值）
# loc=平均值, scale=標準差, size=樣本數
np.random.seed(42)   # 固定種子，確保每次執行結果相同（可重現性）
diameters = np.random.normal(loc=10.00,   # 規格中心值 = 10mm
                              scale=0.05, # 製程標準差 = 0.05mm
                              size=500)   # 模擬 500 個量測值

print(f"陣列形狀：{diameters.shape}")
print(f"前 5 個量測值：{diameters[:5].round(3)}")
print(f"最小值：{diameters.min():.3f} mm")
print(f"最大值：{diameters.max():.3f} mm")
print(f"平均值：{diameters.mean():.3f} mm")
print(f"標準差：{diameters.std():.3f} mm")
```

<img width="578" height="110" alt="image" src="https://github.com/user-attachments/assets/b1a56004-0c72-4ad9-bbc6-62f2c7dc7aec" />

---

## 二、陣列索引與切片（批次資料篩選）

```python
import numpy as np

# 模擬 200 個零件的直徑量測值
np.random.seed(0)
diameters = np.random.normal(10.0, 0.05, 200)

# ===== 基本索引 =====
print(f"第 1 個：{diameters[0]:.3f}")      # 索引從 0 開始
print(f"最後 1 個：{diameters[-1]:.3f}")   # 負索引從末尾算

# ===== 切片（Slicing）=====
first_batch  = diameters[:50]           # 前 50 個（第一批）
second_batch = diameters[50:100]        # 第 51~100 個
every_10th   = diameters[::10]          # 每隔 10 個抽樣一次（系統抽樣）

# ===== 【品管應用】布林索引（快速篩選失控點）=====
USL = 10.15   # 規格上限 (Upper Spec Limit)
LSL = 9.85    # 規格下限 (Lower Spec Limit)

# 找出超出規格的不良品
nonconforming_mask = (diameters > USL) | (diameters < LSL)  # | 表示 OR
nonconforming_vals = diameters[nonconforming_mask]
nonconforming_idx  = np.where(nonconforming_mask)[0]        # 取得不良品的索引位置

print(f"\n規格範圍：{LSL} ~ {USL} mm")
print(f"總量測數：{len(diameters)}")
print(f"不良品數：{nonconforming_mask.sum()}")
print(f"不良率：{nonconforming_mask.mean() * 100:.2f}%")
print(f"不良品出現在第幾個：{nonconforming_idx + 1}")  # +1 換成人類習慣的 1 開始計數
```

<img width="578" height="148" alt="image" src="https://github.com/user-attachments/assets/c1a91347-fcff-414b-97b2-34e199e05e7b" />

---

## 三、矩陣運算（多機台、多量測值的同步處理）

```python
import numpy as np

# ===== 情境：3 台機台，各量測 5 個零件 =====
# 建立 3×5 矩陣（列=機台，行=量測次序）
np.random.seed(1)
machine_data = np.array([
    np.random.normal(10.00, 0.04, 5),   # 機台 A
    np.random.normal(10.02, 0.06, 5),   # 機台 B（有 0.02mm 偏移）
    np.random.normal( 9.98, 0.03, 5),   # 機台 C（有 -0.02mm 偏移）
])

print("各機台量測數據（mm）：")
print(machine_data.round(3))
print(f"矩陣形狀：{machine_data.shape}（{machine_data.shape[0]} 台機台 × {machine_data.shape[1]} 次量測）")

# ===== 沿軸計算（axis=0/1）=====
# axis=1：沿著「行」方向計算 → 對每列（每台機台）的結果
machine_means  = machine_data.mean(axis=1)   # 每台機台的平均值
machine_stds   = machine_data.std(axis=1)    # 每台機台的標準差
machine_ranges = machine_data.max(axis=1) - machine_data.min(axis=1)  # 每台的全距

print(f"\n各機台平均值：{machine_means.round(4)}")
print(f"各機台標準差：{machine_stds.round(4)}")
print(f"各機台全距：{machine_ranges.round(4)}")

# axis=0：沿著「列」方向計算 → 對每行（每個時間點）的結果
time_means = machine_data.mean(axis=0)   # 每個時間點，3 台機台的平均
print(f"\n各時間點全廠平均：{time_means.round(4)}")

# ===== 廣播機制（Broadcasting）=====
# 校正偏移：每台機台減去自己的平均值，使所有機台置中到 0
machine_centered = machine_data - machine_means[:, np.newaxis]
# ↑ machine_means[:, np.newaxis] 將形狀從 (3,) 擴展為 (3,1)，才能對 (3,5) 廣播
print(f"\n校正後各機台平均（應接近 0）：{machine_centered.mean(axis=1).round(6)}")
```

<img width="570" height="219" alt="image" src="https://github.com/user-attachments/assets/e8224cd0-be57-407b-bb90-2c4b85f4b25b" />

---

## 四、🎯 核心應用：品質管制圖（X-bar & R Chart）模擬

### 4.1 理論背景

品質管制圖（Control Chart）由 Walter A. Shewhart 在 1920 年代發明，是統計製程管制（SPC）的核心工具。

```
X-bar Chart（均值管制圖）：監控製程「位置」的穩定性
R Chart（全距管制圖）：監控製程「變異」的穩定性

管制界限的計算（基於 3σ 原則）：
─────────────────────────────────────────
X-bar Chart：
  中心線（CL）  = X̄（總平均）
  上管制界限（UCL）= X̄ + A₂ × R̄
  下管制界限（LCL）= X̄ - A₂ × R̄

R Chart：
  中心線（CL）  = R̄（平均全距）
  上管制界限（UCL）= D₄ × R̄
  下管制界限（LCL）= D₃ × R̄

其中 A₂、D₃、D₄ 為查表常數，與子組大小 n 有關
```

### 4.2 完整程式碼

```python
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ===== 設定中文字型（Windows/Mac 通用方案）=====
plt.rcParams['font.family'] = ['Microsoft JhengHei', 'PingFang TC',
                                'Noto Sans CJK TC', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False  # 解決負號顯示問題

# ============================================================
# 第一步：參數設定
# ============================================================
np.random.seed(42)

TARGET      = 50.00   # 規格目標值（mm）
SIGMA       = 0.30    # 製程標準差
N_SUBGROUPS = 25      # 子組數量（通常 20~25 組建立管制圖）
SUBGROUP_N  = 5       # 每組樣本數（常見為 4 或 5）

# SPC 查表常數（n=5 時）
# 來源：AIAG SPC 手冊 附表
A2 = 0.577   # X-bar Chart 控制限係數
D3 = 0.0     # R Chart 下限係數（n<7 時 D3=0，代表 LCL 不存在）
D4 = 2.115   # R Chart 上限係數

# ============================================================
# 第二步：模擬量測資料（含「異常事件」）
# ============================================================
# 基礎數據：正常製程
data = np.random.normal(loc=TARGET, scale=SIGMA,
                         size=(N_SUBGROUPS, SUBGROUP_N))

# 注入異常事件（模擬真實製程中可能發生的問題）
# 異常 1：第 15 組開始，刀具磨損 → 均值漂移 +0.8mm（趨勢型失控）
data[14:18] += np.linspace(0, 0.8, 4)[:, np.newaxis]

# 異常 2：第 20 組，換批原料 → 突發性偏移 +1.5mm（突變型失控）
data[19] += 1.5

# 異常 3：第 22 組，夾具鬆動 → 變異增大 3 倍（離散型失控）
data[21] = np.random.normal(TARGET, SIGMA * 3, SUBGROUP_N)

# ============================================================
# 第三步：計算管制圖統計量（NumPy 向量化，一行一個計算！）
# ============================================================
subgroup_means  = data.mean(axis=1)               # 每組的 X-bar（均值）
subgroup_ranges = data.max(axis=1) - data.min(axis=1)  # 每組的 R（全距）

X_bar_bar = subgroup_means.mean()     # 總平均（X-bar 管制圖的中心線）
R_bar     = subgroup_ranges.mean()   # 平均全距（R 管制圖的中心線）

# X-bar 管制界限
UCL_xbar = X_bar_bar + A2 * R_bar
LCL_xbar = X_bar_bar - A2 * R_bar

# R 管制界限
UCL_R = D4 * R_bar
LCL_R = D3 * R_bar   # n=5 時 = 0（無下管制限）

# ============================================================
# 第四步：判定失控點（布林索引應用）
# ============================================================
xbar_ooc_upper = subgroup_means > UCL_xbar
xbar_ooc_lower = subgroup_means < LCL_xbar
xbar_ooc       = xbar_ooc_upper | xbar_ooc_lower  # Out of Control

r_ooc_upper    = subgroup_ranges > UCL_R
r_ooc          = r_ooc_upper

subgroup_labels = np.arange(1, N_SUBGROUPS + 1)  # x 軸標籤（1~25）

print("=" * 55)
print("📊 X-bar & R 管制圖 統計摘要")
print("=" * 55)
print(f"  總平均 (X̄)        = {X_bar_bar:.4f} mm")
print(f"  平均全距 (R̄)      = {R_bar:.4f} mm")
print(f"  X-bar UCL         = {UCL_xbar:.4f} mm")
print(f"  X-bar LCL         = {LCL_xbar:.4f} mm")
print(f"  R Chart UCL       = {UCL_R:.4f} mm")
print(f"  X-bar 失控組數    = {xbar_ooc.sum()} 組（第 {np.where(xbar_ooc)[0]+1} 組）")
print(f"  R Chart 失控組數  = {r_ooc.sum()} 組（第 {np.where(r_ooc)[0]+1} 組）")
print("=" * 55)

# ============================================================
# 第五步：繪製管制圖
# ============================================================
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), sharex=True)
fig.suptitle('X-bar & R 品質管制圖（零件直徑，mm）', fontsize=15, fontweight='bold', y=0.98)

# --- X-bar Chart ---
ax1.set_title('X-bar 均值管制圖', fontsize=12)
ax1.plot(subgroup_labels, subgroup_means, 'b-o',
         linewidth=1.5, markersize=5, zorder=3, label='各組均值')

# 管制界限線
ax1.axhline(X_bar_bar, color='green',  linewidth=2,   linestyle='-',  label=f'CL = {X_bar_bar:.4f}')
ax1.axhline(UCL_xbar,  color='red',    linewidth=1.5, linestyle='--', label=f'UCL = {UCL_xbar:.4f}')
ax1.axhline(LCL_xbar,  color='red',    linewidth=1.5, linestyle='--', label=f'LCL = {LCL_xbar:.4f}')

# 標示失控點（紅色大點）
if xbar_ooc.any():
    ax1.plot(subgroup_labels[xbar_ooc], subgroup_means[xbar_ooc],
             'r*', markersize=18, zorder=5, label=f'⚠️ 失控點 ({xbar_ooc.sum()} 個)')

# 填色警示區
ax1.fill_between(subgroup_labels, UCL_xbar, ax1.get_ylim()[1] if ax1.get_ylim()[1] > UCL_xbar else UCL_xbar + 0.5,
                  alpha=0.05, color='red')

ax1.set_ylabel('均值 X̄ (mm)', fontsize=11)
ax1.legend(loc='upper left', fontsize=9)
ax1.grid(True, alpha=0.3, linestyle=':')
ax1.yaxis.set_major_formatter(plt.FormatStrFormatter('%.3f'))

# --- R Chart ---
ax2.set_title('R 全距管制圖', fontsize=12)
ax2.plot(subgroup_labels, subgroup_ranges, 'purple',
         linestyle='-', marker='s', linewidth=1.5, markersize=5, label='各組全距')

ax2.axhline(R_bar,   color='green', linewidth=2,   linestyle='-',  label=f'CL = {R_bar:.4f}')
ax2.axhline(UCL_R,   color='red',   linewidth=1.5, linestyle='--', label=f'UCL = {UCL_R:.4f}')
if LCL_R > 0:
    ax2.axhline(LCL_R, color='red', linewidth=1.5, linestyle='--', label=f'LCL = {LCL_R:.4f}')
else:
    ax2.text(1, UCL_R * 0.05, 'LCL = 0（n≤6 無下管制限）',
             color='gray', fontsize=9)

if r_ooc.any():
    ax2.plot(subgroup_labels[r_ooc], subgroup_ranges[r_ooc],
             'r*', markersize=18, zorder=5, label=f'⚠️ 失控點 ({r_ooc.sum()} 個)')

ax2.set_xlabel('子組編號', fontsize=11)
ax2.set_ylabel('全距 R (mm)', fontsize=11)
ax2.legend(loc='upper left', fontsize=9)
ax2.grid(True, alpha=0.3, linestyle=':')
ax2.set_xticks(subgroup_labels)
ax2.yaxis.set_major_formatter(plt.FormatStrFormatter('%.3f'))

plt.tight_layout()
plt.savefig('control_chart.png', dpi=150, bbox_inches='tight')
plt.show()
print("✅ 管制圖已儲存為 control_chart.png")
```

<img width="2087" height="1332" alt="control_chart" src="https://github.com/user-attachments/assets/b2653365-abb5-4524-ac25-5c770aef163e" />

---

## 五、NumPy 核心函式速查表

```python
# -*- coding: utf-8 -*-
"""
Created on Tue May 26 21:02:11 2026

@author: user
"""

import numpy as np

# ===== 統計函式 =====
a = np.random.normal(10, 0.5, 100)

np.mean(a)          # 算術平均值
np.median(a)        # 中位數
np.std(a)           # 標準差（population std，分母 N）
np.std(a, ddof=1)   # 樣本標準差（分母 N-1，統計推論用）
np.var(a)           # 變異數
np.percentile(a, [25, 50, 75])  # 四分位數（Q1, Q2, Q3）
np.min(a); np.max(a); np.ptp(a) # 最小、最大、全距（Peak-to-Peak）
np.cumsum(a)        # 累積和（繪製不良品累積曲線常用）
np.cumprod(a)       # 累積積

# ===== 搜尋與排序 =====
np.argmin(a)        # 最小值的索引
np.argmax(a)        # 最大值的索引
np.argsort(a)       # 排序後的索引陣列（間接排序）
np.where(a > 10)    # 滿足條件的索引（等同布林索引）

# ===== 矩陣操作 =====
A = np.array([[1, 2], [3, 4]])
B = np.array([[5, 6], [7, 8]])

A.T               # 轉置矩陣
A @ B             # 矩陣乘法（dot product）
np.linalg.inv(A)  # 反矩陣（解線性方程組）
np.linalg.det(A)  # 行列式
np.linalg.eig(A)  # 特徵值與特徵向量（PCA 分析基礎）

# ===== 亂數生成（品質工程常用分配）=====
mu=1.0
sigma=0.2
n=30
low=10
high=30
lambda_=20

np.random.seed(42)                         # 固定種子
np.random.normal(mu, sigma, n)             # 正態分配（製程量測值）
np.random.uniform(low, high, n)            # 均勻分配（模擬公差帶）
np.random.exponential(1/lambda_, n)        # 指數分配（故障時間、壽命）
np.random.poisson(lambda_, n)              # 卜瓦松分配（單位時間缺陷數）
np.random.binomial(n=10, p=0.05, size=100) # 二項分配（不良品抽樣）
```

---

## 六、🖥️ Matplotlib 應用：互動式管制圖分析

```python
# 延伸：將管制圖加入 Streamlit（簡化版，完整版見 Streamlit 模組）
# 儲存為 app_spc.py

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.title("📊 品質管制圖模擬器")

with st.sidebar:
    target    = st.number_input("規格目標值", value=50.0)
    sigma     = st.slider("製程標準差 σ", 0.1, 1.0, 0.3, 0.05)
    n_groups  = st.slider("子組數量", 15, 50, 25)
    sub_n     = st.select_slider("每組樣本數 n", [3, 4, 5], value=5)
    add_shift = st.checkbox("注入均值漂移異常")

A2_TABLE = {3: 1.023, 4: 0.729, 5: 0.577}
D4_TABLE = {3: 2.574, 4: 2.282, 5: 2.115}
A2 = A2_TABLE[sub_n]
D4 = D4_TABLE[sub_n]

np.random.seed(42)
data = np.random.normal(target, sigma, (n_groups, sub_n))
if add_shift:
    data[int(n_groups * 0.6):] += sigma * 3  # 後 40% 發生偏移

means  = data.mean(axis=1)
ranges = data.max(axis=1) - data.min(axis=1)
xbar   = means.mean()
rbar   = ranges.mean()

ucl_x = xbar + A2 * rbar
lcl_x = xbar - A2 * rbar
ucl_r = D4 * rbar

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7))
x = np.arange(1, n_groups + 1)

# X-bar
ax1.plot(x, means, 'b-o', markersize=4)
ax1.axhline(xbar, color='g', linewidth=2)
ax1.axhline(ucl_x, color='r', linestyle='--')
ax1.axhline(lcl_x, color='r', linestyle='--')
ooc = (means > ucl_x) | (means < lcl_x)
if ooc.any():
    ax1.plot(x[ooc], means[ooc], 'r*', markersize=15)
ax1.set_title('X-bar Chart')
ax1.set_ylabel('均值')
ax1.grid(True, alpha=0.3)

# R Chart
ax2.plot(x, ranges, 'purple', marker='s', markersize=4)
ax2.axhline(rbar, color='g', linewidth=2)
ax2.axhline(ucl_r, color='r', linestyle='--')
ax2.set_title('R Chart')
ax2.set_ylabel('全距')
ax2.grid(True, alpha=0.3)

st.pyplot(fig)

col1, col2, col3 = st.columns(3)
col1.metric("製程平均", f"{xbar:.4f}")
col2.metric("X-bar 失控點", f"{ooc.sum()} 個", delta=f"{'⚠️ 失控' if ooc.any() else '✅ 穩定'}")
col3.metric("估計 Cpk", f"{min((ucl_x - xbar), (xbar - lcl_x)) / (3 * sigma):.2f}")
```

<img width="1527" height="694" alt="image" src="https://github.com/user-attachments/assets/645473d2-0514-4311-8048-7efbd63e5ca8" />

---

## 七、課後練習

### 練習 1：計算製程能力指數

```python
import numpy as np

# 情境：某零件規格為 50.00 ± 0.50 mm
USL = 50.50   # 規格上限
LSL = 49.50   # 規格下限
TARGET = 50.00

# 蒐集 100 個量測值
np.random.seed(0)
measurements = np.random.normal(50.05, 0.18, 100)   # 稍微偏移、變異較大

# 請你計算：
# 1. Cp  = (USL - LSL) / (6σ)      → 製程精度（只考慮變異）
# 2. Cpk = min((USL-μ)/3σ, (μ-LSL)/3σ) → 製程能力（同時考慮偏移）
# 3. 理論不良率（假設常態分配，利用 scipy.stats.norm.cdf）

# --- 請在此完成計算 ---
mu    = measurements.mean()
sigma = measurements.std(ddof=1)
Cp    = (USL - LSL) / (6 * sigma)
Cpk   = min((USL - mu) / (3 * sigma), (mu - LSL) / (3 * sigma))

print(f"平均值 μ = {mu:.4f} mm")
print(f"標準差 σ = {sigma:.4f} mm")
print(f"Cp       = {Cp:.3f}（≥ 1.33 為合格）")
print(f"Cpk      = {Cpk:.3f}（≥ 1.33 為合格）")
```

<img width="570" height="80" alt="image" src="https://github.com/user-attachments/assets/23d4542d-c518-46b8-9e1a-1f165c4928ed" />

### 練習 2：思考題

1. 為什麼 SPC 管制界限是用 **3σ**，而不是規格界限（USL/LSL）？這兩者的差異代表什麼管理意義？
2. X-bar Chart 和 R Chart 需要**同時**看，為什麼？單看 X-bar Chart 可能漏掉什麼問題？
3. 本範例中注入的三種異常（漂移、突變、變異增大）分別對應工廠中的哪些實際問題？

---

## 📎 重點整理

```
NumPy 核心觀念
├── 向量化運算 → 取代迴圈，速度提升 10~100×
├── 廣播機制  → 不同形狀的陣列自動對齊計算
├── 布林索引  → 快速篩選符合條件的資料（品管應用！）
└── 亂數生成  → 模擬真實製程的統計分配

SPC 品管圖核心
├── X-bar Chart → 監控製程「位置」（均值穩定性）
├── R Chart     → 監控製程「變異」（全距穩定性）
├── 失控判定   → 超出 UCL/LCL 或連續趨勢
└── 失控種類   → 突變型、趨勢型、離散型
```

---

*上一單元：[模組 1-2：QR Code](./Module1_2_QRCode.md) ｜ 下一單元：[模組 2-1：SciPy](./Module2_1_SciPy.md)*
