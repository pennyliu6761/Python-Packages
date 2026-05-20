# 模組 4-1：Requests & BeautifulSoup — 原物料價格即時看板

> **學習目標**：理解 HTTP 通訊協定與 HTML 結構，實作網路爬蟲抓取公開市場資料，並以視覺化呈現採購決策所需的價格趨勢。

---

## 📌 為什麼工管系要學網路爬蟲？

採購成本是工廠製造成本的最大佔比（通常 40~60%）。**即時掌握原物料市場行情**，是採購部門降低成本的第一步：
- 銅、鋼、鋁等原材料的現貨價格影響每日採購決策
- 比較多家供應商報價，判斷是否有套利空間
- 追蹤競品定價，做為自家訂價策略的參考

爬蟲讓我們能**自動化地從公開網頁收集數據**，取代人工查詢的低效率。

---

## 🔧 安裝

```bash
pip install requests beautifulsoup4 pandas matplotlib streamlit lxml
```

---

## 一、HTTP 基礎：瀏覽器與伺服器的對話

```
你（Client）                     網站伺服器（Server）
     │                                  │
     │── GET /commodity/copper HTTP/1.1 ──→│   請求（Request）
     │                                  │
     │←── HTTP/1.1 200 OK ───────────────│   回應（Response）
     │    Content-Type: text/html        │
     │    <html>...<td>8500</td>...</html>│
     │                                  │

HTTP 方法：
  GET    → 取得頁面（爬蟲最常用）
  POST   → 送出表單（登入、搜尋）

HTTP 狀態碼：
  200 OK          → 成功
  301/302         → 重新導向
  403 Forbidden   → 被拒絕（需要登入或防爬機制）
  404 Not Found   → 頁面不存在
  429 Too Many    → 請求太頻繁（被限速）
  500 Server Error→ 伺服器錯誤
```

---

## 二、Requests：發送 HTTP 請求

```python
import requests
from requests.exceptions import RequestException
import time

# ===== 基本 GET 請求 =====
url = "https://example.com"
response = requests.get(url)

print(f"狀態碼：{response.status_code}")       # 200 表示成功
print(f"內容長度：{len(response.text)} 字元")
print(f"編碼：{response.encoding}")
print(response.text[:500])                    # 印出前 500 字元的 HTML

# ===== 加入請求標頭（Headers）=====
# 很多網站會檢查 User-Agent，若發現不是瀏覽器就拒絕
# 加入 headers 模擬瀏覽器行為（合理的技術行為）
headers = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/120.0.0.0 Safari/537.36'),
    'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

response = requests.get(url, headers=headers, timeout=10)  # timeout=10 秒

# ===== 錯誤處理（爬蟲一定要有！）=====
def safe_get(url: str, headers: dict = None, retries: int = 3) -> requests.Response | None:
    """
    帶有重試機制的安全 GET 請求
    
    Parameters:
        url:     目標 URL
        headers: 請求標頭
        retries: 最大重試次數
    
    Returns:
        Response 物件，或 None（失敗）
    """
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()   # 若狀態碼 >= 400，拋出例外
            return response

        except requests.exceptions.Timeout:
            print(f"⏱️ 第 {attempt} 次嘗試：請求超時")
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP 錯誤：{e}")
            break   # 4xx/5xx 錯誤不重試
        except requests.exceptions.ConnectionError:
            print(f"🔌 第 {attempt} 次嘗試：連線失敗")
        except RequestException as e:
            print(f"⚠️ 未知錯誤：{e}")
            break

        if attempt < retries:
            wait_time = 2 ** attempt  # 指數退避：2秒、4秒、8秒
            print(f"   {wait_time} 秒後重試...")
            time.sleep(wait_time)

    return None


# ===== 送出 POST 請求（例如查詢特定日期的資料）=====
# post_data = {'date': '2024-01-15', 'material': 'copper'}
# response = requests.post("https://api.example.com/prices", data=post_data, headers=headers)
```

---

## 三、BeautifulSoup：解析 HTML

