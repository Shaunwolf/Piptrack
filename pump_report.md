# Pump Research Report
Criterion: **broad** (intraday high ≥ 5x the previous close, or a run of up to 5 days reaching 5x). Pre-pump window: 10 trading days; baseline: the 60 trading days before that.

- Candidates researched: **26**
- Pump located in price data: **26**
- Clear the criterion: **17**
- Events with a usable pre-pump window: **22**, compared with **76** ordinary windows from the same stocks

## Data coverage
| Source | error | needs_key | no_data | ok | partial | skipped |
|---|---|---|---|---|---|---|
| gdelt_news | 0 | 0 | 0 | 0 | 0 | 26 |
| hf_ohlcv_1m | 0 | 0 | 0 | 8 | 0 | 0 |
| polygon_news | 0 | 24 | 0 | 0 | 0 | 2 |
| reddit | 24 | 0 | 0 | 0 | 0 | 2 |
| reddit_arctic_shift | 1 | 0 | 0 | 0 | 23 | 2 |
| sec_filings | 24 | 0 | 0 | 0 | 0 | 2 |
| yahoo_prices | 0 | 0 | 8 | 18 | 0 | 0 |

## Events
| Ticker | Pump date | Category | Type | Close | High | Run | Qualifies | Window return | Volume vs base | Filings | Reddit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| PHUN | 2021-10-21 | extreme | multi_day_run | 5.7x | 15.7x | 8.6x | yes | +18% | 1.2x | ? | ≥? |
| TOP | 2023-04-27 | extreme | multi_day_run | 5.4x | 12.8x | 17.3x | yes | +48% | 4.5x | ? | ≥? |
| MEGL | 2022-08-05 | extreme | ipo_debut | 24.0x | 58.4x | 29.0x | yes | – | – | ? | ? |
| ATXG | 2022-08-31 | extreme | single_day | 87.5x | 87.5x | 87.5x | yes | +0% | – | ? | ≥? |
| LFIN | 2017-12-15 | extreme | multi_day_run | 3.3x | 6.5x | 14.5x | yes | – | – | ? | ? |
| AMAM | 2022-12-09 | extreme | single_day | 11.1x | 11.1x | 11.1x | yes | -17% | 18.1x | ? | ≥? |
| NMAX | 2025-03-31 | extreme | ipo_debut | 8.4x | 8.4x | 23.3x | yes | – | – | ? | ? |
| QMMM | 2025-09-08 | extreme | multi_day_run | 22.4x | 26.6x | 38.9x | yes | +105% | 0.5x | ? | ≥? |
| HKD | 2022-07-22 | extreme | multi_day_run | 3.3x | 3.5x | 29.8x | yes | – | – | ? | ≥? |
| KODK | 2020-07-27 | extreme | multi_day_run | 4.2x | 7.6x | 15.8x | yes | +0% | 0.4x | ? | ≥? |
| KOSS | 2021-01-25 | extreme | multi_day_run | 5.8x | 7.0x | 19.2x | yes | +6% | 0.6x | ? | ≥? |
| HOLO | 2024-02-07 | extreme | single_day | 11.9x | 12.3x | 19.0x | yes | -29% | 0.5x | ? | ≥1 |
| NUKK | 2024-12-17 | extreme | single_day | 8.6x | 13.0x | 37.8x | yes | -18% | 0.1x | ? | ≥? |
| GME | 2021-01-26 | famous_squeeze | multi_day_run | 2.3x | 2.6x | 8.9x | yes | +334% | 8.5x | ? | ≥28 |
| AMC | 2021-01-21 | famous_squeeze | multi_day_run | 4.0x | 4.1x | 6.7x | yes | +50% | 3.8x | ? | ≥9 |
| AMC | 2021-06-01 | famous_squeeze | multi_day_run | 2.0x | 2.3x | 3.8x | no | +101% | 2.8x | ? | ≥377 |
| DWAC | 2021-10-21 | famous_squeeze | single_day | 4.6x | 5.2x | 9.5x | yes | +0% | 1.5x | ? | ≥? |
| BB | 2021-01-21 | famous_squeeze | multi_day_run | 1.3x | 1.5x | 2.0x | no | +89% | 3.1x | ? | ≥3 |
| BBBY | 2021-01-21 | famous_squeeze | multi_day_run | 1.0x | 1.6x | 2.1x | no | +26% | 2.2x | ? | ≥67 |
| EXPR | 2021-01-21 | famous_squeeze | multi_day_run | 3.2x | 4.6x | 8.3x | yes | +20% | 1.2x | ? | ≥6 |
| NOK | 2021-01-21 | famous_squeeze | multi_day_run | 1.4x | 2.1x | 1.6x | no | +4% | 1.3x | ? | ≥4 |
| SPCE | 2021-01-26 | famous_squeeze | multi_day_run | 1.1x | 1.4x | 1.5x | no | +43% | 1.4x | ? | ≥7 |
| CLOV | 2021-06-07 | famous_squeeze | multi_day_run | 1.9x | 2.1x | 2.9x | no | +26% | 0.8x | ? | ≥22 |
| MMAT | 2021-07-06 | famous_squeeze | multi_day_run | 1.1x | 1.2x | 1.1x | no | – | – | ? | ≥1 |
| IRNT | 2021-09-03 | famous_squeeze | multi_day_run | 1.2x | 1.8x | 2.4x | no | – | – | ? | ≥3 |
| SPRT | 2021-08-26 | famous_squeeze | multi_day_run | 1.3x | 3.0x | 3.3x | no | +95% | 7.7x | ? | ≥6 |

## What separates pre-pump windows from ordinary ones
`P(event higher)` is the chance a random pre-pump window scores higher than a random ordinary window for the same stocks: 0.5 means no difference, near 1 or 0 means a strong tell. Small samples: treat p-values as rough.

| Feature | Pre-pump median | Ordinary median | P(event higher) | p-value | n (events/ordinary) |
|---|---|---|---|---|---|
| ta_macd_hist_pct | 0.0279 | 0.00434 | 0.80 | 0.000 | 19/76 |
| volume_trend_slope | 0.133 | -0.0242 | 0.76 | 0.000 | 20/76 |
| ta_close_vs_wma20 | 0.124 | -0.0254 | 0.75 | 0.001 | 19/76 |
| ta_bb_pct_b | 0.955 | 0.424 | 0.75 | 0.001 | 18/72 |
| ta_kalman_strength | 36.5 | 0 | 0.75 | 0.001 | 20/76 |
| ta_close_vs_vwma20 | 0.152 | -0.0377 | 0.75 | 0.001 | 18/72 |
| ta_close_vs_ema21 | 0.126 | -0.0243 | 0.74 | 0.001 | 19/76 |
| ta_di_spread | 17.6 | 3.51 | 0.74 | 0.001 | 19/72 |
| ta_stoch_d | 73.4 | 39.5 | 0.74 | 0.002 | 18/72 |
| ta_close_vs_wma10 | 0.0453 | -0.0141 | 0.73 | 0.001 | 20/76 |
| ta_gann_box_price_fraction | -0.119 | 0.345 | 0.27 | 0.002 | 19/72 |
| window_return | 0.231 | 0 | 0.73 | 0.001 | 20/76 |
| ta_close_vs_ema8 | 0.0543 | -0.00916 | 0.73 | 0.002 | 20/76 |
| ta_ema21_slope_5d | 0.0549 | -0.00299 | 0.73 | 0.002 | 19/76 |
| ta_close_vs_vwap20 | 0.148 | -0.0484 | 0.72 | 0.003 | 18/72 |
| last3_volume_ratio | 1.4 | 0.753 | 0.72 | 0.003 | 19/72 |
| ta_close_vs_wma50 | 0.111 | -0.0308 | 0.71 | 0.004 | 19/76 |
| ta_close_vs_ema50 | 0.0977 | -0.0338 | 0.71 | 0.005 | 19/76 |
| ta_higher_lows | 7 | 4 | 0.70 | 0.006 | 20/76 |
| ta_fear_greed | 60.5 | 43.7 | 0.70 | 0.008 | 19/76 |
| rsi_14 | 63 | 47.7 | 0.69 | 0.010 | 20/76 |
| ta_rsi14 | 63 | 47.7 | 0.69 | 0.010 | 20/76 |
| ta_close_vs_sma50 | 0.108 | -0.0181 | 0.68 | 0.014 | 19/76 |
| ta_close_vs_hma20 | 0.0292 | -0.0121 | 0.68 | 0.014 | 19/76 |
| ta_dist_to_support | 0.248 | 0.123 | 0.68 | 0.043 | 14/45 |
| ta_fib_confluence | 1 | 1 | 0.32 | 0.013 | 19/72 |
| up_days_share | 0.556 | 0.444 | 0.68 | 0.013 | 20/76 |
| ta_range_expansion_last | 0.87 | 0.814 | 0.67 | 0.028 | 19/72 |
| ta_stoch_k | 63 | 35.5 | 0.65 | 0.042 | 19/72 |
| max_volume_ratio | 4.99 | 1.88 | 0.65 | 0.045 | 19/72 |
| ta_candle_inside_bar | 1 | 2 | 0.35 | 0.034 | 20/76 |
| ta_obv_slope | 0.328 | 0.0598 | 0.65 | 0.046 | 19/72 |
| volatility_ratio | 1.16 | 0.796 | 0.64 | 0.058 | 19/72 |
| ta_mfi14 | 65.2 | 58.2 | 0.64 | 0.067 | 19/72 |
| gap_ups_5pct | 1 | 0 | 0.63 | 0.053 | 20/76 |
| ta_gann_square_diagonal_gap | -3.35 | -2.38 | 0.37 | 0.090 | 19/72 |
| avg_volume_ratio | 1.39 | 0.986 | 0.63 | 0.090 | 19/72 |
| ta_close_vs_kalman | 0.00657 | -0.00208 | 0.62 | 0.087 | 20/76 |
| ta_bb_bandwidth | 0.527 | 0.371 | 0.61 | 0.124 | 19/76 |
| ta_fib_arc_ratio | 1.84 | 1.22 | 0.61 | 0.126 | 19/72 |
| ta_fib_circle_ratio | 3.77 | 2.65 | 0.61 | 0.142 | 19/72 |
| ta_fib_channel_position | 0.949 | 1 | 0.39 | 0.142 | 19/72 |
| ta_fib_wedge_ratio | 2.14 | 1.68 | 0.61 | 0.153 | 19/72 |
| ta_sr_sell_signals | 0 | 0 | 0.39 | 0.105 | 20/76 |
| ta_fib_ext_position | 0.192 | 0.135 | 0.60 | 0.164 | 19/72 |
| ta_gann_fixed_diagonal_gap | -4.66 | -4.01 | 0.40 | 0.192 | 19/72 |
| ta_chart_bearish_in_window | 0 | 0 | 0.40 | 0.102 | 20/76 |
| avg_dollar_volume | 9.19e+06 | 6.62e+06 | 0.59 | 0.199 | 20/76 |
| ta_chart_bullish_in_window | 1 | 1 | 0.59 | 0.175 | 20/76 |
| avg_range_pct | 0.0972 | 0.0806 | 0.59 | 0.205 | 20/76 |
| close_vs_period_low | 1.45 | 1.24 | 0.59 | 0.211 | 20/76 |
| window_volatility | 0.0741 | 0.0481 | 0.59 | 0.218 | 20/76 |
| ta_alltime_fib_nearest | 0.236 | 0.236 | 0.59 | 0.222 | 19/72 |
| ta_candles_bearish | 2.5 | 4 | 0.41 | 0.222 | 20/76 |
| ta_gann_fan_zone | 0 | 0 | 0.41 | 0.207 | 19/72 |
| ta_fib_ext_nearest | 0.236 | 0.236 | 0.58 | 0.248 | 19/72 |
| ta_pitchfan_position | 0.255 | -0.168 | 0.58 | 0.289 | 19/72 |
| ta_fib_spiral_proximity | 0.285 | 0.239 | 0.58 | 0.308 | 19/72 |
| ta_candles_bullish | 4 | 3 | 0.57 | 0.341 | 20/76 |
| ta_candle_hammer | 0 | 0 | 0.44 | 0.274 | 20/76 |
| ta_gann_box_time_fraction | 2.67 | 2.32 | 0.56 | 0.449 | 19/72 |
| ta_fib_trend_time_bars_to_next | 2 | 1 | 0.56 | 0.452 | 18/69 |
| ta_close_vs_sma200 | 0 | 0.0117 | 0.55 | 0.584 | 19/18 |
| ta_close_vs_ema200 | 0 | 0.00463 | 0.55 | 0.605 | 19/18 |
| ta_alltime_fib_position | 0.241 | 0.232 | 0.55 | 0.504 | 19/72 |
| last_close | 13.4 | 8.43 | 0.55 | 0.531 | 20/76 |
| ta_candle_morning_star | 0 | 0 | 0.54 | 0.050 | 20/76 |
| ta_consecutive_up_closes | 0 | 0.5 | 0.54 | 0.552 | 20/76 |
| ta_harmonic_bullish_in_window | 0 | 0 | 0.46 | 0.200 | 20/76 |
| ta_rsi_min_in_window | 46 | 43.2 | 0.54 | 0.610 | 20/76 |
| ta_fib_retracement | 0.16 | 0.179 | 0.46 | 0.622 | 19/72 |
| ta_fib_timezone_bars_to_next | 5 | 4 | 0.54 | 0.641 | 19/72 |
| ta_ema_ribbon_width | 0.155 | 0.134 | 0.53 | 0.652 | 19/76 |
| ta_fib_speed_fan_zone | 0 | 0 | 0.47 | 0.597 | 19/72 |
| ta_cmf20 | -0.101 | -0.0557 | 0.47 | 0.690 | 18/72 |
| ta_harmonic_bearish_in_window | 0 | 0 | 0.47 | 0.458 | 20/76 |
| ta_fib_nearest_level | 0.236 | 0.236 | 0.47 | 0.709 | 19/72 |
| ta_candle_doji | 0 | 0 | 0.53 | 0.686 | 20/76 |
| ta_atr_pct | 0.109 | 0.0949 | 0.53 | 0.735 | 20/76 |
| ta_candle_gap_up | 0 | 0 | 0.53 | 0.684 | 20/76 |
| ta_candle_shooting_star | 0 | 0 | 0.52 | 0.432 | 20/76 |
| ta_sr_buy_signals | 0 | 0 | 0.48 | 0.717 | 20/76 |
| ta_close_vs_period_high | -0.455 | -0.511 | 0.52 | 0.776 | 20/76 |
| ta_adx | 23.3 | 24.6 | 0.48 | 0.836 | 18/72 |
| ta_candle_bullish_engulfing | 0 | 0 | 0.49 | 0.836 | 20/76 |
| ta_dist_to_resistance | 0.106 | 0.11 | 0.49 | 0.927 | 11/51 |
| ta_fib_time_confluence | 0 | 0 | 0.49 | 0.938 | 19/72 |

