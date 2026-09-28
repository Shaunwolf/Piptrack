# PipSqueak (Piptrack): Project Overview

*Written September 2026 after a review and debugging pass. The last feature work was June 2025, built mostly with the Replit Agent.*

## What it is

**PipSqueak** is a web app for stock traders. It scans the US stock market for setups, scores them, draws possible price paths, and gives you a trading journal with game-style progress tracking. The pitch on the landing page is "AI-driven stock analysis" with a **closed beta of 100 users**. Each new signup gets a beta number, and the landing page shows how many spots are left.

It's a server-rendered **Flask** app (Jinja templates, Tailwind CSS from a CDN, Plotly charts, vanilla JS). It pulls market data from **Yahoo Finance via `yfinance`** and stores data in **PostgreSQL** (SQLite works for local testing).

> **Honest note on the "AI":** most of the analysis is rule-based technical analysis, not machine learning. It uses RSI, MACD, Bollinger Bands, volume spikes and Fibonacci levels, mostly via the `ta` library. Only one feature calls an LLM: the one-paragraph "AI insight" on personalized recommendations, which uses OpenAI `gpt-4o`. Without an API key it falls back to template text.

## Features that work today

| Feature | URL | What it does | Main code |
|---|---|---|---|
| Landing page | `/` (logged out) | Marketing page and beta counter | `templates/landing.html` |
| Accounts | `/register`, `/login`, `/profile`, `/settings` | Email/password auth with Flask-Login | `auth_forms.py`, `models.User` |
| Dashboard | `/`, `/dashboard` | Your tracked stocks and recent journal entries | `templates/index.html` |
| **AI Picks** (in the nav) | `/recommendations_dashboard`, `/recommendation_setup` | Personalized stock suggestions scored on technical, fundamental, sentiment and fit to your profile | `personalized_recommender.py` |
| **Journal** (in the nav) | `/journal` | Trade journal with a "notebook" look: entry, stop, target, mood, reflections | `templates/journal_clean.html` |
| Forecast | `/forecast/<SYM>`, `/forecast_enhanced/<SYM>` | "Spaghetti model" with 4 possible 5-day price paths (momentum, retest, breakdown, sideways) and their probabilities | `forecasting_engine.py` |
| Confidence score | used everywhere | A 0–100 score: weighted mix of RSI, volume surge, pattern, Fibonacci position, trend and volatility | `confidence_scorer.py` |
| AI coach | `/ai_review/<SYM>`, `/chart_story/<SYM>` | Rule-based commentary: pattern detection, mood tag ("breakout", "risky"…), chart annotations, voice-alert text | `ai_coach.py` |
| Pattern evolution | `/pattern_evolution/<SYM>`, `/pattern_dashboard` | Tracks patterns like bull flags and wedges: stage, completion %, breakout odds | `pattern_evolution_tracker.py` |
| Trading journey | `/api/trading_journey*` | XP, levels, achievements, leaderboard | `trading_journey.py`, `animated_trading_journey.py` |
| Widgets / sparklines | `/widgets`, `/api/sparkline/<SYM>` | Mini charts with an animated "candle guy" mascot | `stock_widgets.py`, `animated_sparklines.py` |
| Background market scanner | `/api/background-scan/*`, `/api/market/*` | Threads that scan hardcoded lists of tickers every 1, 5 and 30 minutes and cache the results | `background_scanner.py`, `market_data_engine.py` |
| Stock scanner | `/scanner`, `/scanner_dashboard` | Top gappers and technical screen. **Hidden from the nav** ("until fully operational") | `stock_scanner.py`, `scanner_monitor.py` |
| Exports | `/export_weekly_report` | PDF report (`pdfkit`) and Google Sheets sync (`gspread`). Both need extra setup | `pdf_generator.py`, `google_sheets_integration.py` |

## Features that are broken (backend code deleted)

On 15 June 2025, commit `0d37565` ("Remove old pump detection files") deleted 9 Python modules. **About 20 routes still import them** and return `{"error": "No module named …"}`:

- **Pump detection / backtesting:** `/backtest`, `/pump-analysis`, `/early_detection`, `/historical_backtest`, `/enhanced_detector` and their `/api/…` endpoints. These were meant to spot stocks about to jump 75%+ in a few days, and were tested against the case list in `attached_assets/pumped_stock_cases_*.csv`.
- **Physics view and widget presets** (`/physics/<SYM>`, `/api/physics/*`, `/api/widgets`): `physics_market_engine.py` and `scanner_widgets.py` were deleted, so these endpoints now answer "not available".
- **Historical comparison** (`/api/historical-comparison/<SYM>`, and "similar to META's Nov 2022 bottom" text in the AI coach). It quietly falls back to generic text.
- **Biotech catalysts and options flow** scans.

**Backtest** and **Pump Analysis** were still linked in the main nav, so users could click straight into broken pages. They're hidden now. To bring them back, restore the files from git (`git show 0d37565^:simple_pump_analyzer.py > simple_pump_analyzer.py`, etc.) or delete the dead routes and templates.

