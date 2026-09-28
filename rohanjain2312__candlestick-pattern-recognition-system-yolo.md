# rohanjain2312/candlestick-pattern-recognition-system-yolo (model)

```json
{
  "kind": "model",
  "id": "rohanjain2312/candlestick-pattern-recognition-system-yolo",
  "url": "https://huggingface.co/rohanjain2312/candlestick-pattern-recognition-system-yolo",
  "meta": {
    "pipeline_tag": "object-detection",
    "library_name": "ultralytics",
    "tags": [
      "ultralytics",
      "object-detection",
      "yolo",
      "candlestick",
      "finance",
      "license:mit",
      "region:us"
    ],
    "downloads": 651,
    "likes": 0,
    "cardData": {
      "license": "mit",
      "tags": [
        "object-detection",
        "yolo",
        "ultralytics",
        "candlestick",
        "finance"
      ],
      "library_name": "ultralytics",
      "pipeline_tag": "object-detection"
    },
    "lastModified": "2026-09-17T07:57:33.000Z",
    "gated": false,
    "private": false
  },
  "files": [
    {
      "path": "results",
      "size": 0,
      "type": "directory"
    },
    {
      "path": "training",
      "size": 0,
      "type": "directory"
    },
    {
      "path": ".gitattributes",
      "size": 1653,
      "type": "file"
    },
    {
      "path": "README.md",
      "size": 3265,
      "type": "file"
    },
    {
      "path": "best.pt",
      "size": 5476314,
      "type": "file"
    },
    {
      "path": "detection_metrics.json",
      "size": 1656,
      "type": "file"
    },
    {
      "path": "last.pt",
      "size": 5476314,
      "type": "file"
    },
    {
      "path": "results/dataset_stats.json",
      "size": 808,
      "type": "file"
    },
    {
      "path": "results/detection_metrics.json",
      "size": 2064,
      "type": "file"
    },
    {
      "path": "results/downstream_signal_comparison.json",
      "size": 2066,
      "type": "file"
    },
    {
      "path": "training/confusion_matrix_normalized.png",
      "size": 243783,
      "type": "file"
    },
    {
      "path": "training/results.csv",
      "size": 6571,
      "type": "file"
    },
    {
      "path": "training/results.png",
      "size": 303169,
      "type": "file"
    }
  ]
}
```

## README

---
license: mit
tags: [object-detection, yolo, ultralytics, candlestick, finance]
library_name: ultralytics
pipeline_tag: object-detection
---

# Candlestick pattern detector (YOLO11n)

Detects 8 candlestick patterns in 640x640 renderings of
20-candle daily charts.

## The headline finding

Adding this detector's predictions to a plain price-feature baseline changed next-day direction accuracy by **+0.0036** (95% bootstrap CI -0.0041 to +0.0114, McNemar p = 0.443) over 1936 out-of-sample days on SPY. The interval contains zero. Neither variant beats the majority-class rate of 0.5537, and both have a ROC AUC near 0.496.

**So: this model detects the patterns well, and detecting them does not help predict the next day.** That is the result, reported as found.

## Labels are rule-based, not human-verified

Training boxes came from TA-Lib's `CDLxxx` functions. Nobody annotated these
charts by hand, so this model imitates a published heuristic. Where TA-Lib and
an experienced trader would disagree about the same candles, this model follows
TA-Lib. Detection metrics below therefore measure **agreement with a rule**, not
correctness.

## Detection, held-out test split

| class | instances | precision | recall | mAP@50 |
|---|---:|---:|---:|---:|
| Hammer | 557 | 0.665 | 0.720 | 0.757 |
| ShootingStar | 570 | 0.801 | 0.798 | 0.893 |
| BullishEngulfing | 1178 | 0.999 | 0.983 | 0.995 |
| BearishEngulfing | 1368 | 0.908 | 0.997 | 0.976 |
| MorningStar | 198 | 0.602 | 0.773 | 0.772 |
| EveningStar | 180 | 0.773 | 0.550 | 0.669 |
| Doji | 5261 | 0.893 | 0.948 | 0.975 |
| Harami | 2350 | 0.824 | 0.946 | 0.944 |
| **aggregate** | | **0.808** | **0.839** | **0.872** |

Reported per class because the classes are very unevenly represented. The
pattern in those numbers is not random: classes defined by a relationship
between whole candle bodies (Engulfing, Harami) are close to solved, while those
defined by a proportion inside a single candle (Hammer, Shooting Star, the
Stars) are much harder -- at this resolution a candle body is only a few pixels
tall, so the measurement the rule depends on is the one the image barely
resolves.

## Usage

```python
from huggingface_hub import hf_hub_download
from ultralytics import YOLO

model = YOLO(hf_hub_download("rohanjain2312/candlestick-pattern-recognition-system-yolo", "best.pt"))
results = model.predict("chart.png", conf=0.25)
```

Charts must be rendered the same way the training data was: 20
candles, 640x640, no axes, no gridlines, no volume
panel. Use `src/data_pipeline/render_charts.py` from the repo -- a differently
drawn chart is an input distribution this model has never seen. Note also that
Ultralytics expects **BGR** arrays while most renderers emit RGB.

## Splits

Chronological with an embargo gap, never random. Consecutive windows overlap in
19 of 20 candles, so the first 20 windows after each boundary
are discarded and no test chart shares a candle with a training chart.

- Code: https://github.com/rohanjain2312/candlestick-pattern-recognition-system
- Dataset: https://huggingface.co/datasets/rohanjain2312/candlestick-pattern-recognition-system-data
- Demo: https://huggingface.co/spaces/rohanjain2312/candlestick-pattern-recognition-system-demo

Not investment advice.

