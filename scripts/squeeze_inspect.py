"""
Fetch a sample from every squeeze data source (needs internet; run from CI) and record
status codes, sizes and the first lines, so the parsers can be checked against real files.
Writes squeeze_inspect/report.json plus one text sample per source.
"""

import io
import json
import os
import zipfile

import requests

OUT = "squeeze_inspect"
UA = os.environ.get("SEC_USER_AGENT") or "PipSqueak research admin@example.com"
H = {"User-Agent": UA, "Accept-Encoding": "gzip, deflate"}

URLS = {
    "finra_cnms_recent": "https://cdn.finra.org/equity/regsho/daily/CNMSshvol20251031.txt",
    "finra_cnms_2021": "https://cdn.finra.org/equity/regsho/daily/CNMSshvol20210113.txt",
    "finra_cnms_2018": "https://cdn.finra.org/equity/regsho/daily/CNMSshvol20180904.txt",
    "finra_cnms_2017": "https://cdn.finra.org/equity/regsho/daily/CNMSshvol20171201.txt",
    "finra_nasdaq_2017": "https://cdn.finra.org/equity/regsho/daily/FNSQshvol20171201.txt",
    "nasdaq_threshold_recent": "https://www.nasdaqtrader.com/dynamic/symdir/regsho/nasdaqth20251031.txt",
    "nasdaq_threshold_2021": "https://www.nasdaqtrader.com/dynamic/symdir/regsho/nasdaqth20210113.txt",
    "nasdaq_threshold_2017": "https://www.nasdaqtrader.com/dynamic/symdir/regsho/nasdaqth20171201.txt",
    "nyse_threshold_a": "https://www.nyse.com/api/regulatory/threshold-securities/download?selectedDate=31-Oct-2025&market=NYSE",
    "nyse_threshold_b": "https://www.nyse.com/api/regulatory/threshold-securities/download?market=NYSE&selectedDate=2025-10-31",
    "apewisdom": "https://apewisdom.io/api/v1.0/filter/all-stocks/page/1",
    "sec_ftd_2021a": "https://www.sec.gov/files/data/fails-deliver-data/cnsfails202101a.zip",
    "sec_ftd_recent": "https://www.sec.gov/files/data/fails-deliver-data/cnsfails202509b.zip",
    "finra_short_interest_file": "https://cdn.finra.org/equity/otcmarket/biweekly/shrt20251015.csv",
}


def main():
    os.makedirs(OUT, exist_ok=True)
    report = {}
    for key, url in URLS.items():
        try:
            r = requests.get(url, headers=H, timeout=40)
            body = r.content
            entry = {"url": url, "status": r.status_code, "bytes": len(body), "type": r.headers.get("content-type")}
            text = ""
            if url.endswith(".zip") and r.status_code == 200:
                with zipfile.ZipFile(io.BytesIO(body)) as z:
                    name = z.namelist()[0]
                    entry["zip_member"] = name
                    text = z.read(name).decode("latin-1")
            else:
                text = body.decode("utf-8", "replace")
            lines = text.splitlines()
            entry["lines"] = len(lines)
            entry["head"] = lines[:8]
            entry["tail"] = lines[-3:]
            with open(os.path.join(OUT, f"{key}.txt"), "w") as f:
                f.write("\n".join(lines[:60]))
        except Exception as e:
            entry = {"url": url, "error": f"{type(e).__name__}: {e}"}
        report[key] = entry
        print(key, entry.get("status"), entry.get("bytes"), entry.get("error", ""))

    # FINRA's query API for consolidated short interest (public dataset)
    try:
        r = requests.post("https://api.finra.org/data/group/otcMarket/name/consolidatedShortInterest",
                          json={"limit": 3, "compareFilters": [{"compareType": "EQUAL", "fieldName": "symbolCode", "fieldValue": "GME"}]},
                          headers={"Accept": "application/json"}, timeout=40)
        report["finra_api_short_interest"] = {"status": r.status_code, "body": r.text[:1500]}
    except Exception as e:
        report["finra_api_short_interest"] = {"error": str(e)}

    # yfinance: short interest fields and an option chain
    try:
        import yfinance as yf
        t = yf.Ticker("GME")
        info = t.info
        report["yf_info"] = {k: info.get(k) for k in ("sharesShort", "shortPercentOfFloat", "shortRatio", "floatShares",
                                                     "sharesOutstanding", "sharesShortPriorMonth", "dateShortInterest",
                                                     "exchange", "quoteType", "marketCap", "averageVolume")}
        exps = t.options
        report["yf_options"] = {"expirations": list(exps[:6])}
        if exps:
            ch = t.option_chain(exps[0])
            report["yf_options"]["call_columns"] = list(ch.calls.columns)
            report["yf_options"]["calls_head"] = ch.calls.head(3).astype(str).to_dict("records")
    except Exception as e:
        report["yf"] = {"error": f"{type(e).__name__}: {e}"}

    with open(os.path.join(OUT, "report.json"), "w") as f:
        json.dump(report, f, indent=2, default=str)


if __name__ == "__main__":
    main()
