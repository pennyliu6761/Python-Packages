# 模組 2-2：Pandas — OEE 設備綜合效率戰情儀表板

> **學習目標**：掌握 DataFrame 的資料清理、群組運算與時間序列分析，以「OEE 儀表板」為載體，實現工廠數據的端對端分析流程。

---

## 📌 為什麼工管系要學 Pandas？

製造業的資料 90% 以「表格」形式存在——機台報工、品質記錄、物料清單（BOM）、採購訂單。Pandas 是 Python 中最強大的**表格資料分析工具**，掌握 Pandas 等於掌握了工廠數據的「通用語言」。

**OEE（Overall Equipment Effectiveness，設備綜合效率）**是智慧製造的核心 KPI，由三個指標構成：

```
OEE = 稼動率 × 效能率 × 良率

稼動率（Availability）= 實際運轉時間 / 計畫運轉時間
效能率（Performance）= 理論產能 × 實際運轉時間 / 實際產量  （或反向計算）
良率（Quality）       = 良品數 / 總產品數
```

---

## 🔧 安裝

```bash
pip install pandas matplotlib streamlit
```

---

## 一、Pandas 基礎：DataFrame 操作

```python
import pandas as pd
import numpy as np

# ===== 1. 建立 DataFrame =====
# 方法一：從字典建立（最常見）
data = {
    '機台': ['CNC-01', 'CNC-02', 'CNC-03'],
    '計畫工時': [480, 480, 480],      # 分鐘
    '故障時間': [30, 90, 15],
    '換線時間': [20, 10, 25],
    '良品數':  [820, 650, 890],
    '不良品數': [15, 40, 10],
}
df = pd.DataFrame(data)

# 方法二：從 CSV 讀取（最常用的工廠資料來源）
# df = pd.read_csv('machine_data.csv', encoding='utf-8-sig')

# 方法三：從 Excel 讀取
# df = pd.read_excel('production_report.xlsx', sheet_name='日報表')

# ===== 2. 基本探索 =====
print(df.head())          # 前 5 列
print(df.tail(3))         # 後 3 列
print(df.info())          # 欄位名稱、型態、非空值數
print(df.describe())      # 數值欄位的統計摘要

# ===== 3. 欄位操作 =====
# 選取單一欄位（回傳 Series）
machine_names = df['機台']

# 選取多欄（回傳 DataFrame）
subset = df[['機台', '良品數', '不良品數']]

# 新增計算欄位
df['總產品數']  = df['良品數'] + df['不良品數']
df['良率']      = df['良品數'] / df['總產品數']
df['實際運轉時間'] = df['計畫工時'] - df['故障時間'] - df['換線時間']
df['稼動率']    = df['實際運轉時間'] / df['計畫工時']

print("\n加入 OEE 指標後：")
print(df[['機台', '稼動率', '良率']].round(3))
```

<img width="568" height="133" alt="image" src="https://github.com/user-attachments/assets/a84acc55-d4c1-4e95-b42a-55498c646cd0" />

---

## 二、資料清理（Data Cleaning）

```python
import pandas as pd
import numpy as np

# ===== 模擬一份「髒數據」CSV（工廠資料常見的問題）=====
dirty_data = {
    '日期':    ['2024-01-15', '2024-01-16', None,          '2024/01/18', '2024-01-19'],
    '機台':    ['CNC-01',     'CNC-01',     'CNC-01',      'CNC-01',     'cnc-01'],  # 大小寫不一致
    '運轉時間': [420,          380,          -50,            440,          460],       # 負值異常
    '良品數':  ['820',        '  750  ',    '880',          '錯誤資料',   '810'],     # 字串/空白/非數值
    '總產品數': [835,          780,          895,            900,          820],
}
df = pd.DataFrame(dirty_data)
print("原始髒數據：")
print(df)
print(f"\n缺失值統計：\n{df.isnull().sum()}")

# ===== 清理步驟 =====

# 1. 處理缺失值
df['日期'] = df['日期'].fillna('2024-01-17')   # 用已知值填補

# 2. 統一日期格式
df['日期'] = pd.to_datetime(df['日期'], format='mixed')   # mixed 自動辨識多種格式

# 3. 字串標準化（消除空白、統一大寫）
df['機台'] = df['機台'].str.strip().str.upper()

# 4. 數值轉換（錯誤值變成 NaN）
df['良品數'] = pd.to_numeric(df['良品數'].str.strip(), errors='coerce')
# errors='coerce'：無法轉換的值變成 NaN

# 5. 移除/處理異常值（運轉時間不可為負）
df.loc[df['運轉時間'] < 0, '運轉時間'] = np.nan   # 負值設為 NaN

# 6. 填補 NaN（使用前後值的均值或特定邏輯）
df['運轉時間'] = df['運轉時間'].fillna(df['運轉時間'].median())
df['良品數']   = df['良品數'].fillna(df['良品數'].mean().round())

# 7. 移除重複列
df = df.drop_duplicates()

# 8. 重設索引
df = df.reset_index(drop=True)

print("\n清理後的乾淨數據：")
print(df)
print(f"\n清理後缺失值：\n{df.isnull().sum()}")
```

