# PipSqueak (Piptrack)

This is a Flask web app for stock traders. It includes:
- a market scanner, confidence scores and price-path forecasts
- a trading journal with progress tracking
- **Pump Research**, which studies what happened in the 1–2 weeks before extreme price spikes, using a full technical analysis engine

See [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) for what's in the app and its current state, and [pump_research/README.md](pump_research/README.md) for the research toolkit.

## Run it locally

You need Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync                                   # install dependencies (including test tools)
cp .env.example .env                      # optional settings; export them with: set -a; . ./.env; set +a
uv run gunicorn --bind 0.0.0.0:5000 main:app
```

Open http://localhost:5000 and register an account.
- With no `DATABASE_URL` set, the app uses a local SQLite file (`instance/pipsqueak.db`).
- Market data comes from Yahoo Finance, so the machine needs internet access.
- `DISABLE_BACKGROUND_SCANNER=1` turns off the background market scanner threads.

## Test it

```bash
uv run ruff check .                       # lint (errors only: syntax, undefined names, unused imports)
uv run python -m pytest tests             # 40 offline tests, no network needed
```

GitHub Actions runs both on every push and pull request (`.github/workflows/ci.yml`).

## Collect real pump data

The research needs internet access to Yahoo Finance, SEC EDGAR and the Reddit archive. There are two ways to run it.

**On your machine**
```bash
export SEC_USER_AGENT="Your Name you@example.com"   # SEC asks for a contact
uv run python -m pump_research check                 # which sources are reachable
uv run python -m pump_research collect               # research the candidates in pump_research/seeds.csv
uv run python -m pump_research train                 # fit the pre-pump similarity model
uv run python -m pump_research score GME             # score a ticker today
```

**On GitHub** (no local setup): run the **Collect pump data** workflow from the Actions tab, or add the `collect-data` label to a pull request. It runs the same commands on GitHub's servers and:
- uploads the results as a workflow artifact;
- pushes them to the `pump-data` branch, where the web app and Claude Code sessions can pick them up (`git fetch origin pump-data && git archive origin/pump-data | tar -x -C pump_data`).

Optional repository settings (Settings → Secrets and variables → Actions):
- the `SEC_USER_AGENT` variable (your name and email, for SEC's fair-access policy);
- the `POLYGON_API_KEY` secret (adds delisted tickers and news history).

Results land in `pump_data/`: the combined `pump_dataset.json`, `pump_summary.csv`, `pump_report.md` and `model.json`. The **Pump Research** page in the app reads that folder.

## Claude Code on the web

`.claude/hooks/session-start.sh` runs at the start of every cloud session. It installs dependencies with `uv sync` and pulls the latest `pump-data` results, so tests and the research pages work right away.
