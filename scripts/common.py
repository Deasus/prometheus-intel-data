"""Shared helpers for prometheus-intel-data fetchers.

Every fetcher writes a slim JSON to data/<name>.json in the PanelPayload-adjacent
shape the frontend consumes. We keep the RAW upstream shape out of the repo — only
the fields the CYBER/KINETIC panels + AI need. Fail LOUD (non-zero exit) so a broken
feed shows up in GHA rather than silently publishing garbage.
"""
from __future__ import annotations
import json, sys, urllib.request, urllib.error, datetime, html, re

UA = "prometheus-doi-intel/1.0 (+https://github.com/Deasus/prometheus-intel-data)"


def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get(url: str, timeout: int = 40, accept: str | None = None) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, **({"Accept": accept} if accept else {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def get_json(url: str, timeout: int = 40):
    return json.loads(get(url, timeout, accept="application/json"))


def strip_html(s: str) -> str:
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", "", s)
    return html.unescape(s).strip()


def write(name: str, payload: dict) -> None:
    """Write data/<name>.json with a stable, pretty-ish (compact) form."""
    payload.setdefault("generated", now_iso())
    payload.setdefault("version", "v1")
    path = f"data/{name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    print(f"WROTE {path}  ({len(payload.get('items', []))} items, "
          f"{sum(1 for _ in json.dumps(payload))} bytes-ish)")


def fail(msg: str) -> "NoReturn":  # type: ignore[valid-type]
    print(f"FATAL: {msg}", file=sys.stderr)
    sys.exit(1)
