# 📝 Winnie 的專案開發工作日誌 (Work Log)

- **專案名稱：** `wi` (Interactive Live Clock & Showcase)
- **開發日期：** 2026-05-29
- **開發人員：** Winnie (winnieshih1107@gmail.com)

---

## 🛠️ 今日開發記錄

### 1. 建立網頁核心與視覺設計 (`index.html`)
- **功能設計：**
  - Hello 歡迎詞與 Winnie 個人名稱展示。
  - 動態即時時鐘（12小時制，含 AM/PM 指示器，每秒更新）。
  - 根據系統目前時間自動判斷早安、午安、晚安的智慧問候標籤。
- **介面美化（符合 Rich Aesthetics 規範）：**
  - **毛玻璃效果 (Glassmorphism)：** 使用 `backdrop-filter: blur` 與半透明卡片邊框。
  - **背景氛圍燈：** 兩個會緩慢移動並放大縮小的漸層光暈（Ambient Glow）。
  - **3D 懸停效果 (3D Tilt Effect)：** 當滑鼠在卡片上移動時，卡片會隨著游標的相對位置產生流暢的 3D 傾斜立體視覺。
  - **一鍵切換主題：** 支援深色模式（Dark Theme）與淺色模式（Light Theme），並自動記錄於瀏覽器快取（Local Storage）。

### 2. 初始化 Git 與 GitHub 連線
- 設定全域帳號資訊：
  - 名稱：`Winnie`
  - 信箱：`winnieshih1107@gmail.com`
- 建立 `.gitignore` 檔案排除系統快取檔。
- 完成本地端 Git 初始化、暫存並提交首個版本 (`Initial commit`)。

### 3. 上傳專案至 GitHub
- 於 GitHub 建立全新公開專案 `wi`。
- 設定 Remote Origin 並成功推送到主分支 (`main`)：
  - 專案網址：https://github.com/winnieshih1107/wi

### 4. 撰寫專案說明文件與測試
- 撰寫結構完整的 `README.md`，提供功能介紹、本地啟動方式與技術棧說明。
- 新增本機端預覽連結：`file:///D:/wi/index.html`。
- 啟動並設定 GitHub Pages 靜態網站服務，更新線上 Live Demo 連結於 README 中：
  - 線上預覽：https://winnieshih1107.github.io/wi/

### 5. 導出對話紀錄
- 產生 [dialog_export.md](file:///d:/wi/dialog_export.md)，記錄開發過程中的問答。

---
*日誌更新時間：2026-05-29*
