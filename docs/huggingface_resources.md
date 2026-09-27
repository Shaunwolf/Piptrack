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

---

# Pattern resources: harmonics, candlesticks, price action, Bollinger, Fibonacci/Gann

*Second survey, September 2026, from Hugging Face Hub search results. Most of these entries have no model card or a very thin one, so the descriptions below stick to what the listing shows. Check the license and read the code before using any of them.*

**Harmonic patterns, Gann, Fibonacci spirals:** no Hugging Face model or dataset covers harmonic patterns (Gartley, Bat, Butterfly, Crab, Shark, Cypher, 5-0), Gann tools or Fibonacci spirals. Searches for "harmonic", "gartley", "gann", "fibonacci spiral" and "fib retracement" return only unrelated items (audio harmonics, and stewy33's "subtle_fibonacci_trading" models, which are LLM belief-research artefacts rather than trading tools). The in-house engine (`technicals/harmonics.py`, `technicals/fib_tools.py`) is still the only implementation available. The closest Hub material is the Elliott-wave datasets below, which are also Fibonacci-ratio wave structures.

## Candlestick patterns

| # | Name | Type | What it is |
|---|---|---|---|
| 1 | [foduucom/CandleStickScan-Stock-trading-yolov8](https://huggingface.co/spaces/foduucom/CandleStickScan-Stock-trading-yolov8) | Space | YOLOv8 demo that detects candlestick formations in chart images |
| 2 | [rohanjain2312/candlestick-pattern-recognition-system-demo](https://huggingface.co/spaces/rohanjain2312/candlestick-pattern-recognition-system-demo) | Space | Demo of the 8-pattern YOLO model that is already integrated (`yolo_candlesticks`) |
| 3 | [khizarali07/candlestick_classifier](https://huggingface.co/khizarali07/candlestick_classifier) | Model | Image classifier for candlestick patterns |
| 4 | [ceruka/beit-candlestick-indicator](https://huggingface.co/ceruka/beit-candlestick-indicator) | Model | BEiT vision transformer fine-tuned on candlestick chart images |
| 5 | [aungkyawwin/Candlestick_Pattern](https://huggingface.co/aungkyawwin/Candlestick_Pattern) | Model | Candlestick-pattern recognition model |
| 6 | [nguyenquocanh/Candlestick](https://huggingface.co/datasets/nguyenquocanh/Candlestick) | Dataset | Candlestick chart images |
| 7 | [Tiru8055/NSE_top100_chart_candlestick_order_5min_tf](https://huggingface.co/datasets/Tiru8055/NSE_top100_chart_candlestick_order_5min_tf) | Dataset | Candlestick charts for India's NSE top 100 stocks (sibling sets at 1, 3, 10 and 15 minutes) |
| 8 | [arvind7754/btc-candlestick-dataset](https://huggingface.co/datasets/arvind7754/btc-candlestick-dataset) | Dataset | Bitcoin candlestick data |
| 9 | [doinglean/dinov3-candlestick-api](https://huggingface.co/spaces/doinglean/dinov3-candlestick-api) | Space | DINOv3 image-embedding API for candlestick charts |
| 10 | [siladitya41/indian-candlestick-scanner](https://huggingface.co/spaces/siladitya41/indian-candlestick-scanner) | Space | Scans Indian stocks for candlestick patterns |

## Chart patterns and price action

| # | Name | Type | What it is |
|---|---|---|---|
| 11 | [JONNYVERSE/stockmarket-pattern-detection-yolov8-onnx](https://huggingface.co/JONNYVERSE/stockmarket-pattern-detection-yolov8-onnx) | Model | ONNX export of the foduucom chart-pattern YOLO; runs with onnxruntime and no PyTorch, so the `yolo_chart_patterns` switch could use it as a lighter backend |
| 12 | [JavyAI/yolov8-stock-patterns](https://huggingface.co/JavyAI/yolov8-stock-patterns) | Model | YOLOv8 chart-pattern detector |
| 13 | [SyedAbdullahh/stock-chart-pattern-detector](https://huggingface.co/SyedAbdullahh/stock-chart-pattern-detector) | Model | Chart-pattern detector (head and shoulders, double tops/bottoms and similar) |
| 14 | [yasirapunsith/chart-pattern-locator](https://huggingface.co/yasirapunsith/chart-pattern-locator) | Model | Locates chart patterns in price charts |
| 15 | [jadhavmanasi70/chart-pattern-nse](https://huggingface.co/datasets/jadhavmanasi70/chart-pattern-nse) | Dataset | Labelled chart patterns on NSE stocks (the most downloaded pattern dataset in the search) |
| 16 | [StephanAkkerman/stock-charts](https://huggingface.co/datasets/StephanAkkerman/stock-charts) | Dataset | Stock chart images collected from financial Twitter |
| 17 | [diamond-in/trading-chart-patterns](https://huggingface.co/datasets/diamond-in/trading-chart-patterns) | Dataset | Trading chart-pattern examples |
| 18 | [gunahkarcasper/stock-market-chart-patterns-and-volume](https://huggingface.co/datasets/gunahkarcasper/stock-market-chart-patterns-and-volume) | Dataset | Chart patterns paired with volume, relevant to the volume-led tremor signal |
| 19 | [qbtrain/stock-chart-patterns-db](https://huggingface.co/datasets/qbtrain/stock-chart-patterns-db) | Dataset | Database of stock chart patterns |
| 20 | [hercegnovi/llama-3-8b-priceaction4](https://huggingface.co/hercegnovi/llama-3-8b-priceaction4) | Model | Llama 3 8B fine-tuned on price-action descriptions |
| 21 | [incredible45/finetuning-sentiment-model-on-price-action](https://huggingface.co/incredible45/finetuning-sentiment-model-on-price-action) | Model | Text classifier fine-tuned on price-action text |
| 22 | [ZackyZacky/Price_Action_Trading_Bot](https://huggingface.co/spaces/ZackyZacky/Price_Action_Trading_Bot) | Space | Price-action trading-bot demo |

## Bollinger Bands

| # | Name | Type | What it is |
|---|---|---|---|
| 23 | [SpaceGhost/Nexus-V11-Bollinger-Kinematics](https://huggingface.co/SpaceGhost/Nexus-V11-Bollinger-Kinematics) | Model | Model built on Bollinger-band "kinematics" (band velocity/acceleration) |
| 24 | [netflypsb/bollinger_bands](https://huggingface.co/spaces/netflypsb/bollinger_bands) | Space | Bollinger Bands charting and signal app |
| 25 | [Qondl173893/bollinger-bandit-scanner](https://huggingface.co/spaces/Qondl173893/bollinger-bandit-scanner) | Space | Scanner for Bollinger band breakouts and squeezes |
| 26 | [joememas/macd-rsi-bollinger-bands-tracker](https://huggingface.co/spaces/joememas/macd-rsi-bollinger-bands-tracker) | Space | MACD, RSI and Bollinger tracker |

## Fibonacci and Elliott waves

| # | Name | Type | What it is |
|---|---|---|---|
| 27 | [tosin2013/fibonacci_price_target](https://huggingface.co/spaces/tosin2013/fibonacci_price_target) | Space | Fibonacci retracement/extension price targets (the only Fibonacci trading tool on the Hub) |
| 28 | [usamaahmedsh/elliott-wave-market-data-complete](https://huggingface.co/datasets/usamaahmedsh/elliott-wave-market-data-complete) | Dataset | Market data labelled with Elliott-wave structure |
| 29 | [THULab/elliott_wave_market_data](https://huggingface.co/datasets/THULab/elliott_wave_market_data) | Dataset | Elliott-wave market data from a university lab |
| 30 | [usamaahmedsh/synthetic-elliott-waves](https://huggingface.co/datasets/usamaahmedsh/synthetic-elliott-waves) | Dataset | Synthetic Elliott-wave series with known labels, useful for testing a wave or harmonic detector |
| 31 | [usamaahmedsh/elliott-wave-scorer-training](https://huggingface.co/datasets/usamaahmedsh/elliott-wave-scorer-training) | Dataset | Training data for scoring Elliott-wave counts |

## General signals and TA

| # | Name | Type | What it is |
|---|---|---|---|
| 32 | [ewin-reg/Stock-Market-Trading-Signals](https://huggingface.co/datasets/ewin-reg/Stock-Market-Trading-Signals) | Dataset | Stock prices with indicator-based buy/sell signals |
| 33 | [tosin2013/forex-trend-trading-signals](https://huggingface.co/spaces/tosin2013/forex-trend-trading-signals) | Space | Trend-following signal app (forex) |
| 34 | [SudheerMamidela/nifty50-sp500-trading-signals-lstm](https://huggingface.co/SudheerMamidela/nifty50-sp500-trading-signals-lstm) | Model | LSTM trading signals for Nifty 50 and S&P 500 |
| 35 | [Hungry-Socrates/Technical_Analysis_Unsloth_v3](https://huggingface.co/Hungry-Socrates/Technical_Analysis_Unsloth_v3) | Model | LLM fine-tuned to write technical analysis |

**Best next integrations:** #11 (ONNX chart patterns, no torch), #30 (synthetic labelled waves to test the harmonic/zigzag engine), #15 (real labelled chart patterns to benchmark `chart_patterns.py`, like the candlestick benchmark), and #27 (to cross-check Fibonacci targets).
