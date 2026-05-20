# 模組 2-1：SciPy — 產能最佳化決策面板

> **學習目標**：理解線性規劃（LP）的數學模型建構，並使用 SciPy 求解，以視覺化方式展現可行解區域與最佳解。

---

## 📌 為什麼工管系要學 SciPy 最佳化？

「在有限資源下，如何讓利潤最大？」這是工業工程的核心問題。線性規劃（Linear Programming, LP）是求解這類**有限制條件最佳化問題**的標準方法，廣泛用於：
- **生產排程**：決定各產品的最佳生產量
- **採購決策**：在預算限制下最大化採購效益
- **物流配送**：最短路徑、最低運輸成本
- **人力排班**：在法規限制下最小化人力成本

---

## 🔧 安裝

```bash
pip install scipy matplotlib numpy streamlit
```

---

## 一、線性規劃（LP）理論速覽

```
問題結構：
────────────────────────────────────────
目標函數（Objective Function）：
  最大化 z = c₁x₁ + c₂x₂  （利潤）

決策變數（Decision Variables）：
  x₁ = 產品 A 的生產數量
  x₂ = 產品 B 的生產數量

限制條件（Constraints）：
  a₁₁x₁ + a₁₂x₂ ≤ b₁  （工時限制）
  a₂₁x₁ + a₂₂x₂ ≤ b₂  （原料限制）
  x₁, x₂ ≥ 0            （非負限制）

幾何意義：
  每個限制條件 → 一條直線，將平面分成「可行」和「不可行」兩側
  所有限制條件的交集 → 可行解區域（Feasible Region，多邊形）
  最佳解 → 必定在可行解區域的「頂點（Vertex）」上
────────────────────────────────────────
```

---

## 二、SciPy 求解 LP 的方法

```python
from scipy.optimize import linprog
import numpy as np

# ============================================================
# 問題設定：工廠生產 A、B 兩種產品
# ============================================================
# 產品 A：每件利潤 5 萬元，需 2 工時，消耗 4kg 原料
# 產品 B：每件利潤 4 萬元，需 3 工時，消耗 2kg 原料
# 工時上限：12 工時（每天）
# 原料上限：16 kg（每天）

# ===== ⚠️ 重要：linprog 預設為「最小化」目標函數 =====
# 因此「最大化利潤」需要改為「最小化負利潤」
# 原目標：max 5x₁ + 4x₂
# 等價於：min -5x₁ - 4x₂

c = [-5, -4]   # 目標函數係數（負號！因為要最小化負利潤）

# ===== 限制條件（不等式，≤ 形式）=====
# 工時限制：2x₁ + 3x₂ ≤ 12
# 原料限制：4x₁ + 2x₂ ≤ 16

A_ub = [
    [2, 3],   # 工時限制的係數
    [4, 2],   # 原料限制的係數
]
b_ub = [12, 16]   # 右端值（資源上限）

# ===== 決策變數的邊界（非負限制）=====
x1_bounds = (0, None)   # x₁ ≥ 0
x2_bounds = (0, None)   # x₂ ≥ 0

# ===== 求解 =====
result = linprog(
    c,                              # 目標函數係數
    A_ub=A_ub,                      # 不等式限制係數矩陣
    b_ub=b_ub,                      # 不等式限制右端值
    bounds=[x1_bounds, x2_bounds],  # 決策變數邊界
    method='highs'                  # 推薦使用 HiGHS 求解器（最新最穩定）
)

# ===== 解讀結果 =====
print("=" * 45)
print("📊 線性規劃求解結果")
print("=" * 45)
print(f"求解狀態：{'✅ 成功找到最佳解' if result.success else '❌ 求解失敗'}")
print(f"最佳解：x₁（產品 A）= {result.x[0]:.2f} 件")
print(f"         x₂（產品 B）= {result.x[1]:.2f} 件")
print(f"最大利潤：{-result.fun:.2f} 萬元")   # fun 是最小化值，取負值得到最大利潤

# 驗證資源使用量
x1, x2 = result.x
print(f"\n資源使用確認：")
print(f"  工時使用：{2*x1 + 3*x2:.1f} / 12 工時")
print(f"  原料使用：{4*x1 + 2*x2:.1f} / 16 kg")
print("=" * 45)
```

---

## 三、可行解區域視覺化

