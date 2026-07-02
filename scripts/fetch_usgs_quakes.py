"""USGS significant earthquakes (past week) -> data/kinetic-quakes.json.

Anonymous/keyless GeoJSON. A real KINETIC-adjacent disaster signal (mass-casualty /
infrastructure impact potential). Feed:
https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_week.geojson
"""
from __future__ import annotations
import datetime
from common import get_json, write, fail

URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_week.geojson"


def main() -> None:
    try:
        d = get_json(URL, timeout=30)
    except Exception as e:  # noqa: BLE001
        fail(f"USGS quakes fetch failed: {e}")

    feats = d.get("features") or []
    items = []
    maxmag = 0.0
    for f in feats:
        p = f.get("properties", {})
        mag = p.get("mag") or 0
        try:
            maxmag = max(maxmag, float(mag))
        except (TypeError, ValueError):
            pass
        ts = None
        if p.get("time"):
            try:
                ts = datetime.datetime.fromtimestamp(p["time"] / 1000, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            except Exception:  # noqa: BLE001
                pass
        m = mag if isinstance(mag, (int, float)) else 0
        # GeoJSON Point coordinates: [lon, lat, depth]. Expose lat/lng for the map.
        geom = (f.get("geometry") or {}).get("coordinates") or []
        lng = geom[0] if len(geom) >= 2 else None
        lat = geom[1] if len(geom) >= 2 else None
        items.append({
            "id": f.get("id"),
            "title": f"M{mag} — " + (p.get("place") or "unknown"),
            "subtitle": ("TSUNAMI ALERT" if p.get("tsunami") else (p.get("alert") or "").upper() or "significant"),
            "tone": "critical" if m >= 7.0 else "elevated" if m >= 6.0 else "moderate",
            "ts": ts,
            "meta": {"mag": mag, "alert": p.get("alert"), "tsunami": p.get("tsunami"),
                     "lat": lat, "lng": lng, "depth": (geom[2] if len(geom) >= 3 else None), "url": p.get("url")},
        })
    items.sort(key=lambda x: x["meta"].get("mag") or 0, reverse=True)

    n = len(feats)
    write("kinetic-quakes", {
        "domain": "kinetic", "source": "usgs-quakes", "status": "ok" if n else "empty",
        "headline": {"label": "SIGNIFICANT QUAKES (7d)", "value": str(n),
                     "tone": "critical" if maxmag >= 7 else "elevated" if maxmag >= 6 else "moderate" if n else "neutral"},
        "metrics": [
            {"label": "COUNT 7D", "value": str(n), "tone": "info"},
            {"label": "MAX MAG", "value": (f"{maxmag:.1f}" if maxmag else "—"), "tone": "elevated" if maxmag >= 6 else "info"},
        ],
        "items": items,
        "attribution": "USGS Earthquake Hazards Program",
    })


if __name__ == "__main__":
    main()
