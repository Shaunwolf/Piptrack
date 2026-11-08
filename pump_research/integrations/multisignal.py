"""
#31 Rodri1970/MultiSignal-Trader — technical random forest + FinBERT news sentiment.

A port of the Space's app.py (MIT License): a random forest on SMA 10/50, RSI,
daily range and returns predicts whether tomorrow closes higher (trained on the
first 80% of history, scored on the last 20%), FinBERT scores recent headlines,
and the two combine into the Space's four decisions.
"""

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .base import Integration

FINBERT = "ProsusAI/finbert"
_PIPELINE = None


def _features(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    close = df["close"]
    out["Close"] = close
    out["SMA_10"] = close.rolling(10).mean()
    out["SMA_50"] = close.rolling(50).mean()
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    out["RSI"] = 100 - 100 / (1 + gain / loss)
    out["Volatilidad"] = (df["high"] - df["low"]) / close
    out["Retorno"] = close.pct_change()
    out["Target"] = (close.shift(-1) > close).astype(int)
    return out


def news_sentiment(headlines: List[str]) -> Optional[float]:
    """Mean FinBERT score in -1..1 (positive adds the score, negative subtracts it), or None without transformers"""
    global _PIPELINE
    if not headlines:
        return 0.0
    try:
        from transformers import pipeline
    except ImportError:
        return None
    if _PIPELINE is None:
        _PIPELINE = pipeline("text-classification", model=FINBERT)
    total = 0.0
    for res in _PIPELINE(headlines[:5]):
        total += res["score"] if res["label"] == "positive" else -res["score"] if res["label"] == "negative" else 0.0
    return total / min(len(headlines), 5)


def multisignal_trader(prices: pd.DataFrame, headlines: Optional[List[str]] = None) -> Dict:
    from sklearn.ensemble import RandomForestClassifier
    df = _features(prices).replace([np.inf, -np.inf], np.nan)
    last_row = df.iloc[[-1]]
    df = df.dropna()
    if len(df) < 100:
        return {"error": "needs at least 100 bars (the Space uses 2 years)"}
    feats = ["Close", "SMA_10", "SMA_50", "RSI", "Volatilidad", "Retorno"]
    # The last bar has no known "tomorrow", so it's never trained on
    train_df = df.iloc[:-1]
    split = int(len(train_df) * 0.8)
    model = RandomForestClassifier(n_estimators=100, max_depth=4, random_state=42)
    model.fit(train_df[feats].iloc[:split], train_df["Target"].iloc[:split])
    accuracy = float(model.score(train_df[feats].iloc[split:], train_df["Target"].iloc[split:]))
    latest = last_row[feats].fillna(df[feats].iloc[-1])
    technical_up = int(model.predict(latest)[0])
    sentiment = news_sentiment(headlines or [])
    s = sentiment or 0.0
    if s > 0.2 and technical_up == 1:
        decision = "strong_buy"
    elif s < -0.2 and technical_up == 0:
        decision = "strong_sell"
    elif technical_up == 1:
        decision = "moderate_buy"
    else:
        decision = "hold_or_moderate_sell"
    base_rate = float(train_df["Target"].iloc[split:].mean())
    return {"decision": decision, "technical_prediction": "up" if technical_up else "down",
            "technical_probability_up": float(model.predict_proba(latest)[0][1]),
            "holdout_accuracy": accuracy, "holdout_up_rate": base_rate,
            "news_sentiment": sentiment, "headlines_scored": len(headlines or []),
            "note": ("FinBERT unavailable (pip install transformers torch); decision uses the technical model only"
                     if sentiment is None else "Compare holdout accuracy with the up-rate: beating it is the bar.")}


INTEGRATION = Integration(
    key="multisignal_trader", title="MultiSignal Trader (Rodri1970 Space)", hf_id="Rodri1970/MultiSignal-Trader",
    hf_kind="space", category="signal",
    description="Random forest on SMA/RSI/volatility/returns plus FinBERT headline sentiment → strong/moderate buy, hold or strong sell.",
    requires=["sklearn"], pip=["transformers", "torch"])