```python
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyArrowPatch

plt.rcParams['font.family'] = ['Microsoft JhengHei', 'PingFang TC', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

def plot_feasible_region(profits, time_limit, material_limit,
                          time_coeffs, material_coeffs):
    """
    繪製二維線性規劃的可行解區域
    
    Parameters:
        profits          : [c1, c2] 利潤係數
        time_limit       : 工時上限
        material_limit   : 原料上限
        time_coeffs      : [a11, a12] 工時消耗係數
        material_coeffs  : [a21, a22] 原料消耗係數
    """
    fig, ax = plt.subplots(figsize=(10, 8))

    x1_max = max(time_limit / time_coeffs[0],
                 material_limit / material_coeffs[0]) + 1
    x2_max = max(time_limit / time_coeffs[1],
                 material_limit / material_coeffs[1]) + 1

    x1 = np.linspace(0, x1_max, 500)

    # ===== 繪製限制線 =====
    # 工時限制：a₁₁x₁ + a₁₂x₂ ≤ b₁ → x₂ ≤ (b₁ - a₁₁x₁) / a₁₂
    x2_time     = (time_limit     - time_coeffs[0]     * x1) / time_coeffs[1]
    x2_material = (material_limit - material_coeffs[0] * x1) / material_coeffs[1]

    ax.plot(x1, x2_time,     'b-',  linewidth=2.5,
            label=f'工時限制：{time_coeffs[0]}x₁ + {time_coeffs[1]}x₂ ≤ {time_limit}')
    ax.plot(x1, x2_material, 'r-',  linewidth=2.5,
            label=f'原料限制：{material_coeffs[0]}x₁ + {material_coeffs[1]}x₂ ≤ {material_limit}')
    ax.axvline(x=0, color='gray', linewidth=1.5)
    ax.axhline(y=0, color='gray', linewidth=1.5)

    # ===== 填色：可行解區域 =====
    # 可行解區域 = 所有限制條件同時滿足的區域
    x1_fill = np.linspace(0, x1_max, 1000)
    x2_time_fill     = np.clip((time_limit     - time_coeffs[0]     * x1_fill) / time_coeffs[1],     0, x2_max)
    x2_material_fill = np.clip((material_limit - material_coeffs[0] * x1_fill) / material_coeffs[1], 0, x2_max)
    x2_upper         = np.minimum(x2_time_fill, x2_material_fill)

    ax.fill_between(x1_fill, 0, x2_upper,
                    where=(x2_upper >= 0),
                    alpha=0.25, color='green',
                    label='✅ 可行解區域（Feasible Region）')

    # ===== 標示頂點（Vertex）=====
    # 頂點是最佳解的候選點
    vertices = []

    # 原點 (0, 0)
    vertices.append((0, 0))

    # x₁ 軸截距（令 x₂=0）
    v_time_x1     = time_limit     / time_coeffs[0]
    v_material_x1 = material_limit / material_coeffs[0]
    vertices.append((min(v_time_x1, v_material_x1), 0))

    # x₂ 軸截距（令 x₁=0）
    v_time_x2     = time_limit     / time_coeffs[1]
    v_material_x2 = material_limit / material_coeffs[1]
    vertices.append((0, min(v_time_x2, v_material_x2)))

    # 兩條限制線的交點（聯立方程）
    A = np.array([[time_coeffs[0],     time_coeffs[1]],
                  [material_coeffs[0], material_coeffs[1]]])
    b = np.array([time_limit, material_limit])
    try:
        intersection = np.linalg.solve(A, b)
        if intersection[0] >= 0 and intersection[1] >= 0:
            vertices.append(tuple(intersection))
    except np.linalg.LinAlgError:
        pass  # 平行線，無交點

    # ===== 計算各頂點的目標值，找出最佳頂點 =====
    best_val    = -np.inf
    best_vertex = None
    for v in vertices:
        val = profits[0] * v[0] + profits[1] * v[1]
        if val > best_val:
            best_val    = val
            best_vertex = v

    # 繪製頂點
    for v in vertices:
        z   = profits[0] * v[0] + profits[1] * v[1]
        is_best = (abs(v[0] - best_vertex[0]) < 1e-6 and
                   abs(v[1] - best_vertex[1]) < 1e-6)
        color  = '#e74c3c' if is_best else '#2ecc71'
        marker = '*' if is_best else 'o'
        size   = 200 if is_best else 80

        ax.scatter(*v, color=color, s=size, zorder=5, marker=marker)
        ax.annotate(f'  ({v[0]:.1f}, {v[1]:.1f})\n  z={z:.1f}',
                    xy=v, fontsize=10, color=color,
                    fontweight='bold' if is_best else 'normal')

    # ===== 繪製等利潤線（Iso-profit Line）=====
    # 以最佳解的利潤值畫一條「等利潤線」，切過最佳頂點
    z_opt = best_val
    if profits[1] != 0:
        x2_iso = (z_opt - profits[0] * x1) / profits[1]
        mask    = (x2_iso >= -1) & (x2_iso <= x2_max + 1)
        ax.plot(x1[mask], x2_iso[mask], 'gold',
                linewidth=2, linestyle='-.', zorder=4,
                label=f'最佳等利潤線（z = {z_opt:.1f} 萬元）')

    # ===== 圖形美化 =====
    ax.set_xlim(-0.3, x1_max)
    ax.set_ylim(-0.3, x2_max)
    ax.set_xlabel('x₁（產品 A 生產量）', fontsize=13)
    ax.set_ylabel('x₂（產品 B 生產量）', fontsize=13)
    ax.set_title('線性規劃：可行解區域與最佳解', fontsize=15, fontweight='bold')
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.3, linestyle=':')

    # 標注最佳解
    ax.annotate(f'⭐ 最佳解\nx₁={best_vertex[0]:.1f}, x₂={best_vertex[1]:.1f}\n利潤={z_opt:.1f} 萬',
                xy=best_vertex,
                xytext=(best_vertex[0] + 0.5, best_vertex[1] + 0.5),
                fontsize=11, color='#e74c3c', fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='#e74c3c', lw=2))

    plt.tight_layout()
    return fig, best_vertex, best_val


# 執行並顯示
fig, opt_x, opt_z = plot_feasible_region(
    profits          = [5, 4],
    time_limit       = 12,
    material_limit   = 16,
    time_coeffs      = [2, 3],
    material_coeffs  = [4, 2]
)
plt.savefig('feasible_region.png', dpi=150, bbox_inches='tight')
plt.show()
```

