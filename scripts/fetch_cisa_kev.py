"""CISA Known Exploited Vulnerabilities catalog -> data/cyber-kev.json.

Anonymous. Source: https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json
Slim to: headline (KEV added last 7d), metrics (total, ransomware-linked, added-7d),
and the ~40 most recently added items.
"""
from __future__ import annotations
import datetime
from common import get_json, write, fail, now_iso

URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"


def main() -> None:
    try:
        d = get_json(URL)
    except Exception as e:  # noqa: BLE001
        fail(f"CISA KEV fetch failed: {e}")

    vulns = d.get("vulnerabilities") or []
    if not vulns:
        fail("CISA KEV returned zero vulnerabilities (schema change?)")

    def dt(s):
        try:
            return datetime.date.fromisoformat(s)
        except Exception:  # noqa: BLE001
            return None

    today = datetime.date.today()
    wk = today - datetime.timedelta(days=7)
    added_7d = [v for v in vulns if (dt(v.get("dateAdded")) or datetime.date(1970, 1, 1)) >= wk]
    ransom = [v for v in vulns if str(v.get("knownRansomwareCampaignUse", "")).lower() == "known"]

    # Most-recently-added first, cap 40.
    recent = sorted(vulns, key=lambda v: v.get("dateAdded", ""), reverse=True)[:40]
    items = []
    for v in recent:
        items.append({
            "id": v.get("cveID"),
            "title": v.get("cveID"),
            "subtitle": " · ".join(x for x in [v.get("vendorProject"), v.get("product")] if x),
            "tone": "critical" if str(v.get("knownRansomwareCampaignUse", "")).lower() == "known" else "elevated",
            "ts": (v.get("dateAdded") + "T00:00:00Z") if v.get("dateAdded") else None,
            "meta": {
                "name": v.get("vulnerabilityName"),
                "dueDate": v.get("dueDate"),
                "ransomware": v.get("knownRansomwareCampaignUse"),
                "desc": (v.get("shortDescription") or "")[:280],
            },
        })

    n7 = len(added_7d)
    write("cyber-kev", {
        "domain": "cyber", "source": "cisa-kev", "status": "ok",
        "catalogVersion": d.get("catalogVersion"),
        "headline": {"label": "CISA KEV ADDED (7d)", "value": str(n7),
                     "tone": "critical" if n7 >= 10 else "elevated" if n7 > 0 else "neutral"},
        "metrics": [
            {"label": "TOTAL KEVs", "value": str(len(vulns)), "tone": "info"},
            {"label": "RANSOMWARE-LINKED", "value": str(len(ransom)), "tone": "critical"},
            {"label": "ADDED 7D", "value": str(n7), "tone": "moderate" if n7 else "neutral"},
        ],
        "items": items,
        "attribution": "CISA Known Exploited Vulnerabilities Catalog",
    })


if __name__ == "__main__":
    main()
