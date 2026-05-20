# 模組 4-2：Scrapy — 大規模結構化爬蟲（進階）

> **學習目標**：理解 Scrapy 框架的非同步架構，掌握大規模、結構化資料搜集的工程實踐；以「競品價格雷達圖」為最終成果展示。

> ⚠️ **適用對象**：本模組屬於期末進階延伸，建議完成前四個模組後再挑戰。

---

## 📌 為什麼需要 Scrapy？

| 比較項目 | requests + BeautifulSoup | Scrapy |
|----------|--------------------------|--------|
| 學習難度 | ⭐⭐ 低（程序式，直觀） | ⭐⭐⭐⭐ 中高（框架式） |
| 資料量 | 幾十~幾百頁 | 幾萬~幾百萬頁 |
| 速度 | 慢（同步，一次一個請求）| 快（非同步並行，可設並發數）|
| 資料儲存 | 手動處理 | 內建 Pipeline 自動儲存 |
| 防爬應對 | 手動處理 Retry、Delay | 內建 Middleware 統一管理 |
| 適用場景 | 教學、小型任務 | **生產環境、大規模任務** |

---

## 🔧 安裝

```bash
pip install scrapy
scrapy version   # 確認安裝成功
```

---

## 一、Scrapy 架構概覽

```
┌─────────────────────────────────────────────────────┐
│                    Scrapy Engine                     │
│  （調度所有元件，負責資料流的流轉）                    │
└──────┬─────────────────────────────────────┬─────────┘
       │                                     │
┌──────▼──────┐  Request/Response  ┌─────────▼──────────┐
│   Scheduler  │←───────────────────│      Downloader    │
│  （管理待爬  │   (排隊處理)       │  （實際發送 HTTP  │
│   URL 佇列）│                    │   請求下載網頁）   │
└─────────────┘                    └────────────────────┘
                                           │
                                   ┌───────▼─────────┐
                                   │     Spider       │
                                   │  （你寫的爬蟲   │
                                   │   解析 HTML）    │
                                   └───────┬──────────┘
                                           │ Item
                                   ┌───────▼──────────┐
                                   │  Item Pipeline   │
                                   │  （資料清理、    │
                                   │   存入 CSV/DB）  │
                                   └──────────────────┘

Middleware 層（可插拔的中介軟體）：
  - 自動加 User-Agent 輪換
  - 自動重試失敗請求
  - 設定代理 IP 池
```

---

## 二、建立 Scrapy 專案

```bash
# ===== 指令操作 =====
# 1. 建立專案
scrapy startproject commodity_tracker

# 專案結構：
# commodity_tracker/
# ├── scrapy.cfg                    ← 部署設定檔
# └── commodity_tracker/
#     ├── __init__.py
#     ├── settings.py               ← 全域設定（速度、Pipeline、Middleware）
#     ├── items.py                  ← 定義資料結構（欄位）
#     ├── pipelines.py              ← 資料清理與儲存邏輯
#     ├── middlewares.py            ← 自訂中介軟體
#     └── spiders/
#         └── your_spider.py        ← 你的爬蟲邏輯

# 2. 進入專案目錄
cd commodity_tracker

# 3. 建立新的 Spider
scrapy genspider price_spider example.com
```

---

## 三、定義資料結構（items.py）

```python
# commodity_tracker/items.py
import scrapy

class CommodityPriceItem(scrapy.Item):
    """
    定義爬取的資料欄位（類似 Python dataclass）
    每個欄位都是 scrapy.Field()
    """
    # 商品基本資訊
    product_name  = scrapy.Field()    # 商品名稱
    product_id    = scrapy.Field()    # 商品 ID / 料號
    category      = scrapy.Field()    # 分類（原材料/半成品/成品）

    # 價格資訊
    price         = scrapy.Field()    # 現貨價格
    currency      = scrapy.Field()    # 幣別（TWD/USD）
    unit          = scrapy.Field()    # 單位（噸/公斤/件）

    # 來源與時間
    source_url    = scrapy.Field()    # 來源網頁 URL
    source_name   = scrapy.Field()    # 資料來源名稱
    scraped_at    = scrapy.Field()    # 爬取時間

    # 供應商資訊（若有）
    supplier      = scrapy.Field()
    location      = scrapy.Field()    # 產地 / 供應商所在地
```

