# mypersonalnote

## 備忘錄網頁

## 啟動方式

```bash
cd C:\Users\junic\.openclaw\workspace\memo-web
python server.py
```

瀏覽器打開：`http://127.0.0.1:8080`

## 功能
- 搜尋
- 狀態/分類篩選
- 新增/編輯/刪除
- 標籤管理（tags.html）
- 自動同步 FAISS（faiss_metadata.json）與 memos.json

## 手動匯出

```bash
python export_memos.py
```
