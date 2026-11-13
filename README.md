# 每日一 BUG｜Earth Glitch Daily

每天認識一種地球上的奇特真實物種。純靜態網站，適合 GitHub Pages。

## 功能

- 每天依 **Asia/Taipei** 日期自動顯示一種新物種。
- 歷史圖鑑可搜尋、分類並開啟研究檔案；未來日期的卡片顯示為鎖定。
- 首頁不依賴即時 API；照片在需要時使用 iNaturalist API 查詢，查不到時保留純文字與替代圖。
- 30 日示範排程：2026-11-13 至 2026-12-12。

## 本機執行

```bash
python scripts/validate.py
python -m http.server 8000
```

開啟 <http://localhost:8000/>。**請勿直接用 file:// 雙擊開啟**，瀏覽器可能阻止 `fetch` 讀取 JSON。

## 上傳與部署 GitHub Pages

1. 在 GitHub 建立公開 Repository，例如 `earth-glitch-daily`。
2. 將本資料夾內所有檔案推送到 Repository 預設分支。
3. 開啟 **Settings → Pages → Build and deployment**，選擇 **Deploy from a branch**，分支選 `main`、資料夾選 `/(root)`，儲存。
4. 等待 GitHub Pages 完成部署，從 Pages 設定頁取得實際網址，檢查首頁與資料頁。不要假設範例網址已生效。

## 新增每日物種

先閱讀 [AGENTS.md](AGENTS.md)，再在 `data/species.json` 追加符合格式的一筆，日期需接續最後一天。執行 `python scripts/validate.py` 確認資料有效。新增物種不需要修改 HTML 或 CSS。

## 資料來源與注意

物種候選清單、中文簡介為本專案編輯資料。iNaturalist 的物種資料和圖片透過 [iNaturalist API](https://www.inaturalist.org/pages/api+reference) 查詢；網站嘗試精確學名匹配，照片必須有可用的 Creative Commons 授權才會呈現。

請注意：**本示範環境無法直接連到 iNaturalist API 完成逐筆核對**。正式對外發布前，請人工驗證 30 種物種的精確學名、中文俗名與簡介，尤其是名稱可能隨分類學修訂變更的物種。網站在查無物種或照片時會回退到自製替代圖及搜尋連結。

iNaturalist 照片各自有其著作權及授權條款；非商業使用與署名義務視每張照片授權而定。本站的娛樂性 `BUG 指數` 不是科學量測。未來資料雖在 UI 鎖定，但靜態 JSON 可公開檢視，**並非真正保密**。

更多說明： [iNaturalist 開發者頁](https://www.inaturalist.org/pages/developers) · [iNaturalist 照片授權說明](https://help.inaturalist.org/en/support/solutions/articles/151000173511)