```python
from bs4 import BeautifulSoup

# ===== 理解 HTML 的樹狀結構 =====
html_example = """
<html>
<body>
    <div class="price-table">
        <h2>銅期貨價格</h2>
        <table id="market-data">
            <thead>
                <tr>
                    <th>日期</th>
                    <th>收盤價（元/噸）</th>
                    <th>漲跌</th>
                </tr>
            </thead>
            <tbody>
                <tr class="data-row">
                    <td>2024-01-15</td>
                    <td class="price">68,500</td>
                    <td class="change positive">+350</td>
                </tr>
                <tr class="data-row">
                    <td>2024-01-14</td>
                    <td class="price">68,150</td>
                    <td class="change negative">-200</td>
                </tr>
            </tbody>
        </table>
    </div>
</body>
</html>
"""

# ===== 建立 BeautifulSoup 物件 =====
soup = BeautifulSoup(html_example, 'lxml')   # lxml 解析器，速度快

# ===== 各種選取方式 =====

# 1. find()：找到第一個符合的元素
title = soup.find('h2')
print(f"標題：{title.text}")   # .text 取得文字內容

# 2. find_all()：找到所有符合的元素（回傳 list）
all_rows = soup.find_all('tr', class_='data-row')   # class_ 注意底線（避免與 Python 保留字衝突）
print(f"\n找到 {len(all_rows)} 列資料")

# 3. CSS Selector（最強大的選取方式）
# select() 使用 CSS 選擇器語法，與前端開發一致
prices      = soup.select('#market-data .price')        # id=market-data 下的 class=price
positive    = soup.select('.change.positive')           # 同時有 change 和 positive 的元素
first_price = soup.select_one('#market-data .price')    # 只取第一個

print(f"\n所有價格：{[p.text for p in prices]}")
print(f"上漲：{[p.text for p in positive]}")

# 4. 取得屬性值
link_example = BeautifulSoup('<a href="https://example.com" data-id="123">點我</a>', 'lxml')
anchor = link_example.find('a')
print(f"\nhref 屬性：{anchor['href']}")
print(f"data-id 屬性：{anchor.get('data-id', '無')}")   # .get() 更安全，找不到時返回預設值

# ===== 解析表格資料（工廠資料最常見的格式）=====
import pandas as pd

table  = soup.find('table', id='market-data')
headers = [th.text for th in table.find_all('th')]
rows   = []
for tr in table.find('tbody').find_all('tr'):
    cells = [td.text.strip() for td in tr.find_all('td')]
    rows.append(cells)

df_table = pd.DataFrame(rows, columns=headers)
print(f"\n解析後的表格：")
print(df_table)
```

---

## 四、完整爬蟲範例：公開金屬價格資料

```python
# ===== 實際範例：爬取公開資料（以範例 URL 結構說明）=====
# ⚠️ 爬蟲前請務必：
#    1. 確認網站的 robots.txt 是否允許爬取
#    2. 閱讀網站服務條款（Terms of Service）
#    3. 控制爬取頻率，避免對伺服器造成負擔（加 time.sleep）
#    4. 優先使用官方 API（若有提供）

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from datetime import datetime, timedelta

def scrape_metal_price(metal: str = "copper", days: int = 7) -> pd.DataFrame:
    """
    爬取金屬現貨價格的通用框架
    （此為說明程式碼架構，實際 URL 需根據目標網站調整）
    
    替代方案（建議用於教學）：
    - yfinance 套件：免費取得商品期貨的歷史數據
    - 台灣銀行匯率公告（政府公開資料，合法爬取）
    - 中鋼公告牌價（官方公開，可參考使用）
    """
    headers = {
        'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                       'AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36')
    }
    
    all_prices = []

    for i in range(days):
        target_date = datetime.now() - timedelta(days=i)

        # ===== 以下為結構示意，實際 URL 需替換 =====
        # url = f"https://public-commodity-site.example/price?metal={metal}&date={target_date.strftime('%Y-%m-%d')}"

        # ===== 改用模擬資料展示流程 =====
        # （實際爬蟲時，此處換成 requests.get(url, headers=headers)）
        simulated_price = {
            'copper': 68000 + random.gauss(0, 500),
            'steel':  4500  + random.gauss(0, 100),
            'aluminum': 18000 + random.gauss(0, 300),
        }.get(metal, 10000 + random.gauss(0, 200))

        all_prices.append({
            '日期':   target_date.strftime('%Y-%m-%d'),
            '品名':   metal,
            '收盤價': round(simulated_price, 0),
        })

        time.sleep(random.uniform(1.0, 2.5))   # 隨機等待（禮貌性延遲，避免被封鎖）

    df = pd.DataFrame(all_prices).sort_values('日期')
    df['收盤價'] = pd.to_numeric(df['收盤價'])
    df['日期']   = pd.to_datetime(df['日期'])
    return df.reset_index(drop=True)


# ===== 使用 yfinance 取得真實期貨資料（教學推薦）=====
# pip install yfinance

def get_commodity_price_yfinance(ticker: str = "HG=F", days: int = 30) -> pd.DataFrame:
    """
    使用 yfinance 取得商品期貨歷史價格（完全合法、免費）
    
    常用 Ticker：
      HG=F  → 銅期貨（LME，美元/磅）
      SI=F  → 白銀期貨
      GC=F  → 黃金期貨
      ZS=F  → 大豆期貨
      CL=F  → 原油期貨（West Texas Intermediate）
    """
    try:
        import yfinance as yf
        end   = datetime.now()
        start = end - timedelta(days=days)
        
        data = yf.download(ticker, start=start, end=end, progress=False)
        df = data[['Close']].reset_index()
        df.columns = ['日期', '收盤價']
        df['Ticker'] = ticker
        return df
    except ImportError:
        print("請先安裝：pip install yfinance")
        return pd.DataFrame()
    except Exception as e:
        print(f"資料取得失敗：{e}")
        return pd.DataFrame()
```