---

## 四、撰寫 Spider（爬蟲主體）

```python
# commodity_tracker/spiders/price_spider.py
import scrapy
from datetime import datetime
from commodity_tracker.items import CommodityPriceItem


class PriceSpider(scrapy.Spider):
    """
    商品價格爬蟲
    
    Scrapy Spider 的三個必要元素：
    1. name     → 爬蟲的識別名稱（執行時用）
    2. start_urls → 起始 URL 清單
    3. parse()  → 預設的解析函式
    """

    name = 'price_spider'

    # 起始 URL（可以是多個頁面的入口）
    start_urls = [
        # 'https://commodity-site.example.com/metals/',
        # 'https://another-source.example.com/materials/',
    ]

    # 設定此 Spider 的個別參數（覆蓋 settings.py 的全域設定）
    custom_settings = {
        'DOWNLOAD_DELAY': 2,         # 每個請求間隔 2 秒（禮貌性延遲）
        'RANDOMIZE_DOWNLOAD_DELAY': True,  # 隨機化延遲（更難被偵測）
        'CONCURRENT_REQUESTS': 4,    # 同時最多 4 個並行請求
    }

    def parse(self, response):
        """
        解析首頁，找到所有商品的連結，依序爬取
        
        ⭐ Scrapy 的精髓：parse() 可以 yield Request，形成「爬蟲鏈」
        """
        # 找出所有商品連結（CSS Selector）
        product_links = response.css('a.product-link::attr(href)').getall()

        for link in product_links:
            # yield Request：告訴 Scrapy 去爬這個連結
            # callback：指定用 parse_product() 來解析這個頁面
            yield response.follow(
                link,
                callback=self.parse_product,
                meta={'source_name': response.url}   # 傳遞額外資訊給下一個 callback
            )

        # 處理分頁：找「下一頁」按鈕
        next_page = response.css('a.next-page::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def parse_product(self, response):
        """
        解析商品詳細頁面，提取價格資訊
        """
        item = CommodityPriceItem()

        # ===== 資料提取（CSS Selector）=====
        item['product_name'] = response.css('h1.product-title::text').get('').strip()
        item['product_id']   = response.css('[data-sku]::attr(data-sku)').get('')
        item['category']     = response.css('.breadcrumb > li:last-child::text').get('')

        # 價格（通常需要去除逗號、貨幣符號）
        price_text = response.css('.price-value::text').get('0')
        price_text = price_text.replace(',', '').replace('NT$', '').strip()

        try:
            item['price'] = float(price_text)
        except ValueError:
            item['price'] = None   # 無法解析時設為 None，由 Pipeline 處理

        item['currency']    = 'TWD'
        item['unit']        = response.css('.price-unit::text').get('件')
        item['source_url']  = response.url
        item['source_name'] = response.meta.get('source_name', '')
        item['scraped_at']  = datetime.now().isoformat()
        item['supplier']    = response.css('.supplier-name::text').get('')
        item['location']    = response.css('.location::text').get('')

        yield item  # 將 Item 交給 Pipeline 處理


# ===== 使用 XPath 的替代寫法（有時比 CSS Selector 更強大）=====
# response.xpath('//h1[@class="product-title"]/text()').get()
# response.xpath('//table[@id="price-table"]//tr/td[2]/text()').getall()
```

---

## 五、資料清理與儲存（pipelines.py）

