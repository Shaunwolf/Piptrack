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