## Yes/no technical signals: before pumps vs ordinary windows
| Signal | Before pumps | Ordinary | Lift | p-value |
|---|---|---|---|---|
| ta_macd_bull_cross_in_window | 70% | 32% | 2.2x | 0.004 |
| ta_break_of_structure | 40% | 3% | 15.2x | 0.000 |
| ta_kalman_uptrend | 75% | 46% | 1.6x | 0.025 |
| ta_ema_bull_stack | 58% | 30% | 1.9x | 0.033 |
| ta_kalman_turned_up_in_window | 65% | 41% | 1.6x | 0.077 |
| ta_ema8_cross_up_ema21_in_window | 40% | 17% | 2.3x | 0.037 |
| ta_wma_bull_stack | 53% | 32% | 1.7x | 0.111 |
| ta_pattern_range_breakout | 40% | 20% | 2.0x | 0.078 |
| ta_gann_box_near_price | 0% | 15% | 0.0x | 0.111 |
| ta_close_cross_up_hma20_in_window | 55% | 70% | 0.8x | 0.286 |
| ta_pattern_rising_wedge | 0% | 14% | 0.0x | 0.113 |
| ta_pattern_consolidation | 55% | 41% | 1.3x | 0.314 |
| ta_structure_downtrend | 35% | 21% | 1.7x | 0.240 |
| ta_pitchfan_above_median | 58% | 44% | 1.3x | 0.315 |
| ta_ema_bear_stack | 26% | 39% | 0.7x | 0.426 |
| ta_bb_squeeze | 20% | 30% | 0.7x | 0.418 |
| ta_pattern_bull_flag | 30% | 20% | 1.5x | 0.366 |
| ta_fib_ext_near | 5% | 15% | 0.3x | 0.448 |
| ta_obv_bullish_divergence | 0% | 9% | 0.0x | 0.339 |
| ta_close_cross_up_wma20_in_window | 55% | 46% | 1.2x | 0.616 |
| ta_fib_upswing | 53% | 44% | 1.2x | 0.609 |
| ta_rsi_bullish_divergence | 5% | 13% | 0.4x | 0.449 |
| ta_close_cross_up_kalman_in_window | 70% | 78% | 0.9x | 0.558 |
| ta_fib_channel_near | 11% | 18% | 0.6x | 0.729 |
| ta_fib_trend_time_now | 11% | 18% | 0.6x | 0.729 |

## Warning signs present before the pump
| Signal | Share of events | Events with data |
|---|---|---|
| kalman_uptrend | 75% | 20 |
| macd_bull_cross | 70% | 20 |
| volume_rising | 65% | 20 |
| bullish_chart_pattern | 65% | 20 |
| kalman_turned_up | 65% | 20 |
| bullish_candles_outnumber_bearish | 60% | 20 |
| ema_bull_stack | 58% | 19 |
| above_pitchfan_median | 58% | 19 |
| wma_bull_stack | 53% | 19 |
| already_up_20pct | 50% | 20 |
| volume_spike_5x_day | 47% | 19 |
| fib_time_line_today | 47% | 19 |
| reddit_chatter_accelerating | 46% | 13 |
| sr_buy_signal | 45% | 20 |
| trend_strong_adx_25 | 44% | 18 |
| volume_2x_baseline | 42% | 19 |
| break_of_structure | 40% | 20 |
| volatility_1_5x_baseline | 32% | 19 |
| sub_5_dollar_price | 30% | 20 |
| sr_sell_signal | 30% | 20 |
| money_flow_positive | 28% | 18 |
| near_all_time_low | 26% | 19 |
| bollinger_squeeze | 20% | 20 |
| extreme_greed | 11% | 19 |
| oversold_rsi_below_35 | 10% | 20 |
| fib_confluence_4plus | 5% | 19 |
| near_trend_fib_extension | 5% | 19 |
| extreme_fear | 5% | 19 |
| sub_1_dollar_price | 5% | 20 |
| rsi_bullish_divergence | 5% | 20 |
| offering_filing_in_window | – | 0 |
| any_news_in_window | – | 0 |
| obv_accumulation_divergence | 0% | 20 |
| fib_golden_pocket | 0% | 19 |
| bullish_harmonic_completed | 0% | 20 |
| above_gann_1x1 | 0% | 19 |

## Countdown: median day-by-day behavior before the pump
| Day | Events | Median return | Median volume vs baseline |
|---|---|---|---|
| -10 | 20 | +0% | 0.6x |
| -9 | 20 | +1% | 0.7x |
| -8 | 20 | +1% | 0.9x |
| -7 | 20 | +3% | 0.8x |
| -6 | 20 | -0% | 0.8x |
| -5 | 20 | +0% | 0.6x |
| -4 | 20 | +2% | 2.3x |
| -3 | 20 | +0% | 1.5x |
| -2 | 20 | +1% | 1.3x |
| -1 | 20 | -0% | 2.1x |

## Event dossiers

