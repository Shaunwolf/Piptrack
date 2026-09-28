"""Hugging Face integrations, tested offline with fakes for the Hub, YOLO and datasets"""

import io
import json
import os
import sys
import tarfile
from datetime import date

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(__file__))
from test_pump_research import make_prices  # noqa: E402
from test_technicals import bars  # noqa: E402

import pump_research.integrations as integ
from pump_research.integrations import base, candle_benchmark as bench, ohlcv_minute, reddit_corpora
from pump_research.integrations import candlesticks_yolo as ycandles, chart_patterns_yolo as ycharts, yolo_common
from pump_research.integrations.render import render_candlestick_window, CANDLE_WINDOW


@pytest.fixture(autouse=True)
def temp_config(tmp_path, monkeypatch):
    monkeypatch.setenv(base.CONFIG_ENV, str(tmp_path / "integrations.json"))
    yolo_common._MODELS.clear()
    reddit_corpora._CACHE.clear()


# --- Registry and switches -------------------------------------------------------------------

def test_every_requested_resource_is_registered():
    ids = {i["hf_id"] for i in integ.list_integrations()}
    assert ids == {
        "foduucom/stockmarket-pattern-detection-yolov8", "rohanjain2312/candlestick-pattern-recognition-system-yolo",
        "rohanjain2312/candlestick-pattern-recognition-system-data", "Rodri1970/MultiSignal-Trader",
        "tuankg1028/candlefusion", "Sentdex/wsb_reddit_v001", "kowalsky/reddit_about_money", "mito0o852/OHLCV-1m",
        "JONNYVERSE/stockmarket-pattern-detection-yolov8-onnx"}


def test_switches_persist_and_gate_what_runs(monkeypatch):
    assert not any(i["enabled"] for i in integ.list_integrations())
    integ.set_enabled("multisignal_trader", True)
    assert integ.is_enabled("multisignal_trader")
    out = integ.run_enabled(make_prices("2020-01-01", 300, seed=1), ticker="X")
    assert set(out) == {"multisignal_trader"}
    integ.set_enabled("multisignal_trader", False)
    assert integ.run_enabled(make_prices("2020-01-01", 300, seed=1), ticker="X") == {}
    with pytest.raises(KeyError):
        integ.set_enabled("nope", True)


def test_price_source_joins_when_enabled():
    from pump_research.config import Settings
    from pump_research.sources import default_price_sources
    assert "hf_ohlcv_1m" not in [s.name for s in default_price_sources(Settings())]
    integ.set_enabled("ohlcv_1m_prices", True)
    assert default_price_sources(Settings())[-1].name == "hf_ohlcv_1m"


def test_missing_packages_are_reported_not_raised(monkeypatch):
    monkeypatch.setattr(integ.REGISTRY["candlefusion"], "requires", ["definitely_not_installed_pkg"])
    out = integ.run_integration("candlefusion", make_prices("2020-01-01", 60))
    assert "missing packages" in out["error"]


# --- Rendering and YOLO -----------------------------------------------------------------------

def test_candlestick_renderer_matches_training_geometry():
    window = make_prices("2021-01-01", CANDLE_WINDOW, seed=3)
    image, mapper = render_candlestick_window(window)
    assert image.shape == (640, 640, 3) and image.dtype == np.uint8
    # Candle centres sit at (i + 0.8) / 20.6 of the width, like the training renderer
    for i in (0, 10, 19):
        x_norm = (i + 0.8) / (CANDLE_WINDOW - 1 + 1.6)
        assert mapper.candle_at(x_norm) == pytest.approx(i, abs=0.05)


class FakeBoxes:
    def __init__(self, xyxyn, cls, conf):
        self.xyxyn, self.cls, self.conf = np.array(xyxyn), np.array(cls), np.array(conf)

    def __len__(self):
        return len(self.cls)


class FakeYolo:
    def __init__(self, names, boxes):
        self.names, self._boxes = names, boxes
        self.seen = None

    def predict(self, image, conf=0.25, verbose=False):
        self.seen = image
        return [type("R", (), {"boxes": self._boxes, "names": self.names})()]


def test_yolo_candlesticks_maps_boxes_to_candles(monkeypatch):
    window = make_prices("2021-01-01", 40, seed=4)
    last_x = (19 + 0.8) / 20.6
    fake = FakeYolo({i: n for i, n in enumerate(ycandles.CLASSES)},
                    FakeBoxes([[last_x - 0.06, 0.2, last_x + 0.015, 0.5]], [2], [0.91]))
    monkeypatch.setattr(ycandles, "load_yolo", lambda repo, weights: fake)
    out = ycandles.yolo_candlesticks(window)
    p = out["patterns"][0]
    assert p["name"] == "BullishEngulfing" and p["direction"] == "bullish" and p["on_last_candle"]
    assert p["completed_date"] == window.index[-1].isoformat()
    assert fake.seen.shape == (640, 640, 3)  # BGR array handed to the model


