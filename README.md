# LLM Latency Lab｜LLM 為什麼回得慢？

這是一份面向初學者的教學 HTML 簡報，以獨立 LLM Wiki 為知識來源。

- [教學 HTML 簡報](https://seankohjs.github.io/llm-latency-wiki/slides/)
- [可瀏覽 Wiki](https://seankohjs.github.io/llm-latency-wiki/wiki/)
- [流程圖、實際執行與反思](https://seankohjs.github.io/llm-latency-wiki/workflow/)
- [選題與討論](SCOPE.md) · [可讀 Markdown Wiki](wiki/README.md) · [AI 規則](AGENTS.md)

## 工作方式

先討論教學範圍，再由 Codex 讀六份第一手文件，整理為具來源、段落與限制的 `sources/intake.json`。`ingest` 生成 Wiki（六份來源頁、五個概念頁及十四個主張），之後的查詢與簡報生成以 `wiki/index.json` 為知識庫。

初版關鍵字前三筆先形成草稿要點，再查必備概念，五題中兩題缺少對應資料。修正版在查詢後立刻檢查分類，缺少就重查該概念（最多兩輪）；五題通過才進入編排。Codex 讀取 `lesson/checked-evidence.json`，用 `lesson/slides.json` 安排教學順序，渲染器直接取 Wiki 主張文字，並為各技術投影片建立來源錨點。

`records/` 保存六次取得原文的結果、基線草稿與覆蓋檢查、重查記錄、AI 語意核對及簡報對應表。未發佈缺漏的草稿。查核分類與 ID 不代表能證明語意；需要查原文。

## 重跑

Python 3.10+，不需第三方 Python 套件、GPU 或模型 key。重跑使用當次已核對的來源整理與取得紀錄，並不重新擷取或更新外部文件。

```sh
python3 pipeline.py ingest
python3 pipeline.py baseline
python3 pipeline.py select
python3 render.py
python3 check.py
python3 -m http.server 8020 --directory docs --bind 127.0.0.1
```

瀏覽 `docs/slides/index.html` 或本機網址的 `/slides/`。可用按鈕、左右鍵或頁選單換頁；有教學時間模型、來源連結及一題自我檢查。關閉 JS 時仍可依序閱讀所有頁面，互動以初始示例與靜態解答替代。

GitHub Pages 發佈 `codex/llm-latency-wiki` 的 `/docs`。更新 Wiki 後重跑建置，提交 source、records 與 docs。私人的學生資料與繳交文字留在公開 checkout 外。

本專案是 AI 在開發時依 Wiki 整理與生成，不是網站在瀏覽時呼叫 LLM。數字為清楚標示的教學假設，不是研究重現或部署實測。