```python
# commodity_tracker/pipelines.py
import csv
import json
import sqlite3
from datetime import datetime
from itemadapter import ItemAdapter


class ValidationPipeline:
    """
    第一道 Pipeline：資料驗證
    丟棄不完整或明顯錯誤的資料
    """

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        # 必要欄位檢查
        if not adapter.get('product_name'):
            raise DropItem(f"缺少商品名稱：{item}")

        if adapter.get('price') is None or adapter['price'] <= 0:
            raise DropItem(f"無效價格：{item}")

        return item   # 返回 item，繼續傳給下一個 Pipeline


class CleaningPipeline:
    """
    第二道 Pipeline：資料清理
    標準化格式、修正常見錯誤
    """

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        # 字串欄位去除前後空白
        for field in ['product_name', 'category', 'supplier', 'location']:
            if adapter.get(field):
                adapter[field] = adapter[field].strip()

        # 統一商品名稱大小寫
        if adapter.get('product_name'):
            adapter['product_name'] = adapter['product_name'].upper()

        return item


class CsvExportPipeline:
    """
    第三道 Pipeline：儲存為 CSV
    """

    def open_spider(self, spider):
        """Spider 啟動時開啟 CSV 檔案"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        self.file = open(f'prices_{timestamp}.csv', 'w',
                         newline='', encoding='utf-8-sig')
        self.writer = csv.DictWriter(self.file, fieldnames=[
            'product_name', 'price', 'currency', 'unit',
            'supplier', 'location', 'source_url', 'scraped_at'
        ])
        self.writer.writeheader()

    def close_spider(self, spider):
        """Spider 結束時關閉檔案"""
        self.file.close()
        print(f"✅ 資料已儲存至 CSV（共 {self.count} 筆）")

    def process_item(self, item, spider):
        self.writer.writerow(dict(item))
        self.count = getattr(self, 'count', 0) + 1
        return item


class SqlitePipeline:
    """
    進階 Pipeline：儲存到 SQLite 資料庫（方便後續查詢）
    """

    def open_spider(self, spider):
        self.conn   = sqlite3.connect('commodity_prices.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS prices (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT,
                price        REAL,
                currency     TEXT,
                unit         TEXT,
                supplier     TEXT,
                source_url   TEXT,
                scraped_at   TEXT
            )
        ''')
        self.conn.commit()

    def close_spider(self, spider):
        self.conn.close()

    def process_item(self, item, spider):
        self.cursor.execute('''
            INSERT INTO prices (product_name, price, currency, unit, supplier, source_url, scraped_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            item.get('product_name'),
            item.get('price'),
            item.get('currency'),
            item.get('unit'),
            item.get('supplier'),
            item.get('source_url'),
            item.get('scraped_at'),
        ))
        self.conn.commit()
        return item
```

---

## 六、全域設定（settings.py 關鍵設定）

```python
# commodity_tracker/settings.py

BOT_NAME = 'commodity_tracker'

# ===== 爬蟲身分設定 =====
USER_AGENT = 'commodity_tracker (+https://your-company.com/bot-info)'  # 誠實公告爬蟲身分

# ===== 請求速率設定（重要！禮貌爬蟲）=====
DOWNLOAD_DELAY         = 2      # 每個請求之間最少等待 2 秒
RANDOMIZE_DOWNLOAD_DELAY = True  # 在 0.5×~1.5× DELAY 之間隨機
CONCURRENT_REQUESTS     = 8     # 同時最多 8 個並行請求
CONCURRENT_REQUESTS_PER_DOMAIN = 2  # 每個域名最多 2 個並行（避免封鎖）

# ===== 遵守 robots.txt =====
ROBOTSTXT_OBEY = True   # 若設 False 會無視 robots.txt（不建議）

# ===== 啟用的 Pipeline（數字越小越先執行）=====
ITEM_PIPELINES = {
    'commodity_tracker.pipelines.ValidationPipeline': 100,
    'commodity_tracker.pipelines.CleaningPipeline':   200,
    'commodity_tracker.pipelines.CsvExportPipeline':  300,
    # 'commodity_tracker.pipelines.SqlitePipeline':   400,
}

# ===== 重試設定 =====
RETRY_ENABLED    = True
RETRY_TIMES      = 3      # 最多重試 3 次
RETRY_HTTP_CODES = [429, 500, 503]  # 遇到這些狀態碼才重試

# ===== 快取（開發時很有用，避免重複爬取）=====
# HTTPCACHE_ENABLED = True   # 開發時啟用（爬過的頁面存本地，重跑不再爬）
```

