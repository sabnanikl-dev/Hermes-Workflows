<!-- Archived source skill consolidated into `marta-tracker-api` by Hermes skill curator. Original directory moved to .archive/curator-umbrella-20260508-195103. -->

---
name: marta-realtime-tracker
description: Query MARTA real-time train departures using their OpenTripPlanner GraphQL API
version: 1.0.0
tags: [marta, transit, atlanta, graphql, real-time]
---

# MARTA Real-Time Tracker

Query MARTA train departures via their OpenTripPlanner GraphQL API. No API key required.

## API Endpoint

```
POST https://tracker.itsmarta.com/otp/routers/default/index/graphql
Content-Type: application/json
```

**IMPORTANT:** MARTA's old developer API (`developer.itsmarta.com`) is DEAD (returns 404).
The only working API is via their OpenTripPlanner GraphQL endpoint.

## Station IDs

Station IDs follow the format `MARTA:{name}-station`. The complete mapping:

```python
STATIONS = {
    "airport": "MARTA:airport-station",
    "east point": "MARTA:east-point-station",
    "college park": "MARTA:college-park-station",
    "lakewood": "MARTA:lakewood-fulton-county-stadium-station",
    "west end": "MARTA:west-end-station",
    "garnett": "MARTA:garnett-station",
    "five points": "MARTA:five-points-station",
    "georgia state": "MARTA:georgia-state-station",
    "king memorial": "MARTA:king-memorial-station",
    "inman park": "MARTA:inman-park-reynoldstown-station",
    "edgewood": "MARTA:edgewood-candler-park-station",
    "east lake": "MARTA:east-lake-station",
    "decatur": "MARTA:decatur-station",
    "avondale": "MARTA:avondale-station",
    "kensington": "MARTA:kensington-station",
    "indian creek": "MARTA:indian-creek-station",
    "ashby": "MARTA:ashby-station",
    "vine city": "MARTA:vine-city-station",
    "state farm arena": "MARTA:omni-dome-station",
    "midtown": "MARTA:midtown-station",
    "arts center": "MARTA:arts-center-station",
    "north avenue": "MARTA:north-avenue-station",
    "lindbergh": "MARTA:lindbergh-center-station",
    "buckhead": "MARTA:buckhead-station",
    "lenox": "MARTA:lenox-station",
    "brookhaven": "MARTA:brookhaven-oglethorpe-university-station",
    "chamblee": "MARTA:chamblee-station",
    "doraville": "MARTA:doraville-station",
    "peachtree center": "MARTA:peachtree-center-station",
}
```

## GraphQL Query for Departures

```json
{
  "query": "{
    station(id: \"MARTA:lenox-station\") {
      name
      stoptimesWithoutPatterns(numberOfDepartures: 20) {
        scheduledDeparture
        realtimeDeparture
        realtime
        serviceDay
        headsign
        trip {
          tripHeadsign
          route {
            shortName
            longName
            mode
            color
          }
        }
      }
    }
  }"
}
```

## Response Decoding

- **mode**: `"SUBWAY"` for trains, `"BUS"` for buses
- **shortName**: Line name — `"GOLD"`, `"RED"`, `"BLUE"`, `"GREEN"` (not "G", "R", etc.)
- **scheduledDeparture / realtimeDeparture**: Seconds since midnight (serviceDay) + serviceDay (Unix timestamp at midnight ET)
- **realtime**: Boolean — true if using real-time GTFS-RT data
- **headsign**: Direction (e.g., "Airport", "Doraville", "North Springs")

### Converting times to "minutes from now"

```python
from datetime import datetime, timezone, timedelta

def dep_to_minutes(dep, use_realtime=False):
    now = datetime.now(timezone.utc)
    et = timezone(timedelta(hours=-5))
    
    seconds = dep["realtimeDeparture"] if (use_realtime and dep["realtime"]) else dep["scheduledDeparture"]
    departure_utc = datetime.fromtimestamp(dep["serviceDay"] + seconds, tz=timezone.utc)
    departure_et = departure_utc.astimezone(et)
    now_et = now.astimezone(et)
    
    return int((departure_et - now_et).total_seconds() / 60)
```

## Listing All Stations via API

```json
{"query": "{ stations { id gtfsId name lat lon } }"}
```

## Python Implementation

A ready-to-use script is at `~/projects/_shared/marta.py`. Usage:

```bash
python3 ~/projects/_shared/marta.py lenox              # All trains at Lenox
python3 ~/projects/_shared/marta.py lenox airport      # Only Airport-bound
python3 ~/projects/_shared/marta.py midtown            # All trains at Midtown
python3 ~/projects/_shared/marta.py five points        # Five Points
python3 ~/projects/_shared/marta.py peachtree          # Peachtree Center
python3 ~/projects/_shared/marta.py list               # List all stations
```

## Known Pitfalls

1. **Old API is dead**: `developer.itsmarta.com` returns 404. Only the OTP GraphQL works.
2. **Station IDs need the feed prefix**: `"Lenex"` fails, `"MARTA:lenox-station"` works.
3. **Response includes buses AND trains**: Filter `mode == "SUBWAY"` to get only trains.
4. **shortName is the full line name**: It's `"GOLD"` not `"G"`, `"RED"` not `"R"`.
5. **Some headsign values are null**: OTP sometimes returns `null` for headsign on certain trips.
6. **ET timezone**: serviceDay is midnight in Eastern Time, not UTC. Use UTC-5 offset.