---

## 四、敏感度分析（Sensitivity Analysis）

```python
from scipy.optimize import linprog
import numpy as np

# ===== 敏感度分析：利潤係數改變時，最佳解如何變化？=====
# 實際意義：若市場行情變動，A 的利潤從 5 萬漲到 8 萬，最佳決策會改變嗎？

profit_A_range = np.linspace(1, 10, 50)   # 掃描 A 的利潤從 1 到 10 萬
opt_x1_list    = []
opt_x2_list    = []
opt_z_list     = []

for profit_A in profit_A_range:
    c = [-profit_A, -4]   # 負號（最小化負利潤）
    result = linprog(
        c,
        A_ub=[[2, 3], [4, 2]],
        b_ub=[12, 16],
        bounds=[(0, None), (0, None)],
        method='highs'
    )
    if result.success:
        opt_x1_list.append(result.x[0])
        opt_x2_list.append(result.x[1])
        opt_z_list.append(-result.fun)
    else:
        opt_x1_list.append(np.nan)
        opt_x2_list.append(np.nan)
        opt_z_list.append(np.nan)

import matplotlib.pyplot as plt

fig, axes = plt.subplots(3, 1, figsize=(10, 10))
fig.suptitle('敏感度分析：產品 A 利潤係數的影響', fontsize=14, fontweight='bold')

axes[0].plot(profit_A_range, opt_x1_list, 'b-o', markersize=3)
axes[0].set_ylabel('最佳 x₁（產品 A 數量）')
axes[0].grid(True, alpha=0.3)
axes[0].axvline(5, color='red', linestyle='--', alpha=0.7, label='當前利潤 = 5 萬')
axes[0].legend()

axes[1].plot(profit_A_range, opt_x2_list, 'r-s', markersize=3)
axes[1].set_ylabel('最佳 x₂（產品 B 數量）')
axes[1].grid(True, alpha=0.3)
axes[1].axvline(5, color='red', linestyle='--', alpha=0.7)

axes[2].plot(profit_A_range, opt_z_list, 'g-^', markersize=3)
axes[2].set_ylabel('最大利潤 z（萬元）')
axes[2].set_xlabel('產品 A 的利潤係數（萬元/件）')
axes[2].grid(True, alpha=0.3)
axes[2].axvline(5, color='red', linestyle='--', alpha=0.7, label='當前值')
axes[2].legend()

plt.tight_layout()
plt.savefig('sensitivity.png', dpi=150, bbox_inches='tight')
plt.show()
print("✅ 敏感度分析圖已儲存！")
```

---