---

## 五、資料解析與清理

```python
import pandas as pd
import numpy as np

def clean_price_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    原物料價格資料的清理流程
    （爬取回來的資料常需要以下處理）
    """
    df = df.copy()
    
    # 1. 去除價格中的千分位逗號 "68,500" → 68500
    if df['收盤價'].dtype == object:
        df['收盤價'] = df['收盤價'].str.replace(',', '', regex=False)
        df['收盤價'] = pd.to_numeric(df['收盤價'], errors='coerce')

    # 2. 移除缺失值（假日、停市日）
    df = df.dropna(subset=['收盤價'])

    # 3. 移除明顯異常值（若價格超過合理範圍的 3 倍標準差）
    mean  = df['收盤價'].mean()
    std   = df['收盤價'].std()
    df    = df[(df['收盤價'] > mean - 3 * std) & (df['收盤價'] < mean + 3 * std)]

    # 4. 確保日期排序
    df = df.sort_values('日期').reset_index(drop=True)

    # 5. 計算衍生指標
    df['日漲跌']  = df['收盤價'].diff()                    # 每日漲跌金額
    df['日漲跌率'] = df['收盤價'].pct_change() * 100       # 每日漲跌百分比
    df['5日均線']  = df['收盤價'].rolling(5, min_periods=1).mean()   # 短期趨勢
    df['20日均線'] = df['收盤價'].rolling(20, min_periods=1).mean()  # 中期趨勢

    return df


# 模擬生成 30 天價格資料（教學用）
import random
random.seed(42)
dates  = pd.date_range('2024-01-01', periods=30)
prices = [68000]
for _ in range(29):
    prices.append(prices[-1] * (1 + random.gauss(0, 0.01)))  # ±1% 隨機波動

raw_df = pd.DataFrame({'日期': dates, '收盤價': prices})
df_cleaned = clean_price_data(raw_df)
print(df_cleaned.tail(10).round(1))
```

---

## 六、🖥️ Streamlit 應用：原物料價格即時看板