<img width="568" height="255" alt="image" src="https://github.com/user-attachments/assets/829d99e0-54d5-4d06-90a7-c91dec35edbf" />
<img width="573" height="256" alt="image" src="https://github.com/user-attachments/assets/d6eef394-1118-4441-b916-1ff5ac9df7ae" />

---

## 三、群組運算（GroupBy）

```python
import pandas as pd
import numpy as np

# ===== 模擬一個月的生產日報（30 天 × 5 台機台 = 150 筆記錄）=====
np.random.seed(42)
n_records = 150

df = pd.DataFrame({
    '日期': pd.date_range('2024-01-01', periods=30).repeat(5),
    '機台': ['CNC-01', 'CNC-02', 'CNC-03', 'IMM-01', 'IMM-02'] * 30,
    '班別': np.random.choice(['早班', '中班'], 150),
    '計畫工時': 480,
    '故障時間': np.random.randint(0, 60, 150),
    '換線時間': np.random.randint(10, 40, 150),
    '良品數':  np.random.randint(700, 950, 150),
    '不良品數': np.random.randint(5, 50, 150),
    '機台類型': ['CNC', 'CNC', 'CNC', 'IMM', 'IMM'] * 30
})

# 計算基礎指標
df['總產品數']     = df['良品數'] + df['不良品數']
df['實際運轉時間'] = df['計畫工時'] - df['故障時間'] - df['換線時間']
df['稼動率']       = df['實際運轉時間'] / df['計畫工時']
df['良率']         = df['良品數'] / df['總產品數']
df['OEE']          = df['稼動率'] * df['良率']   # 簡化版（忽略效能率）

# ===== GroupBy 各種用法 =====

# 1. 各機台的月平均 OEE
machine_oee = df.groupby('機台')['OEE'].mean().round(3).sort_values(ascending=False)
print("各機台平均 OEE（由高到低）：")
print(machine_oee)

# 2. 同時計算多個統計量
machine_summary = df.groupby('機台').agg(
    平均稼動率=('稼動率', 'mean'),
    平均良率  =('良率',   'mean'),
    平均OEE   =('OEE',    'mean'),
    總良品數  =('良品數', 'sum'),
    故障次數  =('故障時間', lambda x: (x > 30).sum()),  # 故障時間>30分鐘視為故障
).round(3)
print("\n機台月報摘要：")
print(machine_summary)

# 3. 按機台類型分組比較
type_comparison = df.groupby('機台類型').agg({
    'OEE':    ['mean', 'std', 'min', 'max'],
    '不良品數': 'sum'
}).round(3)
print("\n機台類型比較：")
print(type_comparison)

# 4. 多層分組（機台 + 班別）
shift_analysis = df.groupby(['機台', '班別'])['OEE'].mean().unstack()
print("\n各機台各班別 OEE（樞紐分析）：")
print(shift_analysis.round(3))

# 5. 找出 OEE 最差的前 5 筆記錄（需要改善的優先目標）
worst_days = df.nsmallest(5, 'OEE')[['日期', '機台', '故障時間', 'OEE']]
print("\n⚠️ OEE 最差的 5 個事件：")
print(worst_days)
```

<img width="566" height="276" alt="image" src="https://github.com/user-attachments/assets/cabf06e5-e02b-4339-a3ac-ee9e04949d77" />
<img width="566" height="248" alt="image" src="https://github.com/user-attachments/assets/a670cd0a-75b7-418e-bb5f-9feda751a688" />
<img width="567" height="113" alt="image" src="https://github.com/user-attachments/assets/411314bb-d407-443d-a9cc-112061df23db" />

---

## 四、時間序列分析（Time Series）

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 使用上方的 df（已有 '日期' 欄）
# 將日期設為索引（時間序列的標準做法）
df_ts = df.set_index('日期')

# ===== 時間序列操作 =====

