# W01 一次請求的階段

[回 Wiki](../README.md) · [量測邊界與延遲指標](metrics.md) · [KV cache 與區塊](kv.md)

## c01

Prefill 處理輸入的 prompt，建立後續生成所需的狀態，並形成第一個輸出 token。

**限制：** 這裡介紹自回歸文字生成的概念；不假設服務一定用一整批一次完成 prefill。
**來源：** [S01](../sources/s01.md)，§2.1 LLM Inference。

## c02

Decode 接續生成後面的 token；後續輸出會依賴先前的上下文與已生成的 token。

**限制：** 這是自回歸生成的順序關係，不代表每次網路串流都只傳一個 token。
**來源：** [S01](../sources/s01.md)，§2.1 LLM Inference。

## c03

請求到達後可能先等待排程；排隊時間與模型實際處理輸入的時間可以分開觀察。

**限制：** 不同觀測位置的事件與計時方式可能不同。
**來源：** [S02](../sources/s02.md)，V1 Design → Interval Calculations。
