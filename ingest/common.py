"""Shared helpers for all ingest modules: HTTP with retry/backoff, raw paths, manifest."""
from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
MANIFEST = RAW / "manifest.json"

log = logging.getLogger("ingest")

# FRED blocks browser-like user agents from this network, so default to a plain UA.
PLAIN_UA = "tradewar-analytics/1.0 (+https://github.com/nishanttyagi28)"
BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)


def load_env() -> None:
    """Load E:/da-flagship/.env if present (never printed)."""
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def http_get(url: str, *, params=None, headers=None, ua: str = PLAIN_UA, retries: int = 4,
             timeout: int = 60, method: str = "GET", json_body=None) -> requests.Response:
    """GET/POST with exponential backoff on network errors, 429 and 5xx."""
    h = {"User-Agent": ua}
    if headers:
        h.update(headers)
    last = None
    for attempt in range(retries):
        try:
            r = requests.request(method, url, params=params, headers=h, timeout=timeout, json=json_body)
            if r.status_code == 429 or r.status_code >= 500:
                raise requests.HTTPError(f"HTTP {r.status_code}", response=r)
            r.raise_for_status()
            return r
        except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
            last = e
            resp = getattr(e, "response", None)
            if resp is not None and 400 <= resp.status_code < 500 and resp.status_code != 429:
                raise
            wait = 2 ** attempt * 2
            log.warning("retry %s/%s for %s (%s); sleeping %ss", attempt + 1, retries, url[:90], e, wait)
            time.sleep(wait)
    raise RuntimeError(f"failed after {retries} retries: {url[:120]}") from last


def raw_dir(source: str) -> Path:
    p = RAW / source
    p.mkdir(parents=True, exist_ok=True)
    return p


def save(df: pd.DataFrame, source: str, name: str) -> Path:
    """Write a raw snapshot as Parquet (overwrites -> idempotent)."""
    p = raw_dir(source) / f"{name}.parquet"
    df.to_parquet(p, index=False)
    return p


def save_bytes(content: bytes, source: str, filename: str) -> Path:
    p = raw_dir(source) / filename
    p.write_bytes(content)
    return p


def record(source: str, name: str, df: pd.DataFrame | None, *, url: str, date_col: str | None = None,
           status: str = "ok", note: str = "") -> dict:
    """Append/replace a manifest entry for a dataset."""
    entry = {
        "source": source,
        "dataset": name,
        "url": url,
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rows": int(len(df)) if df is not None else 0,
        "status": status,
        "note": note,
    }
    if df is not None and date_col and date_col in df.columns and len(df):
        d = pd.to_datetime(df[date_col], errors="coerce")
        entry["min_date"] = str(d.min().date()) if d.notna().any() else None
        entry["max_date"] = str(d.max().date()) if d.notna().any() else None
    RAW.mkdir(parents=True, exist_ok=True)
    data = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    data[f"{source}/{name}"] = entry
    MANIFEST.write_text(json.dumps(data, indent=2, sort_keys=True))
    log.info("%s/%s rows=%s %s", source, name, entry["rows"], status)
    return entry
