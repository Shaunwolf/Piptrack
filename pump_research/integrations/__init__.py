"""
Switchable Hugging Face integrations. Each one is a separate function you can
call directly, and a registry entry you can turn on or off:

    from pump_research.integrations import yolo_chart_patterns, yolo_candlesticks, multisignal_trader, ...
    from pump_research.integrations import list_integrations, set_enabled, run_enabled

Turn them on/off with `python -m pump_research integrations enable KEY`, the
settings page (/pump-research/integrations) or integrations.json.
"""

from typing import Dict, List, Optional

import pandas as pd

from .base import Integration, IntegrationUnavailable, load_config, save_config
from .candlefusion_model import INTEGRATION as _CANDLEFUSION, candlefusion
from .candle_benchmark import INTEGRATION as _BENCHMARK, candlestick_benchmark
from .multisignal import INTEGRATION as _MULTISIGNAL, multisignal_trader
from .ohlcv_minute import INTEGRATION as _OHLCV, HfMinutePrices, daily_prices
from .reddit_corpora import MONEY_INTEGRATION as _MONEY, WSB_INTEGRATION as _WSB, reddit_money_mentions, wsb_corpus_mentions
from .candlesticks_yolo import INTEGRATION as _YOLO_CANDLES, yolo_candlesticks
from .chart_patterns_yolo import INTEGRATION as _YOLO_CHARTS, yolo_chart_patterns

REGISTRY: Dict[str, Integration] = {i.key: i for i in (
    _YOLO_CHARTS, _YOLO_CANDLES, _BENCHMARK, _MULTISIGNAL, _CANDLEFUSION, _WSB, _MONEY, _OHLCV)}

# Integrations that analyse a ticker's recent prices (run on scans and dossiers)
ANALYSIS_KEYS = ("yolo_chart_patterns", "yolo_candlesticks", "multisignal_trader", "candlefusion", "wsb_corpus",
                 "reddit_money_corpus")

__all__ = ["REGISTRY", "list_integrations", "set_enabled", "is_enabled", "run_integration", "run_enabled",
           "yolo_chart_patterns", "yolo_candlesticks", "candlestick_benchmark", "multisignal_trader", "candlefusion",
           "wsb_corpus_mentions", "reddit_money_mentions", "daily_prices", "HfMinutePrices", "IntegrationUnavailable"]


def list_integrations() -> List[Dict]:
    config = load_config()
    return [i.status(config) for i in REGISTRY.values()]


def is_enabled(key: str) -> bool:
    return bool(load_config().get(key))


def set_enabled(key: str, enabled: bool) -> Dict:
    if key not in REGISTRY:
        raise KeyError(f"unknown integration {key!r}; choose from {sorted(REGISTRY)}")
    config = load_config()
    config[key] = bool(enabled)
    save_config(config)
    return REGISTRY[key].status(config)


def run_integration(key: str, prices: Optional[pd.DataFrame] = None, ticker: str = "", **kwargs) -> Dict:
    """Run one integration regardless of its switch (errors come back as {'error': ...})"""
    if key not in REGISTRY:
        raise KeyError(f"unknown integration {key!r}")
    integ = REGISTRY[key]
    missing = integ.missing_packages()
    if missing:
        return {"error": f"missing packages: {', '.join(missing)}", "install": " ".join(integ.pip)}
    try:
        if key == "multisignal_trader":
            return multisignal_trader(prices, kwargs.get("headlines"))
        return integ.run(prices=prices, ticker=ticker, **kwargs)
    except IntegrationUnavailable as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {str(e)[:200]}"}


def run_enabled(prices: pd.DataFrame, ticker: str = "", headlines: Optional[List[str]] = None,
                keys=ANALYSIS_KEYS) -> Dict[str, Dict]:
    """Every switched-on analysis integration on the same prices"""
    config = load_config()
    return {k: run_integration(k, prices, ticker=ticker, headlines=headlines) for k in keys if config.get(k)}