## 五、🖥️ Streamlit 應用：產能最佳化決策面板

```python
# 檔案名稱：app_lp.py
# 執行方式：streamlit run app_lp.py

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import linprog

plt.rcParams['font.family'] = ['Microsoft JhengHei', 'PingFang TC', 'sans-serif']

st.set_page_config(page_title="產能最佳化決策面板", page_icon="🏭", layout="wide")
st.title("🏭 產能最佳化決策面板")
st.markdown("調整利潤與資源限制，即時看到線性規劃的最佳解與可行解區域。")

# ===== 側邊欄參數 =====
with st.sidebar:
    st.header("⚙️ 參數設定")

    st.subheader("💰 利潤（萬元/件）")
    profit_A = st.slider("產品 A 利潤", 1.0, 15.0, 5.0, 0.5)
    profit_B = st.slider("產品 B 利潤", 1.0, 15.0, 4.0, 0.5)

    st.subheader("🕐 工時消耗（hr/件）")
    time_A = st.slider("產品 A 工時", 0.5, 8.0, 2.0, 0.5)
    time_B = st.slider("產品 B 工時", 0.5, 8.0, 3.0, 0.5)

    st.subheader("🧱 原料消耗（kg/件）")
    mat_A = st.slider("產品 A 原料", 0.5, 10.0, 4.0, 0.5)
    mat_B = st.slider("產品 B 原料", 0.5, 10.0, 2.0, 0.5)

    st.subheader("📦 資源上限")
    time_cap = st.slider("工時上限（hr）", 5.0, 50.0, 12.0, 1.0)
    mat_cap  = st.slider("原料上限（kg）", 5.0, 80.0, 16.0, 1.0)

# ===== 求解 =====
result = linprog(
    [-profit_A, -profit_B],
    A_ub=[[time_A, time_B], [mat_A, mat_B]],
    b_ub=[time_cap, mat_cap],
    bounds=[(0, None), (0, None)],
    method='highs'
)

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📈 可行解區域與最佳解")

    fig, ax = plt.subplots(figsize=(8, 7))

    x1_max = max(time_cap / time_A, mat_cap / mat_A) * 1.2
    x2_max = max(time_cap / time_B, mat_cap / mat_B) * 1.2
    x1     = np.linspace(0, x1_max, 500)

    # 限制線
    x2_t = np.clip((time_cap - time_A * x1) / time_B, 0, x2_max)
    x2_m = np.clip((mat_cap  - mat_A  * x1) / mat_B,  0, x2_max)
    ax.plot(x1, x2_t, 'b-', linewidth=2, label=f'工時限制（上限={time_cap}hr）')
    ax.plot(x1, x2_m, 'r-', linewidth=2, label=f'原料限制（上限={mat_cap}kg）')

    # 可行解區域
    x2_upper = np.minimum(x2_t, x2_m)
    ax.fill_between(x1, 0, x2_upper, where=x2_upper >= 0,
                    alpha=0.2, color='green', label='可行解區域')

    # 最佳解
    if result.success:
        ax.scatter(*result.x, color='red', s=300, zorder=5, marker='*')
        ax.annotate(f'最佳解\nA={result.x[0]:.1f}, B={result.x[1]:.1f}',
                    xy=result.x,
                    xytext=(result.x[0] + 0.3, result.x[1] + 0.3),
                    fontsize=11, color='red', fontweight='bold',
                    arrowprops=dict(arrowstyle='->', color='red'))

    ax.set_xlim(0, x1_max)
    ax.set_ylim(0, x2_max)
    ax.set_xlabel('x₁（產品 A）', fontsize=12)
    ax.set_ylabel('x₂（產品 B）', fontsize=12)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)

with col2:
    st.subheader("📊 最佳化結果")
    if result.success:
        x1_opt, x2_opt = result.x
        max_profit      = -result.fun

        st.metric("產品 A 最佳生產量", f"{x1_opt:.1f} 件")
        st.metric("產品 B 最佳生產量", f"{x2_opt:.1f} 件")
        st.metric("最大利潤", f"{max_profit:.1f} 萬元")

        st.subheader("📋 資源使用")
        time_used = time_A * x1_opt + time_B * x2_opt
        mat_used  = mat_A  * x1_opt + mat_B  * x2_opt

        st.progress(time_used / time_cap,
                    text=f"工時：{time_used:.1f} / {time_cap:.1f} hr")
        st.progress(mat_used / mat_cap,
                    text=f"原料：{mat_used:.1f} / {mat_cap:.1f} kg")

        # 判斷哪個資源是瓶頸
        st.subheader("🔍 瓶頸分析")
        if abs(time_used - time_cap) < 0.01 and abs(mat_used - mat_cap) < 0.01:
            st.warning("⚠️ 工時與原料同時耗盡（交叉點最佳解）")
        elif abs(time_used - time_cap) < 0.01:
            st.error("🕐 瓶頸：工時已滿載！增加產能優先考慮加班")
        elif abs(mat_used - mat_cap) < 0.01:
            st.error("🧱 瓶頸：原料已耗盡！增加產能優先考慮採購")
        else:
            st.success("✅ 資源尚未完全利用（邊界解）")
    else:
        st.error("❌ 求解失敗：可能是限制條件互相矛盾，請調整參數。")
```

