# 小糖罐 · sugarjar

一只水彩玻璃罐。一颗糖 = 一条碎片。想到就丢一颗。

```bash
python3 add_candy.py --text "今天她把一整条心电图纸带看完了"
python3 add_candy.py --text "例：她说『那就单开一个嘿嘿』" --color plum --shape twist --size 1.3
```

- `--color`  `plum / peach / mint / lemon / berry / grape / apricot / rose / lime / caramel / sky / cherry`
- `--shape`  `round / twist / drop / star / cube / bean / heart / ring`
- `--size`   `0.82 ~ 1.30`（多重的一颗糖）
- `--src`    来源，默认 `碎片集`

不给颜色/形状/大小时，按文本 MD5 稳定分配：**同一句话永远是同一颗糖**。

数据落在 `candies.jsonl`，一行一颗：

```json
{"id":"20261018000100","date":"2026-10-18","text":"…","color":"peach","shape":"heart","size":1.0,"src":"碎片集"}
```

`candies.sample.jsonl` 是示例，别往里面丢真糖。

## 还没做的

把 `candies.jsonl` 画成一只水彩玻璃罐：木塞、麻绳、玻璃上一点水汽和手印，糖堆着斜着互相压着，点开一颗看一句话。

方向定了：水彩的那点「脏」是骨架，不能擦得太干净。