# 1. 按時間重採樣（Resample）：日資料 → 週資料
weekly_oee = df_ts.groupby('機台')['OEE'].resample('W').mean()
# 注意：groupby + resample 的組合是多機台時序分析的標準寫法

# 2. 滾動平均（Rolling Mean）：消除日間波動，看趨勢
df_cnc01 = df[df['機台'] == 'CNC-01'].set_index('日期').sort_index()
df_cnc01['OEE_7天移動平均'] = df_cnc01['OEE'].rolling(window=7, min_periods=1).mean()
df_cnc01['OEE_累積平均']   = df_cnc01['OEE'].expanding().mean()

# 3. 視覺化：OEE 時間趨勢
fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(df_cnc01.index, df_cnc01['OEE'],
        alpha=0.4, color='steelblue', linewidth=1, label='每日 OEE')
ax.plot(df_cnc01.index, df_cnc01['OEE_7天移動平均'],
        color='red', linewidth=2.5, label='7 天移動平均')
ax.plot(df_cnc01.index, df_cnc01['OEE_累積平均'],
        color='green', linewidth=2, linestyle='--', label='累積平均')
ax.axhline(0.85, color='orange', linestyle=':', linewidth=2, label='OEE 目標 85%')
ax.set_title('CNC-01 OEE 月度趨勢')
ax.set_ylabel('OEE')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('oee_trend.png', dpi=150)
plt.show()
```

<img width="1713" height="705" alt="image" src="https://github.com/user-attachments/assets/0b09e64d-8b9a-422e-8da4-29f3b4357eaa" />

---

## 五、🖥️ Streamlit 應用：OEE 戰情儀表板

```python
# 檔案名稱：app_oee.py
# 執行方式：streamlit run app_oee.py

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io

plt.rcParams['font.family'] = ['Microsoft JhengHei', 'PingFang TC', 'sans-serif']

st.set_page_config(page_title="OEE 戰情儀表板", page_icon="🏭", layout="wide")
st.title("🏭 OEE 設備綜合效率戰情儀表板")

# ===== 資料來源選擇 =====
data_source = st.radio("📂 資料來源", ["使用範例資料", "上傳 CSV 檔案"], horizontal=True)

if data_source == "上傳 CSV 檔案":
    uploaded = st.file_uploader(
        "上傳機台日報 CSV",
        type=["csv"],
        help="CSV 需包含欄位：機台, 日期, 計畫工時, 故障時間, 換線時間, 良品數, 不良品數"
    )
    if uploaded:
        df_raw = pd.read_csv(uploaded, encoding='utf-8-sig')
    else:
        st.info("請上傳 CSV 檔案，或切換到「使用範例資料」。")
        st.stop()
else:
    # 自動生成範例資料
    np.random.seed(42)
    n = 150
    df_raw = pd.DataFrame({
        '日期':    pd.date_range('2024-01-01', periods=30).repeat(5),
        '機台':    ['CNC-01', 'CNC-02', 'CNC-03', 'IMM-01', 'IMM-02'] * 30,
        '計畫工時':   480,
        '故障時間': np.random.randint(0,  60, n),
        '換線時間': np.random.randint(10, 40, n),
        '良品數':   np.random.randint(700, 950, n),
        '不良品數': np.random.randint(5,   50, n),
    })

# ===== 資料處理 =====
df = df_raw.copy()
df['日期']         = pd.to_datetime(df['日期'])
df['總產品數']     = df['良品數'] + df['不良品數']
df['實際運轉時間'] = df['計畫工時'] - df['故障時間'] - df['換線時間']
df['稼動率']       = (df['實際運轉時間'] / df['計畫工時']).clip(0, 1)
df['良率']         = (df['良品數'] / df['總產品數']).clip(0, 1)
df['OEE']          = df['稼動率'] * df['良率']

# ===== 篩選器 =====
with st.sidebar:
    st.header("🔍 篩選條件")
    selected_machines = st.multiselect("選擇機台", df['機台'].unique(), default=list(df['機台'].unique()))
    date_range = st.date_input("日期範圍",
                                value=(df['日期'].min(), df['日期'].max()))

df_filtered = df[
    (df['機台'].isin(selected_machines)) &
    (df['日期'] >= pd.to_datetime(date_range[0])) &
    (df['日期'] <= pd.to_datetime(date_range[1]))
]

# ===== KPI 卡片 =====
st.subheader("📊 全廠 KPI 總覽")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
OEE_TARGET = 0.85

