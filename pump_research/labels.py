"""Plain-language names for features and signals shown in the web pages and reports"""

import re

FEATURES = {
    "window_return": "Price change over the window",
    "window_volatility": "Daily volatility",
    "volatility_ratio": "Volatility vs its baseline",
    "avg_volume_ratio": "Average volume vs baseline",
    "max_volume_ratio": "Biggest volume day vs baseline",
    "last3_volume_ratio": "Last-3-day volume vs baseline",
    "volume_trend_slope": "Volume trend (rising > 0)",
    "up_days_share": "Share of up days",
    "avg_range_pct": "Average daily range",
    "gap_ups_5pct": "Gap-ups over 5%",
    "rsi_14": "RSI (14)",
    "close_vs_period_low": "Price vs recent low",
    "last_close": "Share price",
    "avg_dollar_volume": "Dollar volume traded",
    "ta_rsi14": "RSI (14)",
    "ta_rsi_min_in_window": "Lowest RSI in window",
    "ta_stoch_k": "Stochastic %K",
    "ta_stoch_d": "Stochastic %D",
    "ta_macd_hist_pct": "MACD histogram",
    "ta_adx": "Trend strength (ADX)",
    "ta_di_spread": "Buyers vs sellers (+DI − −DI)",
    "ta_atr_pct": "Average true range",
    "ta_bb_pct_b": "Position in Bollinger Bands",
    "ta_bb_bandwidth": "Bollinger bandwidth",
    "ta_obv_slope": "On-balance volume slope",
    "ta_mfi14": "Money flow index",
    "ta_cmf20": "Chaikin money flow",
    "ta_close_vs_vwap20": "Price vs 20-day VWAP",
    "ta_higher_lows": "Higher lows",
    "ta_dist_to_resistance": "Room to resistance",
    "ta_dist_to_support": "Cushion above support",
    "ta_consecutive_up_closes": "Up closes in a row",
    "ta_range_expansion_last": "Last day's range vs ATR",
    "ta_close_vs_period_high": "Price vs 1-year high",
    "ta_fib_retracement": "Fibonacci retracement",
    "ta_fib_nearest_level": "Nearest Fibonacci level",
    "ta_ema21_slope_5d": "EMA 21 slope",
    "ta_ema_ribbon_width": "EMA ribbon width",
    "ta_harmonic_best_score": "Best harmonic fit",
    "ta_harmonic_bullish_in_window": "Bullish harmonics",
    "ta_harmonic_bearish_in_window": "Bearish harmonics",
    "ta_chart_bullish_in_window": "Bullish chart patterns",
    "ta_chart_bearish_in_window": "Bearish chart patterns",
    "ta_candles_bullish": "Bullish candles",
    "ta_candles_bearish": "Bearish candles",
}

FEATURES.update({
    "ta_fib_confluence": "Fibonacci/Gann tools agreeing on price",
    "ta_fib_time_confluence": "Fibonacci time lines on this bar",
    "ta_fib_ext_position": "Position on the trend fib extension",
    "ta_fib_ext_nearest": "Nearest trend fib extension",
    "ta_fib_ext_near": "At a trend fib extension",
    "ta_fib_channel_position": "Position in the fib channel",
    "ta_fib_channel_near": "On a fib channel line",
    "ta_fib_timezone_bars_to_next": "Bars to the next fib time zone",
    "ta_fib_timezone_now": "On a fib time zone",
    "ta_fib_trend_time_bars_to_next": "Bars to the next trend fib time",
    "ta_fib_trend_time_now": "On a trend fib time line",
    "ta_fib_speed_fan_zone": "Fib speed fan lines below price",
    "ta_fib_speed_fan_near": "On a fib speed fan line",
    "ta_fib_circle_ratio": "Fib circle ratio",
    "ta_fib_circle_near": "On a fib circle",
    "ta_fib_spiral_proximity": "Distance from the fib spiral",
    "ta_fib_spiral_near": "On the fib spiral",
    "ta_fib_arc_ratio": "Fib speed arc ratio",
    "ta_fib_arc_near": "On a fib speed arc",
    "ta_fib_wedge_ratio": "Fib wedge ratio",
    "ta_fib_wedge_inside": "Inside the fib wedge",
    "ta_pitchfan_position": "Position vs pitchfan median",
    "ta_pitchfan_above_median": "Above the pitchfan median",
    "ta_gann_box_price_fraction": "Gann box price fraction",
    "ta_gann_box_time_fraction": "Gann box time fraction",
    "ta_gann_box_near_price": "On a Gann box quarter",
    "ta_gann_square_diagonal_gap": "Gap to the Gann square diagonal",
    "ta_gann_square_above_diagonal": "Above the Gann square diagonal",
    "ta_gann_fixed_diagonal_gap": "Gap to the fixed Gann square diagonal",
    "ta_gann_fixed_above_diagonal": "Above the fixed Gann square diagonal",
    "ta_gann_fan_zone": "Gann fan lines below price",
    "ta_gann_above_1x1": "Above the Gann 1×1",
    "ta_gann_fan_near": "On a Gann fan line",
    "ta_kalman_strength": "Kalman trend strength",
    "ta_close_vs_kalman": "Price vs Kalman filter",
    "ta_kalman_uptrend": "Kalman filter trending up",
    "ta_close_cross_up_kalman_in_window": "Price crossed above the Kalman filter",
    "ta_kalman_turned_up_in_window": "Kalman filter turned up",
    "ta_alltime_fib_position": "Position in the all-time range",
    "ta_alltime_fib_nearest": "Nearest all-time fib level",
    "ta_fear_greed": "Fear & Greed (0–100)",
    "ta_sr_buy_signals": "Support/resistance buy signals",
    "ta_sr_sell_signals": "Support/resistance sell signals",
    "ta_ema_bull_stack": "EMA 8/21/50 stacked bullish",
    "ta_ema_bear_stack": "EMA 8/21/50 stacked bearish",
    "ta_wma_bull_stack": "Weighted MAs stacked bullish",
    "ta_ema8_cross_up_ema21_in_window": "EMA 8 crossed above EMA 21",
    "ta_close_cross_up_wma20_in_window": "Price crossed above weighted MA 20",
    "ta_close_cross_up_hma20_in_window": "Price crossed above Hull MA 20",
    "ta_golden_cross_in_window": "Golden cross (SMA 50 over 200)",
    "ta_macd_bull_cross_in_window": "MACD bullish cross",
    "ta_bb_squeeze": "Bollinger squeeze",
    "ta_obv_bullish_divergence": "Volume accumulating while price is flat",
    "ta_rsi_bullish_divergence": "RSI bullish divergence",
    "ta_break_of_structure": "Broke above the last swing high",
    "ta_structure_uptrend": "Higher highs and higher lows",
    "ta_structure_downtrend": "Lower highs and lower lows",
    "ta_fib_upswing": "Pulling back from an upswing",
    "ta_fib_golden_pocket": "In the Fibonacci golden pocket",
})

