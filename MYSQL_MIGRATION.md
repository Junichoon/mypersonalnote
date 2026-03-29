# MySQL 版本轉換指南

## Overview

本專案原本使用 SQLite，現在支援 MySQL。兩者功能完全相容，只是資料庫後端不同。

## 快速開始

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 設定環境變數

```bash
# Linux/macOS
export MEMO_MYSQL_HOST=localhost
export MEMO_MYSQL_PORT=3306
export MEMO_MYSQL_USER=root
export MEMO_MYSQL_PASSWORD=your_password
export MEMO_MYSQL_DATABASE=personalmemo

# Windows (PowerShell)
$env:MEMO_MYSQL_HOST="localhost"
$env:MEMO_MYSQL_PORT="3306"
$env:MEMO_MYSQL_USER="root"
$env:MEMO_MYSQL_PASSWORD="your_password"
$env:MEMO_MYSQL_DATABASE="personalmemo"
```

或複製 `.env.example` 為 `.env` 並填入設定。

### 3. 執行遷移（從 SQLite 搬過來）

```bash
python migrate_to_mysql.py
```

### 4. 啟動 MySQL 版本

```bash
python server_mysql.py
```

瀏覽器打開：`http://127.0.0.1:8080`

---

## 檔案說明

| 檔案 | 說明 |
|------|------|
| `server.py` | SQLite 版本（原始） |
| `server_mysql.py` | MySQL 版本 |
| `migrate_to_mysql.py` | SQLite → MySQL 遷移腳本 |
| `.env.example` | 環境變數範例 |

---

## MySQL 版本特色

- ✅ **完整相容** - 所有 API 端點與 SQLite 版相同
- ✅ **自動建立** - 首次啟動自動建立資料庫和資料表
- ✅ **UTF-8 支援** - 使用 utf8mb4 編碼，完整支援中文
- ✅ **軟刪除** - 刪除的資料不會真的消失（deleted 欄位）
- ✅ **效能更好** - 適合大量資料和高併發

---

## 常見問題

### Q: 遷移後原本的 SQLite 資料還在嗎？
A: 在的。遷移腳本會讀取 `personalmemo.db` 複製到 MySQL，不會刪除原本檔案。

### Q: 可以同時用 SQLite 和 MySQL 嗎？
A: 不行，一次只能用一種。SQLite 用 `server.py`，MySQL 用 `server_mysql.py`。

### Q: MySQL 要另外安裝嗎？
A: 是的。你需要自己有 MySQL 伺服器，或使用雲端服務如：
- [PlanetScale](https://planetscale.com/)（免費）
- [Railway](https://railway.app/)（有免費額度）
- [Aiven](https://aiven.io/)（有免費額度）
- [TiDB](https://tidbcloud.com/)（免費）

### Q: 要怎麼確認成功遷移了？
A: 執行 `python migrate_to_mysql.py`，最後會顯示驗證結果。