avg_oee  = df_filtered['OEE'].mean()
avg_avail = df_filtered['稼動率'].mean()
avg_qual  = df_filtered['良率'].mean()
total_ng  = df_filtered['不良品數'].sum()

kpi1.metric("平均 OEE",   f"{avg_oee:.1%}",
            delta=f"{avg_oee - OEE_TARGET:+.1%} vs 目標 85%",
            delta_color="normal")
kpi2.metric("平均稼動率", f"{avg_avail:.1%}")
kpi3.metric("平均良率",   f"{avg_qual:.1%}")
kpi4.metric("累計不良品", f"{total_ng:,} 件")

st.divider()

# ===== 雙圖並排 =====
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("🏆 各機台 OEE 排行")
    machine_rank = (df_filtered.groupby('機台')['OEE']
                    .mean()
                    .sort_values()
                    .reset_index())
    machine_rank.columns = ['機台', '平均OEE']

    fig, ax = plt.subplots(figsize=(7, 4))
    colors = ['#e74c3c' if v < OEE_TARGET else '#2ecc71'
              for v in machine_rank['平均OEE']]
    bars = ax.barh(machine_rank['機台'], machine_rank['平均OEE'], color=colors)
    ax.axvline(OEE_TARGET, color='orange', linestyle='--', linewidth=2, label=f'目標 {OEE_TARGET:.0%}')
    ax.set_xlabel('平均 OEE')
    ax.set_xlim(0, 1)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0%}'))
    ax.legend()
    ax.grid(True, alpha=0.3, axis='x')
    for bar, val in zip(bars, machine_rank['平均OEE']):
        ax.text(val + 0.01, bar.get_y() + bar.get_height() / 2,
                f'{val:.1%}', va='center', fontsize=10)
    st.pyplot(fig)

with col_b:
    st.subheader("📈 OEE 趨勢（全廠日均）")
    daily_oee = (df_filtered.groupby('日期')['OEE']
                 .mean()
                 .reset_index())
    daily_oee['7天MA'] = daily_oee['OEE'].rolling(7, min_periods=1).mean()

    fig2, ax2 = plt.subplots(figsize=(7, 4))
    ax2.plot(daily_oee['日期'], daily_oee['OEE'],
             alpha=0.4, color='steelblue', linewidth=1)
    ax2.plot(daily_oee['日期'], daily_oee['7天MA'],
             color='red', linewidth=2.5, label='7日移動平均')
    ax2.axhline(OEE_TARGET, color='orange', linestyle='--', linewidth=2, label=f'目標 {OEE_TARGET:.0%}')
    ax2.set_ylabel('OEE')
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0%}'))
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)
    plt.xticks(rotation=30)
    st.pyplot(fig2)

st.divider()

# ===== 詳細數據表 =====
st.subheader("📋 機台詳細報表")
summary = df_filtered.groupby('機台').agg(
    稼動率=('稼動率', lambda x: f'{x.mean():.1%}'),
    良率  =('良率',   lambda x: f'{x.mean():.1%}'),
    OEE   =('OEE',    lambda x: f'{x.mean():.1%}'),
    總良品=('良品數', 'sum'),
    總不良=('不良品數', 'sum'),
    故障總時=('故障時間', 'sum')
).reset_index()

# 加入評等
def oee_grade(val: str) -> str:
    v = float(val.replace('%', '')) / 100
    if v >= 0.85: return '🟢 優秀'
    if v >= 0.70: return '🟡 一般'
    return '🔴 需改善'
summary['評等'] = summary['OEE'].apply(oee_grade)
st.dataframe(summary, hide_index=True, use_container_width=True)

# ===== 下載功能 =====
csv_buf = io.StringIO()
df_filtered.to_csv(csv_buf, index=False, encoding='utf-8-sig')
st.download_button("⬇️ 下載篩選資料 CSV",
                   data=csv_buf.getvalue().encode('utf-8-sig'),
                   file_name='oee_report.csv',
                   mime='text/csv')
```

<img width="1842" height="898" alt="image" src="https://github.com/user-attachments/assets/8caa7be7-b0fa-4d3a-abd4-dc53c35cd1cf" />

---

## 六、Pandas 核心函式速查表

```python
import pandas as pd

# ===== 讀寫 =====
df = pd.read_csv('data.csv', encoding='utf-8-sig', parse_dates=['日期'])
df = pd.read_excel('data.xlsx', sheet_name=0)
df.to_csv('output.csv', index=False, encoding='utf-8-sig')

