#!/usr/bin/env python3
"""Conservative Frontier GoWild public booking-data watcher.

This script reads Frontier's public booking response for explicit routes/dates and
renders a human Markdown summary. It does not log in, book flights, or automate
checkout. Browser-cookie mode is optional and off by default.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import html as html_lib
import json
import random
import re
import sys
import time
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

MAX_DESTINATIONS = 10
MAX_DATES = 7
DEFAULT_MIN_DELAY = 2.0
DEFAULT_MAX_DELAY = 5.0

FRONTIER_SELECT_URL = "https://booking.flyfrontier.com/Flight/InternalSelect"
FRONTIER_SCHEDULE_URL = "https://booking.flyfrontier.com/Flight/RetrieveSchedule"


@dataclasses.dataclass
class Flight:
    origin: str
    destination: str
    date: str
    depart: Optional[str]
    arrive: Optional[str]
    duration: Optional[str]
    stops: Optional[str]
    price: Optional[float]
    seats_remaining: Optional[str]
    flight_numbers: Optional[str]


@dataclasses.dataclass
class RouteResult:
    origin: str
    destination: str
    date: str
    status: str
    flights: List[Flight] = dataclasses.field(default_factory=list)
    error: Optional[str] = None
    booking_url: Optional[str] = None


@dataclasses.dataclass
class ScanResult:
    origin: str
    destinations: List[str]
    dates: List[str]
    filters: Dict[str, Any]
    route_results: Dict[Tuple[str, str, str], RouteResult]
    warnings: List[str]


def parse_csv_codes(value: str, label: str) -> List[str]:
    codes = [item.strip().upper() for item in value.split(",") if item.strip()]
    if not codes:
        raise ValueError(f"{label} must include at least one IATA code")
    invalid = [code for code in codes if not re.fullmatch(r"[A-Z]{3}", code)]
    if invalid:
        raise ValueError(f"Invalid {label} IATA code(s): {', '.join(invalid)}")
    return codes


def parse_dates(value: str) -> List[str]:
    dates: List[str] = []
    for item in [part.strip() for part in value.split(",") if part.strip()]:
        if re.fullmatch(r"[+-]?\d+", item):
            target = dt.date.today() + dt.timedelta(days=int(item))
            dates.append(target.isoformat())
            continue
        try:
            dates.append(dt.date.fromisoformat(item).isoformat())
        except ValueError as exc:
            raise ValueError(f"Invalid date '{item}'. Use YYYY-MM-DD or day offsets like 0,+1,+3") from exc
    if not dates:
        raise ValueError("dates must include at least one date")
    return dates


def enforce_safety_limits(destinations: List[str], dates: List[str]) -> None:
    if len(destinations) > MAX_DESTINATIONS:
        raise ValueError(f"Safety limit: at most {MAX_DESTINATIONS} destinations per run")
    if len(dates) > MAX_DATES:
        raise ValueError(f"Safety limit: at most {MAX_DATES} dates per run")


def format_frontier_date(iso_date: str) -> str:
    target = dt.date.fromisoformat(iso_date)
    # Frontier accepts e.g. May%2021,%202026. requests encodes it later.
    return target.strftime("%b %d, %Y")


def user_agent() -> str:
    chrome = f"{random.randint(119, 126)}.0.{random.randint(1000, 9999)}.{random.randint(100, 999)}"
    return (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        f"AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome} Safari/537.36"
    )


def build_booking_url(origin: str, destination: str, iso_date: str) -> str:
    params = {
        "o1": origin,
        "d1": destination,
        "dd1": format_frontier_date(iso_date),
        "ADT": "1",
        "mon": "true",
        "promo": "",
    }
    return f"{FRONTIER_SELECT_URL}?{urlencode(params)}"


def load_cookie_jar(use_browser_cookies: bool):
    if not use_browser_cookies:
        return None
    try:
        import browsercookie  # type: ignore
    except ImportError as exc:
        raise RuntimeError("browsercookie is required for --use-browser-cookies") from exc
    return browsercookie.chrome()


def maybe_schedule_has_date(session: requests.Session, origin: str, destination: str, iso_date: str, cookies=None) -> Optional[bool]:
    params = {
        "calendarSelectableDays.Origin": origin,
        "calendarSelectableDays.Destination": destination,
    }
    response = session.get(
        FRONTIER_SCHEDULE_URL,
        params=params,
        headers={"User-Agent": user_agent()},
        cookies=cookies,
        timeout=30,
    )
    if response.status_code != 200:
        return None
    try:
        data = response.json()
        cal = data.get("calendarSelectableDays", {})
        disabled = set(cal.get("disabledDates") or [])
        last_available = cal.get("lastAvailableDate")
    except Exception:
        return None
    if last_available == "0001-01-01 00:00:00":
        return False
    target = dt.date.fromisoformat(iso_date).strftime("%m/%d/%Y")
    return target not in disabled


def extract_flight_data(html_text: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html_text, "html.parser")
    for script in soup.find_all("script"):
        text = script.text or ""
        if "FlightData" not in text or "journeys" not in text:
            continue
        decoded = html_lib.unescape(text)
        start = decoded.find("{")
        end = decoded.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("FlightData script found, but JSON object boundaries were not found")
        return json.loads(decoded[start : end + 1])
    raise ValueError("Could not find Frontier FlightData script in response")


def get_path(data: Any, path: Iterable[Any]) -> Any:
    cur = data
    for key in path:
        if isinstance(cur, dict):
            cur = cur.get(key)
        elif isinstance(cur, list) and isinstance(key, int) and 0 <= key < len(cur):
            cur = cur[key]
        else:
            return None
    return cur


def to_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def flight_numbers(raw: Dict[str, Any]) -> Optional[str]:
    legs = raw.get("legs") or []
    numbers = []
    for leg in legs:
        carrier = leg.get("carrierCode") or "F9"
        number = leg.get("flightNumber")
        if number:
            numbers.append(f"{carrier} {number}")
    return ", ".join(numbers) if numbers else None


def normalize_flights(
    payload: Dict[str, Any],
    origin: str,
    destination: str,
    iso_date: str,
    max_price: Optional[float],
    nonstop_only: bool,
    max_stops: Optional[int],
) -> List[Flight]:
    raw_flights = get_path(payload, ["journeys", 0, "flights"]) or []
    flights: List[Flight] = []
    for raw in raw_flights:
        if not isinstance(raw, dict) or not raw.get("isGoWildFareEnabled"):
            continue
        price = to_float(raw.get("goWildFare"))
        stop_count = raw.get("stopCount")
        if max_price is not None and (price is None or price > max_price):
            continue
        if nonstop_only and stop_count != 0:
            continue
        if max_stops is not None and isinstance(stop_count, int) and stop_count > max_stops:
            continue
        first_leg = get_path(raw, ["legs", 0]) or {}
        flights.append(
            Flight(
                origin=origin,
                destination=destination,
                date=iso_date,
                depart=first_leg.get("departureDateFormatted"),
                arrive=(raw.get("arrivalDateFormatted") or first_leg.get("arrivalDateFormatted")),
                duration=raw.get("duration") or raw.get("durationFormatted"),
                stops=raw.get("stopsText") or ("Nonstop" if stop_count == 0 else f"{stop_count} stop(s)"),
                price=price,
                seats_remaining=raw.get("goWildFareSeatsRemaining"),
                flight_numbers=flight_numbers(raw),
            )
        )
    flights.sort(key=lambda f: ((f.price if f.price is not None else 999999), f.depart or ""))
    return flights


def fetch_route(
    session: requests.Session,
    origin: str,
    destination: str,
    iso_date: str,
    max_price: Optional[float],
    nonstop_only: bool,
    max_stops: Optional[int],
    cookies=None,
) -> RouteResult:
    booking_url = build_booking_url(origin, destination, iso_date)
    if origin == destination:
        return RouteResult(origin, destination, iso_date, "skipped", error="origin and destination are identical", booking_url=booking_url)
    schedule_ok = maybe_schedule_has_date(session, origin, destination, iso_date, cookies=cookies)
    if schedule_ok is False:
        return RouteResult(origin, destination, iso_date, "no-schedule", booking_url=booking_url)
    response = session.get(booking_url, headers={"User-Agent": user_agent()}, cookies=cookies, timeout=45)
    if response.status_code != 200:
        return RouteResult(origin, destination, iso_date, "http-error", error=f"HTTP {response.status_code}", booking_url=booking_url)
    try:
        payload = extract_flight_data(response.text)
        flights = normalize_flights(payload, origin, destination, iso_date, max_price, nonstop_only, max_stops)
    except Exception as exc:
        return RouteResult(origin, destination, iso_date, "parse-error", error=str(exc), booking_url=booking_url)
    return RouteResult(origin, destination, iso_date, "ok", flights=flights, booking_url=booking_url)


def scan(args: argparse.Namespace) -> ScanResult:
    origin = args.origin.upper()
    destinations = parse_csv_codes(args.destinations, "destinations")
    dates = parse_dates(args.dates)
    enforce_safety_limits(destinations, dates)
    cookies = load_cookie_jar(args.use_browser_cookies)
    session = requests.Session()
    route_results: Dict[Tuple[str, str, str], RouteResult] = {}
    warnings = [
        "Public Frontier booking data only; manually verify while logged into your GoWild account before booking.",
        f"Safety limits enforced: max {MAX_DESTINATIONS} destinations × {MAX_DATES} dates per run.",
    ]
    if args.use_browser_cookies:
        warnings.append("Browser-cookie mode was enabled; default/recommended mode is off.")
    for iso_date in dates:
        for destination in destinations:
            delay = random.uniform(args.min_delay, args.max_delay)
            time.sleep(delay)
            result = fetch_route(
                session,
                origin,
                destination,
                iso_date,
                max_price=args.max_price,
                nonstop_only=args.nonstop_only,
                max_stops=args.max_stops,
                cookies=cookies,
            )
            route_results[(origin, destination, iso_date)] = result
    return ScanResult(
        origin=origin,
        destinations=destinations,
        dates=dates,
        filters={"max_price": args.max_price, "nonstop_only": args.nonstop_only, "max_stops": args.max_stops},
        route_results=route_results,
        warnings=warnings,
    )


def money(value: Optional[float]) -> str:
    return "n/a" if value is None else f"${value:.2f}"


def render_markdown(result: ScanResult, show_warnings: bool = True) -> str:
    lines: List[str] = []
    lines.append("## Frontier GoWild Watch")
    lines.append("")
    lines.append(f"Origin: `{result.origin}`")
    lines.append(f"Destinations: `{', '.join(result.destinations)}`")
    lines.append(f"Dates: `{', '.join(result.dates)}`")
    filter_bits = []
    if result.filters.get("max_price") is not None:
        filter_bits.append(f"max price {money(result.filters['max_price'])}")
    if result.filters.get("nonstop_only"):
        filter_bits.append("nonstop only")
    if result.filters.get("max_stops") is not None:
        filter_bits.append(f"max stops {result.filters['max_stops']}")
    lines.append(f"Filters: {', '.join(filter_bits) if filter_bits else 'none'}")
    lines.append("")
    if show_warnings:
        for warning in result.warnings:
            lines.append(f"⚠️ {warning}")
        lines.append("")

    total = sum(len(rr.flights) for rr in result.route_results.values())
    if total == 0:
        lines.append("No matching GoWild-enabled flights found for the requested filters.")
    else:
        lines.append(f"Found **{total}** matching GoWild-enabled flight option(s).")
    lines.append("")

    for key in sorted(result.route_results):
        rr = result.route_results[key]
        lines.append(f"### {rr.origin} → {rr.destination} — {rr.date}")
        if rr.status != "ok":
            lines.append(f"Status: `{rr.status}`" + (f" — {rr.error}" if rr.error else ""))
            lines.append("")
            continue
        if not rr.flights:
            lines.append("No matching GoWild-enabled flights after filters.")
            if rr.booking_url:
                lines.append(f"Frontier search: {rr.booking_url}")
            lines.append("")
            continue
        for idx, flight in enumerate(rr.flights, 1):
            parts = [
                f"{idx}. **{flight.depart or 'n/a'} → {flight.arrive or 'n/a'}**",
                f"price {money(flight.price)}",
                flight.stops or "stops n/a",
                flight.duration or "duration n/a",
            ]
            if flight.seats_remaining:
                parts.append(f"seats: {flight.seats_remaining}")
            if flight.flight_numbers:
                parts.append(f"flight: {flight.flight_numbers}")
            lines.append("- " + " · ".join(parts))
        if rr.booking_url:
            lines.append(f"Frontier search: {rr.booking_url}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Conservative Frontier GoWild public booking-data watcher")
    parser.add_argument("--origin", required=True, help="Origin IATA code, e.g. ATL")
    parser.add_argument("--destinations", required=True, help="Comma-separated destination IATA codes, max 10, e.g. DEN,MCO,LAS")
    parser.add_argument("--dates", required=True, help="Comma-separated YYYY-MM-DD dates or offsets like 0,+1,+3, max 7")
    parser.add_argument("--max-price", type=float, default=None, help="Only show GoWild fares at or below this displayed price")
    parser.add_argument("--nonstop-only", action="store_true", help="Only show nonstop flights")
    parser.add_argument("--max-stops", type=int, default=None, help="Only show flights with this many stops or fewer")
    parser.add_argument("--min-delay", type=float, default=DEFAULT_MIN_DELAY, help="Minimum delay between route/date checks")
    parser.add_argument("--max-delay", type=float, default=DEFAULT_MAX_DELAY, help="Maximum delay between route/date checks")
    parser.add_argument("--use-browser-cookies", action="store_true", help="Optional Chrome cookie mode; off by default")
    parser.add_argument("--hide-warnings", action="store_true", help="Suppress warning lines in Markdown output")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.min_delay < 0 or args.max_delay < args.min_delay:
        parser.error("delay values must be non-negative and max-delay must be >= min-delay")
    try:
        result = scan(args)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    print(render_markdown(result, show_warnings=not args.hide_warnings))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
