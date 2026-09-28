# JONNYVERSE/stockmarket-pattern-detection-yolov8-onnx (model)

```json
{
  "kind": "model",
  "id": "JONNYVERSE/stockmarket-pattern-detection-yolov8-onnx",
  "url": "https://huggingface.co/JONNYVERSE/stockmarket-pattern-detection-yolov8-onnx",
  "meta": {
    "tags": [
      "onnx",
      "yolov8",
      "license:apache-2.0",
      "region:us"
    ],
    "downloads": 40,
    "likes": 0,
    "cardData": {
      "license": "apache-2.0"
    },
    "lastModified": "2026-08-24T14:41:12.000Z",
    "gated": false,
    "private": false
  },
  "files": [
    {
      "path": "onnx",
      "size": 0,
      "type": "directory"
    },
    {
      "path": ".gitattributes",
      "size": 1519,
      "type": "file"
    },
    {
      "path": "README.md",
      "size": 28,
      "type": "file"
    },
    {
      "path": "config.json",
      "size": 386,
      "type": "file"
    },
    {
      "path": "onnx/model.onnx",
      "size": 174730985,
      "type": "file"
    },
    {
      "path": "preprocessor_config.json",
      "size": 317,
      "type": "file"
    }
  ]
}
```

## README

---
license: apache-2.0
---


## config.json

```
{
  "model_type": "yolov8",
  "id2label": {
    "0": "Head and shoulders bottom",
    "1": "Head and shoulders top",
    "2": "M_Head",
    "3": "StockLine",
    "4": "Triangle",
    "5": "W_Bottom"
  },
  "label2id": {
    "Head and shoulders bottom": 0,
    "Head and shoulders top": 1,
    "M_Head": 2,
    "StockLine": 3,
    "Triangle": 4,
    "W_Bottom": 5
  }
}
```
