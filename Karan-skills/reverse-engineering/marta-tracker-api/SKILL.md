---
name: marta-tracker-api
description: Reverse-engineer and use MARTA OpenTripPlanner GraphQL API for real-time Atlanta transit tracking
tags: ["marta", "atlanta", "transit", "api", "graphql", "otp", "reverse-engineering"]
---

# MARTA Tracker API

Real-time MARTA (Atlanta transit) train and bus tracking via OpenTripPlanner GraphQL.

## Umbrella Scope: MARTA Realtime Tracking

This is the class-level MARTA transit skill. The narrower `marta-realtime-tracker` skill is absorbed here as the user-facing query workflow: use the reverse-engineered OpenTripPlanner GraphQL endpoint to fetch train departures, normalize station names, and present near-term departures clearly. Keep reverse-engineering notes, request shapes, and response interpretation together here instead of splitting API and tracker usage into separate skills.

The older realtime-tracker instructions are preserved in `references/marta-realtime-tracker.md`.

## The Problem

MARTA killed their old REST API (developer.itsmarta.com) and replaced it with a React SPA (tracker.itsmarta.com) that has no public API documentation. The API URLs are injected at build time via environment variables.

## Finding the API Endpoint

The tracker is built with OpenTripPlanner (OTP). To discover the GraphQL endpoint:

1. **Fetch the JS bundle**: `curl -sL https://tracker.itsmarta.com/assets/index-*.js`
2. **Search for OTP patterns**: Look for `${appConfig.otp.host}${appConfig.otp.path}/index/graphql`
3. **The endpoint is**: `https://tracker.itsmarta.com/otp/routers/default/index/graphql`
4. **Alternative discovery**: Try standard OTP endpoint patterns if URL injection varies

## Station / Stop IDs

OTP uses `feed-scoped IDs` (format: `MARTA:CODE`). The `id` field in GraphQL responses is base64-encoded, the `gtfsId` field is the plain feed-scoped ID.

**Key MARTA rail station stop IDs:**
| Station | Stop ID |
|---------|---------|
| Lenox | MARTA:905666 (also 906827, 908717) |
| Arts Center | MARTA:905004 |
| Midtown | MARTA:905017 |
| Five Points | MARTA:905011 |
| Lindbergh | MARTA:905050 |
| Sandy Springs | MARTA:905060 |
| Airport | MARTA:905071 |
| Doraville | MARTA:905085 |

**To find any station stop ID:**

```graphql
{
  stops(code: "CODE") {
    id
    name
    gtfsId
  }
}
```

Or search by name substring by querying all stops and filtering.

## Query Templates

### Departures for a Station

```json
{
  "query": "{
    stop(id: \"MARTA:905666\") {
      id
      name
      lat
      lon
      stoptimesWithoutPatterns {
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
          }
        }
      }
    }
  }"
}
```

### All Stops

```json
{
  "query": "{ stops { id name gtfsId code lat lon } }"
}
```

### Route List

```json
{
  "query": "{ routes { shortName longName mode } }"
}
```

### Trip Planning

```json
{
  "query": "{
    plan(fromLat: 33.8452, fromLon: -84.3580, toLat: 33.7628, toLon: -84.3903) {
      itineraries {
        duration
        startTime
        legs {
          mode
          route { shortName }
          from { name }
          to { name }
        }
      }
    }
  }"
}
```

### Convert scheduledDeparture to readable time

The `scheduledDeparture` and `realtimeDeparture` fields are seconds since midnight of the `serviceDay` epoch. Convert in Python:

```python
from datetime import datetime, timedelta

epoch = datetime.fromtimestamp(serviceDay)
time_of_day = timedelta(seconds=scheduledDeparture)
arrival = epoch + time_of_day
```

## Interpreting Results

- **mode**: `SUBWAY` for rail lines, `BUS` for buses
- **route.shortName**: Route number (e.g., 27, GOLD for rail via tripHeadsign)
- **realtime**: `true` = GPS-based ETA, `false` = schedule-based
- **serviceDay**: Epoch timestamp for the service day
- **headsign** / **tripHeadsign**: Destination displayed on the vehicle
- **scheduledDeparture** / **realtimeDeparture**: Seconds since midnight UTC

Note: Rail routes don't use `shortName` -- check `trip.tripHeadsign` for direction (e.g., "Airport", "Doraville") to determine Gold/Red/Blue/Green line and direction.

## Python CLI Tool Template

```python
#!/usr/bin/env python3
"""MARTA Tracker CLI Tool"""
import requests
from datetime import datetime, timedelta

API_URL = "https://tracker.itsmarta.com/otp/routers/default/index/graphql"

def departures(stop_id):
    query = {
        "query": """
        {
          stop(id: "%s") {
            name
            stoptimesWithoutPatterns {
              scheduledDeparture
              realtimeDeparture
              realtime
              headsign
              serviceDay
              trip {
                tripHeadsign
                route { shortName longName mode }
              }
            }
          }
        }
        """ % stop_id
    }
    resp = requests.post(API_URL, json=query, timeout=10)
    data = resp.json()
    stop = data.get("data", {}).get("stop")
    if not stop:
        return []
    
    results = []
    epoch = datetime.fromtimestamp(stop["stoptimesWithoutPatterns"][0]["serviceDay"])
    for st in stop["stoptimesWithoutPatterns"]:
        dept = epoch + timedelta(seconds=st.get("realtimeDeparture", st["scheduledDeparture"]))
        results.append({
            "route": st["trip"]["route"]["shortName"],
            "mode": st["trip"]["route"]["mode"],
            "destination": st.get("headsign") or st["trip"]["tripHeadsign"],
            "departure": dept.strftime("%I:%M %p"),
            "realtime": st["realtime"],
            "minutes_away": max(0, int((dept - datetime.now()).total_seconds() / 60)),
        })
    return sorted(results, key=lambda x: x["minutes_away"])
```

## Common Pitfalls

1. **No public API docs** -- This was reverse-engineered by parsing the compiled React SPA. OTP is open-source though, so any OTP-based system uses the same GraphQL schema.
2. **Station vs Stop confusion** -- `station()` query requires a station-scoped ID which may not exist. Use `stop()` instead with `MARTA:CODE` format.
3. **Rail routes don't have shortName** -- Gold/Red/Blue/Green line info comes from `tripHeadsign` ("To Airport", "To Doraville", etc.). Bus routes do have shortName.
4. **Time conversion** -- `scheduledDeparture` is seconds since midnight UTC, not local time. Convert using `serviceDay` epoch + seconds offset.
5. **Rate limiting** -- No observed rate limits for reasonable polling (every 30-60s).