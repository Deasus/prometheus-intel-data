"""CISA ICS advisories RSS -> data/cyber-ics.json.

Anonymous. CORRECTED URL (2026-07-02): the working feed is
https://www.cisa.gov/cybersecurity-advisories/ics-advisories.xml
(the older uscert/ics/advisories/advisories.xml is a dead 301).
"""
from __future__ import annotations
import xml.etree.ElementTree as ET
import datetime, email.utils
from common import get, write, fail, strip_html

URL = "https://www.cisa.gov/cybersecurity-advisories/ics-advisories.xml"


def parse_date(s):
    try:
        return email.utils.parsedate_to_datetime(s).astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:  # noqa: BLE001
        return None


def main() -> None:
    try:
        raw = get(URL, timeout=40, accept="application/rss+xml")
        root = ET.fromstring(raw)
    except Exception as e:  # noqa: BLE001
        fail(f"CISA ICS fetch/parse failed: {e}")

    items_xml = root.findall(".//item")
    if not items_xml:
        fail("CISA ICS returned zero items (feed structure change?)")

    def txt(it, tag):
        for c in it:
            if c.tag.split("}")[-1] == tag:
                return c.text or ""
        return ""

    items = []
    week_count = 0
    wk = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)
    for it in items_xml[:40]:
        ts = parse_date(txt(it, "pubDate"))
        title = strip_html(txt(it, "title"))
        if ts:
            try:
                if datetime.datetime.fromisoformat(ts.replace("Z", "+00:00")) >= wk:
                    week_count += 1
            except Exception:  # noqa: BLE001
                pass
        items.append({
            "id": txt(it, "guid") or txt(it, "link"),
            "title": title,
            "subtitle": strip_html(txt(it, "description"))[:120],
            "tone": "elevated",
            "ts": ts,
            "meta": {"link": txt(it, "link")},
        })

    write("cyber-ics", {
        "domain": "cyber", "source": "cisa-ics", "status": "ok",
        "headline": {"label": "ICS ADVISORIES (7d)", "value": str(week_count),
                     "tone": "moderate" if week_count else "neutral"},
        "metrics": [
            {"label": "TOTAL FEED", "value": str(len(items_xml)), "tone": "info"},
            {"label": "LAST 7D", "value": str(week_count), "tone": "moderate" if week_count else "neutral"},
        ],
        "items": items,
        "attribution": "CISA Industrial Control Systems Advisories",
    })


if __name__ == "__main__":
    main()
