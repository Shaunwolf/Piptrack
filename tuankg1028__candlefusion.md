# tuankg1028/candlefusion (model)

```json
{
  "kind": "model",
  "id": "tuankg1028/candlefusion",
  "url": "https://huggingface.co/tuankg1028/candlefusion",
  "meta": {
    "tags": [
      "pytorch",
      "candlefusion",
      "candlestick",
      "financial-analysis",
      "multimodal",
      "bert",
      "vit",
      "cross-attention",
      "trading",
      "forecasting",
      "dataset:tuankg1028/btc-candlestick-dataset",
      "license:apache-2.0",
      "region:us"
    ],
    "downloads": 189,
    "likes": 0,
    "cardData": {
      "license": "apache-2.0",
      "tags": [
        "pytorch",
        "candlestick",
        "financial-analysis",
        "multimodal",
        "bert",
        "vit",
        "cross-attention",
        "trading",
        "forecasting"
      ],
      "datasets": [
        "tuankg1028/btc-candlestick-dataset"
      ]
    },
    "lastModified": "2025-07-01T02:30:24.000Z",
    "gated": false,
    "private": false
  },
  "files": [
    {
      "path": ".gitattributes",
      "size": 1519,
      "type": "file"
    },
    {
      "path": "README.md",
      "size": 2725,
      "type": "file"
    },
    {
      "path": "config.json",
      "size": 258,
      "type": "file"
    },
    {
      "path": "pytorch_model.bin",
      "size": 797843991,
      "type": "file"
    },
    {
      "path": "training_history.json",
      "size": 3372,
      "type": "file"
    }
  ]
}
```

## README

---
license: apache-2.0
tags:
- pytorch
- candlestick
- financial-analysis
- multimodal
- bert
- vit
- cross-attention
- trading
- forecasting
datasets:
- tuankg1028/btc-candlestick-dataset
---

# CandleFusion Model

A multimodal financial analysis model that combines textual market sentiment with visual candlestick patterns for enhanced trading signal prediction and price forecasting.

## Links
- 🔗 **GitHub Repository**: https://github.com/tuankg1028/CandleFusion
- 🚀 **Demo on Hugging Face Spaces**: https://huggingface.co/spaces/tuankg1028/candlefusion

## Training Results
- **Best Epoch**: 18
- **Best Validation Loss**: 316165.5985
- **Training Epochs**: 23
- **Early Stopping**: Yes

## Architecture Overview

### Core Components
- **Text Encoder**: BERT (bert-base-uncased) for processing market sentiment and news
- **Vision Encoder**: Vision Transformer (ViT-base-patch16-224) for candlestick pattern recognition
- **Cross-Attention Fusion**: Multi-head attention mechanism (8 heads, 768 dim) for text-image integration
- **Dual Task Heads**: 
  - Classification head for trading signals (bullish/bearish)
  - Regression head for next closing price prediction

### Data Flow
1. **Text Processing**: Market sentiment -> BERT -> CLS token (768-dim)
2. **Image Processing**: Candlestick charts -> ViT -> Patch embeddings (197 tokens, 768-dim each)
3. **Cross-Modal Fusion**: Text CLS as query, Image patches as keys/values -> Fused representation
4. **Dual Predictions**: 
   - Fused features -> Classification head -> Trading signal logits
   - Fused features -> Regression head -> Price forecast

### Model Specifications
- **Input Text**: Tokenized to max 64 tokens
- **Input Images**: Resized to 224x224 RGB
- **Hidden Dimension**: 768 (consistent across encoders)
- **Output Classes**: 2 (bullish/bearish)
- **Dropout**: 0.3 in both heads

## Training Details
- **Epochs**: 100
- **Learning Rate**: 2e-05
- **Loss Function**: CrossEntropy (classification) + MSE (regression)
- **Loss Weight (alpha)**: 0.5 for regression term
- **Optimizer**: AdamW with linear scheduling
- **Early Stopping Patience**: 5

## Usage
```python
from model import CrossAttentionModel
import torch

# Load model
model = CrossAttentionModel()
model.load_state_dict(torch.load("pytorch_model.bin"))
model.eval()

# Inference
outputs = model(input_ids, attention_mask, pixel_values)
trading_signals = outputs["logits"]
price_forecast = outputs["forecast"]
```

## Performance
The model simultaneously optimizes for:
- **Classification Task**: Trading signal accuracy
- **Regression Task**: Price prediction MSE

This dual-task approach enables the model to learn both categorical market direction and continuous price movements.

## config.json

```
{
  "model_type": "candlefusion",
  "architecture": "bert+vit+cross_attention",
  "num_labels": 3,
  "epochs": 100,
  "learning_rate": 2e-05,
  "alpha": 0.5,
  "best_epoch": 18,
  "best_val_loss": 316165.5984660823,
  "early_stopping_patience": 5
}
```
