# prometheus-intel-data

CYBER + KINETIC situational-awareness feeds for **PROMETHEUS** (DOI OCIO multi-domain SA platform). Same architecture as the `firestorm-*-data` pipelines: **GHA cron → public gov API → slim JSON → GitHub CDN**. All sources are **anonymous / keyless** — no secrets in this repo.

Consumed by the PROMETHEUS right-rail domain panels via the `window.PROMETHEUS.panels` contract (see the app's `docs/PANELS_DATA_CONTRACT.md`). Each JSON is already shaped as a `PanelPayload`.

## Feeds

| File | Domain | Source | Anon | Cadence |
|---|---|---|---|---|
| `data/cyber-kev.json` | CYBER | CISA Known Exploited Vulnerabilities catalog | ✅ | 6h |
| `data/cyber-nvd.json` | CYBER | NIST NVD recent CVEs (2.0 API) | ✅ | 6h |
| `data/cyber-ics.json` | CYBER | CISA ICS advisories (RSS) | ✅ | 6h |
| `data/kinetic-travel.json` | KINETIC | US State Dept travel advisories (RSS) | ✅ | 6h |
| `data/kinetic-disasters.json` | KINETIC | GDACS active disaster alerts (Orange/Red) | ✅ | 6h |
| `data/kinetic-quakes.json` | KINETIC | USGS significant earthquakes (7d) | ✅ | 6h |

Read via CDN, e.g.:
```
https://raw.githubusercontent.com/Deasus/prometheus-intel-data/main/data/cyber-kev.json
```

## Payload shape (per file)

```jsonc
{
  "domain": "cyber" | "kinetic",
  "source": "cisa-kev",
  "status": "ok" | "empty" | "stale" | "error",
  "generated": "ISO-8601 UTC",
  "version": "v1",
  "headline": { "label": "...", "value": "...", "tone": "critical|elevated|moderate|info|neutral" },
  "metrics":  [ { "label": "...", "value": "...", "tone": "..." } ],
  "items":    [ { "id, title, subtitle, tone, ts, meta" } ],   // ≤40, most-relevant first
  "attribution": "..."
}
```

## Sources NOT used (and why) — verified 2026-07-02

- **ACLED** (conflict events) — requires a free API key + registered email; not anonymous. GDACS + State advisories cover the operational intent keylessly. Revisit if ACLED-grade conflict fidelity is needed (would add a GHA secret).
- **DoD news** (`defense.gov`) — Akamai bot-blocks anonymous RSS (403).
- **USCG MISLE** (maritime incidents) — no public JSON (SOAP `.asmx` only).
- **ReliefWeb** — v1 decommissioned; v2 requires a pre-approved `appname` (email request). Add when the appname is approved (would be `data/kinetic-reliefweb.json`).
- **GDELT** (news) — keyless but aggressively rate-limits (429 even at 6s spacing) and returns empty JSON intermittently; too flaky for an operational feed. GDACS chosen instead.

## Run locally

```bash
python3 scripts/fetch_cisa_kev.py   # writes data/cyber-kev.json
# ... one script per feed; no deps beyond the stdlib.
```

## Attribution
CISA · NIST NVD · US Department of State · GDACS (UN/EC) · USGS. Public-domain / open government data.
