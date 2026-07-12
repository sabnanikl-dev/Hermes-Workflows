import datetime as dt
import json
import pytest

import gowild_watch as gw


def test_parse_dates_accepts_iso_and_offsets(monkeypatch):
    class FixedDate(dt.date):
        @classmethod
        def today(cls):
            return cls(2026, 5, 20)

    monkeypatch.setattr(gw.dt, "date", FixedDate)
    assert gw.parse_dates("2026-05-21,+3,0") == ["2026-05-21", "2026-05-23", "2026-05-20"]


def test_enforce_safety_limits_rejects_too_many_destinations():
    with pytest.raises(ValueError, match="at most 10 destinations"):
        gw.enforce_safety_limits([f"D{i:02d}" for i in range(11)], ["2026-05-21"])


def test_enforce_safety_limits_rejects_too_many_dates():
    with pytest.raises(ValueError, match="at most 7 dates"):
        gw.enforce_safety_limits(["DEN"], [f"2026-05-{day:02d}" for day in range(1, 9)])


def test_extract_flight_data_from_current_frontier_script_shape():
    payload = {"journeys": [{"flights": [{"isGoWildFareEnabled": True, "goWildFare": 98.99}]}]}
    escaped = json.dumps(payload).replace('"', '&quot;')
    html = f"""
    <html><head><script>var unrelated = {{ nope: true }};</script></head>
    <body><script>FlightData = '{escaped}';</script></body></html>
    """
    assert gw.extract_flight_data(html) == payload


def test_normalize_filters_nonstop_and_price():
    raw = {
        "journeys": [{
            "flights": [
                {
                    "isGoWildFareEnabled": True,
                    "goWildFare": 98.99,
                    "goWildFareSeatsRemaining": "2 Seats Left!",
                    "stopsText": "Nonstop",
                    "stopCount": 0,
                    "duration": "3 hrs 30 min",
                    "legs": [{"departureDate": "2026-05-21T07:35:00", "departureDateFormatted": "7:35 AM", "arrivalDateFormatted": "9:05 AM"}],
                },
                {
                    "isGoWildFareEnabled": True,
                    "goWildFare": 197.97,
                    "goWildFareSeatsRemaining": "1 Seat Left!",
                    "stopsText": "1 Stop IAH",
                    "stopCount": 1,
                    "duration": "12 hrs",
                    "legs": [{"departureDate": "2026-05-21T21:25:00", "departureDateFormatted": "9:25 PM", "arrivalDateFormatted": "10:06 AM"}],
                },
                {"isGoWildFareEnabled": False, "goWildFare": 10.0, "legs": [{}]},
            ]
        }]
    }
    flights = gw.normalize_flights(raw, "ATL", "DEN", "2026-05-21", max_price=100, nonstop_only=True, max_stops=None)
    assert len(flights) == 1
    assert flights[0].origin == "ATL"
    assert flights[0].destination == "DEN"
    assert flights[0].price == 98.99
    assert flights[0].stops == "Nonstop"


def test_render_markdown_reports_matches_and_filters():
    result = gw.ScanResult(
        origin="ATL",
        destinations=["DEN"],
        dates=["2026-05-21"],
        filters={"max_price": 100.0, "nonstop_only": True, "max_stops": None},
        route_results={
            ("ATL", "DEN", "2026-05-21"): gw.RouteResult(
                origin="ATL",
                destination="DEN",
                date="2026-05-21",
                status="ok",
                flights=[gw.Flight("ATL", "DEN", "2026-05-21", "7:35 AM", "9:05 AM", "3 hrs 30 min", "Nonstop", 98.99, "2 Seats Left!", "F9 1449")],
            )
        },
        warnings=["Public booking data only"],
    )
    md = gw.render_markdown(result)
    assert "ATL → DEN" in md
    assert "$98.99" in md
    assert "Public booking data only" in md


def test_render_markdown_can_hide_warnings():
    result = gw.ScanResult(
        origin="ATL",
        destinations=["DEN"],
        dates=["2026-05-21"],
        filters={"max_price": None, "nonstop_only": False, "max_stops": None},
        route_results={},
        warnings=["Public booking data only"],
    )
    md = gw.render_markdown(result, show_warnings=False)
    assert "Public booking data only" not in md
    assert "⚠️" not in md
