# W02 量測邊界與延遲指標

[回 Wiki](../README.md) · [一次請求的階段](stages.md) · [共同前綴的重用](prefix.md)

## c04

首個 token 的等待時間（TTFT），在這裡指服務前端接收請求到收到第一個輸出 token 的時間。

**限制：** vLLM v0.11.0 V1 前端量測邊界，包含前端輸入處理與可能的排隊；不是把 prefill 單獨計時。
**來源：** [S02](../sources/s02.md)，V1 Design → Frontend Stats Collection。

## c05

相鄰輸出 token 的間隔（ITL）看的是後續 token 到達的節奏。

**限制：** 不要把相鄰間隔的分布和每個請求的平均 TPOT 當成完全相同的統計量。
**來源：** [S02](../sources/s02.md)，V1 Design → Interval Calculations。

## c06

這裡的完成時間從服務前端收到請求算到最後一個 token。

**限制：** 客戶端所見的完成時間還可能包含網路與前端處理，不能混用計時邊界。
**來源：** [S02](../sources/s02.md)，V1 Design → Frontend Stats Collection。
