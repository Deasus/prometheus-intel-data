"""GDACS active disaster alerts (Orange/Red) -> data/kinetic-disasters.json.

Anonymous/keyless JSON API. Replaces the flaky GDELT feed as the reliable KINETIC
disaster/hazard signal. GDACS = Global Disaster Alerting Coordination System (UN/EC).
Event types: EQ (quake), TC (cyclone), FL (flood), VO (volcano), DR (drought), WF (wildfire).
"""
from __future__ import annotations
from common import get_json, write, fail

URL = ("https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH"
       "?fromDate=&toDate=&alertlevel=Orange;Red&eventlist=EQ;TC;FL;VO;DR;WF")

TYPE_NAME = {"EQ": "Earthquake", "TC": "Cyclone", "FL": "Flood",
             "VO": "Volcano", "DR": "Drought", "WF": "Wildfire"}


def main() -> None:
    try:
        d = get_json(URL, timeout=40)
    except Exception as e:  # noqa: BLE001
        fail(f"GDACS fetch failed: {e}")

    feats = d.get("features") or []
    red = orange = 0
    items = []
    for f in feats:
        p = f.get("properties", {})
        lvl = (p.get("alertlevel") or "").lower()
        if lvl == "red":
            red += 1
        elif lvl == "orange":
            orange += 1
        et = p.get("eventtype", "")
        sev = (p.get("severitydata") or {}).get("severitytext", "")
        # Point geometry is [lon, lat]. Expose lat/lng in meta so the map can plot it.
        geom = (f.get("geometry") or {}).get("coordinates") or []
        lng = geom[0] if len(geom) >= 2 else None
        lat = geom[1] if len(geom) >= 2 else None
        items.append({
            "id": str(p.get("eventid")) + "-" + str(p.get("episodeid", "")),
            "title": p.get("name") or p.get("eventname") or (TYPE_NAME.get(et, et) + " event"),
            "subtitle": " · ".join(x for x in [TYPE_NAME.get(et, et), p.get("country", ""), sev] if x)[:120],
            "tone": "critical" if lvl == "red" else "elevated",
            "ts": (p.get("fromdate") + "Z") if p.get("fromdate") and not p.get("fromdate").endswith("Z") else p.get("fromdate"),
            "meta": {"type": et, "alert": p.get("alertlevel"), "country": p.get("country"),
                     "lat": lat, "lng": lng,
                     "url": p.get("url", {}).get("report") if isinstance(p.get("url"), dict) else p.get("url")},
        })
    # Red first, then by alert score.
    items.sort(key=lambda x: (x["tone"] == "critical"), reverse=True)

    n = len(feats)
    write("kinetic-disasters", {
        "domain": "kinetic", "source": "gdacs", "status": "ok" if n else "empty",
        "headline": {"label": "ACTIVE DISASTERS (O/R)", "value": str(n),
                     "tone": "critical" if red else "elevated" if orange else "neutral"},
        "metrics": [
            {"label": "RED ALERTS", "value": str(red), "tone": "critical"},
            {"label": "ORANGE ALERTS", "value": str(orange), "tone": "elevated"},
            {"label": "TOTAL ACTIVE", "value": str(n), "tone": "info"},
        ],
        "items": items[:40],
        "attribution": "GDACS — Global Disaster Alerting Coordination System (UN/EC)",
    })


if __name__ == "__main__":
    main()