### PHUN — 2021-10-21
*Reported:* +471% close, +1099% intraday (DWAC/Trump SPAC sympathy) ([source](https://www.fool.com/investing/2021/10/22/why-digital-world-acquisition-and-phunware-soared/))
*Measured:* multi day run starting 2021-10-21; biggest day on 2021-10-22: close 5.7x, intraday high 15.7x from $76.50; best 4-day run 8.6x. Qualifies: **yes**
*Pre-pump window (10 days):* return +18%, avg volume 1.2x baseline (max day 2.5x), volatility 0.9x baseline, RSI 63, last close $52.50

| Day | Date | Close | Return | Volume vs baseline |
|---|---|---|---|---|
| -10 | 2021-10-07 | 44.25 | -1% | 0.5x |
| -9 | 2021-10-08 | 45.10 | +2% | 0.4x |
| -8 | 2021-10-11 | 45.50 | +1% | 1.2x |
| -7 | 2021-10-12 | 46.50 | +2% | 0.8x |
| -6 | 2021-10-13 | 46.60 | +0% | 1.0x |
| -5 | 2021-10-14 | 46.40 | -0% | 0.5x |
| -4 | 2021-10-15 | 51.50 | +11% | 2.5x |
| -3 | 2021-10-18 | 51.00 | -1% | 1.1x |
| -2 | 2021-10-19 | 51.00 | +0% | 2.0x |
| -1 | 2021-10-20 | 52.50 | +3% | 2.1x |

**Technical picture at the end of the window**
- Moving averages: EMA 8/21/50 stack mixed; close vs EMA21 +8%, vs WMA20 +10%, vs HMA20 +6%, vs VWMA20 +8%, vs SMA200 -26%
- Momentum: RSI 63, stochastic %K 83, MACD cross in window: yes, ADX 16, RSI bullish divergence: no
- Volatility & flow: Bollinger %B 0.95, squeeze: no, ATR 6% of price, CMF 0.04, MFI 79, OBV accumulation divergence: no
- Fibonacci: downswing $41.00 → $80.00; close at 0.295 bounce (nearest 0.236); pump peaked at the 29.77 extension
- Structure: range (15 higher highs, 14 higher lows); support $51.90, resistance $60.10
- Harmonic patterns: none
- Chart patterns: consolidation (neutral, 2021-10-14)
- Candlesticks: spinning top (neutral, 2021-10-07), tweezer bottom (bullish, 2021-10-08), gravestone doji (bearish, 2021-10-11), spinning top (neutral, 2021-10-11), outside bar (neutral, 2021-10-12), three white soldiers (bullish, 2021-10-12), spinning top (neutral, 2021-10-13), spinning top (neutral, 2021-10-14), spinning top (neutral, 2021-10-18), bearish harami (bearish, 2021-10-18), spinning top (neutral, 2021-10-19), bullish engulfing (bullish, 2021-10-20)
- Support/resistance signals: resistance reject sell (bearish, 2021-10-07), support bounce buy (bullish, 2021-10-08), resistance reject sell (bearish, 2021-10-13), breakout buy (bullish, 2021-10-15), resistance reject sell (bearish, 2021-10-18), resistance reject sell (bearish, 2021-10-19), breakout buy (bullish, 2021-10-20)

*Gaps:* sec_filings: error, polygon_news: needs key, gdelt_news: n/a, reddit: error, reddit_arctic_shift: partial (capped)

### TOP — 2023-04-27
*Reported:* +600% to +1100% in one session, no news ([source](https://www.fool.com/investing/2023/04/28/top-financial-group-has-blasted-more-than-600-high/))
*Notes:* Ticker is an English word: social search uses cashtag only
*Measured:* multi day run starting 2023-04-27; biggest day on 2023-04-28: close 5.4x, intraday high 12.8x from $100.00; best 5-day run 17.3x. Qualifies: **yes**
*Pre-pump window (10 days):* return +48%, avg volume 4.5x baseline (max day 7.3x), volatility 1.0x baseline, RSI 63, last close $33.60

| Day | Date | Close | Return | Volume vs baseline |
|---|---|---|---|---|
| -10 | 2023-04-13 | 25.05 | +11% | 4.4x |
| -9 | 2023-04-14 | 25.75 | +3% | 4.9x |
| -8 | 2023-04-17 | 28.45 | +10% | 4.1x |
| -7 | 2023-04-18 | 29.85 | +5% | 4.0x |
| -6 | 2023-04-19 | 31.20 | +5% | 6.6x |
| -5 | 2023-04-20 | 32.10 | +3% | 1.4x |
| -4 | 2023-04-21 | 31.30 | -2% | 4.2x |
| -3 | 2023-04-24 | 35.20 | +12% | 3.8x |
| -2 | 2023-04-25 | 33.55 | -5% | 7.3x |
| -1 | 2023-04-26 | 33.60 | +0% | 4.4x |

**Technical picture at the end of the window**
- Moving averages: EMA 8/21/50 stack bullish; close vs EMA21 +14%, vs WMA20 +12%, vs HMA20 +1%, vs VWMA20 +16%, vs SMA200 -19%
- Momentum: RSI 63, stochastic %K 87, MACD cross in window: yes, ADX 34, RSI bullish divergence: no
- Volatility & flow: Bollinger %B 0.83, squeeze: no, ATR 11% of price, CMF 0.10, MFI 52, OBV accumulation divergence: no
- Fibonacci: upswing $17.50 → $36.00; close at 0.130 retracement (nearest 0.236); pump peaked at the 68.36 extension
- Structure: uptrend (3 higher highs, 5 higher lows); support $17.75, resistance $35.50
- Harmonic patterns: none
- Chart patterns: double top (bearish, 2023-04-24)
- Candlesticks: bullish engulfing (bullish, 2023-04-13), inside bar (neutral, 2023-04-13), bullish belt hold (bullish, 2023-04-13), three outside up (bullish, 2023-04-14), three white soldiers (bullish, 2023-04-17), inside bar (neutral, 2023-04-18), three white soldiers (bullish, 2023-04-18), outside bar (neutral, 2023-04-19), spinning top (neutral, 2023-04-19), three white soldiers (bullish, 2023-04-19), inside bar (neutral, 2023-04-20), three white soldiers (bullish, 2023-04-20), bearish harami (bearish, 2023-04-21), tweezer top (bearish, 2023-04-21), bullish engulfing (bullish, 2023-04-24), dragonfly doji (bullish, 2023-04-25), inside bar (neutral, 2023-04-25), bearish harami (bearish, 2023-04-25), dragonfly doji (bullish, 2023-04-26), inside bar (neutral, 2023-04-26)
- Support/resistance signals: none

*Gaps:* sec_filings: error, polygon_news: needs key, gdelt_news: n/a, reddit: error, reddit_arctic_shift: partial (capped)

### MEGL — 2022-08-05
*Reported:* +2000% on IPO debut vs $4 IPO price ([source](https://investorplace.com/2022/08/why-is-magic-empire-global-megl-stock-up-2000-today/))
*Notes:* IPO debut: no pre-pump trading history
*Measured:* ipo debut starting 2022-08-05; biggest day: close 24.0x, intraday high 58.4x from $4.00; best 2-day run 29.0x. Qualifies: **yes**

*Gaps:* sec_filings: n/a, polygon_news: n/a, gdelt_news: n/a, reddit: n/a, reddit_arctic_shift: n/a

### ATXG — 2022-08-31
*Reported:* ~+2000% on first days of trading vs $5 IPO price ([source](https://investorplace.com/2022/09/what-is-going-on-with-addentax-atxg-stock-today/))
*Notes:* IPO debut; exact first trading date unverified
*Measured:* single day starting 2022-08-31; biggest day: close 87.5x, intraday high 87.5x from $1125.00; best 5-day run 87.5x. Qualifies: **yes**
*Pre-pump window (10 days):* return +0%, avg volume – baseline (max day –), volatility – baseline, RSI 100, last close $1125.00

| Day | Date | Close | Return | Volume vs baseline |
|---|---|---|---|---|
| -10 | 2022-08-17 | 1125.00 | +0% | – |
| -9 | 2022-08-18 | 1125.00 | +0% | – |
| -8 | 2022-08-19 | 1125.00 | +0% | – |
| -7 | 2022-08-22 | 1125.00 | +0% | – |
| -6 | 2022-08-23 | 1125.00 | +0% | – |
| -5 | 2022-08-24 | 1125.00 | +0% | – |
| -4 | 2022-08-25 | 1125.00 | +0% | – |
| -3 | 2022-08-26 | 1125.00 | +0% | – |
| -2 | 2022-08-29 | 1125.00 | +0% | – |
| -1 | 2022-08-30 | 1125.00 | +0% | – |

**Technical picture at the end of the window**
- Moving averages: EMA 8/21/50 stack mixed; close vs EMA21 +0%, vs WMA20 +0%, vs HMA20 +0%, vs VWMA20 –, vs SMA200 +0%
- Momentum: RSI 100, stochastic %K –, MACD cross in window: no, ADX –, RSI bullish divergence: no
- Volatility & flow: Bollinger %B –, squeeze: yes, ATR 0% of price, CMF –, MFI –, OBV accumulation divergence: no
- Structure: range (0 higher highs, 0 higher lows); support –, resistance –
- Harmonic patterns: none
- Chart patterns: consolidation (neutral, 2022-08-30)
- Candlesticks: none
- Support/resistance signals: none

*Gaps:* sec_filings: error, polygon_news: needs key, gdelt_news: n/a, reddit: error, reddit_arctic_shift: partial (capped)

### LFIN — 2017-12-15
*Reported:* up to +2,400% from float price after Ziddu blockchain deal ([source](https://www.cnbc.com/2017/12/18/small-cap-longfin-soars-2000-percent-after-acquiring-blockchain-company.html))
*Notes:* Delisted 2019; needs a provider with delisted history
*Measured:* multi day run starting 2017-12-15; biggest day on 2017-12-18: close 3.3x, intraday high 6.5x from $22.01; best 4-day run 14.5x. Qualifies: **yes**

*Gaps:* sec_filings: error, polygon_news: needs key, gdelt_news: n/a, reddit: error, reddit_arctic_shift: error

### AMAM — 2022-12-09
*Reported:* ~+1000% in one session after ARX788 trial data ([source](https://www.nasdaq.com/articles/meet-the-biotech-stock-that-jumped-over-1000-in-one-day))
*Notes:* Legitimate catalyst (clinical data) - useful contrast to manipulation; acquired 2024; date approximate
*Measured:* single day starting 2022-12-09; biggest day: close 11.1x, intraday high 11.1x from $0.41; best 1-day run 11.1x. Qualifies: **yes**
*Pre-pump window (10 days):* return -17%, avg volume 18.1x baseline (max day 58.4x), volatility 1.3x baseline, RSI 22, last close $0.41

| Day | Date | Close | Return | Volume vs baseline |
|---|---|---|---|---|
| -10 | 2022-11-25 | 0.49 | -1% | 1.1x |
| -9 | 2022-11-28 | 0.48 | -2% | 2.5x |
| -8 | 2022-11-29 | 0.46 | -3% | 3.8x |
| -7 | 2022-11-30 | 0.49 | +6% | 1.4x |
| -6 | 2022-12-01 | 0.48 | -2% | 5.5x |
| -5 | 2022-12-02 | 0.48 | +0% | 5.9x |
| -4 | 2022-12-05 | 0.52 | +8% | 30.4x |
| -3 | 2022-12-06 | 0.50 | -4% | 58.4x |
| -2 | 2022-12-07 | 0.47 | -6% | 39.5x |
| -1 | 2022-12-08 | 0.41 | -13% | 32.4x |

**Technical picture at the end of the window**
- Moving averages: EMA 8/21/50 stack bearish; close vs EMA21 -28%, vs WMA20 -17%, vs HMA20 -11%, vs VWMA20 -15%, vs SMA200 -84%
- Momentum: RSI 22, stochastic %K 15, MACD cross in window: yes, ADX 16, RSI bullish divergence: yes
- Volatility & flow: Bollinger %B 0.15, squeeze: no, ATR 17% of price, CMF -0.65, MFI 21, OBV accumulation divergence: no
- Fibonacci: downswing $0.38 → $3.50; close at 0.010 bounce (nearest 0); pump peaked at the 1.33 extension
- Structure: downtrend (2 higher highs, 2 higher lows); support –, resistance $1.48
- Harmonic patterns: none
- Chart patterns: falling wedge (bullish, 2022-12-08), range breakdown (bearish, 2022-11-28), range breakdown (bearish, 2022-11-29), range breakdown (bearish, 2022-12-08)
- Candlesticks: bearish marubozu (bearish, 2022-11-25), three black crows (bearish, 2022-11-25), three black crows (bearish, 2022-11-28), three black crows (bearish, 2022-11-29), piercing line (bullish, 2022-11-30), tweezer bottom (bullish, 2022-11-30), bullish belt hold (bullish, 2022-11-30), inside bar (neutral, 2022-12-02), spinning top (neutral, 2022-12-05), bearish marubozu (bearish, 2022-12-06), bearish engulfing (bearish, 2022-12-06), bearish belt hold (bearish, 2022-12-06), bearish marubozu (bearish, 2022-12-07), bearish belt hold (bearish, 2022-12-07), three outside down (bearish, 2022-12-07), three black crows (bearish, 2022-12-08)
- Support/resistance signals: none

*Gaps:* yahoo_prices: none found, sec_filings: error, polygon_news: needs key, gdelt_news: n/a, reddit: error, reddit_arctic_shift: partial (capped)

### NMAX — 2025-03-31
*Reported:* +735% first-day gain vs IPO price ([source](https://site.warrington.ufl.edu/ritter/files/IPOs-doubling-on-the-first-day.pdf))
*Notes:* IPO debut (Reg A); IPO price from memory - verify
*Measured:* ipo debut starting 2025-03-31; biggest day: close 8.4x, intraday high 8.4x from $10.00; best 2-day run 23.3x. Qualifies: **yes**

*Gaps:* sec_filings: n/a, polygon_news: n/a, gdelt_news: n/a, reddit: n/a, reddit_arctic_shift: n/a

### QMMM — 2025-09-08
*Reported:* ~+1700% in a single session ($12 to $207) ([source](https://www.mexc.com/news/92280))
*Notes:* Date approximate; Nasdaq delisting notice 2026
*Measured:* multi day run starting 2025-09-08; biggest day on 2025-09-09: close 22.4x, intraday high 26.6x from $11.28; best 5-day run 38.9x. Qualifies: **yes**
*Pre-pump window (10 days):* return +105%, avg volume 0.5x baseline (max day 0.8x), volatility 2.3x baseline, RSI 85, last close $7.60

| Day | Date | Close | Return | Volume vs baseline |
|---|---|---|---|---|
| -10 | 2025-08-22 | 3.87 | +4% | 0.4x |
| -9 | 2025-08-25 | 4.61 | +19% | 0.2x |
| -8 | 2025-08-26 | 5.18 | +12% | 0.7x |
| -7 | 2025-08-27 | 5.12 | -1% | 0.8x |
| -6 | 2025-08-28 | 4.21 | -18% | 0.8x |
| -5 | 2025-08-29 | 5.32 | +26% | 0.3x |
| -4 | 2025-09-02 | 6.51 | +22% | 0.4x |
| -3 | 2025-09-03 | 6.91 | +6% | 0.4x |
| -2 | 2025-09-04 | 7.12 | +3% | 0.2x |
| -1 | 2025-09-05 | 7.60 | +7% | 0.5x |

**Technical picture at the end of the window**
- Moving averages: EMA 8/21/50 stack bullish; close vs EMA21 +62%, vs WMA20 +48%, vs HMA20 +11%, vs VWMA20 +116%, vs SMA200 +417%
- Momentum: RSI 85, stochastic %K 96, MACD cross in window: no, ADX 25, RSI bullish divergence: no
- Volatility & flow: Bollinger %B 0.99, squeeze: no, ATR 12% of price, CMF 0.65, MFI 93, OBV accumulation divergence: no
- Fibonacci: upswing $0.64 → $7.80; close at 0.028 retracement (nearest 0); pump peaked at the 41.85 extension
- Structure: uptrend (9 higher highs, 11 higher lows); support $3.76, resistance $7.65
- Harmonic patterns: abcd (bearish, 2025-09-05, score 0.846)
- Chart patterns: none
- Candlesticks: three white soldiers (bullish, 2025-08-22), three white soldiers (bullish, 2025-08-25), outside bar (neutral, 2025-08-26), three white soldiers (bullish, 2025-08-26), spinning top (neutral, 2025-08-27), bearish engulfing (bearish, 2025-08-28), bullish engulfing (bullish, 2025-08-29), three outside up (bullish, 2025-09-02), hanging man (bearish, 2025-09-03), doji (neutral, 2025-09-04), three inside up (bullish, 2025-09-05)
- Support/resistance signals: support bounce buy (bullish, 2025-08-25), support bounce buy (bullish, 2025-08-27), support bounce buy (bullish, 2025-08-29), resistance reject sell (bearish, 2025-09-03)

*Gaps:* yahoo_prices: none found, sec_filings: error, polygon_news: needs key, gdelt_news: n/a, reddit: error, reddit_arctic_shift: partial (capped)

### HKD — 2022-07-22
*Reported:* +1500% over 5 sessions, +21000% from IPO ([source](https://www.cbsnews.com/news/amtd-meme-stock-21000-percent-surge/))
*Notes:* Multi-day run; IPO July 2022
*Measured:* multi day run starting 2022-07-22; biggest day: close 3.3x, intraday high 3.5x from $20.32; best 5-day run 29.8x. Qualifies: **yes**

*Gaps:* sec_filings: error, polygon_news: needs key, gdelt_news: n/a, reddit: error, reddit_arctic_shift: partial (capped)

### KODK — 2020-07-27
*Reported:* +203% then +318% (~+1440% over two days) on $765M govt loan ([source](https://www.forbes.com/sites/naeemaslam/2020/07/29/kodak-stock-price-up-over-1440-in-two-days/))
*Notes:* Multi-day run
*Measured:* multi day run starting 2020-07-27; biggest day on 2020-07-29: close 4.2x, intraday high 7.6x from $7.94; best 3-day run 15.8x. Qualifies: **yes**
*Pre-pump window (10 days):* return +0%, avg volume 0.4x baseline (max day 0.7x), volatility 0.3x baseline, RSI 43, last close $2.10

| Day | Date | Close | Return | Volume vs baseline |
|---|---|---|---|---|
| -10 | 2020-07-13 | 2.02 | -4% | 0.4x |
| -9 | 2020-07-14 | 2.06 | +2% | 0.5x |
| -8 | 2020-07-15 | 2.08 | +1% | 0.4x |
| -7 | 2020-07-16 | 2.11 | +1% | 0.3x |
| -6 | 2020-07-17 | 2.18 | +3% | 0.7x |
| -5 | 2020-07-20 | 2.24 | +3% | 0.4x |
| -4 | 2020-07-21 | 2.20 | -2% | 0.4x |
| -3 | 2020-07-22 | 2.16 | -2% | 0.2x |
| -2 | 2020-07-23 | 2.14 | -1% | 0.3x |
| -1 | 2020-07-24 | 2.10 | -2% | 0.2x |

**Technical picture at the end of the window**
- Moving averages: EMA 8/21/50 stack bearish; close vs EMA21 -4%, vs WMA20 -2%, vs HMA20 -2%, vs VWMA20 -6%, vs SMA200 -21%
- Momentum: RSI 43, stochastic %K 36, MACD cross in window: yes, ADX 19, RSI bullish divergence: no
- Volatility & flow: Bollinger %B 0.31, squeeze: yes, ATR 6% of price, CMF -0.33, MFI 33, OBV accumulation divergence: no
- Fibonacci: downswing $1.50 → $3.65; close at 0.279 bounce (nearest 0.236); pump peaked at the 27.21 extension
- Structure: downtrend (5 higher highs, 6 higher lows); support $2.00, resistance $2.95
- Harmonic patterns: none
- Chart patterns: consolidation (neutral, 2020-07-24)
- Candlesticks: bearish marubozu (bearish, 2020-07-13), bearish engulfing (bearish, 2020-07-13), bullish harami (bullish, 2020-07-14), doji (neutral, 2020-07-15), spinning top (neutral, 2020-07-15), spinning top (neutral, 2020-07-20), spinning top (neutral, 2020-07-21), bearish belt hold (bearish, 2020-07-22), three black crows (bearish, 2020-07-22), doji (neutral, 2020-07-23), spinning top (neutral, 2020-07-24)
- Support/resistance signals: support bounce buy (bullish, 2020-07-14), support bounce buy (bullish, 2020-07-15), support bounce buy (bullish, 2020-07-16)

*Gaps:* sec_filings: error, polygon_news: needs key, gdelt_news: n/a, reddit: error, reddit_arctic_shift: partial (capped)

### KOSS — 2021-01-25
*Reported:* +1000% over three days during meme squeeze ([source](https://urbanmilwaukee.com/2021/01/27/koss-stock-up-over-1000-in-three-days/))
*Notes:* Multi-day run
*Measured:* multi day run starting 2021-01-25; biggest day on 2021-01-27: close 5.8x, intraday high 7.0x from $10.00; best 5-day run 19.2x. Qualifies: **yes**
*Pre-pump window (10 days):* return +6%, avg volume 0.6x baseline (max day 2.3x), volatility 1.2x baseline, RSI 57, last close $3.34

| Day | Date | Close | Return | Volume vs baseline |
|---|---|---|---|---|
| -10 | 2021-01-08 | 3.27 | +4% | 0.2x |
| -9 | 2021-01-11 | 3.20 | -2% | 0.1x |
| -8 | 2021-01-12 | 3.24 | +1% | 0.1x |
| -7 | 2021-01-13 | 3.11 | -4% | 0.1x |
| -6 | 2021-01-14 | 3.07 | -1% | 0.1x |
| -5 | 2021-01-15 | 2.90 | -6% | 0.3x |
| -4 | 2021-01-19 | 3.62 | +25% | 2.3x |
| -3 | 2021-01-20 | 3.43 | -5% | 1.9x |
| -2 | 2021-01-21 | 3.54 | +3% | 0.3x |
| -1 | 2021-01-22 | 3.34 | -6% | 0.4x |

**Technical picture at the end of the window**
- Moving averages: EMA 8/21/50 stack bullish; close vs EMA21 +7%, vs WMA20 +3%, vs HMA20 -0%, vs VWMA20 -2%, vs SMA200 +70%
- Momentum: RSI 57, stochastic %K 35, MACD cross in window: yes, ADX 52, RSI bullish divergence: no
- Volatility & flow: Bollinger %B 0.62, squeeze: no, ATR 12% of price, CMF -0.53, MFI 64, OBV accumulation divergence: no
- Fibonacci: upswing $1.79 → $5.10; close at 0.532 retracement (nearest 0.5); pump peaked at the 37.96 extension
- Structure: range (12 higher highs, 12 higher lows); support $2.78, resistance –
- Harmonic patterns: none
- Chart patterns: double bottom (bullish, 2021-01-15), bull flag (bullish, 2021-01-08), bull flag (bullish, 2021-01-11), bull flag (bullish, 2021-01-12), bull flag (bullish, 2021-01-13), bull flag (bullish, 2021-01-14)
- Candlesticks: dragonfly doji (bullish, 2021-01-08), hanging man (bearish, 2021-01-08), dragonfly doji (bullish, 2021-01-11), inside bar (neutral, 2021-01-11), doji (neutral, 2021-01-12), hanging man (bearish, 2021-01-12), spinning top (neutral, 2021-01-12), bearish engulfing (bearish, 2021-01-13), gravestone doji (bearish, 2021-01-14), spinning top (neutral, 2021-01-14), three outside down (bearish, 2021-01-14), three black crows (bearish, 2021-01-15), bullish belt hold (bullish, 2021-01-19), spinning top (neutral, 2021-01-21), bullish harami (bullish, 2021-01-21)
- Support/resistance signals: none

*Gaps:* sec_filings: error, polygon_news: needs key, gdelt_news: n/a, reddit: error, reddit_arctic_shift: partial (capped)

### HOLO — 2024-02-07
*Reported:* reported +600% in a session in Feb 2024 (unconfirmed) ([source](https://investorplace.com/2024/02/microcloud-hologram-holo-stock-pops-another-10-in-speculative-rally/))
*Notes:* Move size unconfirmed
*Measured:* single day starting 2024-02-07; biggest day: close 11.9x, intraday high 12.3x from $1208.00; best 2-day run 19.0x. Qualifies: **yes**
*Pre-pump window (10 days):* return -29%, avg volume 0.5x baseline (max day 1.2x), volatility 0.7x baseline, RSI 27, last close $1208.00

| Day | Date | Close | Return | Volume vs baseline |
|---|---|---|---|---|
| -10 | 2024-01-24 | 1640.00 | -4% | 0.3x |
| -9 | 2024-01-25 | 1552.00 | -5% | 0.3x |
| -8 | 2024-01-26 | 1560.00 | +1% | 0.2x |
| -7 | 2024-01-29 | 1800.00 | +15% | 0.5x |
| -6 | 2024-01-30 | 1656.00 | -8% | 0.3x |
| -5 | 2024-01-31 | 1608.00 | -3% | 0.4x |
| -4 | 2024-02-01 | 1544.00 | -4% | 0.4x |
| -3 | 2024-02-02 | 1464.00 | -5% | 1.0x |
| -2 | 2024-02-05 | 1360.00 | -7% | 1.2x |
| -1 | 2024-02-06 | 1208.00 | -11% | 0.7x |

**Technical picture at the end of the window**
- Moving averages: EMA 8/21/50 stack bearish; close vs EMA21 -34%, vs WMA20 -24%, vs HMA20 -16%, vs VWMA20 -42%, vs SMA200 -93%
- Momentum: RSI 27, stochastic %K 1, MACD cross in window: no, ADX 13, RSI bullish divergence: no
- Volatility & flow: Bollinger %B 0.04, squeeze: no, ATR 23% of price, CMF -0.24, MFI 21, OBV accumulation divergence: no
- Fibonacci: downswing $1200.00 → $90400.00; close at 0.000 bounce (nearest 0); pump peaked at the 0.36 extension
- Structure: downtrend (5 higher highs, 6 higher lows); support –, resistance $4044.00
- Harmonic patterns: none
- Chart patterns: falling wedge (bullish, 2024-02-06), consolidation (neutral, 2024-02-01)
- Candlesticks: spinning top (neutral, 2024-01-25), three black crows (bearish, 2024-01-25), inside bar (neutral, 2024-01-26), bullish kicker (bullish, 2024-01-29), dark cloud cover (bearish, 2024-01-30), bearish belt hold (bearish, 2024-01-30), bearish belt hold (bearish, 2024-01-31), three black crows (bearish, 2024-02-01), hammer (bullish, 2024-02-02), three black crows (bearish, 2024-02-02), three black crows (bearish, 2024-02-05), three black crows (bearish, 2024-02-06)
- Support/resistance signals: none

**Reddit** — ≥1 mentions by 1 authors, avg sentiment 0.36, mentions per day [0, 0, 0, 0, 0, 0, 0, 0, 1, 0]
- 2024-02-05 r/Shortsqueeze (score 1): [HOLO ready to take off after R/S with tiny float and news pending...take a look](https://www.reddit.com/r/Shortsqueeze/comments/1ajifl6/holo_ready_to_take_off_after_rs_with_tiny_float/)

*Gaps:* sec_filings: error, polygon_news: needs key, gdelt_news: n/a, reddit: error, reddit_arctic_shift: partial (capped)

### NUKK — 2024-12-17
*Reported:* all-time-high close $52.10 around private placement news ([source](https://www.macrotrends.net/stocks/charts/NUKK/nukkleus/stock-price-history))
*Notes:* Move size unconfirmed
*Measured:* single day starting 2024-12-17; biggest day: close 8.6x, intraday high 13.0x from $1.36; best 3-day run 37.8x. Qualifies: **yes**
*Pre-pump window (10 days):* return -18%, avg volume 0.1x baseline (max day 0.2x), volatility 0.6x baseline, RSI 36, last close $1.36

| Day | Date | Close | Return | Volume vs baseline |
|---|---|---|---|---|
| -10 | 2024-12-03 | 1.60 | -3% | 0.0x |
| -9 | 2024-12-04 | 1.69 | +6% | 0.1x |
| -8 | 2024-12-05 | 1.46 | -14% | 0.2x |
| -7 | 2024-12-06 | 1.53 | +5% | 0.1x |
| -6 | 2024-12-09 | 1.56 | +2% | 0.0x |
| -5 | 2024-12-10 | 1.53 | -2% | 0.1x |
| -4 | 2024-12-11 | 1.56 | +2% | 0.0x |
| -3 | 2024-12-12 | 1.48 | -5% | 0.0x |
| -2 | 2024-12-13 | 1.39 | -6% | 0.0x |
| -1 | 2024-12-16 | 1.36 | -2% | 0.1x |

**Technical picture at the end of the window**
- Moving averages: EMA 8/21/50 stack bearish; close vs EMA21 -20%, vs WMA20 -12%, vs HMA20 -6%, vs VWMA20 -17%, vs SMA200 -73%
- Momentum: RSI 36, stochastic %K 4, MACD cross in window: yes, ADX 17, RSI bullish divergence: no
- Volatility & flow: Bollinger %B 0.00, squeeze: yes, ATR 17% of price, CMF -0.28, MFI 55, OBV accumulation divergence: no
- Fibonacci: downswing $1.34 → $5.50; close at 0.005 bounce (nearest 0); pump peaked at the 18.50 extension
- Structure: downtrend (11 higher highs, 13 higher lows); support –, resistance $2.03
- Harmonic patterns: none
- Chart patterns: falling wedge (bullish, 2024-12-16), consolidation (neutral, 2024-12-16)
- Candlesticks: inverted hammer (bullish, 2024-12-03), bullish engulfing (bullish, 2024-12-04), outside bar (neutral, 2024-12-04), bullish belt hold (bullish, 2024-12-04), morning star (bullish, 2024-12-04), bearish marubozu (bearish, 2024-12-05), bearish engulfing (bearish, 2024-12-05), bearish belt hold (bearish, 2024-12-05), inside bar (neutral, 2024-12-06), bullish harami (bullish, 2024-12-06), bearish marubozu (bearish, 2024-12-09), inside bar (neutral, 2024-12-09), bullish belt hold (bullish, 2024-12-11), spinning top (neutral, 2024-12-12), bearish harami (bearish, 2024-12-12), three inside down (bearish, 2024-12-13), outside bar (neutral, 2024-12-16)
- Support/resistance signals: none

*Gaps:* yahoo_prices: none found, sec_filings: error, polygon_news: needs key, gdelt_news: n/a, reddit: error, reddit_arctic_shift: partial (capped)

### GME — 2021-01-26
*Reported:* +135% (best day); +600% over the week ([source](https://en.wikipedia.org/wiki/R/wallstreetbets))
*Notes:* Below the single-day 5x bar
*Measured:* multi day run starting 2021-01-26; biggest day on 2021-01-27: close 2.3x, intraday high 2.6x from $36.99; best 5-day run 8.9x. Qualifies: **yes**
*Pre-pump window (10 days):* return +334%, avg volume 8.5x baseline (max day 19.7x), volatility 3.4x baseline, RSI 91, last close $19.20

| Day | Date | Close | Return | Volume vs baseline |
|---|---|---|---|---|
| -10 | 2021-01-11 | 4.99 | +13% | 1.5x |
| -9 | 2021-01-12 | 4.99 | +0% | 0.7x |
| -8 | 2021-01-13 | 7.85 | +57% | 14.5x |
| -7 | 2021-01-14 | 9.98 | +27% | 9.4x |
| -6 | 2021-01-15 | 8.88 | -11% | 4.7x |
| -5 | 2021-01-19 | 9.84 | +11% | 7.5x |
| -4 | 2021-01-20 | 9.78 | -1% | 3.4x |
| -3 | 2021-01-21 | 10.76 | +10% | 5.6x |
| -2 | 2021-01-22 | 16.25 | +51% | 19.7x |
| -1 | 2021-01-25 | 19.20 | +18% | 17.8x |

**Technical picture at the end of the window**
- Moving averages: EMA 8/21/50 stack bullish; close vs EMA21 +123%, vs WMA20 +107%, vs HMA20 +48%, vs VWMA20 +57%, vs SMA200 +660%
- Momentum: RSI 91, stochastic %K 42, MACD cross in window: yes, ADX 56, RSI bullish divergence: no
- Volatility & flow: Bollinger %B 1.20, squeeze: no, ATR 17% of price, CMF -0.04, MFI 93, OBV accumulation divergence: no
- Fibonacci: upswing $1.01 → $39.79; close at 0.531 retracement (nearest 0.5); pump peaked at the 3.09 extension
- Structure: uptrend (8 higher highs, 8 higher lows); support $1.62, resistance –
- Harmonic patterns: none
- Chart patterns: bull flag (bullish, 2021-01-11), bull flag (bullish, 2021-01-12), consolidation (neutral, 2021-01-12), range breakout (bullish, 2021-01-13), range breakout (bullish, 2021-01-14), range breakout (bullish, 2021-01-22), range breakout (bullish, 2021-01-25)
- Candlesticks: gap up (bullish, 2021-01-11), doji (neutral, 2021-01-12), inside bar (neutral, 2021-01-12), spinning top (neutral, 2021-01-14), inside bar (neutral, 2021-01-15), spinning top (neutral, 2021-01-19), morning star (bullish, 2021-01-21), three white soldiers (bullish, 2021-01-22)
- Support/resistance signals: none

**Reddit** — ≥28 mentions by 19 authors, avg sentiment 0.20, mentions per day [0, 0, 1, 3, 0, 3, 0, 1, 2, 10]
- 2021-01-24 r/StockMarket (score 358): [Spreadsheet to calculate GME Exit Strategy, ROI Calculations & Breakeven Analysis](https://www.reddit.com/r/StockMarket/comments/l47hmn/spreadsheet_to_calculate_gme_exit_strategy_roi/)
- 2021-01-24 r/StockMarket (score 170): [The Infinity Squeeze of 08 briefly made $VW the most valuable company in the world. How much would $GME have to go up in order for it to achieve the same?](https://www.reddit.com/r/StockMarket/comments/l46blh/the_infinity_squeeze_of_08_briefly_made_vw_the/)
- 2021-01-24 r/StockMarket (score 136): [Why BB will go much higher than GME](https://www.reddit.com/r/StockMarket/comments/l3o8ve/why_bb_will_go_much_higher_than_gme/)
- 2021-01-25 r/StockMarket (score 58): [GME is sitting at 90 dollart pre-market Google says. +38%, how risky would this stock be to buy today?](https://www.reddit.com/r/StockMarket/comments/l4kfpv/gme_is_sitting_at_90_dollart_premarket_google/)
- 2021-01-24 r/StockMarket (score 45): [Market Commentary (How about that GME and BB craze? Where are we in the market cycle? ) - 1/23/2021](https://www.reddit.com/r/StockMarket/comments/l3uim5/market_commentary_how_about_that_gme_and_bb_craze/)
- 2021-01-25 r/StockMarket (score 34): [I invested in GME when it was at 9, now I'm diverting my money here](https://www.reddit.com/r/StockMarket/comments/l4ydhb/i_invested_in_gme_when_it_was_at_9_now_im/)
- 2021-01-25 r/StockMarket (score 30): [$GME is going back up... Right?](https://www.reddit.com/r/StockMarket/comments/l4u5yc/gme_is_going_back_up_right/)
- 2021-01-19 r/StockMarket (score 11): [Stock Market News for Today | Stimulus Bill | TSLA, NKLA, GME & other Stock Market News [01-19]](https://www.reddit.com/r/StockMarket/comments/l0jill/stock_market_news_for_today_stimulus_bill_tsla/)

*Gaps:* sec_filings: error, polygon_news: needs key, gdelt_news: n/a, reddit: error, reddit_arctic_shift: partial (capped)

### AMC — 2021-01-21
*Reported:* ~+300% in the January 2021 squeeze ([source](https://www.business-standard.com/article/international/free-tickets-and-popcorn-as-amc-jumps-1-400-in-meme-stock-rally-121060201616_1.html))
*Notes:* Below the single-day 5x bar
*Measured:* multi day run starting 2021-01-21; biggest day on 2021-01-27: close 4.0x, intraday high 4.1x from $49.60; best 5-day run 6.7x. Qualifies: **yes**
*Pre-pump window (10 days):* return +50%, avg volume 3.8x baseline (max day 10.6x), volatility 1.0x baseline, RSI 59, last close $29.70

| Day | Date | Close | Return | Volume vs baseline |
|---|---|---|---|---|
| -10 | 2021-01-06 | 20.10 | +2% | 2.8x |
| -9 | 2021-01-07 | 20.50 | +2% | 1.1x |
| -8 | 2021-01-08 | 21.40 | +4% | 1.6x |
| -7 | 2021-01-11 | 22.00 | +3% | 1.7x |
| -6 | 2021-01-12 | 22.90 | +4% | 1.7x |
| -5 | 2021-01-13 | 21.80 | -5% | 1.9x |
| -4 | 2021-01-14 | 21.80 | +0% | 2.1x |
| -3 | 2021-01-15 | 23.30 | +7% | 6.7x |
| -2 | 2021-01-19 | 30.60 | +31% | 10.6x |
| -1 | 2021-01-20 | 29.70 | -3% | 7.5x |

**Technical picture at the end of the window**
- Moving averages: EMA 8/21/50 stack bearish; close vs EMA21 +17%, vs WMA20 +27%, vs HMA20 +22%, vs VWMA20 +17%, vs SMA200 -28%
- Momentum: RSI 59, stochastic %K 74, MACD cross in window: yes, ADX 20, RSI bullish divergence: no
- Volatility & flow: Bollinger %B 1.02, squeeze: no, ATR 11% of price, CMF -0.15, MFI 80, OBV accumulation divergence: no
- Fibonacci: downswing $19.10 → $77.10; close at 0.183 bounce (nearest 0.236); pump peaked at the 3.18 extension
- Structure: downtrend (8 higher highs, 6 higher lows); support $27.00, resistance $32.85
- Harmonic patterns: none
- Chart patterns: consolidation (neutral, 2021-01-14), range breakout (bullish, 2021-01-19)
- Candlesticks: inside bar (neutral, 2021-01-07), spinning top (neutral, 2021-01-07), shooting star (bearish, 2021-01-11), shooting star (bearish, 2021-01-12), three white soldiers (bullish, 2021-01-12), bearish engulfing (bearish, 2021-01-13), spinning top (neutral, 2021-01-14), bullish harami (bullish, 2021-01-14), gap up (bullish, 2021-01-19)
- Support/resistance signals: support bounce buy (bullish, 2021-01-08), breakout buy (bullish, 2021-01-19), resistance reject sell (bearish, 2021-01-20)

**Reddit** — ≥9 mentions by 6 authors, avg sentiment 0.13, mentions per day [0, 0, 2, 0, 0, 0, 0, 1, 1, 1]
- 2021-01-19 r/smallstreetbets (score 28): [For those of you who took my AMC advice, it’s formed a channel today from its other channel. As you can see in the 4h pic, it’s moon shooting. That is all, have a good one fellow autists.](https://www.reddit.com/r/smallstreetbets/comments/l0u5d1/for_those_of_you_who_took_my_amc_advice_its/)
- 2021-01-18 r/Shortsqueeze (score 25): [Short Squeeze AMC](https://www.reddit.com/r/Shortsqueeze/comments/l04qnj/short_squeeze_amc/)
- 2021-01-20 r/smallstreetbets (score 12): [BB or AMC? I hold a couple hundred shares of of both, but finally got my 2019 tax refund and I'm re-upping into one of them! Thoughts?](https://www.reddit.com/r/smallstreetbets/comments/l0yz8b/bb_or_amc_i_hold_a_couple_hundred_shares_of_of/)
- 2021-01-08 r/investing (score 10): [AMC and its prospects](https://www.reddit.com/r/investing/comments/kta7mz/amc_and_its_prospects/)
- 2021-01-16 r/investing (score 6): [What is the likelihood of AMC going bankrupt vs its stock rebounding?](https://www.reddit.com/r/investing/comments/kyqjnn/what_is_the_likelihood_of_amc_going_bankrupt_vs/)
- 2021-01-15 r/StockMarket (score 2): [Imax ceo says they're cash flow neutral. AMC thoughts?](https://www.reddit.com/r/StockMarket/comments/ky3zwx/imax_ceo_says_theyre_cash_flow_neutral_amc/)
- 2021-01-08 r/investing (score 1): [AMC and streaming](https://www.reddit.com/r/investing/comments/kta5ks/amc_and_streaming/)
- 2021-01-16 r/investing (score 1): [What is the likelyhood of AMC going bankrupt or its stock rebounded?](https://www.reddit.com/r/investing/comments/kyqh72/what_is_the_likelyhood_of_amc_going_bankrupt_or/)

*Gaps:* sec_filings: error, polygon_news: needs key, gdelt_news: n/a, reddit: error, reddit_arctic_shift: partial (capped)

### AMC — 2021-06-01
*Reported:* second squeeze, ~+95% day ([source](https://fortune.com/2021/05/18/amc-stock-meme-surge-reddit-twitter))
*Notes:* Below the single-day 5x bar; move size from memory
*Measured:* multi day run starting 2021-06-01; biggest day on 2021-06-02: close 2.0x, intraday high 2.3x from $320.40; best 5-day run 3.8x. Qualifies: **no**
*Pre-pump window (10 days):* return +101%, avg volume 2.8x baseline (max day 7.5x), volatility 1.6x baseline, RSI 85, last close $261.20

| Day | Date | Close | Return | Volume vs baseline |
|---|---|---|---|---|
| -10 | 2021-05-17 | 139.50 | +7% | 1.7x |
| -9 | 2021-05-18 | 140.30 | +1% | 1.8x |
| -8 | 2021-05-19 | 126.40 | -10% | 0.9x |
| -7 | 2021-05-20 | 125.50 | -1% | 0.6x |
| -6 | 2021-05-21 | 120.80 | -4% | 0.6x |
| -5 | 2021-05-24 | 136.80 | +13% | 1.2x |
| -4 | 2021-05-25 | 164.10 | +20% | 2.3x |
| -3 | 2021-05-26 | 195.60 | +19% | 4.0x |
| -2 | 2021-05-27 | 265.20 | +36% | 7.5x |
| -1 | 2021-05-28 | 261.20 | -2% | 7.0x |

**Technical picture at the end of the window**
- Moving averages: EMA 8/21/50 stack bullish; close vs EMA21 +73%, vs WMA20 +65%, vs HMA20 +34%, vs VWMA20 +37%, vs SMA200 +288%
- Momentum: RSI 85, stochastic %K 61, MACD cross in window: no, ADX 35, RSI bullish divergence: no
- Volatility & flow: Bollinger %B 1.11, squeeze: no, ATR 11% of price, CMF 0.05, MFI 96, OBV accumulation divergence: no
- Fibonacci: upswing $19.10 → $367.20; close at 0.305 retracement (nearest 0.236); pump peaked at the 2.03 extension
- Structure: uptrend (9 higher highs, 9 higher lows); support $89.30, resistance –
- Harmonic patterns: none
- Chart patterns: bull flag (bullish, 2021-05-21), bull flag (bullish, 2021-05-24), range breakout (bullish, 2021-05-25), range breakout (bullish, 2021-05-26), range breakout (bullish, 2021-05-27)
- Candlesticks: spinning top (neutral, 2021-05-17), spinning top (neutral, 2021-05-18), spinning top (neutral, 2021-05-19), gap down (bearish, 2021-05-19), doji (neutral, 2021-05-20), three black crows (bearish, 2021-05-20), inside bar (neutral, 2021-05-21), gap up (bullish, 2021-05-26), three white soldiers (bullish, 2021-05-26), three white soldiers (bullish, 2021-05-27)
- Support/resistance signals: none

**Reddit** — ≥377 mentions by 241 authors, avg sentiment 0.06, mentions per day [1, 1, 1, 2, 0, 0, 3, 3, 205, 159]
- 2021-05-27 r/Superstonk (score 22510): [No one's selling GME to buy into AMC.](https://www.reddit.com/r/Superstonk/comments/nmdp1y/no_ones_selling_gme_to_buy_into_amc/)
- 2021-05-27 r/Superstonk (score 17966): [Apes called it weeks ago; squeeze AMC first to try to get people to jump ship from GME. MSM already pushing the narrative and I cant help but laugh](https://www.reddit.com/r/Superstonk/comments/nmcpms/apes_called_it_weeks_ago_squeeze_amc_first_to_try/)
- 2021-05-27 r/Superstonk (score 12061): [For those holding AMC, congratulations on a significant rise! No hate here! To apes who don’t hold AMC, don’t sell your GME shares to buy AMC. Not financial advice.](https://www.reddit.com/r/Superstonk/comments/nmd2ch/for_those_holding_amc_congratulations_on_a/)
- 2021-05-28 r/Superstonk (score 10712): [Why I am Ecstatic GME is Taking a Dump, and the Possible Correlation with AMC and Crypto](https://www.reddit.com/r/Superstonk/comments/nn370o/why_i_am_ecstatic_gme_is_taking_a_dump_and_the/)
- 2021-05-27 r/Superstonk (score 9114): [We literally predicted that they would let AMC run whilst suppressing GME as a tactic & MSM is making it so damn obvious that this is their plan! Stay the course! GME is the way! 💎💎💎🚀🚀🚀🚀🚀💎💎💎](https://www.reddit.com/r/Superstonk/comments/nmesvk/we_literally_predicted_that_they_would_let_amc/)
- 2021-05-27 r/Superstonk (score 6027): [AMC's spike today and what it means for GME: HFs' little experiment went horribly wrong.](https://www.reddit.com/r/Superstonk/comments/nmhm1s/amcs_spike_today_and_what_it_means_for_gme_hfs/)
- 2021-05-27 r/Superstonk (score 4241): [Sir, they are buying more GME with their AMC gains now](https://www.reddit.com/r/Superstonk/comments/nmflrf/sir_they_are_buying_more_gme_with_their_amc_gains/)
- 2021-05-28 r/Superstonk (score 3518): [GME is a BEAST! We went from 150 to 250 with volume for ants. In comparison AMC, because why not.](https://www.reddit.com/r/Superstonk/comments/nmvd5k/gme_is_a_beast_we_went_from_150_to_250_with/)

*Gaps:* sec_filings: error, polygon_news: needs key, gdelt_news: n/a, reddit: error, reddit_arctic_shift: partial (capped)

### DWAC — 2021-10-21
*Reported:* +357% then +107% on Trump Media merger news ([source](https://www.fool.com/investing/2021/10/22/why-digital-world-acquisition-and-phunware-soared/))
*Notes:* SPAC; now trades as DJT (Trump Media)
*Measured:* single day starting 2021-10-21; biggest day: close 4.6x, intraday high 5.2x from $9.96; best 5-day run 9.5x. Qualifies: **yes**
*Pre-pump window (10 days):* return +0%, avg volume 1.5x baseline (max day 7.0x), volatility 2.2x baseline, RSI 40, last close $9.96

| Day | Date | Close | Return | Volume vs baseline |
|---|---|---|---|---|
| -10 | 2021-10-07 | 9.97 | +0% | 6.3x |
| -9 | 2021-10-08 | 9.95 | -0% | 0.1x |
| -8 | 2021-10-11 | 9.95 | +0% | 0.2x |
| -7 | 2021-10-12 | 9.97 | +0% | 0.0x |
| -6 | 2021-10-13 | 9.96 | -0% | 0.0x |
| -5 | 2021-10-14 | 9.97 | +0% | 0.4x |
| -4 | 2021-10-15 | 9.96 | -0% | 0.0x |
| -3 | 2021-10-18 | 9.97 | +0% | 0.0x |
| -2 | 2021-10-19 | 10.01 | +0% | 0.5x |
| -1 | 2021-10-20 | 9.96 | -0% | 7.0x |

**Technical picture at the end of the window**
- Moving averages: EMA 8/21/50 stack mixed; close vs EMA21 –, vs WMA20 –, vs HMA20 –, vs VWMA20 –, vs SMA200 – (EMA200 unavailable: short history)
- Momentum: RSI 40, stochastic %K 10, MACD cross in window: no, ADX –, RSI bullish divergence: no
- Volatility & flow: Bollinger %B –, squeeze: no, ATR 27% of price, CMF –, MFI 43, OBV accumulation divergence: no
- Fibonacci: downswing $9.84 → $17.33; close at 0.016 bounce (nearest 0); pump peaked at the 22.05 extension
- Structure: range (0 higher highs, 0 higher lows); support –, resistance –
- Harmonic patterns: none
- Chart patterns: consolidation (neutral, 2021-10-20)
- Candlesticks: doji (neutral, 2021-10-07), bullish belt hold (bullish, 2021-10-07), doji (neutral, 2021-10-08), bullish marubozu (bullish, 2021-10-08), doji (neutral, 2021-10-11), doji (neutral, 2021-10-12), bullish marubozu (bullish, 2021-10-12), doji (neutral, 2021-10-13), bearish marubozu (bearish, 2021-10-13), bearish belt hold (bearish, 2021-10-13), doji (neutral, 2021-10-14), dragonfly doji (bullish, 2021-10-15), hammer (bullish, 2021-10-15), inverted hammer (bullish, 2021-10-15), bullish marubozu (bullish, 2021-10-18), bullish belt hold (bullish, 2021-10-18), bearish engulfing (bearish, 2021-10-20), bearish belt hold (bearish, 2021-10-20)
- Support/resistance signals: none

*Gaps:* sec_filings: error, polygon_news: needs key, gdelt_news: n/a, reddit: error, reddit_arctic_shift: partial (capped)

### BB — 2021-01-21
*Reported:* meme rally with GME/AMC ([source](https://github.com/shaunwolf/piptrack/blob/main/attached_assets/pumped_stock_cases_1749923665803.csv))
*Notes:* From earlier project notes - verify
*Measured:* multi day run starting 2021-01-21; biggest day on 2021-01-27: close 1.3x, intraday high 1.5x from $18.92; best 5-day run 2.0x. Qualifies: **no**
*Pre-pump window (10 days):* return +89%, avg volume 3.1x baseline (max day 8.7x), volatility 2.1x baseline, RSI 87, last close $12.79

| Day | Date | Close | Return | Volume vs baseline |
|---|---|---|---|---|
| -10 | 2021-01-06 | 6.71 | -1% | 0.6x |
| -9 | 2021-01-07 | 7.06 | +5% | 0.7x |
| -8 | 2021-01-08 | 7.56 | +7% | 1.3x |
| -7 | 2021-01-11 | 7.65 | +1% | 0.9x |
| -6 | 2021-01-12 | 7.63 | -0% | 0.5x |
| -5 | 2021-01-13 | 7.44 | -2% | 0.5x |
| -4 | 2021-01-14 | 9.11 | +22% | 3.7x |
| -3 | 2021-01-15 | 9.84 | +8% | 8.7x |
| -2 | 2021-01-19 | 12.35 | +26% | 6.4x |
| -1 | 2021-01-20 | 12.79 | +4% | 7.3x |

**Technical picture at the end of the window**
- Moving averages: EMA 8/21/50 stack bullish; close vs EMA21 +51%, vs WMA20 +50%, vs HMA20 +29%, vs VWMA20 +28%, vs SMA200 +140%
- Momentum: RSI 87, stochastic %K 88, MACD cross in window: yes, ADX 43, RSI bullish divergence: no
- Volatility & flow: Bollinger %B 1.18, squeeze: no, ATR 6% of price, CMF 0.02, MFI 96, OBV accumulation divergence: no
- Fibonacci: upswing $4.37 → $13.64; close at 0.092 retracement (nearest 0); pump peaked at the 2.63 extension
- Structure: downtrend (4 higher highs, 6 higher lows); support $6.99, resistance –
- Harmonic patterns: none
- Chart patterns: range breakout (bullish, 2021-01-14), range breakout (bullish, 2021-01-15), range breakout (bullish, 2021-01-19), range breakout (bullish, 2021-01-20)
- Candlesticks: gravestone doji (bearish, 2021-01-06), dragonfly doji (bullish, 2021-01-11), three white soldiers (bullish, 2021-01-11), bearish engulfing (bearish, 2021-01-12), inside bar (neutral, 2021-01-12), three outside down (bearish, 2021-01-13), bullish belt hold (bullish, 2021-01-14), gap up (bullish, 2021-01-15), bullish kicker (bullish, 2021-01-19)
- Support/resistance signals: support bounce buy (bullish, 2021-01-08)

**Reddit** — ≥3 mentions by 2 authors, avg sentiment 0.00, mentions per day [0, 0, 0, 0, 0, 0, 0, 0, 0, 2]
- 2021-01-20 r/RobinHoodPennyStocks (score 6): [Thoughts on $BB for the day?](https://www.reddit.com/r/RobinHoodPennyStocks/comments/l17ybz/thoughts_on_bb_for_the_day/)
- 2021-01-18 r/RobinHoodPennyStocks (score 1): [Calls for $BB?](https://www.reddit.com/r/RobinHoodPennyStocks/comments/l050sa/calls_for_bb/)
- 2021-01-20 r/RobinHoodPennyStocks (score 1): [$BB I guess?](https://www.reddit.com/r/RobinHoodPennyStocks/comments/l1lzm0/bb_i_guess/)

*Gaps:* sec_filings: error, polygon_news: needs key, gdelt_news: n/a, reddit: error, reddit_arctic_shift: partial (capped)

### BBBY — 2021-01-21
*Reported:* meme rally with GME/AMC ([source](https://github.com/shaunwolf/piptrack/blob/main/attached_assets/pumped_stock_cases_1749923665803.csv))
*Notes:* Bankrupt 2023; delisted
*Measured:* multi day run starting 2021-01-21; biggest day on 2021-01-25: close 1.0x, intraday high 1.6x from $30.21; best 5-day run 2.1x. Qualifies: **no**
*Pre-pump window (10 days):* return +26%, avg volume 2.2x baseline (max day 5.0x), volatility 2.3x baseline, RSI 65, last close $24.99

| Day | Date | Close | Return | Volume vs baseline |
|---|---|---|---|---|
| -10 | 2021-01-06 | 21.03 | +6% | 2.4x |
| -9 | 2021-01-07 | 18.73 | -11% | 5.0x |
| -8 | 2021-01-08 | 18.93 | +1% | 1.4x |
| -7 | 2021-01-11 | 20.49 | +8% | 2.1x |
| -6 | 2021-01-12 | 21.52 | +5% | 1.1x |
| -5 | 2021-01-13 | 23.04 | +7% | 2.3x |
| -4 | 2021-01-14 | 27.33 | +19% | 3.8x |
| -3 | 2021-01-15 | 25.59 | -6% | 1.7x |
| -2 | 2021-01-19 | 25.03 | -2% | 1.1x |
| -1 | 2021-01-20 | 24.99 | -0% | 0.7x |

**Technical picture at the end of the window**
- Moving averages: EMA 8/21/50 stack bullish; close vs EMA21 +15%, vs WMA20 +14%, vs HMA20 -0%, vs VWMA20 +18%, vs SMA200 +81%
- Momentum: RSI 65, stochastic %K 73, MACD cross in window: no, ADX 25, RSI bullish divergence: no
- Volatility & flow: Bollinger %B 0.87, squeeze: no, ATR 7% of price, CMF 0.16, MFI 64, OBV accumulation divergence: no
- Fibonacci: upswing $10.51 → $27.74; close at 0.160 retracement (nearest 0.236); pump peaked at the 2.52 extension
- Structure: uptrend (10 higher highs, 9 higher lows); support $22.51, resistance –
- Harmonic patterns: none
- Chart patterns: range breakout (bullish, 2021-01-06), range breakout (bullish, 2021-01-13), range breakout (bullish, 2021-01-14), bull flag (bullish, 2021-01-20)
- Candlesticks: gap up (bullish, 2021-01-06), three white soldiers (bullish, 2021-01-06), gap down (bearish, 2021-01-07), inside bar (neutral, 2021-01-08), bullish engulfing (bullish, 2021-01-11), outside bar (neutral, 2021-01-11), three outside up (bullish, 2021-01-12), three white soldiers (bullish, 2021-01-13), three white soldiers (bullish, 2021-01-14), inside bar (neutral, 2021-01-15), doji (neutral, 2021-01-20), inside bar (neutral, 2021-01-20), three black crows (bearish, 2021-01-20)
- Support/resistance signals: support bounce buy (bullish, 2021-01-07), breakout buy (bullish, 2021-01-13)

**Reddit** — ≥67 mentions by 41 authors, avg sentiment 0.25, mentions per day [5, 4, 0, 0, 2, 3, 21, 21, 4, 2]
- 2021-01-15 r/wallstreetbets (score 3283): [Alex Karp says Buy the Dip !!! PLTR MOON SOON !! , while GME BBBY BB AND TSLA celebrate. WSB visualised.](https://www.reddit.com/r/wallstreetbets/comments/kxrcpj/alex_karp_says_buy_the_dip_pltr_moon_soon_while/)
- 2021-01-18 r/wallstreetbets (score 246): [$906.44 to $25,204.53 in two days. 1/12-1/14 $BBBY TO THE MOON!!🚀🚀🚀](https://www.reddit.com/r/wallstreetbets/comments/kznner/90644_to_2520453_in_two_days_112114_bbby_to_the/)
- 2021-01-14 r/wallstreetbets (score 208): [I predicted BBBY - IPOE is my next move](https://www.reddit.com/r/wallstreetbets/comments/kx8dsv/i_predicted_bbby_ipoe_is_my_next_move/)
- 2021-01-16 r/wallstreetbets (score 194): [Top 3 short positions as of 1/15/2021 $GME $LGND $BBBY](https://www.reddit.com/r/wallstreetbets/comments/kyjtax/top_3_short_positions_as_of_1152021_gme_lgnd_bbby/)
- 2021-01-12 r/wallstreetbets (score 128): [The BBBY Short Squeeze Starts Now 🚀🚀🚀 Earnings were NOT a Disaster, and BBBY is about to BURN the Shorters with Buybacks](https://www.reddit.com/r/wallstreetbets/comments/kw1j7a/the_bbby_short_squeeze_starts_now_earnings_were/)
- 2021-01-20 r/wallstreetbets (score 126): [BBBY 40K Yolo - In Tritton We Trust](https://www.reddit.com/r/wallstreetbets/comments/l1ix0v/bbby_40k_yolo_in_tritton_we_trust/)
- 2021-01-14 r/wallstreetbets (score 110): [[Serious DD] Is $BBBY not the exact same as $GME was yesterday?](https://www.reddit.com/r/wallstreetbets/comments/kx8tey/serious_dd_is_bbby_not_the_exact_same_as_gme_was/)
- 2021-01-15 r/wallstreetbets (score 109): [The BBBY Short Squeeze (Little Sister of All Short Squeezes)](https://www.reddit.com/r/wallstreetbets/comments/kxn8it/the_bbby_short_squeeze_little_sister_of_all_short/)

*Gaps:* yahoo_prices: none found, sec_filings: error, polygon_news: needs key, gdelt_news: n/a, reddit: error, reddit_arctic_shift: partial (capped)

### EXPR — 2021-01-21
*Reported:* meme rally with GME/AMC ([source](https://github.com/shaunwolf/piptrack/blob/main/attached_assets/pumped_stock_cases_1749923665803.csv))
*Notes:* Bankrupt 2024; delisted
*Measured:* multi day run starting 2021-01-21; biggest day on 2021-01-27: close 3.2x, intraday high 4.6x from $3.04; best 5-day run 8.3x. Qualifies: **yes**
*Pre-pump window (10 days):* return +20%, avg volume 1.2x baseline (max day 6.4x), volatility 0.9x baseline, RSI 56, last close $1.16

| Day | Date | Close | Return | Volume vs baseline |
|---|---|---|---|---|
| -10 | 2021-01-06 | 1.01 | +4% | 0.4x |
| -9 | 2021-01-07 | 1.02 | +1% | 0.4x |
| -8 | 2021-01-08 | 1.03 | +1% | 0.5x |
| -7 | 2021-01-11 | 1.00 | -3% | 0.6x |
| -6 | 2021-01-12 | 1.05 | +5% | 0.5x |
| -5 | 2021-01-13 | 1.04 | -1% | 0.3x |
| -4 | 2021-01-14 | 1.27 | +22% | 6.4x |
| -3 | 2021-01-15 | 1.25 | -2% | 1.4x |
| -2 | 2021-01-19 | 1.21 | -4% | 0.6x |
| -1 | 2021-01-20 | 1.16 | -4% | 0.6x |

**Technical picture at the end of the window**
- Moving averages: EMA 8/21/50 stack bullish; close vs EMA21 +6%, vs WMA20 +8%, vs HMA20 -2%, vs VWMA20 +2%, vs SMA200 -9%
- Momentum: RSI 56, stochastic %K 46, MACD cross in window: yes, ADX 19, RSI bullish divergence: no
- Volatility & flow: Bollinger %B 0.77, squeeze: no, ATR 10% of price, CMF -0.27, MFI 68, OBV accumulation divergence: no
- Fibonacci: upswing $0.57 → $1.82; close at 0.527 retracement (nearest 0.5); pump peaked at the 10.72 extension
- Structure: range (6 higher highs, 5 higher lows); support $1.01, resistance $1.27
- Harmonic patterns: none
- Chart patterns: symmetrical triangle (neutral, 2021-01-20), range breakout (bullish, 2021-01-14), bull flag (bullish, 2021-01-20)
- Candlesticks: three white soldiers (bullish, 2021-01-06), inside bar (neutral, 2021-01-11), spinning top (neutral, 2021-01-11), tweezer top (bearish, 2021-01-11), spinning top (neutral, 2021-01-13), bearish belt hold (bearish, 2021-01-14), gap up (bullish, 2021-01-14), dragonfly doji (bullish, 2021-01-15), inside bar (neutral, 2021-01-19), three black crows (bearish, 2021-01-19), hammer (bullish, 2021-01-20), three black crows (bearish, 2021-01-20)
- Support/resistance signals: resistance reject sell (bearish, 2021-01-11), support bounce buy (bullish, 2021-01-12), breakout buy (bullish, 2021-01-14), resistance reject sell (bearish, 2021-01-14), breakdown sell (bearish, 2021-01-15), resistance reject sell (bearish, 2021-01-19)

**Reddit** — ≥6 mentions by 5 authors, avg sentiment -0.19, mentions per day [0, 0, 0, 0, 0, 0, 3, 2, 0, 0]
- 2021-01-14 r/wallstreetbets (score 1): [Slap that ask in EXPR and see it do the GME thang! 🚀🚀🚀🚀🚀](https://www.reddit.com/r/wallstreetbets/comments/kxdqww/slap_that_ask_in_expr_and_see_it_do_the_gme_thang/)
- 2021-01-14 r/pennystocks (score 1): [Shout out to my EXPR thread that got 1 reply](https://www.reddit.com/r/pennystocks/comments/kx6ep9/shout_out_to_my_expr_thread_that_got_1_reply/)
- 2021-01-15 r/wallstreetbets (score 1): [YOUR NEXT STOCK... EXPR had highest volume is HISTORY today and broke a 3 year trend You want to know the next BIG stock its EXPRESS clothing it's one of the most beaten down retail stocks and people search for "Express clothing" at 3.5x the rate they search "Gucci clothing"](https://www.reddit.com/r/wallstreetbets/comments/kxiyg8/your_next_stock_expr_had_highest_volume_is/)
- 2021-01-18 r/wallstreetbets (score 1): [EXPR TO THE MOON 🚀🚀🚀](https://www.reddit.com/r/wallstreetbets/comments/kzjob8/expr_to_the_moon/)
- 2021-01-14 r/pennystocks (score 0): [EXPR shot up 57% premarket](https://www.reddit.com/r/pennystocks/comments/kx52dv/expr_shot_up_57_premarket/)
- 2021-01-15 r/pennystocks (score 0): [YOUR NEXT STOCK... EXPR had highest volume is HISTORY today and broke a 3 year trend You want to know the next BIG stock its EXPRESS clothing it's one of the most beaten down retail stocks and people search for "Express clothing" at 3.5x the rate they search "Gucci clothing".](https://www.reddit.com/r/pennystocks/comments/kxiza2/your_next_stock_expr_had_highest_volume_is/)

*Gaps:* yahoo_prices: none found, sec_filings: error, polygon_news: needs key, gdelt_news: n/a, reddit: error, reddit_arctic_shift: partial (capped)

### NOK — 2021-01-21
*Reported:* WSB mentions, breakout volume ([source](https://github.com/shaunwolf/piptrack/blob/main/attached_assets/pumped_stock_cases_1749923665803.csv))
*Notes:* Large cap - useful contrast
*Measured:* multi day run starting 2021-01-21; biggest day on 2021-01-27: close 1.4x, intraday high 2.1x from $4.25; best 5-day run 1.6x. Qualifies: **no**
*Pre-pump window (10 days):* return +4%, avg volume 1.3x baseline (max day 3.0x), volatility 0.7x baseline, RSI 63, last close $3.77

| Day | Date | Close | Return | Volume vs baseline |
|---|---|---|---|---|
| -10 | 2021-01-06 | 3.63 | +0% | 1.2x |
| -9 | 2021-01-07 | 3.58 | -1% | 0.8x |
| -8 | 2021-01-08 | 3.53 | -2% | 0.8x |
| -7 | 2021-01-11 | 3.48 | -2% | 1.2x |
| -6 | 2021-01-12 | 3.60 | +4% | 0.8x |
| -5 | 2021-01-13 | 3.58 | -1% | 1.1x |
| -4 | 2021-01-14 | 3.67 | +3% | 3.0x |
| -3 | 2021-01-15 | 3.66 | -0% | 1.2x |
| -2 | 2021-01-19 | 3.71 | +1% | 1.3x |
| -1 | 2021-01-20 | 3.77 | +2% | 1.4x |

**Technical picture at the end of the window**
- Moving averages: EMA 8/21/50 stack bullish; close vs EMA21 +5%, vs WMA20 +5%, vs HMA20 +3%, vs VWMA20 +5%, vs SMA200 +3%
- Momentum: RSI 63, stochastic %K 88, MACD cross in window: yes, ADX 13, RSI bullish divergence: no
- Volatility & flow: Bollinger %B 1.09, squeeze: yes, ATR 3% of price, CMF -0.08, MFI 63, OBV accumulation divergence: no
- Fibonacci: downswing $2.88 → $4.62; close at 0.513 bounce (nearest 0.5); pump peaked at the 3.41 extension
- Structure: range (11 higher highs, 12 higher lows); support $3.37, resistance $3.85
- Harmonic patterns: none
- Chart patterns: double bottom (bullish, 2021-01-11), consolidation (neutral, 2021-01-13)
- Candlesticks: bearish harami (bearish, 2021-01-06), spinning top (neutral, 2021-01-08), gap down (bearish, 2021-01-08), bullish marubozu (bullish, 2021-01-13), gap up (bullish, 2021-01-14), spinning top (neutral, 2021-01-15), bullish engulfing (bullish, 2021-01-19), outside bar (neutral, 2021-01-19), three outside up (bullish, 2021-01-20)
- Support/resistance signals: resistance reject sell (bearish, 2021-01-14)

**Reddit** — ≥4 mentions by 3 authors, avg sentiment 0.00, mentions per day [0, 0, 0, 0, 0, 0, 0, 2, 0, 2]
- 2021-01-15 r/smallstreetbets (score 5): [(NOK) NOKIA 🚀🚀🚀🚀🚀🚀🚀](https://www.reddit.com/r/smallstreetbets/comments/ky1tp6/nok_nokia/)
- 2021-01-20 r/smallstreetbets (score 4): [NOK or APHA](https://www.reddit.com/r/smallstreetbets/comments/l0xz2k/nok_or_apha/)
- 2021-01-15 r/smallstreetbets (score 1): [Next 10bagger stock. NOK.](https://www.reddit.com/r/smallstreetbets/comments/kxl3t7/next_10bagger_stock_nok/)
- 2021-01-20 r/smallstreetbets (score 1): [Starting my NOK position🚀](https://www.reddit.com/r/smallstreetbets/comments/l12s28/starting_my_nok_position/)

*Gaps:* sec_filings: error, polygon_news: needs key, gdelt_news: n/a, reddit: error, reddit_arctic_shift: partial (capped)

### SPCE — 2021-01-26
*Reported:* meme surge plus test flight news ([source](https://github.com/shaunwolf/piptrack/blob/main/attached_assets/pumped_stock_cases_1749923665803.csv))
*Measured:* multi day run starting 2021-01-26; biggest day on 2021-01-27: close 1.1x, intraday high 1.4x from $841.00; best 5-day run 1.5x. Qualifies: **no**
*Pre-pump window (10 days):* return +43%, avg volume 1.4x baseline (max day 4.0x), volatility 1.3x baseline, RSI 72, last close $720.00

| Day | Date | Close | Return | Volume vs baseline |
|---|---|---|---|---|
| -10 | 2021-01-11 | 498.40 | -1% | 0.4x |
| -9 | 2021-01-12 | 533.20 | +7% | 0.8x |
| -8 | 2021-01-13 | 551.20 | +3% | 1.0x |
| -7 | 2021-01-14 | 660.60 | +20% | 4.0x |
| -6 | 2021-01-15 | 608.60 | -8% | 1.3x |
| -5 | 2021-01-19 | 633.00 | +4% | 1.4x |
| -4 | 2021-01-20 | 640.60 | +1% | 0.9x |
| -3 | 2021-01-21 | 665.40 | +4% | 1.0x |
| -2 | 2021-01-22 | 685.60 | +3% | 0.9x |
| -1 | 2021-01-25 | 720.00 | +5% | 2.2x |

**Technical picture at the end of the window**
- Moving averages: EMA 8/21/50 stack bullish; close vs EMA21 +23%, vs WMA20 +21%, vs HMA20 +5%, vs VWMA20 +21%, vs SMA200 +76%
- Momentum: RSI 72, stochastic %K 82, MACD cross in window: yes, ADX 30, RSI bullish divergence: no
- Volatility & flow: Bollinger %B 0.99, squeeze: no, ATR 7% of price, CMF 0.17, MFI 90, OBV accumulation divergence: no
- Fibonacci: upswing $297.20 → $777.40; close at 0.120 retracement (nearest 0.236); pump peaked at the 1.86 extension
- Structure: downtrend (8 higher highs, 10 higher lows); support $555.50, resistance –
- Harmonic patterns: none
- Chart patterns: consolidation (neutral, 2021-01-12), range breakout (bullish, 2021-01-14), bull flag (bullish, 2021-01-20), bull flag (bullish, 2021-01-21), range breakout (bullish, 2021-01-25)
- Candlesticks: doji (neutral, 2021-01-11), bullish kicker (bullish, 2021-01-12), gap up (bullish, 2021-01-14), three white soldiers (bullish, 2021-01-14), spinning top (neutral, 2021-01-20), three white soldiers (bullish, 2021-01-22), outside bar (neutral, 2021-01-25), spinning top (neutral, 2021-01-25), three white soldiers (bullish, 2021-01-25)
- Support/resistance signals: breakout buy (bullish, 2021-01-14)

**Reddit** — ≥7 mentions by 4 authors, avg sentiment 0.39, mentions per day [0, 0, 0, 1, 0, 0, 0, 0, 2, 2]
- 2021-01-25 r/stocks (score 7): [SPCE](https://www.reddit.com/r/stocks/comments/l4svbt/spce/)
- 2021-01-14 r/stocks (score 1): [ARK is going to space and SPCE rockets upwards of 20%](https://www.reddit.com/r/stocks/comments/kxfg4r/ark_is_going_to_space_and_spce_rockets_upwards_of/)
- 2021-01-16 r/stocks (score 1): [Thoughts on Virgin Galactic (SPCE)?](https://www.reddit.com/r/stocks/comments/kyhhdg/thoughts_on_virgin_galactic_spce/)
- 2021-01-16 r/smallstreetbets (score 1): [Great week 🤝 these PLTR & SPCE calls I’ve been bag holding are finally waking up](https://www.reddit.com/r/smallstreetbets/comments/kyc2rp/great_week_these_pltr_spce_calls_ive_been_bag/)
- 2021-01-22 r/smallstreetbets (score 1): [Awesome day. Jumia, SPCE, PLTR](https://www.reddit.com/r/smallstreetbets/comments/l2xvj7/awesome_day_jumia_spce_pltr/)
- 2021-01-22 r/smallstreetbets (score 1): [Thought we were going to Wendy’s PLTR, SPCE, and Jumia had other ideas.](https://www.reddit.com/r/smallstreetbets/comments/l2x9jo/thought_we_were_going_to_wendys_pltr_spce_and/)
- 2021-01-25 r/stocks (score 1): [Why SPCE isn’t spotted like GME? Only 10.000 Short Shares Available, 81.53% Short Interest. (GME was 138.08%).](https://www.reddit.com/r/stocks/comments/l4zmht/why_spce_isnt_spotted_like_gme_only_10000_short/)

*Gaps:* sec_filings: error, polygon_news: needs key, gdelt_news: n/a, reddit: error, reddit_arctic_shift: partial (capped)

### CLOV — 2021-06-07
*Reported:* meme squeeze (from memory)
*Notes:* No source yet - verify
*Measured:* multi day run starting 2021-06-07; biggest day on 2021-06-08: close 1.9x, intraday high 2.1x from $11.92; best 5-day run 2.9x. Qualifies: **no**
*Pre-pump window (10 days):* return +26%, avg volume 0.8x baseline (max day 2.1x), volatility 0.7x baseline, RSI 61, last close $9.00

| Day | Date | Close | Return | Volume vs baseline |
|---|---|---|---|---|
| -10 | 2021-05-21 | 6.93 | -3% | 0.3x |
| -9 | 2021-05-24 | 6.92 | -0% | 0.2x |
| -8 | 2021-05-25 | 7.02 | +1% | 0.2x |
| -7 | 2021-05-26 | 7.33 | +4% | 0.3x |
| -6 | 2021-05-27 | 7.83 | +7% | 1.3x |
| -5 | 2021-05-28 | 7.64 | -2% | 0.6x |
| -4 | 2021-06-01 | 7.73 | +1% | 0.4x |
| -3 | 2021-06-02 | 8.74 | +13% | 1.5x |
| -2 | 2021-06-03 | 8.94 | +2% | 2.1x |
| -1 | 2021-06-04 | 9.00 | +1% | 0.7x |

**Technical picture at the end of the window**
- Moving averages: EMA 8/21/50 stack mixed; close vs EMA21 +13%, vs WMA20 +16%, vs HMA20 +9%, vs VWMA20 +14%, vs SMA200 -15%
- Momentum: RSI 61, stochastic %K 63, MACD cross in window: yes, ADX 22, RSI bullish divergence: no
- Volatility & flow: Bollinger %B 0.96, squeeze: no, ATR 9% of price, CMF -0.12, MFI 65, OBV accumulation divergence: no
- Fibonacci: downswing $6.31 → $17.45; close at 0.241 bounce (nearest 0.236); pump peaked at the 2.02 extension
- Structure: range (4 higher highs, 4 higher lows); support –, resistance $9.15
- Harmonic patterns: none
- Chart patterns: head shoulders (bearish, 2021-06-03), consolidation (neutral, 2021-05-26)
- Candlesticks: doji (neutral, 2021-05-24), shooting star (bearish, 2021-05-25), three white soldiers (bullish, 2021-05-27), inside bar (neutral, 2021-06-01), spinning top (neutral, 2021-06-01), bullish harami (bullish, 2021-06-01), three inside up (bullish, 2021-06-02), inside bar (neutral, 2021-06-04), bullish harami (bullish, 2021-06-04)
- Support/resistance signals: resistance reject sell (bearish, 2021-06-04)

**Reddit** — ≥22 mentions by 11 authors, avg sentiment 0.28, mentions per day [0, 0, 0, 0, 0, 1, 0, 3, 9, 1]
- 2021-05-30 r/StockMarket (score 52): [All in position: AMC and CLOV](https://www.reddit.com/r/StockMarket/comments/nogmjz/all_in_position_amc_and_clov/)
- 2021-06-03 r/Daytrading (score 8): [#CLOV Stock 🔥 Are we ready to squeeze today! WHY? Chart interest coupled with high short interest!](https://www.reddit.com/r/Daytrading/comments/nrczbq/clov_stock_are_we_ready_to_squeeze_today_why/)
- 2021-05-29 r/StockMarket (score 5): [These STOCKS could receive a boost as they are added to the Russell index at the end of June. HIMS, ASTS, SFT, VLDR, RSI, HYLN, MP, Xl, TTCF, RMO, RIDE, LAZR, DNMR, OPEN, LOTZ, CHPT, NKLA, QS, FSR, DKNG, HOFT, PLBY, CLOV](https://www.reddit.com/r/StockMarket/comments/nnu1mb/these_stocks_could_receive_a_boost_as_they_are/)
- 2021-06-03 r/StockMarket (score 5): [#CLOV Stock 🔥 Are we ready to squeeze today! WHY? Chart interest coupled with high short interest!](https://www.reddit.com/r/StockMarket/comments/nrd0el/clov_stock_are_we_ready_to_squeeze_today_why/)
- 2021-05-30 r/Daytrading (score 2): [CLOV 🦍💪💎🙌🚀 - 46%+ million shares on loan, TA breaking out, added to Russell in June, unusual option activity. What else am I missing?](https://www.reddit.com/r/Daytrading/comments/nom176/clov_46_million_shares_on_loan_ta_breaking_out/)
- 2021-05-28 r/Superstonk (score 1): [GME AMC CLOV BB - The 8am coincidence](https://www.reddit.com/r/Superstonk/comments/nmxn4j/gme_amc_clov_bb_the_8am_coincidence/)
- 2021-05-30 r/stocks (score 1): [$CLOV Short Squuuueeeze potential!](https://www.reddit.com/r/stocks/comments/noe3y4/clov_short_squuuueeeze_potential/)
- 2021-05-30 r/Superstonk (score 1): [CLOV - 46%+ million shares on loan, TA breaking out, unusual option activity, added to Russell in June, Record Revenue and growth 🦍💪💎🙌🚀](https://www.reddit.com/r/Superstonk/comments/nomdgc/clov_46_million_shares_on_loan_ta_breaking_out/)

*Gaps:* sec_filings: error, polygon_news: needs key, gdelt_news: n/a, reddit: error, reddit_arctic_shift: partial (capped)

### MMAT — 2021-07-06
*Reported:* TRCH merger squeeze (from memory)
*Notes:* No source yet - verify
*Measured:* multi day run starting 2021-07-06; biggest day: close 1.1x, intraday high 1.2x from $6.74; best 2-day run 1.1x. Qualifies: **no**

**Reddit** — ≥1 mentions by 1 authors, avg sentiment 0.03, mentions per day [1, 0, 0, 0, 0]
- 2021-06-28 r/pennystocks (score 5): [4x2=8 MMAT and why it matters.....](https://www.reddit.com/r/pennystocks/comments/o9lj90/4x28_mmat_and_why_it_matters/)

*Gaps:* yahoo_prices: none found, sec_filings: error, polygon_news: needs key, gdelt_news: n/a, reddit: error, reddit_arctic_shift: partial (capped)

### IRNT — 2021-09-03
*Reported:* de-SPAC low-float squeeze (from memory)
*Notes:* No source yet - verify
*Measured:* multi day run starting 2021-09-03; biggest day on 2021-09-07: close 1.2x, intraday high 1.8x from $16.52; best 5-day run 2.4x. Qualifies: **no**

**Reddit** — ≥3 mentions by 3 authors, avg sentiment 0.79, mentions per day [0, 1, 0, 0, 2]
- 2021-09-02 r/Shortsqueeze (score 322): [IRNT Gamma Squeeze Set Up](https://www.reddit.com/r/Shortsqueeze/comments/pgo23x/irnt_gamma_squeeze_set_up/)
- 2021-09-02 r/smallstreetbets (score 108): [$IRNT - IronNet Cyber Security, potentially extraordinary market dynamics at play, the hole in the liquidity rulebook](https://www.reddit.com/r/smallstreetbets/comments/pgs07x/irnt_ironnet_cyber_security_potentially/)
- 2021-08-30 r/Shortsqueeze (score 19): [IRNT float is below 2mil shares. Short ban in place](https://www.reddit.com/r/Shortsqueeze/comments/peoybj/irnt_float_is_below_2mil_shares_short_ban_in_place/)

*Gaps:* yahoo_prices: none found, sec_filings: error, polygon_news: needs key, gdelt_news: n/a, reddit: error, reddit_arctic_shift: partial (capped)

### SPRT — 2021-08-26
*Reported:* short squeeze (from memory)
*Notes:* No source yet - verify; merged into Greenidge
*Measured:* multi day run starting 2021-08-26; biggest day on 2021-08-27: close 1.3x, intraday high 3.0x from $19.65; best 5-day run 3.3x. Qualifies: **no**
*Pre-pump window (10 days):* return +95%, avg volume 7.7x baseline (max day 20.9x), volatility 1.2x baseline, RSI 82, last close $13.92

| Day | Date | Close | Return | Volume vs baseline |
|---|---|---|---|---|
| -10 | 2021-08-12 | 7.91 | +11% | 1.7x |
| -9 | 2021-08-13 | 8.12 | +3% | 20.2x |
| -8 | 2021-08-16 | 7.83 | -4% | 2.1x |
| -7 | 2021-08-17 | 8.35 | +7% | 1.8x |
| -6 | 2021-08-18 | 8.13 | -3% | 1.2x |
| -5 | 2021-08-19 | 8.76 | +8% | 1.3x |
| -4 | 2021-08-20 | 8.75 | -0% | 7.5x |
| -3 | 2021-08-23 | 11.17 | +28% | 8.2x |
| -2 | 2021-08-24 | 11.60 | +4% | 20.9x |
| -1 | 2021-08-25 | 13.92 | +20% | 12.3x |

**Technical picture at the end of the window**
- Moving averages: EMA 8/21/50 stack bullish; close vs EMA21 +62%, vs WMA20 +53%, vs HMA20 +33%, vs VWMA20 +40%, vs SMA200 +285%
- Momentum: RSI 82, stochastic %K 87, MACD cross in window: yes, ADX 51, RSI bullish divergence: no
- Volatility & flow: Bollinger %B 1.25, squeeze: no, ATR 11% of price, CMF -0.34, MFI 97, OBV accumulation divergence: no
- Fibonacci: upswing $1.97 → $15.05; close at 0.086 retracement (nearest 0); pump peaked at the 4.41 extension
- Structure: uptrend (9 higher highs, 10 higher lows); support $9.38, resistance –
- Harmonic patterns: none
- Chart patterns: range breakout (bullish, 2021-08-23), range breakout (bullish, 2021-08-24)
- Candlesticks: bullish engulfing (bullish, 2021-08-12), outside bar (neutral, 2021-08-12), piercing line (bullish, 2021-08-17), gravestone doji (bearish, 2021-08-18), bearish harami (bearish, 2021-08-18), inside bar (neutral, 2021-08-19), spinning top (neutral, 2021-08-25), three white soldiers (bullish, 2021-08-25)
- Support/resistance signals: breakout buy (bullish, 2021-08-23)

**Reddit** — ≥6 mentions by 4 authors, avg sentiment 0.38, mentions per day [1, 1, 0, 0, 1, 0, 0, 1, 2, 0]
- 2021-08-18 r/smallstreetbets (score 23): [Understanding The SI% Data Behind $SPRT](https://www.reddit.com/r/smallstreetbets/comments/p6kv4t/understanding_the_si_data_behind_sprt/)
- 2021-08-23 r/smallstreetbets (score 18): [$SPRT AWARENESS](https://www.reddit.com/r/smallstreetbets/comments/pa834i/sprt_awareness/)
- 2021-08-13 r/smallstreetbets (score 2): [Update: Which stocks have the best chance to squeeze? = XELA, SPRT and GEO (see comments for explanation).](https://www.reddit.com/r/smallstreetbets/comments/p3najf/update_which_stocks_have_the_best_chance_to/)
- 2021-08-12 r/smallstreetbets (score 1): [Update: Which stocks have the best chance to squeeze? = XELA, SPRT and GEO (see comments for further explanation).](https://www.reddit.com/r/smallstreetbets/comments/p36x5g/update_which_stocks_have_the_best_chance_to/)
- 2021-08-24 r/smallstreetbets (score 1): [Who ready to have some fun (Not advise LOL) SPRT to the moon! 🚀🚀🚀](https://www.reddit.com/r/smallstreetbets/comments/pauxqh/who_ready_to_have_some_fun_not_advise_lol_sprt_to/)
- 2021-08-24 r/smallstreetbets (score 1): [$SPRT gains.](https://www.reddit.com/r/smallstreetbets/comments/pagjsx/sprt_gains/)

*Gaps:* yahoo_prices: none found, sec_filings: error, polygon_news: needs key, gdelt_news: n/a, reddit: error, reddit_arctic_shift: partial (capped)