SIGNALS = {
    "volume_2x_baseline": "Volume running 2× normal",
    "volume_spike_5x_day": "A 5× volume day",
    "volume_rising": "Volume trending up",
    "volatility_1_5x_baseline": "Volatility 1.5× normal",
    "sub_5_dollar_price": "Priced under $5",
    "sub_1_dollar_price": "Priced under $1",
    "oversold_rsi_below_35": "Oversold (RSI under 35)",
    "already_up_20pct": "Already up 20%+",
    "reddit_chatter_accelerating": "Reddit chatter accelerating",
    "offering_filing_in_window": "Share offering filed",
    "any_news_in_window": "In the news",
    "ema_bull_stack": "EMAs stacked bullish",
    "wma_bull_stack": "Weighted MAs stacked bullish",
    "bollinger_squeeze": "Bollinger squeeze",
    "macd_bull_cross": "MACD bullish cross",
    "rsi_bullish_divergence": "RSI bullish divergence",
    "obv_accumulation_divergence": "Quiet accumulation (OBV)",
    "money_flow_positive": "Money flowing in (CMF)",
    "fib_golden_pocket": "Fibonacci golden pocket",
    "bullish_harmonic_completed": "Bullish harmonic completed",
    "bullish_chart_pattern": "Bullish chart pattern",
    "bullish_candles_outnumber_bearish": "More bullish than bearish candles",
    "break_of_structure": "Broke the last swing high",
    "trend_strong_adx_25": "Strong trend (ADX 25+)",
    "fib_confluence_4plus": "4+ Fibonacci/Gann tools agree",
    "fib_time_line_today": "On a Fibonacci time line",
    "near_trend_fib_extension": "At a trend-based fib extension",
    "above_gann_1x1": "Above the Gann 1×1",
    "above_pitchfan_median": "Above the pitchfan median",
    "kalman_uptrend": "Kalman filter trending up",
    "kalman_turned_up": "Kalman filter turned up",
    "sr_buy_signal": "Support/resistance buy signal",
    "sr_sell_signal": "Support/resistance sell signal",
    "extreme_fear": "Extreme fear (under 25)",
    "extreme_greed": "Extreme greed (over 75)",
    "near_all_time_low": "Near the all-time low",
}

MA_NAMES = {"ema": "EMA", "wma": "weighted MA", "hma": "Hull MA", "vwma": "volume-weighted MA", "sma": "SMA"}


def feature_label(name: str) -> str:
    if name in FEATURES:
        return FEATURES[name]
    m = re.match(r"ta_close_vs_(ema|wma|hma|vwma|sma)(\d+)$", name)
    if m:
        kind, n = m.groups()
        return f"Price vs {n}-day {MA_NAMES[kind]}"
    m = re.match(r"ta_pattern_(.+)$", name)
    if m:
        return m.group(1).replace("_", " ").capitalize() + " pattern"
    m = re.match(r"ta_candle_(.+)$", name)
    if m:
        return m.group(1).replace("_", " ").capitalize() + " candles"
    return name.removeprefix("ta_").replace("_", " ").capitalize()


def signal_label(name: str) -> str:
    return SIGNALS.get(name) or name.replace("_", " ").capitalize()