---

## 六、延伸：多限制條件 LP（更複雜的工廠情境）

```python
from scipy.optimize import linprog

# ===== 進階情境：4 種產品、5 種資源限制 =====
# 決策變數：x = [A, B, C, D]（四種產品的生產量）
# 目標：最大化利潤

# 利潤係數（萬元/件）
c = [-8, -5, -6, -4]   # 負號（linprog 最小化）

# 資源限制矩陣（5 個限制條件 × 4 個決策變數）
A_ub = [
    [3, 2, 1, 4],   # 人工工時限制
    [2, 5, 3, 1],   # 機台工時限制
    [1, 1, 2, 1],   # 原料甲限制
    [4, 2, 0, 3],   # 原料乙限制
    [0, 3, 4, 2],   # 外包加工時數限制
]
b_ub = [100, 80, 40, 120, 60]   # 各資源上限

# 求解
result = linprog(c, A_ub=A_ub, b_ub=b_ub,
                 bounds=[(0, None)] * 4, method='highs')

products = ['A', 'B', 'C', 'D']
if result.success:
    print("最佳生產計畫：")
    for prod, qty in zip(products, result.x):
        print(f"  產品 {prod}：{qty:.2f} 件")
    print(f"最大利潤：{-result.fun:.2f} 萬元")
```

---

## 七、課後練習

### 練習 1：影子價格（Shadow Price）分析

```python
# 如果工時上限從 12 提升到 13（多一小時的加班），利潤能增加多少？
# 這個「每增加一單位資源帶來的利潤增量」稱為「影子價格」

# 請修改 b_ub，逐步將工時從 12 增加到 20，
# 計算每一單位工時的「邊際利潤貢獻」（影子價格）
# 並用折線圖呈現。

import numpy as np
from scipy.optimize import linprog

time_caps = np.arange(12, 25)
profits   = []
for tc in time_caps:
    r = linprog([-5, -4], A_ub=[[2, 3], [4, 2]], b_ub=[tc, 16],
                bounds=[(0, None), (0, None)], method='highs')
    profits.append(-r.fun if r.success else np.nan)

# 計算影子價格（相鄰利潤差值）
shadow_prices = np.diff(profits)
print("工時影子價格（每增加 1 hr 的利潤增量）：", shadow_prices.round(3))
```

### 練習 2：思考題

1. 為什麼線性規劃的最佳解一定在「可行解區域的頂點」？用幾何直覺解釋。
2. 若某個決策變數的最佳值不是整數（例如生產 3.7 件），在實際工廠中要怎麼處理？（提示：Integer Programming）
3. 影子價格在採購談判中有什麼應用？如果工時的影子價格是 2 萬元/小時，工廠願意為加班費支付多少？

---

## 📎 重點整理

```
線性規劃問題三要素
├── 目標函數：要最大化（利潤）或最小化（成本）的式子
├── 決策變數：我們要決定的數量（生產多少件）
└── 限制條件：資源上限（工時、原料、資金）

SciPy linprog 使用要點
├── 只能「最小化」→ 最大化問題需對目標取負
├── 限制條件只接受「≤ 」→ 等式須轉換
├── method='highs' 最穩定（Python 3.9+ 後的推薦）
└── result.x = 最佳解，-result.fun = 最大利潤

可行解區域的幾何意義
├── 每個限制條件 = 一條直線（邊界）
├── 所有限制的交集 = 可行解區域（多邊形）
└── 最佳解 = 必在多邊形的某個頂點
```

---

*上一單元：[模組 1-3：NumPy](./Module1_3_NumPy.md) ｜ 下一單元：[模組 2-2：Pandas](./Module2_2_Pandas.md)*