def test_yolo_chart_patterns_translates_labels(monkeypatch):
    window = make_prices("2021-01-01", 150, seed=5)
    fake = FakeYolo({0: "W_Bottom", 1: "Head and shoulders top"},
                    FakeBoxes([[0.55, 0.3, 0.9, 0.7], [0.1, 0.2, 0.3, 0.5]], [0, 1], [0.7, 0.4]))
    monkeypatch.setattr(ycharts, "load_yolo", lambda repo, weights: fake)
    out = ycharts.yolo_chart_patterns(window)
    names = {p["name"]: p for p in out["patterns"]}
    assert names["double_bottom"]["direction"] == "bullish" and names["head_shoulders"]["direction"] == "bearish"
    assert names["double_bottom"]["start_date"] < names["double_bottom"]["completed_date"]


# --- Candlestick benchmark ----------------------------------------------------------------------

def test_candlestick_benchmark_scores_agreement(tmp_path, monkeypatch):
    # 20-bar window whose last two candles are a bullish engulfing (as TA-Lib would label it)
    rows = [[10 - i * 0.1, 10.1 - i * 0.1, 9.8 - i * 0.1, 9.9 - i * 0.1, 1e5] for i in range(18)]
    rows += [[8.2, 8.25, 7.95, 8.0, 1e5], [7.95, 8.5, 7.9, 8.45, 1e5]]
    df = bars(rows)
    end = df.index[-1]
    cx = (18.5 + 0.8) / 20.6
    label = f"2 {cx:.6f} 0.5 {1.24 / 20.6:.6f} 0.3\n"
    tar_path = tmp_path / "test.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        data = label.encode()
        info = tarfile.TarInfo(f"labels/test/SPY_{end.strftime('%Y%m%d')}.txt")
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    monkeypatch.setattr(bench, "hf_download", lambda *a, **k: str(tar_path))
    labels = bench.read_labels("test")
    assert labels == {("SPY", end): {("BullishEngulfing", 19)}}
    out = bench.candlestick_benchmark(lambda t, s, e: df, labels=labels)
    assert out["charts_compared"] == 1
    assert out["per_pattern"]["BullishEngulfing"]["agree"] == 1


# --- MultiSignal, CandleFusion -------------------------------------------------------------------

def test_multisignal_trader_runs_without_finbert():
    out = integ.run_integration("multisignal_trader", make_prices("2020-01-01", 400, seed=7))
    assert out["decision"] in {"strong_buy", "strong_sell", "moderate_buy", "hold_or_moderate_sell"}
    assert 0 <= out["holdout_accuracy"] <= 1


def test_multisignal_combines_sentiment(monkeypatch):
    from pump_research.integrations import multisignal
    monkeypatch.setattr(multisignal, "news_sentiment", lambda h: 0.6)
    up = make_prices("2020-01-01", 400, seed=8)
    out = multisignal.multisignal_trader(up, ["Company beats estimates"])
    if out["technical_prediction"] == "up":
        assert out["decision"] == "strong_buy"
    else:
        assert out["decision"] == "hold_or_moderate_sell"


def test_candlefusion_text_matches_the_original_formatter():
    from pump_research.integrations.candlefusion_model import format_candle_to_text
    text = format_candle_to_text({"open": 10.0, "high": 11.0, "low": 9.5, "close": 10.5, "volume": 1e6})
    assert text.startswith("Candle: bullish, Price change: 5.00%") and "Volume: normal" in text


# --- Reddit corpora -----------------------------------------------------------------------------

def test_reddit_corpora_count_mentions(tmp_path, monkeypatch):
    wsb = tmp_path / "wsb.json"
    wsb.write_text(json.dumps([{"sample": "[INST]\nKOSS to the moon\n[/INST]\n\nno way"},
                               {"sample": "[INST]\nbuy AAPL\n[/INST]\n\nok"}]))
    stocks = tmp_path / "stocks.csv"
    stocks.write_text('Title,Score,URL,Comments\n"KOSS earnings play",120,https://www.reddit.com/r/stocks/1,"nice"\n'
                      '"Unrelated",5,https://www.reddit.com/r/stocks/2,"meh"\n')
    monkeypatch.setattr(reddit_corpora, "hf_download",
                        lambda repo, name, repo_type="model": str(wsb if name.endswith(".json") else stocks))
    w = reddit_corpora.wsb_corpus_mentions("KOSS")
    assert w["mentions"] == 1 and "moon" in w["examples"][0]
    r = reddit_corpora.reddit_money_mentions("KOSS")
    assert r["mentions"] >= 1 and r["examples"][0]["title"] == "KOSS earnings play"


# --- OHLCV-1m price source -------------------------------------------------------------------------

