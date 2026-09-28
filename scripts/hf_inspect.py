"""
Inspect Hugging Face repositories and run Hub searches (needs internet; run from CI).

Writes hf_inspect/report.json plus one Markdown file per repository with its
metadata, file list, README, dataset sample rows and (for Spaces) app code.
"""

import json
import os
import sys
import time

import requests

HUB = "https://huggingface.co"
VIEWER = "https://datasets-server.huggingface.co"
OUT = "hf_inspect"
HEADERS = {"User-Agent": "PipSqueak-hf-inspect/1.0"}

REPOS = [
    ("model", "foduucom/stockmarket-pattern-detection-yolov8"),
    ("model", "rohanjain2312/candlestick-pattern-recognition-system-yolo"),
    ("dataset", "rohanjain2312/candlestick-pattern-recognition-system-data"),
    ("space", "Rodri1970/MultiSignal-Trader"),
    ("model", "tuankg1028/candlefusion"),
    ("dataset", "Sentdex/wsb_reddit_v001"),
    ("dataset", "kowalsky/reddit_about_money"),
    ("dataset", "mito0o852/OHLCV-1m"),
    # Second round: pattern resources
    ("model", "JONNYVERSE/stockmarket-pattern-detection-yolov8-onnx"),
    ("dataset", "jadhavmanasi70/chart-pattern-nse"),
    ("dataset", "usamaahmedsh/synthetic-elliott-waves"),
    ("dataset", "THULab/elliott_wave_market_data"),
    ("space", "tosin2013/fibonacci_price_target"),
]

SEARCHES = ["harmonic pattern", "harmonic", "gartley", "candlestick", "candlestick pattern", "chart pattern",
            "price action", "stock pattern", "technical analysis", "bollinger", "fibonacci", "gann", "elliott wave",
            "support resistance", "trading signals", "stock chart"]
CODE_FILES = ("app.py", "requirements.txt", "main.py", "inference.py", "predict.py", "model.py", "config.json",
              "data.yaml", "dataset.yaml", "args.yaml", "metadata.yaml", "labels.txt", "classes.txt",
              "utils.py", "fibonacci.py")


def get(url, **kw):
    for attempt in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30, **kw)
            if r.status_code == 429:
                time.sleep(5 * (attempt + 1))
                continue
            return r
        except requests.RequestException as e:
            err = e
            time.sleep(2)
    raise err


def text(url, limit=12000):
    r = get(url)
    return r.text[:limit] if r.status_code == 200 else None


def repo_prefix(kind, rid):
    return {"model": f"{HUB}/{rid}", "dataset": f"{HUB}/datasets/{rid}", "space": f"{HUB}/spaces/{rid}"}[kind]


def inspect(kind, rid):
    api = {"model": "models", "dataset": "datasets", "space": "spaces"}[kind]
    info_r = get(f"{HUB}/api/{api}/{rid}")
    info = info_r.json() if info_r.status_code == 200 else {"error": info_r.status_code}
    tree_r = get(f"{HUB}/api/{api}/{rid}/tree/main", params={"recursive": "true"})
    tree = tree_r.json() if tree_r.status_code == 200 else []
    files = [{"path": f.get("path"), "size": f.get("size"), "type": f.get("type")} for f in tree if isinstance(f, dict)][:400]
    prefix = repo_prefix(kind, rid)
    out = {"kind": kind, "id": rid, "url": prefix,
           "meta": {k: info.get(k) for k in ("pipeline_tag", "library_name", "tags", "downloads", "likes", "sdk",
                                             "cardData", "lastModified", "gated", "private", "error") if k in info},
           "files": files, "readme": text(f"{prefix}/raw/main/README.md"), "code": {}}
    names = {f["path"] for f in files}
    for name in CODE_FILES:
        if name in names:
            out["code"][name] = text(f"{prefix}/raw/main/{name}", 20000)
    # Small code/config files anywhere in the repo
    for f in files:
        p = f["path"] or ""
        if p.endswith((".py", ".yaml", ".yml")) and (f.get("size") or 0) < 60000 and p not in out["code"] and len(out["code"]) < 12:
            out["code"][p] = text(f"{prefix}/raw/main/{p}", 15000)
    if kind == "dataset":
        sp = get(f"{VIEWER}/splits", params={"dataset": rid})
        out["splits"] = sp.json() if sp.status_code == 200 else {"error": sp.status_code, "body": sp.text[:300]}
        rows = []
        for s in (out["splits"].get("splits") or [])[:2]:
            fr = get(f"{VIEWER}/first-rows", params={"dataset": rid, "config": s["config"], "split": s["split"]})
            if fr.status_code == 200:
                j = fr.json()
                rows.append({"config": s["config"], "split": s["split"], "features": j.get("features"),
                             "rows": [r["row"] for r in j.get("rows", [])[:5]]})
            else:
                rows.append({"config": s["config"], "split": s["split"], "error": fr.status_code, "body": fr.text[:300]})
        out["first_rows"] = rows
        # Peek at CSV heads directly (for datasets the viewer can't parse)
        for f in files:
            p = f["path"] or ""
            if p.endswith(".csv") and len(out.setdefault("csv_heads", {})) < 3:
                r = get(f"{prefix}/resolve/main/{p}", stream=True)
                if r.status_code == 200:
                    chunk = next(r.iter_content(4096), b"")
                    out["csv_heads"][p] = chunk.decode("utf-8", "replace").splitlines()[:6]
    return out


def search(query):
    res = {}
    for api in ("models", "datasets", "spaces"):
        r = get(f"{HUB}/api/{api}", params={"search": query, "sort": "downloads", "direction": -1, "limit": 25, "full": "true"})
        items = r.json() if r.status_code == 200 else []
        res[api] = [{"id": i.get("id"), "downloads": i.get("downloads"), "likes": i.get("likes"),
                     "pipeline_tag": i.get("pipeline_tag"), "tags": (i.get("tags") or [])[:12],
                     "lastModified": i.get("lastModified"),
                     "description": ((i.get("cardData") or {}).get("description") or i.get("description") or "")[:300]}
                    for i in items]
    return res


def main():
    os.makedirs(OUT, exist_ok=True)
    report = {"repos": [], "searches": {}}
    for kind, rid in REPOS:
        try:
            data = inspect(kind, rid)
        except Exception as e:
            data = {"kind": kind, "id": rid, "error": f"{type(e).__name__}: {e}"}
        report["repos"].append(data)
        with open(os.path.join(OUT, rid.replace("/", "__") + ".md"), "w") as f:
            f.write(f"# {rid} ({kind})\n\n```json\n{json.dumps({k: v for k, v in data.items() if k not in ('readme', 'code')}, indent=2)[:30000]}\n```\n")
            f.write(f"\n## README\n\n{data.get('readme') or '(none)'}\n")
            for name, body in (data.get("code") or {}).items():
                f.write(f"\n## {name}\n\n```\n{body}\n```\n")
        print(rid, "files:", len(data.get("files", [])), "error:", data.get("error"))
    for q in SEARCHES:
        report["searches"][q] = search(q)
        print("search", q, {k: len(v) for k, v in report["searches"][q].items()})
    with open(os.path.join(OUT, "report.json"), "w") as f:
        json.dump(report, f, indent=1, default=str)


if __name__ == "__main__":
    sys.exit(main())
