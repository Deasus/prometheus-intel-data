"""US State Dept travel advisories RSS -> data/kinetic-travel.json.

Anonymous. Feed: https://travel.state.gov/_res/rss/TAsTWs.xml
Each item has a "Level N: ..." category. Headline = count at Level 4 (Do Not Travel);
items = the L4 + L3 advisories (the operationally relevant ones), most recent first.
"""
from __future__ import annotations
import xml.etree.ElementTree as ET
import datetime, email.utils, re
from common import get, write, fail, strip_html

URL = "https://travel.state.gov/_res/rss/TAsTWs.xml"


def parse_date(s):
    try:
        return email.utils.parsedate_to_datetime(s).astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:  # noqa: BLE001
        return None


def main() -> None:
    try:
        root = ET.fromstring(get(URL, timeout=40, accept="application/rss+xml"))
    except Exception as e:  # noqa: BLE001
        fail(f"State travel fetch/parse failed: {e}")

    items_xml = root.findall(".//item")
    if not items_xml:
        fail("State travel returned zero items (feed change?)")

    def txt(it, tag):
        for c in it:
            if c.tag.split("}")[-1] == tag:
                return c.text or ""
        return ""

    l4 = l3 = 0
    rows = []
    for it in items_xml:
        title = strip_html(txt(it, "title"))
        m = re.search(r"Level\s*(\d)", title)
        lvl = int(m.group(1)) if m else 0
        if lvl == 4:
            l4 += 1
        elif lvl == 3:
            l3 += 1
        if lvl >= 3:
            rows.append({
                "id": txt(it, "guid") or title,
                "title": title.split(" - ")[0] if " - " in title else title,
                "subtitle": (f"Level {lvl}: " + ("Do Not Travel" if lvl == 4 else "Reconsider Travel")),
                "tone": "critical" if lvl == 4 else "elevated",
                "ts": parse_date(txt(it, "pubDate")),
                "meta": {"level": lvl, "link": txt(it, "link")},
            })
    rows.sort(key=lambda r: (r["meta"]["level"], r.get("ts") or ""), reverse=True)

    write("kinetic-travel", {
        "domain": "kinetic", "source": "state-travel", "status": "ok",
        "headline": {"label": "TRAVEL L4 (DO NOT TRAVEL)", "value": str(l4),
                     "tone": "critical" if l4 else "neutral"},
        "metrics": [
            {"label": "LEVEL 4", "value": str(l4), "tone": "critical"},
            {"label": "LEVEL 3", "value": str(l3), "tone": "elevated"},
            {"label": "TOTAL ADVISORIES", "value": str(len(items_xml)), "tone": "info"},
        ],
        "items": rows[:40],
        "attribution": "US Department of State Travel Advisories",
    })


if __name__ == "__main__":
    main()
