# Squeeze playbook

How PipSqueak looks for stocks one to two weeks before a short squeeze or a big jump, what each signal
means, where its data comes from, and how the system checks itself. The framework follows the
microstructure research the project started from (GameStop and AMC, January and May–June 2021), with the
corrections noted below.

## The four ingredients

A squeeze needs fuel, a spark, a setup and a real listing. In Scan Lab each one is a group in the
**Squeeze setup** starter scan.

### 1. Fuel: short pressure that can't exit easily

| Signal | Block | Data | Notes |
|---|---|---|---|
| Short % of float, days to cover | Short interest | Yahoo (current), FINRA short interest (history, twice a month) | Days to cover = short interest ÷ average daily volume. Above ~3 days the exit gets crowded. |
| Reg SHO threshold list streak | Reg SHO threshold list | Nasdaq daily threshold file | A stock lands on the list after 5 straight settlement days of fails ≥ 10,000 shares and ≥ 0.5% of shares outstanding. Under **Rule 203(b)(3)**, brokers must close out fails that last **13 consecutive settlement days** (buy shares regardless of price), and are barred from new shorts until they do. Days 8–13 are the window to watch. (Rule 204 is a separate next-day close-out for any fail.) NYSE's list isn't read yet, so coverage is Nasdaq-listed stocks. |
| Short-volume ratio | Short-volume ratio | FINRA daily short volume (Aug 2018+ consolidated; earlier from the Nasdaq and NYSE facility files) | Market makers short to fill buyers off-exchange, so a high, rising ratio is read as hidden buying (the single-stock cousin of SqueezeMetrics' DIX). Noisy on its own: confirmation only. |
| Fails-to-deliver | (research only) | SEC twice-monthly archives | Published about two weeks late, so it can't time entries; the threshold list is the real-time proxy. The SEC currently blocks automated downloads from cloud servers. |

### 2. Spark: attention and options pressure

| Signal | Block | Data | Notes |
|---|---|---|---|
| Mention velocity | Mention velocity | ApeWisdom (Reddit + StockTwits) | Rate of change beats raw sentiment: 50 → 5,000 mentions in two days matters even if the tone is mixed. |
| Dealers short gamma | Dealer gamma | Yahoo option chains | Net gamma exposure (GEX) per 1% move = Σ gamma × open interest × 100 × spot² × 0.01, calls positive, puts negative (dealers assumed long customer-sold calls, short customer-bought puts). Below zero, dealer hedging chases the trend. These are estimates; real dealer books aren't public. |
| Gamma flip, call wall | Dealer gamma | Same | The flip is where net GEX crosses zero. The call wall (largest call gamma strike) acts as resistance; a close above it can force the most violent hedging. |
| Hot short-dated calls | Dealer gamma | Same | Volume ÷ open interest on near-the-money calls expiring within three weeks: the free proxy for urgent call sweeps. Real sweep vs block tagging needs a paid flow feed. |
| Quiet, then waking volume | Quiet, then waking | Prices | The clearest tell in our own pump data: volume below normal for weeks, then ~2.3× normal about four days before the move. |

### 3. Setup: timing the entry

| Signal | Block | Notes |
|---|---|---|
| Volatility contraction pattern | VCP | Each pullback shallower than the last (e.g. 20% → 11% → 5%) on drying volume, in a Stage 2 uptrend (above a rising 200-day EMA). Entry is a close through the pivot (the last contraction's high) on ≥ 1.5× volume. |
| EMA coil | EMA coil | The 10- and 21-day EMAs squeezed within ~1.5% of each other, both above the 50: a coiled spring. |
| Harmonic reversal zone | Harmonic pattern (forming) | For stocks beaten down into a reversal: the projected D-point zone where XA and BC Fibonacci projections cluster (Gartley 78.6%, Bat 88.6%, Butterfly 127.2% of XA, and more). Stops go just beyond the zone. |
| Breakout | Price breakout | Close above the 20/50-bar high on volume. |

### 4. Real listing: not a pump-and-dump

The **Pump-and-dump filter** block fails stocks with the classic red flags: OTC listing, no listed
options (so no gamma mechanics), sub-$1 price, tiny market cap or thin dollar volume. Other red flags
need a human eye: no verifiable catalyst in SEC filings, paid or undisclosed promotion, and "act now" urgency.

## What the history says (and what we're still testing)

From the 20 historic pumps with full build-up data (see `pump_data/pump_report.md`):

- Volume is below normal until about day −4, then jumps to ~2.3× normal.
- A break of structure appeared before 40% of pumps vs 3% of ordinary windows; a MACD bullish cross
  70% vs 32%; EMA 8/21/50 stacked bullish 58% vs 30%.
- Bollinger squeezes, divergences, harmonics and most Fibonacci/Gann levels showed no edge on these events.

The squeeze features (`sq_*`: short-volume ratio, threshold-list streak, days to cover) are collected for
the same pre-pump and ordinary windows, so the report shows whether they actually rose before these
pumps. Many of these events were low-float IPO pumps rather than short squeezes, so options and short-interest
signals may only matter for the squeeze-type events (GME, AMC, KOSS, EXPR, BB).

## How the system keeps learning

1. **Daily radar** (`.github/workflows/radar.yml`, after each US close): runs Squeeze setup, Pump DNA and
   Momentum breakout over their universes (including today's threshold list and Reddit's fastest-rising
   tickers), and stores every pick and everything scanned on the `radar` branch.
2. **Grading**: once a pick is 10 trading days old, its largest gain within 5 and 10 days is compared
   with the same measure for everything that scan looked at that day (the base rate). The report shows
   hit rates at +20%, +50% and +100%, the lift over the base rate, and which blocks fired on the picks
   that ran.
3. **Scan Lab → Daily radar** shows the latest picks and each scan's track record.

Run it by hand: `python -m pump_research radar run --dir radar`, then `python -m pump_research radar grade --dir radar`.

## Daily workflow for a person

1. Open **Daily radar** for the latest picks and each scan's track record.
2. In Scan Lab, load **Squeeze setup** (or add the Reg SHO and Trending lists to your own scan) and run it.
3. For each match, open the chart analysis: check the VCP pivot or harmonic zone, and the SEC filings for a real catalyst.
4. Save the scan with alerts on, so new matches arrive after each close.

Nothing here is investment advice; these are probabilities measured on a small sample.