---

## 七、執行爬蟲

```bash
# 在專案根目錄執行

# 基本執行
scrapy crawl price_spider

# 輸出到 JSON 檔案（Scrapy 內建輸出格式）
scrapy crawl price_spider -o output.json

# 輸出到 CSV
scrapy crawl price_spider -o output.csv

# 查看爬蟲統計（請求數、Item 數、錯誤數）
# 執行完畢後會自動顯示

# 在互動模式下測試 CSS Selector（開發必備！）
scrapy shell "https://example.com"
# 進入 shell 後：
# response.css('h1::text').get()
# response.css('.price::text').getall()
```

---

## 八、🎯 最終成果：競品價格雷達圖（Pandas + Streamlit）

```python
# Scrapy 爬完後，用 Pandas 分析並畫雷達圖
# 檔案：app_radar.py

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
import matplotlib.patches as mpatches

plt.rcParams['font.family'] = ['Microsoft JhengHei', 'PingFang TC', 'sans-serif']

st.set_page_config(page_title="競品價格雷達圖", page_icon="🎯", layout="wide")
st.title("🎯 競品價格分析雷達圖")

# ===== 載入 Scrapy 爬回的 CSV 資料 =====
@st.cache_data
def load_data() -> pd.DataFrame:
    """
    載入 Scrapy 爬取的競品資料
    若 CSV 不存在，使用模擬資料展示
    """
    try:
        df = pd.read_csv('prices_output.csv', encoding='utf-8-sig')
        return df
    except FileNotFoundError:
        # 模擬資料：4 個供應商 × 5 個料件
        np.random.seed(42)
        suppliers = ['供應商 A', '供應商 B', '供應商 C', '供應商 D']
        products  = ['螺栓 M8', '不銹鋼板', '銅管', '鋁型材', '橡膠墊圈']
        base_prices = [150, 8500, 3200, 2800, 45]

        rows = []
        for prod, base in zip(products, base_prices):
            for sup in suppliers:
                factor = np.random.uniform(0.85, 1.20)
                rows.append({
                    'product_name': prod,
                    'supplier':     sup,
                    'price':        round(base * factor, 0),
                    'scraped_at':   '2024-01-15',
                })

        return pd.DataFrame(rows)

df = load_data()

# ===== 建立樞紐表：料件 × 供應商 → 價格 =====
pivot = df.pivot_table(values='price', index='product_name',
                        columns='supplier', aggfunc='mean')

# ===== 正規化（0~1，方便雷達圖比較）=====
# 各料件的最低價 = 0，最高價 = 1
pivot_norm = pivot.copy()
for idx in pivot.index:
    row_min = pivot.loc[idx].min()
    row_max = pivot.loc[idx].max()
    if row_max > row_min:
        pivot_norm.loc[idx] = (pivot.loc[idx] - row_min) / (row_max - row_min)

# ===== 繪製雷達圖 =====
st.subheader("📡 供應商價格競爭力雷達圖")
st.markdown("數值越低（靠近中心）代表該供應商在此料件的**競爭力越強**（報價越低）。")

categories = list(pivot_norm.index)
N          = len(categories)
angles     = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
angles    += angles[:1]   # 閉合多邊形

fig, ax = plt.subplots(figsize=(9, 9), subplot_kw=dict(polar=True))

colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12']
suppliers = list(pivot_norm.columns)

for i, supplier in enumerate(suppliers):
    values  = pivot_norm[supplier].tolist()
    values += values[:1]  # 閉合
    ax.plot(angles, values, 'o-', linewidth=2.5, color=colors[i], label=supplier)
    ax.fill(angles, values, alpha=0.08, color=colors[i])

# 設定軸標籤
ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=12)

# 設定 y 軸（0=最便宜，1=最貴）
ax.set_ylim(0, 1)
ax.set_yticks([0.25, 0.5, 0.75, 1.0])
ax.set_yticklabels(['25%', '50%', '75%', '最高'],
                    fontsize=8, color='gray')

ax.set_title('供應商競爭力比較（各料件正規化報價）',
             fontsize=14, fontweight='bold', pad=20)
ax.legend(loc='upper right', bbox_to_anchor=(1.35, 1.1), fontsize=11)
ax.grid(True, alpha=0.3)

st.pyplot(fig)

# ===== 詳細數據表 =====
st.subheader("📋 原始報價對照表")
st.dataframe(pivot.round(0).style.highlight_min(axis=1, color='lightgreen')
                                  .highlight_max(axis=1, color='#ffcccc'),
             use_container_width=True)
st.caption("🟢 綠色 = 最低報價（建議優先採購）｜🔴 紅色 = 最高報價")

# ===== 採購建議 =====
st.subheader("💼 最優採購建議")
best_suppliers = pivot.idxmin(axis=1)
total_saving_estimate = 0

for product, best_sup in best_suppliers.items():
    best_price  = pivot.loc[product, best_sup]
    worst_price = pivot.loc[product].max()
    saving_pct  = (worst_price - best_price) / worst_price * 100
    st.markdown(f"- **{product}**：建議向 **{best_sup}** 採購（報價最低 ${best_price:,.0f}，"
                f"較最高報價節省 **{saving_pct:.1f}%**）")
```