def test_minute_bars_aggregate_to_regular_session_days(tmp_path, monkeypatch):
    import pyarrow as pa
    import pyarrow.parquet as pq
    ts = pd.date_range("2021-01-04 13:00", periods=600, freq="1min", tz="UTC")  # 08:00-17:59 New York
    minutes = pd.DataFrame({"timestamp": ts, "open": 10.0, "high": 10.5, "low": 9.5, "close": 10.2, "volume": 1.0,
                            "ticker": "KOSS"})
    minutes.loc[0, "high"] = 99.0  # pre-market spike must be ignored
    other = minutes.assign(ticker="AAPL", close=1.0)
    path = tmp_path / "ohlcv_2021-01.parquet"
    pq.write_table(pa.Table.from_pandas(pd.concat([minutes, other]), preserve_index=False), path)
    monkeypatch.setattr(ohlcv_minute, "hf_download", lambda *a, **k: str(path))
    daily = ohlcv_minute.daily_prices("KOSS", date(2021, 1, 1), date(2021, 1, 31))
    assert list(daily.index) == [date(2021, 1, 4)]
    row = daily.iloc[0]
    assert row["high"] == 10.5 and row["close"] == 10.2 and row["volume"] == 390  # 09:30-15:59 only
    assert ohlcv_minute.months_between(date(2020, 11, 5), date(2021, 2, 1)) == ["2020-11", "2020-12", "2021-01", "2021-02"]


def test_run_integration_passes_ticker_to_yolo_wrappers(monkeypatch):
    fake = FakeYolo({0: "Doji"}, FakeBoxes(np.zeros((0, 4)), [], []))
    monkeypatch.setattr(ycandles, "load_yolo", lambda repo, weights: fake)
    monkeypatch.setattr(ycharts, "load_yolo", lambda repo, weights: fake)
    prices = make_prices("2021-01-01", 150, seed=6)
    for key in ("yolo_candlesticks", "yolo_chart_patterns"):
        monkeypatch.setattr(integ.REGISTRY[key], "requires", [])
    for key in ("yolo_candlesticks", "yolo_chart_patterns"):
        assert "error" not in integ.run_integration(key, prices, ticker="SPY", headlines=["x"])


def test_minute_source_probes_one_month_for_unknown_tickers(monkeypatch):
    calls = []
    monkeypatch.setattr(ohlcv_minute, "_month_minutes", lambda t, m: calls.append(m) or pd.DataFrame())
    out = ohlcv_minute.daily_prices("NOPE", date(2020, 1, 1), date(2021, 3, 1), probe=date(2021, 1, 15))
    assert out.empty and calls == ["2021-01"]


def test_onnx_chart_patterns_decodes_yolov8_output(monkeypatch):
    from pump_research.integrations import chart_patterns_onnx as onnx
    window = make_prices("2021-01-01", 150, seed=9)

    class Input:
        name, shape = "images", [1, 3, 640, 640]

    class FakeSession:
        def get_inputs(self):
            return [Input()]

        def run(self, _, feeds):
            self.tensor = feeds["images"]
            out = np.zeros((1, 10, 3), dtype=np.float32)
            out[0, :4, 0] = [480, 320, 200, 100]; out[0, 4 + 5, 0] = 0.8   # W_Bottom on the right half
            out[0, :4, 1] = [482, 321, 200, 100]; out[0, 4 + 5, 1] = 0.6   # overlapping duplicate, suppressed
            out[0, :4, 2] = [100, 300, 50, 50]; out[0, 4 + 1, 2] = 0.1     # below the confidence bar
            return [out]

    fake = FakeSession()
    monkeypatch.setattr(onnx, "load_session", lambda: fake)
    out = onnx.onnx_chart_patterns(window)
    assert fake.tensor.shape == (1, 3, 640, 640) and fake.tensor.dtype == np.float32 and fake.tensor.max() <= 1
    assert [p["name"] for p in out["patterns"]] == ["double_bottom"]
    p = out["patterns"][0]
    assert p["direction"] == "bullish" and p["start_date"] < p["completed_date"]
    assert p["completed_date"] > window.index[len(window) // 2].isoformat()


def test_minute_bars_are_split_adjusted_before_the_lead_in():
    days = pd.date_range("2024-10-01", periods=40, freq="B").date
    close = np.full(40, 0.27)
    close[20:] = 2.7                    # 1:10 reverse split on day 20
    close[35] = 27.0                    # a genuine 10x pump inside the protected lead-in
    daily = pd.DataFrame({"open": close, "high": close * 1.02, "low": close * 0.98, "close": close,
                          "volume": np.r_[np.full(20, 1e6), np.full(20, 1e5)]}, index=days)
    adjusted, splits = ohlcv_minute.adjust_splits(daily, protect_from=days[30])
    assert splits == [{"date": days[20].isoformat(), "kind": "reverse", "ratio": "1:10"}]
    assert adjusted["close"].iloc[0] == pytest.approx(2.7) and adjusted["volume"].iloc[0] == pytest.approx(1e5)
    assert adjusted["close"].iloc[35] == pytest.approx(27.0)