```python
# 檔案名稱：app_commodity.py
# 執行方式：streamlit run app_commodity.py

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from datetime import datetime, timedelta

plt.rcParams['font.family'] = ['Microsoft JhengHei', 'PingFang TC', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

st.set_page_config(page_title="原物料價格看板", page_icon="📈", layout="wide")
st.title("📈 原物料價格即時看板")
st.markdown("追蹤銅、鋼、鋁等原物料的近期價格走勢，輔助採購成本分析。")

# ===== 資料取得（教學版：模擬資料 + 可替換為真實爬蟲）=====
@st.cache_data(ttl=3600)   # 快取 1 小時（避免每次互動都重新爬取）
def get_price_data(metal: str, days: int) -> pd.DataFrame:
    """
    教學版：使用模擬資料
    實際部署時，替換為 yfinance 或真實爬蟲
    """
    np.random.seed(hash(metal) % 100)

    base_prices = {
        '銅（元/噸）':   68000,
        '鋼鐵（元/噸）':  4500,
        '鋁（元/噸）':   18000,
        '鎳（元/噸）': 125000,
    }
    base = base_prices.get(metal, 10000)
    daily_ret = np.random.normal(0, 0.008, days)  # 每日 ±0.8% 波動

    prices = [base]
    for r in daily_ret[1:]:
        prices.append(prices[-1] * (1 + r))

    dates = pd.date_range(end=datetime.today(), periods=days, freq='B')  # 'B' = 工作日
    df = pd.DataFrame({'日期': dates, '收盤價': prices})
    df['日漲跌率'] = df['收盤價'].pct_change() * 100
    df['5日均線']  = df['收盤價'].rolling(5, min_periods=1).mean()
    df['20日均線'] = df['收盤價'].rolling(20, min_periods=1).mean()
    return df

# ===== 側邊欄 =====
with st.sidebar:
    st.header("⚙️ 設定")
    selected_metal = st.selectbox("選擇原物料", ['銅（元/噸）', '鋼鐵（元/噸）', '鋁（元/噸）', '鎳（元/噸）'])
    days = st.slider("查詢天數", 10, 90, 30)

    st.divider()
    st.button("🔄 更新資料", help="清除快取，重新取得最新資料",
               on_click=st.cache_data.clear)

    st.subheader("📚 採購參考")
    st.markdown("""
    **採購時機參考原則：**
    - 價格低於 20 日均線 → 相對低點，考慮採購
    - 價格連續上漲 5 天 → 考慮提前備貨
    - 日漲跌幅 > 3% → 市場劇烈波動，觀望
    """)

df = get_price_data(selected_metal, days)

# ===== KPI 卡片 =====
latest = df.iloc[-1]
prev   = df.iloc[-2]

col1, col2, col3, col4 = st.columns(4)
col1.metric(f"最新價格",
            f"${latest['收盤價']:,.0f}",
            delta=f"{latest['日漲跌率']:+.2f}%",
            delta_color="inverse")  # inverse：漲紅跌綠（原物料成本觀點）

period_change = (latest['收盤價'] - df.iloc[0]['收盤價']) / df.iloc[0]['收盤價'] * 100
col2.metric(f"{days}天漲跌", f"{period_change:+.1f}%")
col3.metric("期間最高", f"${df['收盤價'].max():,.0f}")
col4.metric("期間最低", f"${df['收盤價'].min():,.0f}")

# ===== 主圖：價格趨勢 =====
st.subheader(f"📊 {selected_metal} 近 {days} 天走勢")
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True,
                                gridspec_kw={'height_ratios': [3, 1]})

# 上圖：價格 + 均線
ax1.fill_between(df['日期'], df['收盤價'],
                  df['收盤價'].min() * 0.99,
                  alpha=0.1, color='steelblue')
ax1.plot(df['日期'], df['收盤價'],   color='steelblue',  linewidth=2,   label='收盤價')
ax1.plot(df['日期'], df['5日均線'],  color='orange',     linewidth=1.5, linestyle='--', label='5日均線 (MA5)')
ax1.plot(df['日期'], df['20日均線'], color='red',        linewidth=1.5, linestyle='--', label='20日均線 (MA20)')

# 標示最新價格
ax1.scatter(df['日期'].iloc[-1], latest['收盤價'],
            color='red', s=100, zorder=5)
ax1.annotate(f"最新：${latest['收盤價']:,.0f}",
             xy=(df['日期'].iloc[-1], latest['收盤價']),
             xytext=(-80, 15), textcoords='offset points',
             fontsize=10, color='red',
             arrowprops=dict(arrowstyle='->', color='red', lw=1.5))

ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'${x:,.0f}'))
ax1.set_ylabel('價格（元/噸）', fontsize=11)
ax1.legend(loc='upper left', fontsize=10)
ax1.grid(True, alpha=0.25, linestyle=':')

# 下圖：日漲跌率（柱狀）
colors_bar = ['#e74c3c' if x > 0 else '#2ecc71' for x in df['日漲跌率'].fillna(0)]
ax2.bar(df['日期'], df['日漲跌率'].fillna(0), color=colors_bar, alpha=0.8)
ax2.axhline(0, color='black', linewidth=0.8)
ax2.set_ylabel('日漲跌（%）', fontsize=10)
ax2.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{x:+.1f}%'))
ax2.grid(True, alpha=0.25, linestyle=':')

plt.xticks(rotation=30)
plt.tight_layout()
st.pyplot(fig)

# ===== 採購建議 =====
st.subheader("💼 採購成本分析")

unit_cost = latest['收盤價']
col_a, col_b = st.columns(2)

with col_a:
    monthly_qty = st.number_input("月需求量（噸）", min_value=1.0, value=10.0, step=0.5)
    monthly_cost = unit_cost * monthly_qty
    st.metric("預估月採購成本", f"${monthly_cost:,.0f} 元")

    # 和 20 日均線比較（判斷相對高低）
    ma20_latest = df['20日均線'].iloc[-1]
    vs_ma20 = (unit_cost - ma20_latest) / ma20_latest * 100
    if vs_ma20 > 2:
        st.warning(f"⚠️ 目前價格高於 20 日均線 {vs_ma20:+.1f}%，建議等待回落或小量分批購入。")
    elif vs_ma20 < -2:
        st.success(f"✅ 目前價格低於 20 日均線 {vs_ma20:+.1f}%，相對低點，可考慮提前採購備料。")
    else:
        st.info(f"ℹ️ 目前價格接近 20 日均線（{vs_ma20:+.1f}%），處於中性區間。")

with col_b:
    st.markdown("**近 5 日價格摘要**")
    recent = df.tail(5)[['日期', '收盤價', '日漲跌率']].copy()
    recent['收盤價']   = recent['收盤價'].map(lambda x: f"${x:,.0f}")
    recent['日漲跌率'] = recent['日漲跌率'].map(lambda x: f"{x:+.2f}%" if pd.notna(x) else "—")
    recent['日期'] = recent['日期'].dt.strftime('%m/%d')
    st.dataframe(recent, hide_index=True, use_container_width=True)
```

