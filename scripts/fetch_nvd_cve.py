"""NIST NVD recent CVEs -> data/cyber-nvd.json.

Anonymous (NVD 2.0 API; anon rate limit ~5 req/30s — one call per cron is fine).
Pull CVEs modified in the last 3 days, keep the highest-severity ~40.
"""
from __future__ import annotations
import datetime
from common import get_json, write, fail

BASE = "https://services.nvd.nist.gov/rest/json/cves/2.0"


def sev_tone(score):
    try:
        s = float(score)
    except (TypeError, ValueError):
        return "neutral"
    if s >= 9.0:
        return "critical"
    if s >= 7.0:
        return "elevated"
    if s >= 4.0:
        return "moderate"
    return "info"


def base_score(cve):
    m = cve.get("metrics", {})
    for k in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        arr = m.get(k)
        if arr:
            data = arr[0].get("cvssData", {})
            return data.get("baseScore"), data.get("baseSeverity", "")
    return None, ""


def main() -> None:
    end = datetime.datetime.utcnow()
    start = end - datetime.timedelta(days=3)
    url = (f"{BASE}?lastModStartDate={start.strftime('%Y-%m-%dT00:00:00.000')}"
           f"&lastModEndDate={end.strftime('%Y-%m-%dT%H:%M:%S.000')}&resultsPerPage=200")
    try:
        d = get_json(url, timeout=50)
    except Exception as e:  # noqa: BLE001
        fail(f"NVD fetch failed: {e}")

    vulns = d.get("vulnerabilities") or []
    total = d.get("totalResults", len(vulns))
    if not vulns:
        # Not fatal — a quiet window is legitimate. Publish empty-but-ok.
        write("cyber-nvd", {
            "domain": "cyber", "source": "nvd-cve", "status": "empty",
            "headline": {"label": "NEW CVEs (3d)", "value": "0", "tone": "neutral"},
            "metrics": [], "items": [], "attribution": "NIST National Vulnerability Database",
        })
        return

    scored = []
    crit = high = 0
    for w in vulns:
        cve = w.get("cve", {})
        score, sev = base_score(cve)
        if sev == "CRITICAL":
            crit += 1
        elif sev == "HIGH":
            high += 1
        desc = ""
        for dd in cve.get("descriptions", []):
            if dd.get("lang") == "en":
                desc = dd.get("value", "")
                break
        scored.append((score if score is not None else -1, {
            "id": cve.get("id"),
            "title": cve.get("id"),
            "subtitle": (f"CVSS {score} {sev}" if score is not None else "unscored") ,
            "tone": sev_tone(score),
            "ts": cve.get("published"),
            "meta": {"severity": sev, "score": score, "desc": desc[:280]},
        }))
    scored.sort(key=lambda x: x[0], reverse=True)
    items = [it for _, it in scored[:40]]

    write("cyber-nvd", {
        "domain": "cyber", "source": "nvd-cve", "status": "ok",
        "windowDays": 3,
        "headline": {"label": "NEW CVEs (3d)", "value": str(total),
                     "tone": "elevated" if crit else "moderate" if total else "neutral"},
        "metrics": [
            {"label": "CRITICAL", "value": str(crit), "tone": "critical"},
            {"label": "HIGH", "value": str(high), "tone": "elevated"},
            {"label": "TOTAL 3D", "value": str(total), "tone": "info"},
        ],
        "items": items,
        "attribution": "NIST National Vulnerability Database (NVD)",
    })


if __name__ == "__main__":
    main()
