"""
#27 tuankg1028/candlefusion — BERT (text) + ViT (chart) with cross-attention.

Ported from github.com/tuankg1028/CandleFusion (Apache-2.0): the model class, the
candle-to-text formatter (including its quirk that volume always reads "normal")
and the 30-candle chart style it was trained on.

Read its outputs carefully:
- it was trained on BTC/USDT, so the price forecast is in the scale of that
  training data and is not meaningful for a stock;
- its "signal" label is the direction of the *last candle already in the chart*
  (close vs open, ±0.5%), so the classification describes today, not tomorrow.
"""

import os
from typing import Dict

import pandas as pd

from .base import Integration, IntegrationUnavailable, hf_download
from .render import render_candlefusion_window

REPO = "tuankg1028/candlefusion"
LABELS = ["bearish", "neutral", "bullish"]
WINDOW = 30
_LOADED = {}


def format_candle_to_text(c: Dict) -> str:
    price_change = c["close"] - c["open"]
    pct = price_change / c["open"] * 100
    rng = c["high"] - c["low"]
    upper = c["high"] - max(c["open"], c["close"])
    lower = min(c["open"], c["close"]) - c["low"]
    body = abs(price_change)
    kind = "bullish" if price_change > 0 else "bearish" if price_change < 0 else "doji"
    volume = "high" if c["volume"] > c.get("avg_volume", c["volume"]) else "normal"
    return (f"Candle: {kind}, Price change: {pct:.2f}%, Open: {c['open']:.2f}, High: {c['high']:.2f}, "
            f"Low: {c['low']:.2f}, Close: {c['close']:.2f}, Volume: {volume}, Range: {rng:.2f}, "
            f"Body size: {body:.2f}, Upper shadow: {upper:.2f}, Lower shadow: {lower:.2f}")


def _backbone(cls, base: str, prefix: str, state: dict):
    """Build a BERT/ViT backbone from the checkpoint's weights under `prefix`, via from_pretrained"""
    import tempfile

    from safetensors.torch import save_file
    config = cls.config_class.from_pretrained(base)
    weights = {k[len(prefix):]: v.contiguous() for k, v in state.items() if k.startswith(prefix)}
    with tempfile.TemporaryDirectory() as tmp:
        config.save_pretrained(tmp)
        save_file(weights, os.path.join(tmp, "model.safetensors"), metadata={"format": "pt"})
        model, info = cls.from_pretrained(tmp, output_loading_info=True)
    missing = [k for k in info.get("missing_keys", []) if "pooler" not in k]  # the pooler is never used
    if missing:
        raise IntegrationUnavailable(f"{base} weights in the CandleFusion checkpoint did not load: {missing[:3]}")
    return model


def _load():
    if "model" in _LOADED:
        return _LOADED["model"], _LOADED["tok"], _LOADED["proc"]
    try:
        import torch
        import torch.nn as nn
        from transformers import BertModel, BertTokenizer, ViTImageProcessor, ViTModel
    except ImportError:
        raise IntegrationUnavailable("needs torch and transformers (pip install torch transformers)")

    class CrossAttentionModel(nn.Module):
        def __init__(self, bert, vit, hidden_dim=768, num_classes=3):
            super().__init__()
            self.bert, self.vit = bert, vit
            self.cross_attention = nn.MultiheadAttention(embed_dim=hidden_dim, num_heads=8, batch_first=True)
            self.classifier = nn.Sequential(nn.Linear(hidden_dim, hidden_dim), nn.ReLU(), nn.Dropout(0.3), nn.Linear(hidden_dim, num_classes))
            self.regressor = nn.Sequential(nn.Linear(hidden_dim, hidden_dim), nn.ReLU(), nn.Dropout(0.3), nn.Linear(hidden_dim, 1))

        def forward(self, input_ids, attention_mask, pixel_values):
            text_cls = self.bert(input_ids=input_ids, attention_mask=attention_mask).last_hidden_state[:, 0:1, :]
            image_tokens = self.vit(pixel_values=pixel_values).last_hidden_state[:, 1:, :]
            fused, _ = self.cross_attention(query=text_cls, key=image_tokens, value=image_tokens)
            fused = fused.squeeze(1)
            return {"logits": self.classifier(fused), "forecast": self.regressor(fused)}

    state = torch.load(hf_download(REPO, "pytorch_model.bin"), map_location="cpu")
    # The checkpoint stores BERT and ViT under transformers-4 layer names. Loading each backbone through
    # from_pretrained lets transformers translate them for whichever version is installed.
    bert = _backbone(BertModel, "bert-base-uncased", "bert.", state)
    vit = _backbone(ViTModel, "google/vit-base-patch16-224", "vit.", state)
    model = CrossAttentionModel(bert, vit)
    head = {k: v for k, v in state.items() if not k.startswith(("bert.", "vit."))}
    result = model.load_state_dict(head, strict=False)
    missing = [k for k in result.missing_keys if not k.startswith(("bert.", "vit."))]
    if missing or result.unexpected_keys:
        raise IntegrationUnavailable(f"CandleFusion checkpoint does not match the model: missing {missing[:3]}, "
                                     f"unexpected {result.unexpected_keys[:3]}")
    model.eval()
    _LOADED.update(model=model, tok=BertTokenizer.from_pretrained("bert-base-uncased"),
                   proc=ViTImageProcessor.from_pretrained("google/vit-base-patch16-224"))
    return _LOADED["model"], _LOADED["tok"], _LOADED["proc"]


def candlefusion(prices: pd.DataFrame) -> Dict:
    window = prices.tail(WINDOW)
    if len(window) < WINDOW:
        return {"error": f"needs {WINDOW} bars"}
    import torch
    model, tok, proc = _load()
    last = {k: float(v) for k, v in window.iloc[-1].items()}
    text = format_candle_to_text(last)
    image = render_candlefusion_window(window)
    enc = tok(text, return_tensors="pt", truncation=True, padding="max_length", max_length=64)
    pix = proc(images=image, return_tensors="pt")["pixel_values"]
    with torch.no_grad():
        out = model(enc["input_ids"], enc["attention_mask"], pix)
    probs = torch.softmax(out["logits"], dim=-1)[0].tolist()
    return {"model": REPO, "candle_text": text,
            "last_candle_class": LABELS[int(max(range(3), key=lambda i: probs[i]))],
            "class_probabilities": dict(zip(LABELS, probs)), "raw_forecast": float(out["forecast"][0, 0]),
            "caveats": ["Trained on BTC/USDT: the forecast is in that training scale, not this stock's price.",
                        "The class describes the latest candle already on the chart (its training label), not the next one."]}


INTEGRATION = Integration(
    key="candlefusion", title="CandleFusion text+chart model (tuankg1028)", hf_id=REPO, hf_kind="model",
    category="signal",
    description="BERT reads a description of the latest candle, ViT reads the 30-candle chart; cross-attention fuses them.",
    requires=["torch", "transformers", "mplfinance", "PIL", "huggingface_hub"],
    pip=["torch", "transformers", "mplfinance", "pillow", "huggingface_hub"])
INTEGRATION.run = lambda prices=None, **kw: candlefusion(prices)
