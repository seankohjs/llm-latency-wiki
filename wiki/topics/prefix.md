# W04 共同前綴的重用

[回 Wiki](../README.md) · [KV cache 與區塊](kv.md) · [快取和負載的取捨](routing.md)

## c09

自動前綴快取（APC）讓新請求重用相同前綴的可用 KV 狀態，減少該段 prefill 的重複計算。

**限制：** 須有相容且仍可用的共同前綴；示例不代表全程都命中。
**來源：** [S04](../sources/s04.md)，Introduction／Example workloads。

## c10

APC 減少共同前綴的輸入處理工作，並不直接縮短後續每個新 token 的 decode 計算。

**限制：** 不能由 APC 命中推出 ITL 必然下降，也不能推估固定延遲改善比例。
**來源：** [S04](../sources/s04.md)，Limits。

## c11

沒有可重用前綴時，不能靠該段快取省下計算；若等待主要來自長輸出，整體改善也可能有限。

**限制：** 實際效果取決於工作負載、排程與快取狀態。
**來源：** [S04](../sources/s04.md)，Limits。