# ===== 探索 =====
df.shape          # (列數, 欄數)
df.dtypes         # 各欄位資料型態
df.isnull().sum() # 各欄位的缺失值數量
df.nunique()      # 各欄位的唯一值數量
df.value_counts() # 某欄位的值分佈

# ===== 選取 =====
df['欄位']           # 單欄 → Series
df[['A', 'B']]       # 多欄 → DataFrame
df.loc[0]            # 第 0 列（by label）
df.iloc[0]           # 第 0 列（by position）
df.loc[df['A'] > 5]  # 條件篩選
df.query('A > 5')    # 用字串查詢（更易讀）

# ===== 清理 =====
df.dropna()                              # 移除含 NaN 的列
df.fillna(0)                             # 填補 NaN
df.drop_duplicates()                     # 移除重複列
df['欄位'].str.strip().str.upper()       # 字串清理
pd.to_numeric(df['欄位'], errors='coerce')  # 強制轉數值
pd.to_datetime(df['日期'], format='mixed')  # 轉日期

# ===== 運算 =====
df.groupby('類別')['值'].mean()               # 分組平均
df.groupby('類別').agg({'A': 'sum', 'B': 'mean'})  # 多欄不同聚合
df.pivot_table(values='值', index='列', columns='欄', aggfunc='mean')  # 樞紐
df.merge(df2, on='key', how='left')          # 合併（類似 SQL JOIN）
df.sort_values('欄位', ascending=False)       # 排序

# ===== 時間序列 =====
df.set_index('日期')                          # 設時間索引
df.resample('W').mean()                       # 週重採樣
df['欄位'].rolling(7).mean()                  # 7 期滾動均值
```

---

## 七、課後練習

### 練習 1：故障帕雷托分析

```python
import pandas as pd
import matplotlib.pyplot as plt

# 情境：一個月的故障原因記錄
failure_log = pd.DataFrame({
    '故障原因': ['刀具磨損', '冷卻液不足', '刀具磨損', '電氣故障', '刀具磨損',
                 '冷卻液不足', '夾具鬆動', '刀具磨損', '電氣故障', '刀具磨損',
                 '夾具鬆動', '刀具磨損', '程式錯誤', '冷卻液不足', '刀具磨損'],
    '停機時間（分鐘）': [45, 20, 50, 120, 40, 25, 35, 55, 90, 60, 30, 45, 15, 20, 50]
})

# 請你：
# 1. 用 groupby 計算各故障原因的總停機時間
# 2. 排序並計算累積百分比
# 3. 繪製帕雷托圖（長條圖 + 累積折線）
# 4. 找出造成 80% 停機時間的「關鍵少數」故障原因

# --- 提示 ---
cause_summary = (failure_log.groupby('故障原因')['停機時間（分鐘）']
                 .sum()
                 .sort_values(ascending=False))
cumulative_pct = cause_summary.cumsum() / cause_summary.sum() * 100
print(cause_summary)
print(cumulative_pct)
# 在此完成帕雷托圖繪製...
```

<img width="1485" height="886" alt="pareto_chart" src="https://github.com/user-attachments/assets/b6f84a8c-032c-4038-911d-da4e94448e75" />

### 練習 2：思考題

1. OEE 低的原因可以是稼動率低、效能率低、或良率低，**三者的改善策略**有何不同？各對應什麼工廠問題？
2. 為什麼要用「7 天移動平均」而不是直接看每日 OEE？在什麼情況下短期波動可以忽略？
3. 如果要把這個儀表板部署讓全廠主管都能用，你需要考慮哪些問題（資料更新方式、權限、網路等）？

---

## 📎 重點整理

```
Pandas 核心操作體系
├── 讀取：read_csv / read_excel
├── 探索：head, info, describe, value_counts
├── 清理：fillna, dropna, str.strip, to_numeric
├── 計算：新增欄位、條件篩選（loc + 布林）
├── 聚合：groupby + agg（分組統計的主力）
└── 時序：set_index, resample, rolling

OEE 指標體系
├── 稼動率 = 實際運轉 / 計畫工時（↑ 減少故障、換線）
├── 效能率 = 標準產能 / 實際產能（↑ 提速、減少空轉）
├── 良率   = 良品 / 總產品（↑ 提升製程穩定度）
└── OEE 世界級水準 ≥ 85%
```

---

*上一單元：[模組 2-1：SciPy](./Module2_1_SciPy.md) ｜ 下一單元：[模組 3-1：Scikit-Learn](./Module3_1_ScikitLearn.md)*
