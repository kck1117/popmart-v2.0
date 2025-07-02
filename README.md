# PopMart 監控系統

## 項目概述

PopMart 監控系統是一個專門用於監控 PopMart 香港官網產品庫存和價格變化的工具。系統通過定期訪問 PopMart 官方 API，獲取最新的產品信息，並將其與本地數據庫中的歷史記錄進行比較，以識別價格變化、庫存狀態更新以及新產品上架等事件。

## 功能特點

- **實時監控**：定期自動檢查 PopMart 官網的產品更新
- **數據追蹤**：記錄產品價格和庫存的歷史變化
- **特定產品關注**：允許用戶指定特定的產品系列或關鍵字進行重點監控
- **用戶友好界面**：提供直觀的 Web 界面，方便用戶查看監控結果
- **高效穩定**：在不影響 PopMart 官網正常運行的前提下，高效穩定地獲取數據

## 技術棧

- **後端**：Python 3.8+, Flask, SQLAlchemy, aiohttp
- **前端**：HTML, CSS, JavaScript (原生)
- **數據庫**：SQLite
- **部署**：Docker (可選)

## 快速開始

### 環境要求

- Python 3.8 或更高版本
- pip (Python 包管理器)

### 安裝步驟

1. 克隆項目到本地：

```bash
git clone https://github.com/yourusername/popmart-monitor.git
cd popmart-monitor
```

2. 創建並激活虛擬環境：

```bash
python -m venv venv
source venv/bin/activate  # 在 Windows 上使用 venv\Scripts\activate
```

3. 安裝依賴：

```bash
pip install -r requirements.txt
```

4. 啟動應用：

```bash
python src/main.py
```

5. 在瀏覽器中訪問：

```
http://localhost:5000
```

## 項目結構

```
popmart_monitor_v2/
├── src/
│   ├── models/
│   │   └── product.py       # 數據模型定義
│   ├── routes/
│   │   └── monitor.py       # API 路由
│   ├── services/
│   │   ├── popmart_api_client.py       # API 客戶端
│   │   ├── monitor.py                  # 監控服務
│   │   ├── specific_monsters_scraper.py # 特定產品爬蟲
│   │   └── scheduler.py                # 排程器
│   ├── static/
│   │   ├── index.html       # 前端頁面
│   │   └── placeholder.png  # 佔位圖片
│   ├── database/
│   │   └── popmart_data.db  # SQLite 數據庫
│   └── main.py              # 應用入口
├── venv/                    # 虛擬環境
├── requirements.txt         # 依賴列表
└── test_system.py           # 測試腳本
```

## API 端點

- `GET /api/products`: 獲取產品列表，支持分頁和過濾
- `GET /api/products/<product_id>`: 獲取單個產品詳情
- `POST /api/update_products`: 觸發產品數據更新
- `GET /api/update_progress`: 獲取更新進度
- `GET /api/scheduler/status`: 獲取排程器狀態
- `POST /api/scheduler/start`: 啟動排程器
- `POST /api/scheduler/stop`: 停止排程器
- `GET /api/monitored_products`: 獲取監控產品列表
- `POST /api/monitored_products`: 添加監控產品
- `DELETE /api/monitored_products/<product_name>`: 移除監控產品

## 部署指南

### 本地部署

按照「快速開始」部分的步驟進行本地部署。

### Docker 部署

1. 構建 Docker 映像：

```bash
docker build -t popmart-monitor .
```

2. 運行 Docker 容器：

```bash
docker run -p 5000:5000 -v /path/on/host/data:/app/src/database/popmart_data.db popmart-monitor
```

## 常見問題

### API 請求頻繁返回 429 (Too Many Requests) 錯誤

- 增加請求之間的延遲時間，例如從 1.5-4.0 秒增加到 3.0-8.0 秒
- 減少並發請求數量，例如將信號量從 3 降低到 1
- 實施更複雜的重試策略，例如指數退避

### API 請求返回 403 (Forbidden) 錯誤

- 檢查請求頭是否包含必要的信息，例如 User-Agent、Accept 等
- 擴展用戶代理池，使用更多的真實瀏覽器 User-Agent
- 考慮使用代理 IP 輪換請求來源

## 維護指南

1. **日誌監控**：定期檢查應用程式日誌，特別是 `ERROR` 和 `WARNING` 級別的日誌
2. **數據庫備份**：定期備份 `popmart_data.db` 文件，防止數據丟失
3. **依賴更新**：定期檢查並更新 `requirements.txt` 中列出的 Python 庫
4. **API 變化適應**：關注 PopMart 官方 API 的變化，及時更新 `popmart_api_client.py`

## 開發設計圖

詳細的開發設計圖請參考 [PopMart監控系統開發設計圖.pdf](PopMart監控系統開發設計圖.pdf)。

## 授權

本項目僅供學習和研究使用，請勿用於商業目的。