**Replaced by `pump_research/`** (see `pump_research/README.md`). It researches the 1–2 weeks before extreme pumps (prices, SEC filings, news, Reddit), runs a full technical analysis engine over each window, compares those windows with ordinary periods, and trains a similarity model. In the app it's the **Pump Research** nav item (`/pump-research`), with an event dossier and a live ticker scan. The 23 dead pump routes and their 4 templates are gone, and the old URLs redirect to the new dashboard. It still needs network access to its data sources before it can collect real data.

## How the code is laid out

```
main.py              entry point: imports app + routes (gunicorn runs main:app)
app.py               Flask app, SQLAlchemy, Flask-Login setup; creates tables on start
models.py            User, Stock, TradeJournal, StockRecommendation, PatternEvolution,
                     ForecastPath, AIAnalysis, ScanResult
routes.py            ~2,500 lines, most routes; also builds every engine at import
                     time and starts the background scanner threads (DISABLE_BACKGROUND_SCANNER=1 skips them)
pump_routes.py       Pump Research pages (Flask blueprint)
pump_research/       pump research toolkit + technical analysis engine (technicals/)
tests/               pytest suite (uv run python -m pytest tests)
*_engine.py, *_scanner.py, *_tracker.py, ai_coach.py, ...   analysis modules (one class each)
templates/           Jinja pages (base.html has the nav)
static/js/           page scripts (forecast, journal, AI coach avatar, voice alerts, ...)
attached_assets/     old Replit prompts/specs, screenshots, the pump case CSV
```

## Running it

```bash
uv sync                                     # installs dependencies from uv.lock
export DATABASE_URL=postgresql://...        # optional: defaults to SQLite at instance/pipsqueak.db
export SESSION_SECRET=change-me             # required in production
export OPENAI_API_KEY=...                   # optional, enables AI insights
uv run gunicorn --bind 0.0.0.0:5000 main:app
```

Market data needs outbound access to Yahoo Finance. Importing `routes.py` starts the background scanner threads right away, so every gunicorn worker runs its own scanner.

## What this review fixed

1. **App crashed on startup without `OPENAI_API_KEY`.** The OpenAI client is now created only when a key is set, and insights fall back to template text otherwise.
2. **Journal saves always failed.** `/journal/save` and `/add_trade` never set `user_id`, which the database requires. Both now require login and save the entry under the current user. They also used to accept requests from anyone.
3. **Settings and Edit Profile pages crashed** (`csrf_token` undefined, `hasattr` in a template, and a link to a `delete_account` route that doesn't exist). The delete button now says deletion isn't available yet.
4. **User menu links went to missing pages** (Preferences, Subscription, Help). Preferences now goes to Settings, the other two show a simple placeholder, and `/ai-picks` redirects to the recommendations page.
5. **Sparkline API called a method that doesn't exist** (`generate_sparkline` instead of `generate_sparkline_data`).
6. **Two Flask-Login managers.** `routes.py` quietly replaced the one set up in `app.py`, so the duplicate is gone.
7. **Nav linked to broken pump pages.** They're hidden now (see above).
8. **Runtime data was committed to git.** The stale SQLite DB (old schema, no user data), ~200 `market_cache/*.pkl` files and `scan_results.json` are no longer tracked, and `.gitignore` covers them.

Verified by logging in and requesting every GET route with Flask's test client. All pages load except the ones that depend on deleted modules. Registration, login, settings, profile editing and journal saves were tested end to end.

## Known issues worth tackling next

- **Collect real pump data:** open the session's network access (and optionally add a Polygon key), then run `pump_research collect` and `train`.
- **Plotly is pinned to `plotly-latest.min.js`**, which has been frozen at v1.58 since 2021. Upgrading means checking the older charts for v2 changes.
- **`/api/historical-comparison/<SYM>`** still imports a deleted module (the AI coach falls back to generic text).
- **Security:**
  - `SESSION_SECRET` falls back to a hardcoded `"dev-secret-key"`.
  - Most `/api/*` routes need no login, including `/api/market/cache/clear` and `/api/background-scan/force/*`, which let anyone wipe the cache or start expensive scans with a plain GET.
  - Only the login and register forms are CSRF-protected.
  - `edit_profile` lets you change your email without checking the format or uniqueness.
  - `main.py` runs with `debug=True` when started directly.
- **Recommendations use made-up history.** `PersonalizedRecommender._get_user_trading_history` returns hardcoded sample trades instead of reading your journal.
- **Some output is random:** the "sideways" forecast path uses `np.random`, and the fallback scanner shuffles a curated list. The same stock can show different results on reload.
- **`routes.py` is huge:** about 2,900 lines, and it builds each engine twice (once in a `try` block at the top and again around line 140). Splitting it into Flask blueprints (auth, journal, analysis, api) would make it much easier to work on.
- **Tests cover only the pump research toolkit and its pages.** CI (`.github/workflows/ci.yml`) runs lint, tests and an app boot check; see `README.md` for setup.
- **Duplicate templates** (`journal.html`, `journal_new.html`, `journal_clean.html`). Only `journal_clean.html` is used.
