# Hugging Face resources for PipSqueak

A survey of models, datasets and apps (Spaces) on Hugging Face related to stock signals, pumps and dumps, price history and price action.

*Compiled September 2026 from Hugging Face search listings. The site itself was blocked from the build environment, so descriptions come from each item's listing summary. Check the license and freshness on the model card before using anything.*

## Best fits for this project

1. **FinTwitBERT-sentiment**: swap for VADER when scoring Reddit and social posts. It's trained on financial tweets, so it handles "$GME 🚀" slang.
2. **SocialGrep WallStreetBets (Aug 2021)** and **Sentdex WSB 2017–18**: offline Reddit history for events the live archives can't reach (SPRT Aug 2021, Longfin Dec 2017).
3. **hfdatalibrary** / **OHLCV-1m**: long US equity price histories that may cover tickers Yahoo has dropped.
4. **Chronos-2**: a zero-shot forecaster that could sit next to (or replace) the spaghetti-model forecast paths.
5. **Candlestick recognition datasets**: labelled pattern data to cross-check `technicals/candles.py`.

## Price history (datasets)

| Name | What it is | How it could help |
|---|---|---|
| [mito0o852/OHLCV-1m](https://huggingface.co/datasets/mito0o852/OHLCV-1m) | Minute OHLCV candles for thousands of US stocks, 1992–2026 (sourced from Finnhub) | Deep history, possibly including delisted pump stocks; intraday view of pump days |
| [elkassabgi/hfdatalibrary](https://huggingface.co/datasets/elkassabgi/hfdatalibrary) | Research-grade OHLCV for 1,391 US equities and ETFs, Dec 2002 → present, 1-minute to monthly, updated daily | Offline price source and control universe |
| [paperswithbacktest/Stocks-Daily-Price](https://huggingface.co/datasets/paperswithbacktest/Stocks-Daily-Price) | Daily stock prices | Simple daily bars for `discover` scans across a wide universe |
| [edarchimbaud/timeseries-1m-stocks](https://huggingface.co/datasets/edarchimbaud/timeseries-1m-stocks) | 1-minute bars for S&P 500 constituents | Large-cap intraday baseline (ordinary behaviour) |
| [Traders-Lab/TroveLedger](https://huggingface.co/datasets/Traders-Lab/TroveLedger) | Full S&P 500 (503 names) with extended intraday history and daily OHLCV | Control windows and a bot-training universe |
| [HaiwenWang/sp500-pit-benchmark](https://huggingface.co/datasets/HaiwenWang/sp500-pit-benchmark) | Point-in-time US equity benchmark at daily, 30-minute and 1-minute frequencies with adjusted OHLCV | Survivorship-bias-aware backtests of the similarity score |
| [pmoe7/SP_500_Stocks_Data-ratios_news_price_10_yrs](https://huggingface.co/datasets/pmoe7/SP_500_Stocks_Data-ratios_news_price_10_yrs) | 10 years of S&P 500 prices with financial ratios and news | Adds fundamentals and news context to windows |
| [infinite-dataset-hub/StockPredictTraining](https://huggingface.co/datasets/infinite-dataset-hub/StockPredictTraining) | OHLCV with up/down/flat labels | Quick sanity checks for classifiers (synthetic-style; don't treat as real history) |

## Social chatter and meme stocks (datasets)

| Name | What it is | How it could help |
|---|---|---|
| [SocialGrep/reddit-wallstreetbets-aug-2021](https://huggingface.co/datasets/SocialGrep/reddit-wallstreetbets-aug-2021) | Every r/wallstreetbets post and comment from August 2021 | Reddit context for the SPRT (Aug 2021) event and the IRNT build-up, bypassing blocked archives |
| [Sentdex/wsb_reddit_v001](https://huggingface.co/datasets/Sentdex/wsb_reddit_v001) | r/wallstreetbets comments/replies, ~2017–2018 | Reddit context for Longfin (Dec 2017) |
| [kowalsky/reddit_about_money](https://huggingface.co/datasets/kowalsky/reddit_about_money) | Reddit money/stocks posts (reddit_stocks.csv) | Extra chatter samples for mention counting |
| [emilpartow/reddit_finance_posts_apple-tesla-microsoft](https://huggingface.co/datasets/emilpartow/reddit_finance_posts_apple-tesla-microsoft) | Small Reddit finance sample (AAPL, TSLA, MSFT) | Fixtures for testing the Reddit pipeline |

## Sentiment models

| Name | What it is | How it could help |
|---|---|---|
| [StephanAkkerman/FinTwitBERT-sentiment](https://huggingface.co/StephanAkkerman/FinTwitBERT-sentiment) | Sentiment for financial tweets, built on FinTwitBERT (pre-trained on 10M financial tweets) | Best fit for Reddit/StockTwits-style text; replace VADER in `sources/social.py` |
| [StephanAkkerman/FinTwitBERT](https://huggingface.co/StephanAkkerman/FinTwitBERT) | Base language model for financial social media | Fine-tune a "pump chatter" classifier |
| [ProsusAI/finbert](https://huggingface.co/ProsusAI/finbert) | The standard financial-news sentiment model | Score news headlines in the window |
| [yiyanghkust/finbert-tone](https://huggingface.co/yiyanghkust/finbert-tone) | FinBERT tuned for tone in analyst and filing text | Tone of 8-Ks and press releases before pumps |
| [ahmedrachid/FinancialBERT-Sentiment-Analysis](https://huggingface.co/ahmedrachid/FinancialBERT-Sentiment-Analysis) | Financial BERT fine-tuned on Financial PhraseBank | Alternative news-sentiment scorer |

## Forecasting models

| Name | What it is | How it could help |
|---|---|---|
| [amazon/chronos-2](https://huggingface.co/amazon/chronos-2) | 120M-parameter time-series foundation model; zero-shot univariate, multivariate and covariate forecasts with quantiles | Probabilistic price paths for the forecast pages; volume as a covariate |
| [amazon/chronos-t5-large](https://huggingface.co/amazon/chronos-t5-large) | Earlier Chronos (T5) that tokenizes series for language-model forecasting | Lighter baseline forecaster |
| [TimesFM](https://huggingface.co/docs/transformers/en/model_doc/timesfm) (Google, in Transformers) | Decoder-only patch model for zero-shot forecasting | Second opinion alongside Chronos |
| [jengyang/lstm-stock-prediction-model](https://huggingface.co/jengyang/lstm-stock-prediction-model) | LSTM stock-price forecaster | Reference architecture; weak for pumps (they're outliers) |
| [Adilbai/stock-trading-rl-agent](https://huggingface.co/Adilbai/stock-trading-rl-agent) | Reinforcement-learning trading agent driven by technical indicators | Idea source for turning signals into position rules |

## Price action and pattern recognition

| Name | What it is | How it could help |
|---|---|---|
| [foduucom/stockmarket-pattern-detection-yolov8](https://huggingface.co/foduucom/stockmarket-pattern-detection-yolov8) | YOLOv8 that detects chart patterns in screenshots of trading charts | Visual cross-check of `chart_patterns.py` |
| [foduucom/stockmarket-future-prediction](https://huggingface.co/foduucom/stockmarket-future-prediction) | YOLOv8s detecting patterns in live chart video | Same, on live screens |
| [rohanjain2312/candlestick-pattern-recognition-system-yolo](https://huggingface.co/rohanjain2312/candlestick-pattern-recognition-system-yolo) | Detects 8 candlestick patterns in rendered 20-candle charts (boxes labelled with TA-Lib) | Validate candle detection against TA-Lib-labelled data |
| [rohanjain2312/candlestick-pattern-recognition-system-data](https://huggingface.co/datasets/rohanjain2312/candlestick-pattern-recognition-system-data) | The labelled dataset behind it | Ground truth for tests |
| [tuankg1028/candlefusion](https://huggingface.co/tuankg1028/candlefusion) | Multimodal model combining text sentiment with candlestick images | Blueprint for mixing Reddit text with the tremor window |

## Apps (Spaces) worth studying

| Name | What it does |
|---|---|
| [Tonic/stock-predictions](https://huggingface.co/spaces/Tonic/stock-predictions) | Chronos forecasts plus RSI, MACD and Bollinger analysis |
| [feliponi/stock](https://huggingface.co/spaces/feliponi/stock) | Technical plus sentiment indicators, trade recommendations and return simulation |
| [park-math/Stock-B](https://huggingface.co/spaces/park-math/Stock-B) | Scans Korean and US stocks and issues buy/wait/sell alerts |
| [Rodri1970/MultiSignal-Trader](https://huggingface.co/spaces/Rodri1970/MultiSignal-Trader) | Combines news sentiment and indicators into buy/hold/sell |
| [openfree/Stock-Trading-Analysis](https://huggingface.co/spaces/openfree/Stock-Trading-Analysis) | News sentiment summary with a price chart |
| [Anvarbekkk/real-time-stock-predictor](https://huggingface.co/spaces/Anvarbekkk/real-time-stock-predictor) | LSTM forecasts with SMA overlays |

## Pump-and-dump specifically

No Hugging Face model or dataset built for **stock** pump-and-dump detection turned up. The closest material is academic:
- [Detecting Pump&Dump Stock Market Manipulation from Online Forums](https://arxiv.org/pdf/2301.11403) (Reddit plus yfinance)
- [Pump and Dumps in the Bitcoin Era](https://arxiv.org/pdf/2005.06610) and [Crypto Pump and Dump Detection via Deep Learning](https://arxiv.org/pdf/2205.04646) (labelled Binance pump events)
- [PumpSense](https://arxiv.org/pdf/2605.09431) (Telegram pump announcements)

Their labelled event lists could extend `seeds.csv`.