---

## 七、爬蟲倫理與法律注意事項

```python
# ===== 合法爬蟲的基本原則 =====

# 1. 檢查 robots.txt
import requests
response = requests.get("https://example.com/robots.txt")
# 確認 Disallow: /  或特定路徑是否被禁止爬取

# 2. 控制爬取頻率（避免 DDoS）
import time
time.sleep(2)   # 每次請求之間至少等待 2 秒

# 3. 使用官方 API（優先選擇！）
# 很多資料提供商有免費 API，效率比爬蟲高且合法
# 例如：FRED API（美聯儲經濟數據）、Alpha Vantage（股票/商品）

# 4. 快取已取得的資料（減少重複請求）
import os
import json

def cached_fetch(url: str, cache_path: str, ttl_hours: int = 6) -> dict:
    """帶有本地快取的請求，避免重複爬取相同資料"""
    import time
    # 若快取存在且未過期，直接讀取
    if os.path.exists(cache_path):
        mtime     = os.path.getmtime(cache_path)
        age_hours = (time.time() - mtime) / 3600
        if age_hours < ttl_hours:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)

    # 快取不存在或已過期，重新爬取
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    data = response.json()

    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return data
```

---

## 八、課後練習

### 練習 1：爬取並解析 HTML 表格

```python
import requests
from bs4 import BeautifulSoup
import pandas as pd

# 台灣銀行牌告匯率（政府公開資料，可合法爬取）
# URL: https://rate.bot.com.tw/xrt?Lang=zh-TW

url = "https://rate.bot.com.tw/xrt?Lang=zh-TW"
headers = {'User-Agent': 'Mozilla/5.0 (compatible; educational-bot/1.0)'}

# 請你：
# 1. 用 requests.get() 取得頁面
# 2. 用 BeautifulSoup 找到匯率表格
# 3. 解析出幣別、即期買入、即期賣出三欄
# 4. 用 Pandas 建立 DataFrame 並計算買賣價差
# 5. 找出「買賣價差最小的幣別」（對跨國採購最有利）

response = requests.get(url, headers=headers, timeout=10)
soup = BeautifulSoup(response.text, 'lxml')
# 在此完成解析...
```

### 練習 2：思考題

1. 如果你要每天早上 8 點自動更新一次原物料價格，應該怎麼實作排程？（提示：Windows 工作排程器、Linux cron job、Python `schedule` 套件）
2. 為什麼要設定 `User-Agent` Header？如果不設定，會發生什麼事？
3. 假設你爬取的資料發現「某供應商的報價比市場均價高 15%」，在採購談判中你會如何使用這個資訊？

---

## 📎 重點整理

```
爬蟲工具鏈
├── requests        → 發送 HTTP 請求（GET/POST）
├── BeautifulSoup   → 解析 HTML，定位元素
├── pandas          → 清理與分析爬回來的資料
└── time.sleep()    → 限速（爬蟲倫理的基本功）

HTML 元素選取優先順序
├── id（唯一）    → #my-table
├── class（多個）→ .price-row
├── tag          → table, tr, td
└── 屬性         → [data-type="price"]

合法爬蟲三原則
├── 1. 確認 robots.txt 允許
├── 2. 控制頻率（至少 1~2 秒間隔）
└── 3. 優先使用官方 API（yfinance、政府開放資料）

採購應用
├── 即時掌握原物料市價 → 判斷報價是否合理
├── 歷史趨勢分析 → 找採購時機（低點買）
└── 跨供應商比價 → 議價籌碼
```

---

*上一單元：[模組 3-1：Scikit-Learn](./Module3_1_ScikitLearn.md) ｜ 下一單元：[模組 4-2：Scrapy](./Module4_2_Scrapy.md)*
