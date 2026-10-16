---
name: mock-exam-workbook
description: 把教材、投影片、規格或筆記做成「模擬考練習簿」：一個單一 HTML 頁面，內含單選、複選、分類、排序、配對、縮寫六種題型，有練習模式、模擬考、錯題與到期複習、易混淆題組、考我一題、每日一題、考前快速瀏覽、誤選分析、熟練追蹤、列印，發佈成 Claude artifact 時還能同步作答紀錄和按鈕請 AI 解析。題目寫成 JSON，套進固定的範本引擎，所以每份練習簿的功能和品質一致。只要使用者想出題、做模擬考、練習簿、題庫、測驗、內訓考題、課後評量，或要把一份資料變成練習題，或要修改、擴充、搬移現有的練習簿，都使用這個 skill，即使沒有提到 HTML 或練習簿。
---

# 模擬考練習簿

練習簿 = 固定的引擎 + 題庫資料。你的工作是**寫出好的題庫 JSON**，再用腳本套進範本。不要重寫或修改範本裡的程式；引擎已經處理好作答、判分、複習排程、誤選分析、列印和同步。

這個 skill 的資料夾（下稱 `<skill>`，在 claude.ai 通常是 `/mnt/skills/user/mock-exam-workbook`）裡有：

- `assets/template.html`：範本引擎，已內嵌一份範例題庫，可以直接開來看效果。
- `assets/example-bank.json`：範例題庫，六種題型各三題，加上兩組易混淆題組。**這是格式和品質的標準。**
- `references/schema.md`：題庫格式的完整說明。
- `references/writing-guide.md`：出題指引（干擾選項、解析寫法、題型選擇）。
- `scripts/build.py`：檢查題庫並產生 HTML；也能從現有練習簿取出題庫。

## 流程

### 1. 確認需求

需要知道：教材（檔案、貼上的文字或圖片）、學員是誰、大約幾題。使用者沒說的就用預設，在回覆裡一句話說明你的假設，不要為此停下來問：

- 題數：教材短（幾頁）出 15 到 25 題，長的出 30 到 60 題。
- 題型比例：照 `writing-guide.md` 的建議。
- 練習簿 id：用主題的英文縮寫加連字號，例如 `fw-upgrade-101`。

沒有教材時，先請使用者提供；不要憑記憶出整份題庫，因為內訓題目要和公司教材一致。

### 2. 讀指引和範例

開始寫題目前，依序讀：

1. `references/writing-guide.md`
2. `assets/example-bank.json`
3. `references/schema.md`（寫到不確定的格式時再查）

範例題目是 5G 領域的，只用來示範格式、題型用法和解析的寫法；內容要完全來自使用者的教材。

### 3. 先列概念和誤解

照 `writing-guide.md`「出題前」一節，在心裡或草稿裡列出關鍵概念和常見誤解，再決定每個概念用什麼題型、哪些題目要綁成易混淆題組。

### 4. 寫題庫

在工作目錄建立 `/home/claude/<id>/bank.json`。使用者有提供圖片時，複製到 `/home/claude/<id>/images/`，檔名改成簡短的英數代號（例如 `topo1.png`），題目用 `img` / `eimg` 引用。出跟圖有關的題目前，先看過圖片。

題數多（超過 30 題）時，分段寫入檔案，避免一次輸出太長。

### 5. 檢查並產生

```bash
python <skill>/scripts/build.py --bank /home/claude/<id>/bank.json \
  [--images /home/claude/<id>/images] \
  --out "/mnt/user-data/outputs/<練習簿標題>.html"
```

- **錯誤**：一定要修正，否則不會產生檔案。
- **品質提醒**：逐條判斷。特別是「正確答案明顯是最長的選項」，這是 AI 出題最常見的毛病，要回頭把干擾選項改寫得一樣具體，不要只是把正確答案刪短。

### 6. 交付

- **有 Artifact 工具時**（claude.ai）：發佈這個 HTML。先用 Artifact 的 `capabilities` 動作確認可用的能力，發佈時宣告 `{"db": {}, "user": {}, "sample": {}, "downloads": true}`，作答紀錄就會跟著帳號同步，「AI 解析」按鈕也會出現。同時用 `present_files` 給 `bank.json`，方便使用者之後修改。
- **沒有 Artifact 工具時**：用 `present_files` 給 HTML 和 `bank.json`。HTML 可以直接用瀏覽器開，或放到內部網站；作答紀錄存在各自的瀏覽器裡，沒有 AI 解析按鈕。

回覆裡簡短說明：題數與題型分布、你做了哪些假設、哪些題目你比較沒把握（建議使用者看一下）。不要逐題列出內容。

## 修改或擴充現有的練習簿

1. 取得現有的 HTML：使用者給的檔案，或用 Artifact 的 `read` 動作讀他給的 artifact 連結。
2. 取出題庫：

   ```bash
   python <skill>/scripts/build.py --extract 現有練習簿.html --dump /home/claude/<id>
   ```

   會得到 `bank.json` 和 `images.json`。舊版練習簿（題目寫在程式裡的版本，包括題目是 JS 物件寫法的）也能取出，`config.storageKeys` 會沿用舊的作答紀錄，不要刪。
3. 修改 `bank.json`。**不要改動已有題目的 `n`**，作答紀錄綁在題號上；新題接在最大題號後面，刪題就讓號碼空著。縮寫題只能加在最後。題庫的題號最多到 999；題庫已經定稿、新題不想算進題庫統計時，改用 1001 以上的內建補充題號，規則見 `schema.md` 2.6。1000 不能用。

   使用者指出某一題不是教材裡的內容，或題目本身有錯、沒辦法修成合理的題目時，**不要刪題**，改成把它標成不可作答：在那一題（或那筆縮寫題）加上 `"void": true` 和 `"voidNote"`，其他欄位原樣保留，並在 `voidNote` 寫清楚哪裡有問題，例如哪個名詞在教材裡找不到、手上的資料實際上怎麼寫。頁面會把這題顯示成灰色刪除線，不再出題也不計分，做過的人點進去看得到原因；作答紀錄不會動，拿掉 `void` 就恢復。只是答案標錯或選項、解析寫錯，改得好的題目直接修正，不用標。規則見 `schema.md` 第 5 節。新出的題庫不要用這兩個欄位。
4. 重新產生：

   ```bash
   python <skill>/scripts/build.py --bank /home/claude/<id>/bank.json \
     --images-json /home/claude/<id>/images.json [--images 新圖片資料夾] \
     --out "/mnt/user-data/outputs/<練習簿標題>.html"
   ```

5. 發佈時傳入原本的 artifact 連結（`url`）更新同一份，並省略 `capabilities`，沿用原本的宣告。

同樣的步驟也能把舊練習簿升級到新版引擎：取出題庫，用新範本重新產生即可。

## 不要做的事

- 不要修改 `template.html` 裡的程式，也不要從頭寫一份新的練習簿 HTML。需要的功能範本都有；範本真的有 bug 時，告訴使用者，不要私下改。
- 不要把考古題、原廠題庫或商業題庫的原文放進練習簿，練習簿會分享給別人。
- 不要在題庫 JSON 裡用 Markdown 語法，頁面會原樣顯示。
