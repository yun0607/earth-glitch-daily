# 每日一 BUG｜Earth Glitch Daily

每天認識一種地球上的奇特真實物種。純靜態網站，適合 GitHub Pages。

## 功能

- 每天依 **Asia/Taipei** 日期自動顯示一種新物種。
- 歷史圖鑑可搜尋、分類並開啟研究檔案；未來日期的卡片顯示為鎖定。
- 照片網址、作者、授權與來源預先存入 JSON；開啟網站及詳細頁都不查詢 iNaturalist API。照片缺漏或載入失敗時顯示自製替代圖。
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

先閱讀 [AGENTS.md](AGENTS.md)，再在 `data/species.json` 追加符合格式的一筆，日期需接續最後一天。新增資料的 `taxonId`、`photo` 先設為 `null`，執行下方圖片更新指令，再執行 `python3 scripts/validate.py` 確認資料有效。新增物種不需要修改 HTML 或 CSS。

## 更新圖片

```bash
python3 scripts/update_photos.py
python3 scripts/validate.py
```

更新腳本只使用 Python 標準函式庫，不需要金鑰或後端。依序核對精確學名、species 階層及有效狀態後，優先使用授權合適的預設照片；否則檢查物種其他照片，再搜尋最多 90 筆該物種觀察紀錄的照片。每張照片獨立核對授權，不以觀察紀錄授權代替照片授權。API 請求循序執行，間隔至少 1.1 秒，並對暫時性失敗有限重試，符合 [iNaturalist 官方 API 速率建議](https://www.inaturalist.org/pages/developers)。

- 已有照片預設跳過；`--refresh` 會重新選圖（也會取代手動指定的圖片）。
- 蘭花螳螂使用使用者指定的原始圖片 `assets/photos/hymenopus-coronatus.png`，未修改影像。`license: user-provided` 僅表示使用者提供，並非 CC 授權；作者未提供，不沿用舊照片署名。
- `--name 'Hymenopus coronatus'` 可僅更新指定學名。
- 預設採用 CC0、CC BY、CC BY-SA；只有確認網站用途符合非商業條款時才加上 `--allow-nc`，允許 CC BY-NC、CC BY-NC-SA。
- 每筆成功結果立即寫入 `data/species.json` 的 `taxonId`、`photo`。`photo` 包含 `url`、`author`、`attribution`、`license`、`source`，畫面顯示原始署名、授權及可點擊的照片來源頁。
- 查詢失敗或查無精確物種時保留原資料並回報錯誤；查詢完成但未找到合適照片時將 `photo` 設為 `null`。無照片的紀錄下次執行仍會重試。
- 腳本只記錄照片網址，不下載或重新散布圖片檔。JSON 的來源與授權是更新當時的紀錄，對外發布前及用途改變時仍應重新審核。

選圖邏輯可離線測試：`python3 -m unittest discover -s scripts -p 'test_*.py'`。

## 資料來源與注意

物種候選清單、中文簡介為本專案編輯資料。iNaturalist 的物種資料和圖片於維護時透過 [iNaturalist API](https://api.inaturalist.org/v1/docs/) 查詢；網站直接使用 JSON 中已確認授權的照片。

`taxonId` 非空代表更新時已核對 iNaturalist 精確學名及物種階層；不代表已驗證中文俗名、簡介或形態論述。正式對外發布前仍需核對這些編輯內容。查無物種或照片時，網站保留文字介紹、自製替代圖及來源搜尋連結。

目前 25 種物種有圖片（24 張 iNaturalist 授權照片及 1 張使用者指定圖片）。`Ptilocercus lowii`、`Dracula simia`、`Kiwa hirsuta` 在此次有限搜尋中未找到符合預設授權條件的照片，保留替代圖。另有兩筆既有學名待確認：`Pseudocreobotra wahlbergii`、`Rafflesia arnoldii`；API 分別回傳 `Pseudocreobotra wahlbergi`、`Rafflesia arnoldi`，不符合精確匹配，故維持原紀錄並將 `taxonId`、`photo` 留為 `null`。若確認需更正學名，應另行更新資料再執行選圖。

iNaturalist 照片各自有其著作權及授權條款；非商業使用與署名義務視每張照片授權而定。本站的娛樂性 `BUG 指數` 不是科學量測。未來資料雖在 UI 鎖定，但靜態 JSON 可公開檢視，**並非真正保密**。

更多說明： [iNaturalist 開發者頁](https://www.inaturalist.org/pages/developers) · [iNaturalist 照片授權說明](https://help.inaturalist.org/en/support/solutions/articles/151000173511)
