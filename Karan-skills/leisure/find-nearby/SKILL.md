---
name: find-nearby
description: Find nearby places (restaurants, cafes, bars, pharmacies, etc.) using OpenStreetMap. Works with coordinates, addresses, cities, zip codes, or Telegram location pins. No API keys needed.
version: 1.0.0
metadata:
  hermes:
    tags: [location, maps, nearby, places, restaurants, local]
    related_skills: []
---

# Find Nearby — Local Place Discovery

## Umbrella Scope: Local Place Discovery

This is the class-level skill for nearby-place queries. The narrower restaurant reservation workflow remains under `research-workflow` because it requires date/time availability and ambiance research; use this skill when the core task is location-based place discovery via coordinates, address, city, zip, landmark, or Telegram location pin.

Find restaurants, cafes, bars, pharmacies, and other places near any location. Uses OpenStreetMap (free, no API keys). Works with:

- **Coordinates** from Telegram location pins (latitude/longitude in conversation)
- **Addresses** ("near 123 Main St, Springfield")
- **Cities** ("restaurants in downtown Austin")
- **Zip codes** ("pharmacies near 90210")
- **Landmarks** ("cafes near Times Square")

## Quick Reference

```bash
# By coordinates (from Telegram location pin or user-provided)
python3 SKILL_DIR/scripts/find_nearby.py --lat <LAT> --lon <LON> --type restaurant --radius 1500

# By address, city, or landmark (auto-geocoded)
python3 SKILL_DIR/scripts/find_nearby.py --near "Times Square, New York" --type cafe

# Multiple place types
python3 SKILL_DIR/scripts/find_nearby.py --near "downtown austin" --type restaurant --type bar --limit 10

# JSON output
python3 SKILL_DIR/scripts/find_nearby.py --near "90210" --type pharmacy --json
```

### Parameters

| Flag | Description | Default |
|------|-------------|---------|
| `--lat`, `--lon` | Exact coordinates | — |
| `--near` | Address, city, zip, or landmark (geocoded) | — |
| `--type` | Place type (repeatable for multiple) | restaurant |
| `--radius` | Search radius in meters | 1500 |
| `--limit` | Max results | 15 |
| `--json` | Machine-readable JSON output | off |

### Common Place Types

`restaurant`, `cafe`, `bar`, `pub`, `fast_food`, `pharmacy`, `hospital`, `bank`, `atm`, `fuel`, `parking`, `supermarket`, `convenience`, `hotel`

## Workflow

1. **Get the location.** Look for coordinates (`latitude: ... / longitude: ...`) from a Telegram pin, or ask the user for an address/city/zip.

2. **Ask for preferences** (only if not already stated): place type, how far they're willing to go, any specifics (cuisine, "open now", etc.).

3. **Run the script** with appropriate flags. Use `--json` if you need to process results programmatically.

4. **Present results** with names, distances, and Google Maps links. If the user asked about hours or "open now," check the `hours` field in results — if missing or unclear, verify with `web_search`.

5. **For directions**, use the `directions_url` from results, or construct: `https://www.google.com/maps/dir/?api=1&origin=<LAT>,<LON>&destination=<LAT>,<LON>`

## Tips

- If results are sparse, widen the radius (1500 → 3000m)
- For "open now" requests: check the `hours` field in results, cross-reference with `web_search` for accuracy since OSM hours aren't always complete
- Zip codes alone can be ambiguous globally — prompt the user for country/state if results look wrong
- The script uses OpenStreetMap data which is community-maintained; coverage varies by region

## Fallback: place name won't geocode

If Nominatim cannot geocode a specific business name (common for new restaurants or places missing from OSM), don't ask the user for the address right away. First try to discover the address from search snippets, then re-run the nearby search with the street address.

Recommended fallback when `web_search` is unavailable/blocked or Google/Yelp hits bot detection:

```bash
python3 - <<'PY'
import urllib.parse, urllib.request
q='"Pink Lotus Thai" "Atlanta"'
url='https://r.jina.ai/http://duckduckgo.com/html/?q='+urllib.parse.quote(q)
req=urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
print(urllib.request.urlopen(req, timeout=30).read().decode()[:5000])
PY
```

Then use the discovered address with normalized street names (e.g. `976 Brady Avenue Northwest, Atlanta, Georgia` instead of `976 Brady Ave NW STE 110 Atlanta GA`) because Nominatim can fail on abbreviations/suite numbers.

Example:

```bash
python3 SKILL_DIR/scripts/find_nearby.py \
  --near "976 Brady Avenue Northwest, Atlanta, Georgia" \
  --type bar --type pub --type cafe \
  --radius 3000 --limit 30 --json
```

For social/birthday recommendations, combine OSM nearby results with search snippets for known venues (e.g. hotel bars, dessert spots, activity bars) and present a short ranked recommendation by vibe/logistics rather than a raw places list.
