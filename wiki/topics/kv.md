# W03 KV cache 與區塊

[回 Wiki](../README.md) · [一次請求的階段](stages.md) · [共同前綴的重用](prefix.md)

## c07

KV cache 保存先前 token 已算出的注意力 key、value，讓後續生成可以使用這些狀態。

**限制：** 保存的是模型中間狀態，不是把整篇已生成的回答當作快取結果。
**來源：** [S03](../sources/s03.md)，§2.2 與 §4.3。

## c08

PagedAttention 把 KV cache 以區塊管理，可隨序列長度配置，區塊不必在記憶體中連續。

**限制：** 原論文設計；這個機制本身不保證特定請求會降低固定比例延遲。
**來源：** [S03](../sources/s03.md)，§4.1–4.2。

## c12

在這份 vLLM 設計中，快取比對用前綴和區塊內的 token 等資訊，且只快取完整區塊。

**限制：** 意思相似不表示前綴一致；這是指定版本文件的實作條件，不套用到所有框架。
**來源：** [S05](../sources/s05.md)，Opening design description／Note 1。