---

## 九、課後練習

### 練習：爬取公開政府資料

```bash
# 政府資料開放平臺（https://data.gov.tw）提供大量 CSV/API
# 以下是合法且適合練習的資料集：
#
# 1. 勞動部「勞動統計查詢系統」— 各業薪資統計
# 2. 工業局「工業生產指數」— 各產業產值趨勢  
# 3. 關務署「進出口貿易統計」— 原物料進口量
#
# 挑戰：
# 1. 使用 Scrapy 爬取其中一個資料集（多頁資料）
# 2. 用 Pipeline 存成 SQLite 資料庫
# 3. 用 Pandas 讀取資料庫，計算月增率
# 4. 用 Streamlit 製作互動式趨勢看板
```

### 思考題

1. 什麼情況下應該選用 Scrapy 而非 requests + BeautifulSoup？說明判斷的三個標準。
2. 如果目標網站的資料是用 JavaScript 動態載入（點頁面看不到資料，資料是 AJAX 取得的），requests + BeautifulSoup 和 Scrapy 都爬不到，應該怎麼辦？（提示：Playwright、Selenium）
3. 競品價格雷達圖能反映什麼決策資訊？它無法反映什麼（有哪些盲點）？

---

## 📎 重點整理

```
Scrapy 核心元件
├── Spider      → 定義起始 URL + 解析邏輯（你寫的主要程式碼）
├── Item        → 資料結構定義（像資料庫的 schema）
├── Pipeline    → 資料清理 → 驗證 → 儲存（流水線式處理）
├── Middleware  → 請求/回應的攔截器（User-Agent、重試、代理）
└── Settings    → 全域參數（速率、Pipeline 開關、快取）

大規模爬蟲的工程實踐
├── 速率控制：DOWNLOAD_DELAY + CONCURRENT_REQUESTS
├── 資料驗證：Pipeline 第一關做驗證，丟棄無效資料
├── 錯誤處理：RETRY_HTTP_CODES + 重試機制
└── 快取機制：HTTPCACHE_ENABLED（開發用）

完整資料搜集流程
Scrapy 爬取 → Pipeline 清理/儲存 CSV → Pandas 分析 → Streamlit 視覺化
```

---

*上一單元：[模組 4-1：Web Scraping](./Module4_1_WebScraping.md)*
