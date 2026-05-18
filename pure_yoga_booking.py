#!/usr/bin/env python3
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import re
import sys
import threading
import time
from dataclasses import dataclass
from datetime import date, datetime, time as dt_time, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import requests
try:
    import httpx
except ImportError:  # pragma: no cover - optional dependency on older VPS copies
    httpx = None


WEB_REGION_CODES = {
    1: "HK",
    2: "SG",
}

API_BASE_URLS = {
    1: "https://pure360-api.pure-international.com/api/v3",
    2: "https://pure360-api-sg.pure-international.com/api/v3",
}

BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/147.0.0.0 Safari/537.36"
)
BROWSER_ACCEPT_LANGUAGE = "en-US,en;q=0.9"
BROWSER_SEC_CH_UA = '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"'
BROWSER_SEC_CH_UA_MOBILE = "?0"
BROWSER_SEC_CH_UA_PLATFORM = '"Windows"'

SITE_DEFINITIONS = {
    "yoga": {
        "label": "Pure Yoga",
        "host": "pure360.pure-yoga.com",
        "aliases": {"yoga", "pilates"},
    },
    "fitness": {
        "label": "Pure Fitness",
        "host": "pure360.pure-fitness.com",
        "aliases": {"fitness"},
    },
}

DAY_NAME_TO_WEEKDAY = {
    "mon": 0,
    "monday": 0,
    "tue": 1,
    "tues": 1,
    "tuesday": 1,
    "wed": 2,
    "weds": 2,
    "wednesday": 2,
    "thu": 3,
    "thur": 3,
    "thurs": 3,
    "thursday": 3,
    "fri": 4,
    "friday": 4,
    "sat": 5,
    "saturday": 5,
    "sun": 6,
    "sunday": 6,
}

META_RE = re.compile(r'<meta name="([^"]+)" content="([^"]*)"')
STATUS_BOOKED = "BOOKED"
STATUS_WAITLISTED = "WAITLISTED"
STATUS_FAILED = "FAILED"
STATUS_NO_MATCH = "NO_MATCH"
STATUS_SKIPPED = "SKIPPED"

BUTTON_STATUS_BOOK = 1
BUTTON_STATUS_BOOKED = 2
BUTTON_STATUS_WAITLIST = 3
BUTTON_STATUS_IN_WAITLIST = 4
BUTTON_STATUS_FULL = 5
BUTTON_STATUS_SIGNED_IN = 7
BUTTON_STATUS_LAST_CHANCE = 16

TARGET_DEFAULTS: dict[str, Any] = {
    "site": "yoga",
    "days": [],
    "class_name": "",
    "start_time": "",
    "location_id": 0,
    "location_name": "",
    "teacher_name": "",
    "teacher_policy": "prefer_named_teacher",
    "mode": "book_all",
    "priority": 999,
    "class_date": "",
    "booking_run_date": "",
    "skip_booking_run_dates": [],
    "class_days_ahead": 5,
    "booking_open_days": 5,
    "schedule_window_days": 1,
}

DEFAULT_CONFIG: dict[str, Any] = {
    "credentials": {
        "username": "",
        "password": "",
    },
    "region_id": 2,
    "language_id": "1",
    "location_ids": [19],
    "target": {
        "class_name": "Hot Vinyasa",
        "start_time": "19:30",
        "location_id": 19,
        "location_name": "Yoga - Ngee Ann City",
        "teacher_name": "",
        "class_date": "",
        "class_days_ahead": 5,
        "booking_open_days": 5,
        "schedule_window_days": 1,
    },
    "targets": [],
    "booking": {
        "open_time": "09:00:00",
        "wake_seconds_before": 20,
        "spin_window_ms": 150,
        "aggressive_probe_enabled": True,
        "aggressive_probe_lead_ms": 200,
        "aggressive_probe_max_retries": 40,
        "aggressive_probe_retry_interval_ms": 15,
        "late_transport_warmup_enabled": True,
        "late_transport_warmup_ms_before_open": 500,
        "waitlist_fallback": True,
        "login_retry_attempts": 4,
        "login_retry_interval_ms": 750,
        "max_booking_retries": 25,
        "retry_interval_ms": 50,
        "latency_warning_warmup_rtt_ms": 150,
        "include_existing_bookings_in_limit_warnings": True,
        "book_all_submission_strategy": "focus_first",
        "focus_first_head_start_ms": 120,
        "parallel_book_all_submissions": True,
        "stop_after_first_priority_success": True,
        "continue_to_next_priority_on_waitlist": True,
    },
    "notifications": {
        "telegram_bot_token": "",
        "telegram_chat_id": "",
    },
    "runtime": {
        "timezone": "Asia/Singapore",
        "logs_dir": "logs",
        "request_timeout_seconds": 20,
        "verify_ssl": True,
    },
}

FIXED_OFFSET_TIMEZONES = {
    "Asia/Singapore": timezone(timedelta(hours=8), name="SGT"),
    "Singapore": timezone(timedelta(hours=8), name="SGT"),
    "Asia/Hong_Kong": timezone(timedelta(hours=8), name="HKT"),
    "Hong Kong": timezone(timedelta(hours=8), name="HKT"),
    "Asia/Tokyo": timezone(timedelta(hours=9), name="JST"),
    "Japan": timezone(timedelta(hours=9), name="JST"),
    "UTC": timezone.utc,
}


class PureYogaError(RuntimeError):
    pass


class PureYogaAPIError(PureYogaError):
    def __init__(self, code: int, message: str):
        super().__init__(f"Pure booking API error {code}: {message}")
        self.code = code
        self.message = message


@dataclass
class TargetSpec:
    index: int
    site: str
    days: list[int]
    class_name: str
    start_time: str
    location_id: int
    location_name: str
    teacher_name: str
    teacher_policy: str
    mode: str
    priority: int
    class_date: date | None
    booking_run_date: date | None
    skip_booking_run_dates: list[date]
    class_days_ahead: int
    booking_open_days: int
    schedule_window_days: int

    @property
    def label(self) -> str:
        teacher = self.teacher_name or "any teacher"
        day_text = ",".join(self.day_labels()) if self.days else "rolling"
        return (
            f"{self.site} | {day_text} | {self.class_name} | {self.start_time} | "
            f"{self.location_name or self.location_id} | {teacher}"
        )

    def day_labels(self) -> list[str]:
        reverse = {
            0: "Mon",
            1: "Tue",
            2: "Wed",
            3: "Thu",
            4: "Fri",
            5: "Sat",
            6: "Sun",
        }
        return [reverse[day] for day in self.days]


@dataclass
class ResolvedTarget:
    target: TargetSpec
    target_date: date
    booking_open_dt: datetime
    status: str
    message: str
    class_item: dict[str, Any] | None = None


@dataclass
class BookingResult:
    target: TargetSpec
    target_date: date
    status: str
    code: int
    message: str
    class_item: dict[str, Any] | None = None
    deferred_confirmation: bool = False
    request_trace: BookingRequestTrace | None = None


@dataclass
class BookingRequestTrace:
    class_id: int
    book_type: int
    sent_at: str
    response_at: str
    send_started_ns: int
    response_received_ns: int
    http_rtt_ms: float
    http_version: str = ""
    response_date: str = ""
    response_via: str = ""
    response_cf_pop: str = ""
    response_server_timing: str = ""


@dataclass(frozen=True)
class PlannedOccurrence:
    target: TargetSpec
    class_date: date
    class_type: str


@dataclass(frozen=True)
class ExistingBookingOccurrence:
    class_date: date
    start_time: str
    class_name: str
    location_name: str
    class_type: str
    status: str


def booking_limit_class_type(target: TargetSpec) -> str:
    if normalize_text(target.site) == "fitness":
        return "Fitness"

    class_name = normalize_text(target.class_name)
    if any(marker in class_name for marker in ("reformer", "pilates")):
        return "Pilates"
    return "Yoga"


def booking_limit_class_type_from_booking(item: dict[str, Any]) -> str:
    class_item = item.get("class") or item
    sector = normalize_text(str(item.get("sector") or class_item.get("sector") or ""))
    location = class_item.get("location") or {}
    location_name = str(
        location.get("name")
        or (location.get("names") or {}).get("en")
        or class_item.get("location_name")
        or ""
    )
    class_type = class_item.get("class_type") or {}
    class_name = normalize_text(
        str(class_type.get("name") or class_item.get("class_name") or class_item.get("name") or "")
    )
    if sector in {"f", "fitness"} or normalize_text(location_name).startswith("fitness"):
        return "Fitness"
    if any(marker in class_name for marker in ("reformer", "pilates")):
        return "Pilates"
    return "Yoga"


@dataclass
class TransportWarmupTrace:
    sent_at: str
    response_at: str
    send_started_ns: int
    response_received_ns: int
    http_rtt_ms: float
    status_code: int
    http_version: str = ""
    response_date: str = ""
    response_via: str = ""
    response_cf_pop: str = ""
    response_server_timing: str = ""


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_runtime_timezone(name: str) -> tuple[Any, str]:
    try:
        return ZoneInfo(name), "zoneinfo"
    except ZoneInfoNotFoundError:
        fallback = FIXED_OFFSET_TIMEZONES.get(name)
        if fallback is not None:
            return fallback, "fixed-offset"
        raise PureYogaError(
            f"Timezone '{name}' is unavailable on this Python install. "
            "Install the 'tzdata' package or choose a supported fixed-offset timezone."
        ) from None


def post_telegram_message(
    token: str,
    chat_id: str,
    text: str,
    *,
    timeout: int,
    verify_ssl: bool,
) -> None:
    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": text},
        timeout=timeout,
        verify=verify_ssl,
    )
    response.raise_for_status()


def safe_notify_from_config(config: dict[str, Any] | None, text: str) -> None:
    if not config:
        return
    notifications = config.get("notifications", {})
    token = str(notifications.get("telegram_bot_token", "")).strip()
    chat_id = str(notifications.get("telegram_chat_id", "")).strip()
    if not token or not chat_id:
        return
    runtime = config.get("runtime", {})
    timeout = int(runtime.get("request_timeout_seconds", 20) or 20)
    verify_ssl = bool(runtime.get("verify_ssl", True))
    try:
        post_telegram_message(token, chat_id, text, timeout=timeout, verify_ssl=verify_ssl)
    except requests.RequestException:
        pass


def response_header_value(response: Any, header_name: str) -> str:
    headers = getattr(response, "headers", None)
    if not headers:
        return ""
    try:
        value = headers.get(header_name)
    except Exception:
        value = None
    if value:
        return str(value)
    lowered = header_name.lower()
    try:
        for key, candidate in headers.items():
            if str(key).lower() == lowered and candidate:
                return str(candidate)
    except Exception:
        return ""
    return ""


def response_http_version(response: Any) -> str:
    version = getattr(response, "http_version", "")
    if version:
        return str(version)
    raw = getattr(response, "raw", None)
    raw_version = getattr(raw, "version", None)
    return {
        10: "HTTP/1.0",
        11: "HTTP/1.1",
        20: "HTTP/2",
    }.get(raw_version, "")


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def normalize_time(value: str | None) -> str:
    if not value:
        return ""
    value = value.strip()
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(value, fmt).strftime("%H:%M")
        except ValueError:
            continue
    if "T" in value:
        try:
            return datetime.fromisoformat(value).strftime("%H:%M")
        except ValueError:
            pass
    raise PureYogaError(f"Unsupported time format: {value}")


def parse_clock(value: str) -> dt_time:
    parts = [int(part) for part in value.split(":")]
    if len(parts) == 2:
        return dt_time(parts[0], parts[1], 0)
    if len(parts) == 3:
        return dt_time(parts[0], parts[1], parts[2])
    raise PureYogaError(f"Unsupported clock format: {value}")


def parse_date_or_blank(value: str) -> date | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise PureYogaError(f"Invalid class_date '{value}'. Use YYYY-MM-DD.") from exc


def safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def canonical_site(site: str | None) -> str:
    normalized = normalize_text(site)
    for key, value in SITE_DEFINITIONS.items():
        aliases = {normalize_text(item) for item in value["aliases"]}
        if normalized == normalize_text(key) or normalized in aliases:
            return key
    raise PureYogaError(f"Unsupported site '{site}'. Use 'yoga', 'pilates', or 'fitness'.")


def parse_days(value: Any) -> list[int]:
    if not value:
        return []
    items = value if isinstance(value, list) else [item.strip() for item in str(value).split(",")]
    days: list[int] = []
    for item in items:
        key = str(item).strip().lower()
        if not key:
            continue
        if key not in DAY_NAME_TO_WEEKDAY:
            raise PureYogaError(f"Unsupported day name '{item}'. Use Mon/Tue/Wed/Thu/Fri/Sat/Sun.")
        weekday = DAY_NAME_TO_WEEKDAY[key]
        if weekday not in days:
            days.append(weekday)
    return days


def normalize_teacher_policy(value: str | None) -> str:
    normalized = normalize_text(value or "prefer_named_teacher")
    if normalized in {"exact", "requireteacher"}:
        return "exact"
    if normalized in {"prefernamedteacher", "prefer", "fallbackanyteacher", "preferreplacement"}:
        return "prefer_named_teacher"
    if normalized in {"any", "anyteacher", "ignoreteacher"}:
        return "any_teacher"
    raise PureYogaError(
        f"Unsupported teacher_policy '{value}'. Use 'exact', 'prefer_named_teacher', or 'any_teacher'."
    )


def normalize_mode(value: str | None) -> str:
    normalized = normalize_text(value or "book_all")
    if normalized in {"bookall", "all"}:
        return "book_all"
    if normalized in {"priority", "sequential"}:
        return "priority"
    raise PureYogaError(f"Unsupported mode '{value}'. Use 'book_all' or 'priority'.")


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise PureYogaError(
            f"Config file not found: {path}\n"
            f"Copy pure_yoga_config.example.json to {path.name} and fill in your details."
        )
    with path.open("r", encoding="utf-8") as handle:
        raw_config = json.load(handle)
    return deep_merge(DEFAULT_CONFIG, raw_config)


class SiteClient:
    def __init__(self, bot: "PureYogaBot", site: str, location_ids: list[int]):
        self.bot = bot
        self.site = canonical_site(site)
        self.location_ids = sorted({value for value in location_ids if value})
        self.jwt = ""
        self.locations_by_id: dict[int, dict[str, Any]] = {}
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": BROWSER_USER_AGENT,
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": BROWSER_ACCEPT_LANGUAGE,
            }
        )
        self.booking_transport = self.build_booking_transport()
        self.booking_transport_mode = "httpx-http2" if self.booking_transport is not None else "requests-fallback"
        self.booking_transport_announced = False
        self.last_transport_warmup_trace: TransportWarmupTrace | None = None

    @property
    def label(self) -> str:
        return SITE_DEFINITIONS[self.site]["label"]

    @property
    def host(self) -> str:
        return SITE_DEFINITIONS[self.site]["host"]

    @property
    def api_base_url(self) -> str:
        return API_BASE_URLS[self.bot.region_id]

    def log(self, message: str) -> None:
        self.bot.log(f"[{self.site}] {message}")

    def request_json(
        self,
        method: str,
        path_or_url: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[dict[str, Any], requests.Response, int, str]:
        url = path_or_url if path_or_url.startswith("http") else f"{self.api_base_url}/{path_or_url}"
        response = self.session.request(
            method=method,
            url=url,
            params=params,
            json=json_body,
            headers=headers,
            timeout=self.bot.timeout,
            verify=self.bot.verify_ssl,
        )
        try:
            payload = response.json()
        except ValueError as exc:
            raise PureYogaError(
                f"Non-JSON response from {url}: HTTP {response.status_code} {response.text[:200]}"
            ) from exc
        error_info = payload.get("error", {})
        code = safe_int(error_info.get("code", response.status_code))
        message = str(error_info.get("message", response.reason))
        return payload, response, code, message

    def build_booking_transport(self) -> Any | None:
        if httpx is None:
            return None
        return httpx.Client(
            http2=True,
            verify=self.bot.verify_ssl,
            timeout=self.bot.timeout,
            headers={
                "User-Agent": self.session.headers.get("User-Agent", ""),
                "Accept": self.session.headers.get("Accept", "application/json, text/plain, */*"),
                "Accept-Language": self.session.headers.get("Accept-Language", BROWSER_ACCEPT_LANGUAGE),
            },
        )

    def sync_booking_transport_state(self) -> None:
        if self.booking_transport is None:
            return
        self.booking_transport.headers.update(
            {
                "User-Agent": self.session.headers.get("User-Agent", BROWSER_USER_AGENT),
                "Accept": self.session.headers.get("Accept", "application/json, text/plain, */*"),
                "Accept-Language": self.session.headers.get("Accept-Language", BROWSER_ACCEPT_LANGUAGE),
            }
        )
        self.booking_transport.cookies.clear()
        self.booking_transport.cookies.update(self.session.cookies.get_dict())

    def browser_request_context_headers(self) -> dict[str, str]:
        origin = f"https://{self.host}"
        return {
            "Origin": origin,
            "Referer": f"{origin}/",
            "Priority": "u=1, i",
            "Sec-CH-UA": BROWSER_SEC_CH_UA,
            "Sec-CH-UA-Mobile": BROWSER_SEC_CH_UA_MOBILE,
            "Sec-CH-UA-Platform": BROWSER_SEC_CH_UA_PLATFORM,
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
        }

    def booking_transport_headers(self, *, include_jwt: bool = True) -> dict[str, str]:
        headers: dict[str, str] = dict(self.browser_request_context_headers())
        for key in ("Content-Type", "X-Date", "X-Token", "X-Features"):
            value = self.session.headers.get(key)
            if value:
                headers[key] = value
        if include_jwt and self.jwt:
            headers["X-JWT-Token"] = self.jwt
        return headers

    def prime_booking_transport(self) -> None:
        if not self.booking_transport_announced:
            self.log(f"Booking transport mode: {self.booking_transport_mode}.")
            self.booking_transport_announced = True
        if self.booking_transport is None:
            return
        try:
            self.booking_transport.get(
                f"{self.api_base_url}/view_location",
                params={
                    "region_id": self.bot.region_id,
                    "language_id": self.bot.language_id,
                },
                headers=self.booking_transport_headers(include_jwt=False),
            )
        except Exception as exc:
            self.log(
                f"Could not prime shared booking transport: {type(exc).__name__}: {exc}. "
                "Continuing with on-demand connection setup."
            )

    def late_warmup_booking_transport(self) -> TransportWarmupTrace | None:
        if not self.booking_transport_announced:
            self.log(f"Booking transport mode: {self.booking_transport_mode}.")
            self.booking_transport_announced = True
        if self.booking_transport is None:
            return None
        sent_at = self.bot.now().strftime("%H:%M:%S.%f")[:-3]
        send_started_ns = time.time_ns()
        try:
            response = self.booking_transport.get(
                f"{self.api_base_url}/view_location",
                params={
                    "region_id": self.bot.region_id,
                    "language_id": self.bot.language_id,
                },
                headers=self.booking_transport_headers(),
            )
        except Exception as exc:
            self.log(
                f"Could not perform late booking transport warmup: {type(exc).__name__}: {exc}. "
                "Continuing without late warmup."
            )
            return None
        response_received_ns = time.time_ns()
        trace = TransportWarmupTrace(
            sent_at=sent_at,
            response_at=self.bot.now().strftime("%H:%M:%S.%f")[:-3],
            send_started_ns=send_started_ns,
            response_received_ns=response_received_ns,
            http_rtt_ms=(response_received_ns - send_started_ns) / 1_000_000,
            status_code=response.status_code,
            http_version=response_http_version(response),
            response_date=response_header_value(response, "Date"),
            response_via=response_header_value(response, "Via"),
            response_cf_pop=response_header_value(response, "X-Amz-Cf-Pop"),
            response_server_timing=response_header_value(response, "Server-Timing"),
        )
        self.last_transport_warmup_trace = trace
        self.log(
            f"Late booking transport warmup sent_at={trace.sent_at} response_at={trace.response_at} "
            f"http_rtt_ms={trace.http_rtt_ms:.1f} status={trace.status_code} "
            f"http_version={trace.http_version or 'unknown'} "
            f"cf_pop={trace.response_cf_pop or '-'} via={trace.response_via or '-'} "
            f"server_timing={trace.response_server_timing or '-'}."
        )
        return trace

    def bootstrap_headers(self) -> None:
        location_ids = ",".join(str(value) for value in self.location_ids) if self.location_ids else ""
        page_url = f"https://{self.host}/en/{self.bot.web_region_code}?location_ids={location_ids}"
        started_at_ms = time.time_ns() / 1_000_000
        response = self.session.get(page_url, timeout=self.bot.timeout, verify=self.bot.verify_ssl)
        finished_at_ms = time.time_ns() / 1_000_000
        response.raise_for_status()
        meta = dict(META_RE.findall(response.text))
        token = meta.get("token")
        timestamp = meta.get("timestamp")
        if not token or not timestamp:
            raise PureYogaError(f"Could not find X-Token/X-Date meta tags on {self.label}.")
        self.bot.observe_server_time_sample(timestamp, started_at_ms, finished_at_ms)
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "X-Date": timestamp,
                "X-Token": token,
                "X-Features": "last_chance_booking",
            }
        )
        self.sync_booking_transport_state()
        offset_ms = self.bot.server_time_offset_ms
        self.log(f"Refreshed request headers (X-Date={timestamp}, server_offset={offset_ms:+.1f}ms).")

    def fetch_locations(self) -> dict[int, dict[str, Any]]:
        payload, _, code, message = self.request_json(
            "GET",
            "view_location",
            params={
                "region_id": self.bot.region_id,
                "language_id": self.bot.language_id,
            },
        )
        if code != 200:
            raise PureYogaAPIError(code, message)
        locations = payload.get("data", {}).get("locations", [])
        self.locations_by_id = {safe_int(item["id"]): item for item in locations}
        return self.locations_by_id

    def location_name(self, location_id: int, fallback: str = "") -> str:
        location = self.locations_by_id.get(location_id, {})
        names = location.get("names", {})
        return names.get("en") or names.get("zh-hk") or names.get("zh-cn") or fallback or str(location_id)

    def fetch_schedule(self, target_date: date, days: int) -> list[dict[str, Any]]:
        payload, _, code, message = self.request_json(
            "GET",
            "view_schedule",
            params={
                "region_id": self.bot.region_id,
                "language_id": self.bot.language_id,
                "location_ids": ",".join(str(value) for value in self.location_ids),
                "start_date": target_date.isoformat(),
                "days": max(1, days),
                "api_version": 3,
            },
        )
        if code != 200:
            raise PureYogaAPIError(code, message)
        return payload.get("data", {}).get("classes", [])

    def fetch_booking_history(self, start_date: date, end_date: date, *, history_type: str = "all") -> list[dict[str, Any]]:
        payload, _, code, message = self.request_json(
            "GET",
            "get_booking_history",
            params={
                "region_id": self.bot.region_id,
                "language_id": self.bot.language_id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "page": 1,
                "per_page": 999,
                "type": history_type,
                "api_version": 3,
            },
        )
        if code != 200:
            raise PureYogaAPIError(code, message)
        return payload.get("data", {}).get("bookings", [])

    def format_class_line(self, item: dict[str, Any], fallback_location_name: str = "") -> str:
        class_type = item.get("class_type", {})
        teacher = item.get("teacher", {})
        location_id = safe_int(item.get("location_id"))
        return (
            f"{item.get('start_date')} {item.get('start_time_display')} | "
            f"{class_type.get('name', 'Unknown')} | "
            f"{self.location_name(location_id, fallback_location_name)} | "
            f"{teacher.get('full_name') or teacher.get('name', 'Unknown teacher')} | "
            f"class_id={item.get('id')}"
        )

    def list_classes(self, classes: list[dict[str, Any]], target_date: date) -> None:
        target_date_str = target_date.isoformat()
        rows = [item for item in classes if item.get("start_date") == target_date_str]
        if not rows:
            self.log(f"No classes returned for {target_date_str}.")
            return
        self.log(f"Classes returned for {target_date_str}:")
        for item in rows:
            self.log(f"  {self.format_class_line(item)}")

    def login(self, credentials: dict[str, Any]) -> None:
        username = str(credentials.get("username", "")).strip()
        password = str(credentials.get("password", ""))
        if not username or not password:
            raise PureYogaError("Username/password are required for login and booking.")

        payload, response, code, message = self.request_json(
            "POST",
            "login",
            json_body={
                "username": username,
                "password": password,
                "region_id": self.bot.region_id,
                "language_id": self.bot.language_id,
                "jwt": True,
            },
        )
        if code != 200:
            raise PureYogaAPIError(code, message)

        user = payload.get("data", {}).get("user", {})
        jwt = (
            user.get("jwt")
            or payload.get("data", {}).get("jwt")
            or response.headers.get("X-JWT-Token")
            or response.headers.get("x-jwt-token")
        )
        if not jwt:
            raise PureYogaError(f"Login succeeded on {self.label} but no JWT token was returned.")

        self.jwt = str(jwt)
        self.session.headers["X-JWT-Token"] = self.jwt
        self.sync_booking_transport_state()
        self.log("Login succeeded.")

    def bootstrap_and_login(self, credentials: dict[str, Any], *, context: str) -> None:
        max_attempts = max(1, safe_int(self.bot.booking.get("login_retry_attempts", 4)))
        retry_interval = max(50, safe_int(self.bot.booking.get("login_retry_interval_ms", 750))) / 1000.0
        last_error: Exception | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                self.bootstrap_headers()
                self.login(credentials)
                if attempt > 1:
                    self.log(f"{context} recovered on attempt {attempt}/{max_attempts}.")
                return
            except (PureYogaError, requests.RequestException) as exc:
                last_error = exc
                if attempt >= max_attempts:
                    break
                self.log(
                    f"{context} attempt {attempt}/{max_attempts} failed: {type(exc).__name__}: {exc}. "
                    f"Retrying in {retry_interval:.3f}s."
                )
                time.sleep(retry_interval)

        raise PureYogaError(
            f"{context} failed after {max_attempts} attempts: {type(last_error).__name__}: {last_error}"
        )

    def clone_for_parallel_requests(self) -> "SiteClient":
        clone = SiteClient(self.bot, self.site, self.location_ids)
        clone.jwt = self.jwt
        clone.locations_by_id = dict(self.locations_by_id)
        clone.session.headers.update(dict(self.session.headers))
        clone.session.cookies.update(self.session.cookies.get_dict())
        if clone.booking_transport is not None and clone.booking_transport is not self.booking_transport:
            try:
                clone.booking_transport.close()
            except Exception:
                pass
        clone.booking_transport = self.booking_transport
        return clone

    def booking_request(
        self,
        class_id: int,
        book_type: int,
        *,
        on_send: Callable[[datetime, str, int], None] | None = None,
    ) -> tuple[int, str, BookingRequestTrace]:
        submitted_dt = self.bot.now()
        submitted_at = submitted_dt.strftime("%H:%M:%S.%f")[:-3]
        send_started_ns = time.time_ns()
        if on_send is not None:
            on_send(submitted_dt, submitted_at, send_started_ns)
        warmup_trace = self.last_transport_warmup_trace
        if warmup_trace is not None:
            warmup_gap_ms = (send_started_ns - warmup_trace.response_received_ns) / 1_000_000
            self.log(f"Gap from late transport warmup to booking POST send: {warmup_gap_ms:.1f}ms.")
            self.last_transport_warmup_trace = None
        booking_payload = {
            "class_id": class_id,
            "book_type": book_type,
            "booked_from": "WEB",
            "language_id": self.bot.language_id,
            "region_id": self.bot.region_id,
        }
        if self.booking_transport is not None:
            response = self.booking_transport.post(
                f"{self.api_base_url}/booking",
                json=booking_payload,
                headers=self.booking_transport_headers(),
            )
            response_reason = response.reason_phrase
        else:
            response = self.session.request(
                method="POST",
                url=f"{self.api_base_url}/booking",
                json=booking_payload,
                headers=self.booking_transport_headers(),
                timeout=self.bot.timeout,
                verify=self.bot.verify_ssl,
            )
            response_reason = response.reason
        response_received_ns = time.time_ns()
        response_at = self.bot.now().strftime("%H:%M:%S.%f")[:-3]
        try:
            payload = response.json()
        except ValueError as exc:
            raise PureYogaError(
                f"Non-JSON response from {self.api_base_url}/booking: "
                f"HTTP {response.status_code} {response.text[:200]}"
            ) from exc

        error_info = payload.get("error", {})
        code = safe_int(error_info.get("code", response.status_code))
        message = str(error_info.get("message", response_reason))
        api_message = payload.get("error", {}).get("message") or message
        trace = BookingRequestTrace(
            class_id=class_id,
            book_type=book_type,
            sent_at=submitted_at,
            response_at=response_at,
            send_started_ns=send_started_ns,
            response_received_ns=response_received_ns,
            http_rtt_ms=(response_received_ns - send_started_ns) / 1_000_000,
            http_version=response_http_version(response),
            response_date=response_header_value(response, "Date"),
            response_via=response_header_value(response, "Via"),
            response_cf_pop=response_header_value(response, "X-Amz-Cf-Pop"),
            response_server_timing=response_header_value(response, "Server-Timing"),
        )
        self.log(
            f"Booking request class_id={class_id} book_type={book_type} "
            f"sent_at={submitted_at} response_at={response_at} "
            f"http_rtt_ms={trace.http_rtt_ms:.1f} code={code}."
        )
        self.log(
            f"Booking response meta class_id={class_id} http_version={trace.http_version or 'unknown'} "
            f"date={trace.response_date or '-'} cf_pop={trace.response_cf_pop or '-'} "
            f"via={trace.response_via or '-'} server_timing={trace.response_server_timing or '-'}."
        )
        return code, str(api_message), trace

    def interpret_schedule_booking_state(
        self,
        class_item: dict[str, Any],
        success_message: str,
    ) -> tuple[str, str] | None:
        button_status = safe_int(class_item.get("button_status"))
        waiting_number = safe_int(class_item.get("waiting_number"))
        clean_success_message = success_message.rstrip(". ")

        if button_status == BUTTON_STATUS_BOOKED:
            return STATUS_BOOKED, clean_success_message or "Success"
        if button_status == BUTTON_STATUS_IN_WAITLIST:
            suffix = f" Current waitlist number: {waiting_number}." if waiting_number else ""
            base_message = clean_success_message or "Success"
            return STATUS_WAITLISTED, f"{base_message}.{suffix}".strip()
        if button_status == BUTTON_STATUS_FULL:
            return STATUS_FAILED, "Class is full and your account is not booked or in the waitlist."
        return None

    def verify_post_booking_result(
        self,
        class_item: dict[str, Any],
        assumed_status: str,
        message: str,
    ) -> tuple[str, int, str]:
        class_id = safe_int(class_item.get("id"))
        start_date = str(class_item.get("start_date", "")).strip()
        if not class_id or not start_date:
            return assumed_status, 200, message

        try:
            target_date = date.fromisoformat(start_date)
        except ValueError:
            return assumed_status, 200, message

        for attempt in range(1, 5):
            try:
                classes = self.fetch_schedule(target_date, 1)
            except PureYogaError as exc:
                self.log(f"Could not refresh schedule to verify booking result: {exc}")
                return assumed_status, 200, message

            refreshed = next((item for item in classes if safe_int(item.get("id")) == class_id), None)
            if not refreshed:
                return assumed_status, 200, message

            interpreted = self.interpret_schedule_booking_state(refreshed, message)
            if interpreted is not None:
                status, resolved_message = interpreted
                return status, 200, resolved_message

            # The schedule can lag briefly right after the booking request.
            button_status = safe_int(refreshed.get("button_status"))
            if button_status in {BUTTON_STATUS_BOOK, BUTTON_STATUS_WAITLIST} and attempt < 4:
                time.sleep(0.35)
                continue

            return assumed_status, 200, message

        return assumed_status, 200, message

    def finalize_deferred_bookings(self, results: list[BookingResult], target_date: date) -> None:
        pending: dict[int, BookingResult] = {}
        for result in results:
            class_id = safe_int((result.class_item or {}).get("id"))
            if not class_id or not result.deferred_confirmation:
                continue
            pending[class_id] = result

        if not pending:
            return

        self.log(f"Refreshing schedule to confirm {len(pending)} deferred booking result(s).")
        for attempt in range(1, 5):
            try:
                classes = self.fetch_schedule(target_date, 1)
            except PureYogaError as exc:
                self.log(f"Could not refresh schedule to verify deferred booking results: {exc}")
                return

            by_id = {safe_int(item.get("id")): item for item in classes}
            unresolved: list[int] = []
            for class_id, result in pending.items():
                refreshed = by_id.get(class_id)
                if not refreshed:
                    unresolved.append(class_id)
                    continue

                result.class_item = refreshed
                interpreted = self.interpret_schedule_booking_state(refreshed, result.message)
                if interpreted is None:
                    unresolved.append(class_id)
                    continue

                result.status, result.message = interpreted
                result.deferred_confirmation = False

            if not unresolved:
                return

            if attempt < 4:
                self.log(
                    f"Deferred verification still pending for {len(unresolved)} class(es); "
                    "retrying after 0.20s."
                )
                time.sleep(0.20)
                continue

            self.log(
                "Deferred verification did not settle before the retry budget ended. "
                "Keeping the provisional booking statuses."
            )
            return

    def attempt_booking(
        self,
        class_item: dict[str, Any],
        *,
        defer_confirmation: bool = False,
        aggressive_probe_enabled_override: bool | None = None,
        probe_release_notifier: Callable[[datetime, str], None] | None = None,
    ) -> tuple[str, int, str, BookingRequestTrace | None]:
        class_id = safe_int(class_item.get("id"))
        button_status = safe_int(class_item.get("button_status"))
        waiting_number = safe_int(class_item.get("waiting_number"))
        aggressive_probe_enabled = (
            bool(self.bot.booking.get("aggressive_probe_enabled", False))
            if aggressive_probe_enabled_override is None
            else bool(aggressive_probe_enabled_override)
        )
        aggressive_probe_max_retries = max(1, safe_int(self.bot.booking.get("aggressive_probe_max_retries", 40)))
        aggressive_probe_retry_interval = (
            max(1, safe_int(self.bot.booking.get("aggressive_probe_retry_interval_ms", 15))) / 1000.0
        )
        max_retries = max(1, safe_int(self.bot.booking.get("max_booking_retries", 15)))
        retry_interval = max(1, safe_int(self.bot.booking.get("retry_interval_ms", 100))) / 1000.0
        waitlist_fallback = bool(self.bot.booking.get("waitlist_fallback", True))
        pre_open_retry_count = 0

        if button_status == BUTTON_STATUS_BOOKED:
            return STATUS_BOOKED, 200, "Already booked according to the live schedule state.", None

        if button_status == BUTTON_STATUS_IN_WAITLIST:
            suffix = f" Current waitlist number: {waiting_number}." if waiting_number else ""
            return STATUS_WAITLISTED, 200, f"Already in waitlist according to the live schedule state.{suffix}", None

        if button_status == BUTTON_STATUS_FULL:
            return (
                STATUS_FAILED,
                409,
                "Class is marked full in the live schedule and waitlist is not available.",
                None,
            )

        initial_book_type = 2 if button_status == BUTTON_STATUS_WAITLIST else 1
        initial_status = STATUS_WAITLISTED if initial_book_type == 2 else STATUS_BOOKED
        if initial_book_type == 2:
            self.log("Live schedule shows waitlist mode. Submitting a waitlist request directly.")
        elif button_status == BUTTON_STATUS_LAST_CHANCE:
            self.log("Live schedule shows last-chance booking mode. Submitting a normal booking request.")

        total_attempts = max_retries + (aggressive_probe_max_retries if aggressive_probe_enabled else 0)
        for attempt in range(1, total_attempts + 1):
            on_send = None
            if probe_release_notifier is not None and pre_open_retry_count > 0:
                def on_send(submitted_dt: datetime, submitted_at: str, send_started_ns: int) -> None:
                    probe_release_notifier(submitted_dt, submitted_at)

            code, message, trace = self.booking_request(class_id, initial_book_type, on_send=on_send)
            if code == 200:
                if pre_open_retry_count:
                    self.log(
                        f"Booking gate opened after {pre_open_retry_count} early probe "
                        f"attempt(s) for class_id={class_id}."
                    )
                if defer_confirmation:
                    self.log("Deferring post-booking schedule verification until the current batch has been submitted.")
                    return initial_status, 200, message, trace
                status, verify_code, verify_message = self.verify_post_booking_result(class_item, initial_status, message)
                return status, verify_code, verify_message, trace

            if code == 409 and waitlist_fallback and initial_book_type == 1:
                self.log("Class filled before the booking landed. Retrying once on the waitlist.")
                waitlist_code, waitlist_message, waitlist_trace = self.booking_request(class_id, 2)
                if waitlist_code == 200:
                    if defer_confirmation:
                        self.log(
                            "Deferring waitlist verification until the current batch has been submitted."
                        )
                        return STATUS_WAITLISTED, waitlist_code, waitlist_message, waitlist_trace
                    return STATUS_WAITLISTED, waitlist_code, waitlist_message, waitlist_trace
                return STATUS_FAILED, waitlist_code, waitlist_message, waitlist_trace

            if code == 401 and attempt < max_retries:
                self.log("JWT expired or session was replaced. Refreshing headers and logging in again.")
                self.bootstrap_and_login(self.bot.config["credentials"], context="Mid-booking re-login")
                continue

            if code in {426, 428} and attempt < total_attempts:
                if aggressive_probe_enabled and pre_open_retry_count < aggressive_probe_max_retries:
                    pre_open_retry_count += 1
                    time.sleep(aggressive_probe_retry_interval)
                    continue

                self.log(
                    f"Attempt {attempt}/{total_attempts} returned code {code} ({message}). "
                    f"Retrying in {retry_interval:.3f}s."
                )
                time.sleep(retry_interval)
                continue

            return STATUS_FAILED, code, message, trace

        return STATUS_FAILED, 999, "Retries exhausted.", None


class PureYogaBot:
    def __init__(self, config: dict[str, Any], config_path: Path):
        self.config = config
        self.config_path = config_path.resolve()
        self.base_dir = self.config_path.parent
        runtime = config["runtime"]
        self.tz, self.tz_source = load_runtime_timezone(str(runtime["timezone"]))
        self.runtime_timezone_name = str(runtime["timezone"])
        self.timeout = int(runtime["request_timeout_seconds"])
        self.verify_ssl = bool(runtime["verify_ssl"])
        self.region_id = safe_int(config["region_id"])
        self.language_id = str(config["language_id"])
        self.booking = config["booking"]
        self.notifications = config["notifications"]
        self.server_time_offset_ms = 0.0
        self._server_time_samples = 0
        self._batch_sequence = 0
        self.summary_notes: list[str] = []

        if self.region_id not in WEB_REGION_CODES or self.region_id not in API_BASE_URLS:
            raise PureYogaError(
                f"Unsupported region_id {self.region_id}. This bot is currently configured for region_id 1 (HK) and 2 (SG)."
            )

        logs_dir = self.base_dir / runtime["logs_dir"]
        logs_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = logs_dir / f"pure_booking_{datetime.now(self.tz).strftime('%Y%m%d')}.log"
        self._log_lock = threading.Lock()
        try:
            self._log_handle = self.log_path.open("a", encoding="utf-8", buffering=1)
        except OSError:
            self._log_handle = None
        if self.tz_source == "fixed-offset":
            self.log(
                f"Timezone data for '{self.runtime_timezone_name}' was unavailable on this Python install. "
                "Using the bot's built-in fixed-offset fallback. Installing 'tzdata' is still recommended."
            )

    @property
    def web_region_code(self) -> str:
        return WEB_REGION_CODES[self.region_id]

    def log(self, message: str) -> None:
        timestamp = self.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        line = f"[{timestamp}] {message}"
        with self._log_lock:
            print(line)
            if self._log_handle is not None:
                try:
                    self._log_handle.write(line + "\n")
                except OSError:
                    self._log_handle = None

    def now(self) -> datetime:
        adjusted_epoch_seconds = time.time() + (self.server_time_offset_ms / 1000.0)
        return datetime.fromtimestamp(adjusted_epoch_seconds, tz=self.tz)

    def next_batch_id(self, site: str, target_date: date) -> str:
        self._batch_sequence += 1
        return f"{site}-{target_date.strftime('%Y%m%d')}-{self._batch_sequence:03d}"

    def observe_server_time_sample(self, server_timestamp_ms: str, started_at_ms: float, finished_at_ms: float) -> None:
        server_ms = safe_int(server_timestamp_ms)
        if not server_ms:
            return
        midpoint_ms = (started_at_ms + finished_at_ms) / 2.0
        observed_offset_ms = server_ms - midpoint_ms
        if abs(observed_offset_ms) > 30_000:
            return

        if self._server_time_samples == 0:
            self.server_time_offset_ms = float(observed_offset_ms)
        else:
            self.server_time_offset_ms = (self.server_time_offset_ms * 0.7) + (observed_offset_ms * 0.3)
        self._server_time_samples += 1

    def build_targets(self) -> list[TargetSpec]:
        targets_raw = list(self.config.get("targets") or [])
        if not targets_raw:
            legacy = dict(TARGET_DEFAULTS)
            legacy.update(self.config.get("target", {}))
            legacy["site"] = legacy.get("site", "yoga")
            targets_raw = [legacy]

        targets: list[TargetSpec] = []
        for index, raw in enumerate(targets_raw, start=1):
            merged = dict(TARGET_DEFAULTS)
            merged.update(raw)
            site = canonical_site(str(merged.get("site", "yoga")))
            class_name = str(merged.get("class_name", "")).strip()
            start_time = str(merged.get("start_time", "")).strip()
            location_id = safe_int(merged.get("location_id"))
            location_name = str(merged.get("location_name", "")).strip()
            if not class_name or not start_time or not (location_id or location_name):
                raise PureYogaError(
                    f"Target #{index} is missing required fields. "
                    "Each target needs class_name, start_time, and location_id or location_name."
                )

            mode = normalize_mode(str(merged.get("mode", "book_all")))
            priority_source = raw.get("priority") if isinstance(raw, dict) else None
            priority = safe_int(priority_source if priority_source not in (None, "") else index)

            targets.append(
                TargetSpec(
                    index=index,
                    site=site,
                    days=parse_days(merged.get("days", [])),
                    class_name=class_name,
                    start_time=start_time,
                    location_id=location_id,
                    location_name=location_name,
                    teacher_name=str(merged.get("teacher_name", "")).strip(),
                    teacher_policy=normalize_teacher_policy(str(merged.get("teacher_policy", "prefer_named_teacher"))),
                    mode=mode,
                    priority=priority,
                    class_date=parse_date_or_blank(str(merged.get("class_date", "")).strip()),
                    booking_run_date=parse_date_or_blank(str(merged.get("booking_run_date", "")).strip()),
                    skip_booking_run_dates=[
                        parsed
                        for item in (merged.get("skip_booking_run_dates") or [])
                        if (parsed := parse_date_or_blank(str(item).strip())) is not None
                    ],
                    class_days_ahead=max(0, safe_int(merged.get("class_days_ahead", 5))),
                    booking_open_days=max(0, safe_int(merged.get("booking_open_days", 5))),
                    schedule_window_days=max(1, safe_int(merged.get("schedule_window_days", 1))),
                )
            )
        return targets

    def resolve_target_date(self, target: TargetSpec, override: str | None) -> date:
        if override:
            try:
                return date.fromisoformat(override)
            except ValueError as exc:
                raise PureYogaError(f"Invalid --target-date '{override}'. Use YYYY-MM-DD.") from exc
        if target.class_date:
            return target.class_date
        today_sg = self.now().date()
        return today_sg + timedelta(days=target.class_days_ahead)

    def booking_open_datetime(self, target: TargetSpec, target_date: date) -> datetime:
        booking_open_date = target_date - timedelta(days=target.booking_open_days)
        return datetime.combine(booking_open_date, parse_clock(str(self.booking["open_time"])), self.tz)

    def is_target_active(self, target: TargetSpec, target_date: date, override: str | None = None) -> bool:
        active_run_date = self.booking_open_datetime(target, target_date).date() if override else self.now().date()
        if active_run_date in target.skip_booking_run_dates:
            return False
        if target.booking_run_date:
            if active_run_date != target.booking_run_date:
                return False
        if not target.days:
            return True
        return target_date.weekday() in target.days

    def wait_until(self, target_dt: datetime) -> None:
        now = self.now()
        if now >= target_dt:
            self.log(f"Booking time already reached ({target_dt.isoformat()}). Proceeding immediately.")
            return

        spin_window = max(10, safe_int(self.booking.get("spin_window_ms", 150))) / 1000.0
        while True:
            now = self.now()
            remaining = (target_dt - now).total_seconds()
            if remaining <= spin_window:
                break
            if remaining > 2:
                time.sleep(min(0.5, remaining / 2))
            else:
                time.sleep(min(0.01, max(0.001, (remaining - spin_window) / 2)))

        while self.now() < target_dt:
            pass

    def resolve_target_match(
        self,
        client: SiteClient,
        target: TargetSpec,
        classes: list[dict[str, Any]],
        target_date: date,
    ) -> ResolvedTarget:
        target_date_str = target_date.isoformat()
        target_name = normalize_text(target.class_name)
        target_time = normalize_time(target.start_time)
        target_teacher = normalize_text(target.teacher_name)
        target_location_name = normalize_text(target.location_name)

        location_matches: list[dict[str, Any]] = []
        time_matches: list[dict[str, Any]] = []
        base_matches: list[dict[str, Any]] = []

        for item in classes:
            if item.get("start_date") != target_date_str:
                continue

            location_id = safe_int(item.get("location_id"))
            class_name = item.get("class_type", {}).get("name", "")
            class_time = item.get("start_time_display") or item.get("start_time")
            location_name = client.location_name(location_id, target.location_name)

            same_location = (target.location_id and location_id == target.location_id) or (
                target_location_name and target_location_name in normalize_text(location_name)
            )
            same_time = normalize_time(class_time) == target_time
            same_name = normalize_text(class_name) == target_name

            if same_location:
                location_matches.append(item)
            if same_location and same_time:
                time_matches.append(item)
            if same_location and same_time and same_name:
                base_matches.append(item)

        if not base_matches:
            if time_matches:
                suggestions = "\n".join(
                    f"  {client.format_class_line(item, target.location_name)}" for item in time_matches[:6]
                )
                return ResolvedTarget(
                    target=target,
                    target_date=target_date,
                    booking_open_dt=self.booking_open_datetime(target, target_date),
                    status=STATUS_NO_MATCH,
                    message=(
                        "No exact class name match at the target time/location.\n"
                        f"Closest matches:\n{suggestions}"
                    ),
                )
            if location_matches:
                suggestions = "\n".join(
                    f"  {client.format_class_line(item, target.location_name)}" for item in location_matches[:6]
                )
                return ResolvedTarget(
                    target=target,
                    target_date=target_date,
                    booking_open_dt=self.booking_open_datetime(target, target_date),
                    status=STATUS_NO_MATCH,
                    message=(
                        "No exact class/time match at the target location.\n"
                        f"Closest matches:\n{suggestions}"
                    ),
                )
            return ResolvedTarget(
                target=target,
                target_date=target_date,
                booking_open_dt=self.booking_open_datetime(target, target_date),
                status=STATUS_NO_MATCH,
                message="No matching class found at the target location. The class may be cancelled that day.",
            )

        if not target_teacher or target.teacher_policy == "any_teacher":
            if len(base_matches) == 1:
                return ResolvedTarget(
                    target=target,
                    target_date=target_date,
                    booking_open_dt=self.booking_open_datetime(target, target_date),
                    status="MATCHED",
                    message="Matched target class.",
                    class_item=base_matches[0],
                )
            details = "\n".join(f"  {client.format_class_line(item, target.location_name)}" for item in base_matches)
            return ResolvedTarget(
                target=target,
                target_date=target_date,
                booking_open_dt=self.booking_open_datetime(target, target_date),
                status=STATUS_NO_MATCH,
                message=f"Multiple classes matched. Add teacher_name to disambiguate.\n{details}",
            )

        teacher_matches = []
        for item in base_matches:
            teacher = item.get("teacher", {})
            teacher_name = teacher.get("full_name") or teacher.get("name", "")
            if target_teacher in normalize_text(teacher_name):
                teacher_matches.append(item)

        if teacher_matches:
            if len(teacher_matches) == 1:
                return ResolvedTarget(
                    target=target,
                    target_date=target_date,
                    booking_open_dt=self.booking_open_datetime(target, target_date),
                    status="MATCHED",
                    message="Matched target class with the named teacher.",
                    class_item=teacher_matches[0],
                )
            details = "\n".join(
                f"  {client.format_class_line(item, target.location_name)}" for item in teacher_matches
            )
            return ResolvedTarget(
                target=target,
                target_date=target_date,
                booking_open_dt=self.booking_open_datetime(target, target_date),
                status=STATUS_NO_MATCH,
                message=f"Multiple classes matched the named teacher.\n{details}",
            )

        if target.teacher_policy == "exact":
            return ResolvedTarget(
                target=target,
                target_date=target_date,
                booking_open_dt=self.booking_open_datetime(target, target_date),
                status=STATUS_NO_MATCH,
                message=(
                    "The class exists at the target time/location, but the named teacher is not scheduled. "
                    "Teacher policy is exact, so the bot will not book a replacement teacher."
                ),
            )

        if len(base_matches) == 1:
            replacement_teacher = (
                base_matches[0].get("teacher", {}).get("full_name")
                or base_matches[0].get("teacher", {}).get("name")
                or "Unknown teacher"
            )
            return ResolvedTarget(
                target=target,
                target_date=target_date,
                booking_open_dt=self.booking_open_datetime(target, target_date),
                status="MATCHED",
                message=(
                    f"Named teacher not found. Falling back to replacement teacher '{replacement_teacher}' "
                    "for the same class/time/location."
                ),
                class_item=base_matches[0],
            )

        details = "\n".join(f"  {client.format_class_line(item, target.location_name)}" for item in base_matches)
        return ResolvedTarget(
            target=target,
            target_date=target_date,
            booking_open_dt=self.booking_open_datetime(target, target_date),
            status=STATUS_NO_MATCH,
            message=(
                "Named teacher not found and multiple replacement-teacher classes match the same class/time/location.\n"
                f"{details}"
            ),
        )

    def format_target_summary(self, result: ResolvedTarget | BookingResult, client: SiteClient | None = None) -> str:
        class_item = result.class_item
        message = (result.message or "").strip()
        if class_item:
            teacher = class_item.get("teacher", {})
            class_line = (
                f"{class_item.get('start_date')} {class_item.get('start_time_display')} | "
                f"{class_item.get('class_type', {}).get('name', 'Unknown')} | "
                f"{teacher.get('full_name') or teacher.get('name', 'Unknown teacher')}"
            )
            location_line = result.target.location_name or result.target.location_id
        else:
            class_line = result.target.label
            location_line = ""

        lines = [f"{result.status} | {class_line}"]
        if location_line:
            lines.append(str(location_line))

        if result.status == STATUS_WAITLISTED:
            waiting_number = safe_int((class_item or {}).get("waiting_number"))
            if waiting_number:
                lines.append(f"Waitlist number: {waiting_number}")
            elif message and normalize_text(message) != "success":
                lines.append(message)
        elif result.status not in {STATUS_BOOKED, "MATCHED"} and message:
            lines.append(message)

        return "\n".join(lines)

    def send_telegram(self, text: str) -> None:
        token = str(self.notifications.get("telegram_bot_token", "")).strip()
        chat_id = str(self.notifications.get("telegram_chat_id", "")).strip()
        if not token or not chat_id:
            return
        post_telegram_message(token, chat_id, text, timeout=self.timeout, verify_ssl=self.verify_ssl)

    def notify_summary(self, lines: list[str]) -> None:
        text = "\n\n".join(lines)
        for line in lines:
            self.log(line)
        try:
            self.send_telegram(text)
        except Exception as exc:
            self.log(f"Telegram notification failed: {type(exc).__name__}: {exc}")

    def record_latency_note(self, site: str, batch_id: str, warmup_rtt_ms: float) -> None:
        threshold_ms = max(0, safe_int(self.booking.get("latency_warning_warmup_rtt_ms", 150)))
        if threshold_ms and warmup_rtt_ms > threshold_ms:
            note = (
                f"Note: {site} network/backend latency was elevated before booking "
                f"({batch_id} warmup RTT {warmup_rtt_ms:.1f}ms)."
            )
            if note not in self.summary_notes:
                self.summary_notes.append(note)

    def planned_occurrences_for_window(self, start_date: date, end_date: date) -> list[PlannedOccurrence]:
        occurrences: list[PlannedOccurrence] = []
        targets = self.build_targets()
        for target in targets:
            if target.class_date:
                class_dates = [target.class_date]
            else:
                class_dates = [
                    start_date + timedelta(days=offset)
                    for offset in range((end_date - start_date).days + 1)
                    if (start_date + timedelta(days=offset)).weekday() in target.days
                ]

            for class_date in class_dates:
                if class_date < start_date or class_date > end_date:
                    continue
                booking_run_date = class_date - timedelta(days=target.booking_open_days)
                if booking_run_date in target.skip_booking_run_dates:
                    continue
                occurrences.append(
                    PlannedOccurrence(
                        target=target,
                        class_date=class_date,
                        class_type=booking_limit_class_type(target),
                    )
                )
        return occurrences

    def existing_booking_occurrences_for_window(
        self,
        active_targets: list[tuple[TargetSpec, date, datetime]],
        start_date: date,
        end_date: date,
    ) -> list[ExistingBookingOccurrence]:
        if not bool(self.booking.get("include_existing_bookings_in_limit_warnings", True)):
            return []

        location_ids = sorted({target.location_id for target, _, _ in active_targets if target.location_id})
        site = "yoga"
        if active_targets and not any(target.site == "yoga" for target, _, _ in active_targets):
            site = active_targets[0][0].site

        client = SiteClient(self, site, location_ids)
        client.bootstrap_and_login(self.config["credentials"], context="Existing bookings warning check")
        bookings = client.fetch_booking_history(start_date, end_date, history_type="all")

        occurrences: list[ExistingBookingOccurrence] = []
        for booking in bookings:
            class_item = booking.get("class") or {}
            class_date = parse_date_or_blank(str(class_item.get("start_date", "")).strip())
            if not class_date or class_date < start_date or class_date > end_date:
                continue

            button_status = safe_int(booking.get("button_status"))
            if button_status not in {
                BUTTON_STATUS_BOOKED,
                BUTTON_STATUS_IN_WAITLIST,
                BUTTON_STATUS_SIGNED_IN,
            }:
                continue

            class_type = class_item.get("class_type") or {}
            location = class_item.get("location") or {}
            location_name = str(
                location.get("name")
                or (location.get("names") or {}).get("en")
                or class_item.get("location_name")
                or ""
            )
            status = "waitlisted" if button_status == BUTTON_STATUS_IN_WAITLIST else "booked"
            if button_status == BUTTON_STATUS_SIGNED_IN:
                status = "signed in"
            occurrences.append(
                ExistingBookingOccurrence(
                    class_date=class_date,
                    start_time=str(class_item.get("start_time_display") or class_item.get("start_time") or ""),
                    class_name=str(class_type.get("name") or class_item.get("class_name") or "Unknown class"),
                    location_name=location_name,
                    class_type=booking_limit_class_type_from_booking(booking),
                    status=status,
                )
            )

        self.log(
            f"Existing bookings warning check found {len(occurrences)} booked/waitlisted/signed-in "
            f"class(es) from {start_date.isoformat()} to {end_date.isoformat()}."
        )
        return occurrences

    def occurrence_key(self, item: PlannedOccurrence | ExistingBookingOccurrence) -> tuple[str, str, str, str]:
        if isinstance(item, PlannedOccurrence):
            return (
                item.class_date.isoformat(),
                normalize_time(item.target.start_time),
                normalize_text(item.target.class_name),
                normalize_text(item.target.location_name),
            )
        return (
            item.class_date.isoformat(),
            normalize_time(item.start_time),
            normalize_text(item.class_name),
            normalize_text(item.location_name),
        )

    def booking_limit_warning_lines(
        self,
        active_targets: list[tuple[TargetSpec, date, datetime]],
        existing_occurrences: list[ExistingBookingOccurrence] | None = None,
    ) -> list[str]:
        if not active_targets:
            return []

        active_dates = sorted({target_date for _, target_date, _ in active_targets})
        start_date = min(active_dates) - timedelta(days=4)
        end_date = max(active_dates) + timedelta(days=4)
        planned_occurrences = self.planned_occurrences_for_window(start_date, end_date)
        existing_occurrences = existing_occurrences or []
        existing_keys = {self.occurrence_key(item) for item in existing_occurrences}
        occurrences: list[PlannedOccurrence | ExistingBookingOccurrence] = list(existing_occurrences)
        occurrences.extend(
            item for item in planned_occurrences if self.occurrence_key(item) not in existing_keys
        )
        warning_lines: list[str] = []

        for class_date in active_dates:
            same_day = [item for item in occurrences if item.class_date == class_date]
            for class_type in ("Yoga", "Pilates", "Fitness"):
                count = sum(1 for item in same_day if item.class_type == class_type)
                if count > 2:
                    warning_lines.append(
                        f"{class_date.isoformat()}: {count} {class_type} booking(s) already booked/waitlisted "
                        "or planned; Pure daily limit is 2."
                    )

        window_start = start_date
        while window_start <= end_date - timedelta(days=4):
            window_end = window_start + timedelta(days=4)
            if any(window_start <= active_date <= window_end for active_date in active_dates):
                in_window = [
                    item for item in occurrences if window_start <= item.class_date <= window_end
                ]
                for class_type in ("Yoga", "Pilates", "Fitness"):
                    count = sum(1 for item in in_window if item.class_type == class_type)
                    if count > 6:
                        warning_lines.append(
                            f"{window_start.isoformat()} to {window_end.isoformat()}: "
                            f"{count} {class_type} booking(s) already booked/waitlisted or planned; "
                            "Pure 5-day limit is 6."
                        )
            window_start += timedelta(days=1)

        return sorted(set(warning_lines))

    def schedule_change_warning_lines(self, resolved: list[ResolvedTarget]) -> list[str]:
        warning_lines: list[str] = []
        for item in resolved:
            if item.status == STATUS_NO_MATCH:
                warning_lines.append(
                    f"{item.target.class_name} {item.target.start_time} at {item.target.location_name}: "
                    f"not matched. {item.message.splitlines()[0]}"
                )
                continue

            if item.status != "MATCHED":
                continue

            message = item.message or ""
            if "Falling back to replacement teacher" in message:
                teacher = (
                    (item.class_item or {}).get("teacher", {}).get("full_name")
                    or (item.class_item or {}).get("teacher", {}).get("name")
                    or "replacement teacher"
                )
                warning_lines.append(
                    f"{item.target.class_name} {item.target.start_time} at {item.target.location_name}: "
                    f"teacher changed from {item.target.teacher_name or 'named teacher'} to {teacher}."
                )

        return warning_lines

    def notify_pre_run_warnings(
        self,
        target_date: date,
        active_targets: list[tuple[TargetSpec, date, datetime]],
        resolved: list[ResolvedTarget],
        existing_occurrences: list[ExistingBookingOccurrence] | None = None,
    ) -> None:
        sections: list[str] = []
        limit_lines = self.booking_limit_warning_lines(active_targets, existing_occurrences)
        schedule_lines = self.schedule_change_warning_lines(resolved)

        if limit_lines:
            sections.append("Booking limit warning:\n" + "\n".join(f"- {line}" for line in limit_lines))
        if schedule_lines:
            sections.append("Schedule/teacher warning:\n" + "\n".join(f"- {line}" for line in schedule_lines))
        if not sections:
            return

        text = f"Pure pre-run warning for {target_date.isoformat()}\n\n" + "\n\n".join(sections)
        for section in sections:
            self.log(section)
        try:
            self.send_telegram(text)
        except Exception as exc:
            self.log(f"Telegram pre-run warning failed: {type(exc).__name__}: {exc}")

    def run(self, args: argparse.Namespace) -> int:
        targets = self.build_targets()
        active_targets: list[tuple[TargetSpec, date, datetime]] = []
        for target in targets:
            target_date = self.resolve_target_date(target, args.target_date)
            if not self.is_target_active(target, target_date, args.target_date):
                continue
            active_targets.append((target, target_date, self.booking_open_datetime(target, target_date)))

        self.log(f"Config file: {self.config_path}")

        if not active_targets:
            if args.target_date:
                message = f"No configured targets are active for {args.target_date}."
            else:
                message = "No configured targets are active for this run's rolling target date."
            self.log(message)
            if not args.lookup_only and not args.dry_run:
                self.notify_summary([f"Pure booking run skipped", message])
            return 0

        target_dates = sorted({item[1] for item in active_targets})
        if len(target_dates) > 1:
            raise PureYogaError(
                "This config activates targets with different class dates in the same run. "
                "Split them into separate configs or runs."
            )
        target_date = target_dates[0]

        booking_opens = sorted({item[2] for item in active_targets})
        if len(booking_opens) > 1:
            raise PureYogaError(
                "This config activates targets with different booking-open datetimes in the same run. "
                "Split them into separate configs or runs."
            )
        booking_open_dt = booking_opens[0]
        wake_dt = booking_open_dt - timedelta(seconds=float(self.booking.get("wake_seconds_before", 10)))

        self.log(f"Target class date: {target_date.isoformat()}")
        self.log(f"Booking opens at: {booking_open_dt.isoformat()}")
        self.log("Active targets:")
        for target, _, _ in active_targets:
            self.log(f"  {target.label} | mode={target.mode} | teacher_policy={target.teacher_policy}")

        clients: dict[str, SiteClient] = {}
        resolved: list[ResolvedTarget] = []
        active_by_site: dict[str, list[TargetSpec]] = {}
        for target, _, _ in active_targets:
            active_by_site.setdefault(target.site, []).append(target)

        for site, site_targets in active_by_site.items():
            location_ids = sorted({target.location_id for target in site_targets if target.location_id})
            if not location_ids:
                raise PureYogaError(f"No location IDs resolved for site '{site}'.")

            client = SiteClient(self, site, location_ids)
            clients[site] = client

            client.bootstrap_headers()
            client.fetch_locations()
            schedule_days = max(target.schedule_window_days for target in site_targets)
            classes = client.fetch_schedule(target_date, schedule_days)
            if args.list_classes:
                client.list_classes(classes, target_date)

            for target in site_targets:
                result = self.resolve_target_match(client, target, classes, target_date)
                resolved.append(result)
                if result.status == "MATCHED":
                    self.log(self.format_target_summary(result, client))
                else:
                    self.log(self.format_target_summary(result))

        existing_occurrences: list[ExistingBookingOccurrence] = []
        if not args.lookup_only and not args.dry_run:
            active_dates = sorted({target_date for _, target_date, _ in active_targets})
            history_start = min(active_dates) - timedelta(days=4)
            history_end = max(active_dates) + timedelta(days=4)
            try:
                existing_occurrences = self.existing_booking_occurrences_for_window(
                    active_targets,
                    history_start,
                    history_end,
                )
            except Exception as exc:
                self.log(
                    f"Existing bookings warning check failed: {type(exc).__name__}: {exc}. "
                    "Continuing with config-only booking-limit warnings."
                )
            self.notify_pre_run_warnings(target_date, active_targets, resolved, existing_occurrences)

        if args.lookup_only:
            self.log("Lookup-only mode complete.")
            return 0 if all(item.status == "MATCHED" for item in resolved) else 1

        matched_site_items = [item for item in resolved if item.status == "MATCHED"]
        matched_sites = sorted(
            {item.target.site for item in matched_site_items},
            key=lambda site: min(
                (
                    site_item.target.priority,
                    site_item.target.index,
                    site_item.target.site,
                )
                for site_item in matched_site_items
                if site_item.target.site == site
            ),
        )
        if args.dry_run:
            if not matched_sites:
                self.log("Dry-run mode complete, but no active targets matched the schedule.")
                return 1
            for site in matched_sites:
                clients[site].bootstrap_and_login(self.config["credentials"], context="Dry-run login")
            self.log("Dry-run mode complete. Booking requests were skipped.")
            return 0 if all(item.status == "MATCHED" for item in resolved) else 1

        if not matched_sites:
            summary_lines = [f"Pure booking run for {target_date.isoformat()}"]
            for item in resolved:
                summary_lines.append(self.format_target_summary(item))
            summary_lines.append("No active targets matched the schedule, so no booking requests will be sent.")
            self.notify_summary(summary_lines)
            return 1

        now = self.now()
        if now < wake_dt:
            self.log(f"Sleeping until wake time: {wake_dt.isoformat()}")
            self.wait_until(wake_dt)

        prelogged_site: str | None = None
        if matched_sites:
            prelogged_site = matched_sites[0]
            clients[prelogged_site].bootstrap_and_login(self.config["credentials"], context="Pre-book login")
            clients[prelogged_site].prime_booking_transport()
            if len(matched_sites) > 1:
                self.log(
                    f"Multi-site run detected. Deferring login for remaining site(s) until their turn "
                    f"to avoid session replacement across sites."
                )

        parallel_book_all = bool(self.booking.get("parallel_book_all_submissions", True))
        submission_strategy = normalize_text(str(self.booking.get("book_all_submission_strategy", "parallel")))
        prepared_parallel_batches: dict[str, dict[str, Any]] = {}
        if prelogged_site is not None and parallel_book_all and submission_strategy in {"focusfirst", "parallel"}:
            prelogged_matches = [
                item for item in resolved if item.target.site == prelogged_site and item.status == "MATCHED"
            ]
            prelogged_book_all_targets = sorted(
                [item for item in prelogged_matches if item.target.mode == "book_all"],
                key=lambda item: (item.target.priority, item.target.index),
            )
            if len(prelogged_book_all_targets) > 1:
                request_clients = [
                    clients[prelogged_site].clone_for_parallel_requests() for _ in prelogged_book_all_targets
                ]
                executor = ThreadPoolExecutor(max_workers=len(prelogged_book_all_targets))
                warm_futures = [executor.submit(time.sleep, 0.0) for _ in prelogged_book_all_targets]
                for future in warm_futures:
                    future.result()
                prepared_parallel_batches[prelogged_site] = {
                    "request_clients": request_clients,
                    "executor": executor,
                }
                self.log(
                    f"[{prelogged_site}] Pre-armed booking worker pool for "
                    f"{len(prelogged_book_all_targets)} book-all target(s)."
                )

        booking_start_dt = booking_open_dt
        if bool(self.booking.get("aggressive_probe_enabled", False)):
            probe_lead_ms = max(0, safe_int(self.booking.get("aggressive_probe_lead_ms", 120)))
            if probe_lead_ms > 0:
                booking_start_dt = booking_open_dt - timedelta(milliseconds=probe_lead_ms)
                self.log(
                    f"Aggressive probe mode enabled. Beginning booking attempts at "
                    f"{booking_start_dt.isoformat()} ({probe_lead_ms}ms before open)."
                )

        late_transport_warmup_enabled = bool(self.booking.get("late_transport_warmup_enabled", True))
        late_transport_warmup_ms = max(0, safe_int(self.booking.get("late_transport_warmup_ms_before_open", 500)))
        late_transport_warmup_dt = booking_start_dt - timedelta(milliseconds=late_transport_warmup_ms)
        if (
            prelogged_site is not None
            and late_transport_warmup_enabled
            and late_transport_warmup_ms > 0
            and late_transport_warmup_dt > self.now()
        ):
            self.wait_until(late_transport_warmup_dt)
            clients[prelogged_site].late_warmup_booking_transport()

        self.wait_until(booking_start_dt)

        booking_results: list[BookingResult] = []
        for site in matched_sites:
            client = clients[site]
            if site != prelogged_site:
                client.bootstrap_and_login(self.config["credentials"], context="Deferred multi-site login")
                client.prime_booking_transport()
            site_matches = [item for item in resolved if item.target.site == site and item.status == "MATCHED"]
            priority_targets = sorted(
                [item for item in site_matches if item.target.mode == "priority"],
                key=lambda item: (item.target.priority, item.target.index),
            )
            book_all_targets = sorted(
                [item for item in site_matches if item.target.mode == "book_all"],
                key=lambda item: (item.target.priority, item.target.index),
            )

            priority_done = False
            priority_stop_message = "Skipped because a higher-priority target already resolved this booking window."
            for item in priority_targets:
                if priority_done:
                    booking_results.append(
                        BookingResult(
                            target=item.target,
                            target_date=item.target_date,
                            status=STATUS_SKIPPED,
                            code=0,
                            message=priority_stop_message,
                            class_item=item.class_item,
                        )
                    )
                    continue

                status, code, message, trace = client.attempt_booking(item.class_item or {})
                booking_results.append(
                    BookingResult(
                        target=item.target,
                        target_date=item.target_date,
                        status=status,
                        code=code,
                        message=message,
                        class_item=item.class_item,
                        request_trace=trace,
                    )
                )

                if status == STATUS_BOOKED and bool(self.booking.get("stop_after_first_priority_success", True)):
                    priority_done = True
                    priority_stop_message = (
                        "Skipped because a higher-priority target already booked successfully."
                    )
                elif status == STATUS_WAITLISTED and not bool(
                    self.booking.get("continue_to_next_priority_on_waitlist", True)
                ):
                    priority_done = True
                    priority_stop_message = (
                        "Skipped because a higher-priority target already landed on the waitlist."
                    )

            deferred_site_results: list[BookingResult] = []
            if parallel_book_all and len(book_all_targets) > 1 and submission_strategy == "focusfirst":
                head_start_ms = max(0, safe_int(self.booking.get("focus_first_head_start_ms", 120)))
                focus_item = book_all_targets[0]
                batch_id = self.next_batch_id(site, target_date)
                batch_warmup_trace = client.last_transport_warmup_trace
                self.log(
                    f"[{site}] Batch {batch_id} focus class: "
                    f"{client.format_class_line(focus_item.class_item or {}, focus_item.target.location_name)} "
                    f"(head start {head_start_ms}ms)."
                )
                prepared_batch = prepared_parallel_batches.pop(site, None)
                request_clients = (
                    prepared_batch["request_clients"]
                    if prepared_batch is not None
                    else [client.clone_for_parallel_requests() for _ in book_all_targets]
                )
                executor = (
                    prepared_batch["executor"]
                    if prepared_batch is not None
                    else ThreadPoolExecutor(max_workers=len(book_all_targets))
                )
                release_lock = threading.Lock()
                follower_release_info: dict[str, datetime | str | None] = {
                    "latest_focus_retry_dt": None,
                    "latest_focus_retry_sent_at": None,
                }

                def record_focus_retry_send(submitted_dt: datetime, submitted_at: str) -> None:
                    with release_lock:
                        follower_release_info["latest_focus_retry_dt"] = submitted_dt
                        follower_release_info["latest_focus_retry_sent_at"] = submitted_at
                try:
                    futures: list[Any] = [None] * len(book_all_targets)
                    futures[0] = executor.submit(
                        request_clients[0].attempt_booking,
                        book_all_targets[0].class_item or {},
                        defer_confirmation=True,
                        aggressive_probe_enabled_override=True,
                        probe_release_notifier=record_focus_retry_send,
                    )
                    default_follower_release_dt = booking_start_dt + timedelta(milliseconds=head_start_ms)
                    follower_release_dt = default_follower_release_dt
                    while True:
                        with release_lock:
                            latest_focus_retry_dt = follower_release_info["latest_focus_retry_dt"]
                        desired_release_dt = default_follower_release_dt
                        if isinstance(latest_focus_retry_dt, datetime):
                            desired_release_dt = max(
                                desired_release_dt,
                                latest_focus_retry_dt + timedelta(milliseconds=head_start_ms),
                            )
                        if self.now() >= desired_release_dt:
                            follower_release_dt = desired_release_dt
                            break
                        time.sleep(0.002)
                    for idx in range(1, len(book_all_targets)):
                        futures[idx] = executor.submit(
                            request_clients[idx].attempt_booking,
                            book_all_targets[idx].class_item or {},
                            defer_confirmation=True,
                            aggressive_probe_enabled_override=False,
                        )
                    batch_results = [future.result() for future in futures]
                finally:
                    executor.shutdown(wait=True)
                self.log(
                    f"[{site}] Batch {batch_id} submitted {len(book_all_targets)} book-all target(s) with focus-first strategy "
                    f"(followers released at {follower_release_dt.strftime('%H:%M:%S.%f')[:-3]}, "
                    f"configured head start {head_start_ms}ms); refreshing the schedule to confirm results."
                )
                focus_trace = batch_results[0][3] if batch_results else None
                second_trace = batch_results[1][3] if len(batch_results) > 1 else None
                if focus_trace and second_trace:
                    send_delta_ms = (second_trace.send_started_ns - focus_trace.send_started_ns) / 1_000_000
                    residual_jitter_ms = send_delta_ms - head_start_ms
                    self.log(
                        f"[{site}] Batch {batch_id} focus send delta_ms={send_delta_ms:.1f} "
                        f"configured_head_start_ms={head_start_ms} residual_jitter_ms={residual_jitter_ms:+.1f}."
                    )
                    response_gap_ms = (
                        second_trace.response_received_ns - focus_trace.response_received_ns
                    ) / 1_000_000
                    warmup_rtt_ms = batch_warmup_trace.http_rtt_ms if batch_warmup_trace is not None else None
                    if warmup_rtt_ms is not None:
                        self.record_latency_note(site, batch_id, warmup_rtt_ms)
                        focus_queue_proxy_ms = focus_trace.http_rtt_ms - warmup_rtt_ms
                        follower_queue_proxy_ms = second_trace.http_rtt_ms - warmup_rtt_ms
                        self.log(
                            f"[{site}] Batch {batch_id} response_gap_ms={response_gap_ms:+.1f} "
                            f"warmup_http_rtt_ms={warmup_rtt_ms:.1f} "
                            f"focus_queue_proxy_ms={focus_queue_proxy_ms:+.1f} "
                            f"follower_queue_proxy_ms={follower_queue_proxy_ms:+.1f}."
                        )
                    else:
                        self.log(
                            f"[{site}] Batch {batch_id} response_gap_ms={response_gap_ms:+.1f} "
                            "warmup_http_rtt_ms=unavailable."
                        )
            elif parallel_book_all and len(book_all_targets) > 1:
                batch_id = self.next_batch_id(site, target_date)
                batch_warmup_trace = client.last_transport_warmup_trace
                prepared_batch = prepared_parallel_batches.pop(site, None)
                request_clients = (
                    prepared_batch["request_clients"]
                    if prepared_batch is not None
                    else [client.clone_for_parallel_requests() for _ in book_all_targets]
                )
                executor = (
                    prepared_batch["executor"]
                    if prepared_batch is not None
                    else ThreadPoolExecutor(max_workers=len(book_all_targets))
                )
                try:
                    futures = [
                        executor.submit(request_client.attempt_booking, item.class_item or {}, defer_confirmation=True)
                        for request_client, item in zip(request_clients, book_all_targets)
                    ]
                    batch_results = [future.result() for future in futures]
                finally:
                    executor.shutdown(wait=True)
                self.log(
                    f"[{site}] Batch {batch_id} submitted {len(book_all_targets)} book-all target(s) in parallel; "
                    "refreshing the schedule to confirm results."
                )
                first_trace = batch_results[0][3] if batch_results else None
                second_trace = batch_results[1][3] if len(batch_results) > 1 else None
                if first_trace and second_trace:
                    send_delta_ms = (second_trace.send_started_ns - first_trace.send_started_ns) / 1_000_000
                    response_gap_ms = (
                        second_trace.response_received_ns - first_trace.response_received_ns
                    ) / 1_000_000
                    self.log(
                        f"[{site}] Batch {batch_id} parallel send delta_ms={send_delta_ms:.1f} "
                        f"configured_head_start_ms=0 response_gap_ms={response_gap_ms:+.1f}."
                    )
                    if batch_warmup_trace is not None:
                        warmup_rtt_ms = batch_warmup_trace.http_rtt_ms
                        self.record_latency_note(site, batch_id, warmup_rtt_ms)
                        self.log(
                            f"[{site}] Batch {batch_id} warmup_http_rtt_ms={warmup_rtt_ms:.1f} "
                            f"first_queue_proxy_ms={first_trace.http_rtt_ms - warmup_rtt_ms:+.1f} "
                            f"second_queue_proxy_ms={second_trace.http_rtt_ms - warmup_rtt_ms:+.1f}."
                        )
            else:
                batch_results = [
                    client.attempt_booking(item.class_item or {}, defer_confirmation=True) for item in book_all_targets
                ]
                if book_all_targets:
                    self.log(
                        f"[{site}] Submitted {len(book_all_targets)} book-all target(s); "
                        "refreshing the schedule to confirm results."
                    )

            for item, (status, code, message, trace) in zip(book_all_targets, batch_results):
                result = BookingResult(
                    target=item.target,
                    target_date=item.target_date,
                    status=status,
                    code=code,
                    message=message,
                    class_item=item.class_item,
                    deferred_confirmation=(code == 200 and status in {STATUS_BOOKED, STATUS_WAITLISTED}),
                    request_trace=trace,
                )
                booking_results.append(result)
                if result.deferred_confirmation:
                    deferred_site_results.append(result)

            if deferred_site_results:
                client.finalize_deferred_bookings(deferred_site_results, target_date)

        summary_lines = [
            f"Pure booking run for {target_date.isoformat()}",
        ]
        any_failure = False
        for item in resolved:
            if item.status != "MATCHED":
                summary_lines.append(self.format_target_summary(item))
                any_failure = True
        for item in booking_results:
            summary_lines.append(self.format_target_summary(item))
            if item.status == STATUS_FAILED:
                any_failure = True
        summary_lines.extend(self.summary_notes)

        self.notify_summary(summary_lines)

        return 1 if any_failure else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pure recurring booking bot")
    parser.add_argument(
        "--config",
        default="pure_yoga_config.json",
        help="Path to the bot config JSON file.",
    )
    parser.add_argument(
        "--target-date",
        help="Override the target class date in YYYY-MM-DD for lookup/dry-run/manual tests.",
    )
    parser.add_argument(
        "--lookup-only",
        action="store_true",
        help="Resolve active targets for the chosen date and exit. No login and no booking.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve active targets, test login on the required site(s), then exit before booking.",
    )
    parser.add_argument(
        "--list-classes",
        action="store_true",
        help="Print every class returned for the active site(s) and target date.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    config_path = Path(args.config)
    config: dict[str, Any] | None = None

    try:
        config = load_config(config_path)
        bot = PureYogaBot(config, config_path)
        return bot.run(args)
    except requests.exceptions.SSLError as exc:
        if not args.lookup_only and not args.dry_run:
            safe_notify_from_config(
                config,
                f"Pure booking run failed with SSL verification error.\n{type(exc).__name__}: {exc}",
            )
        print(
            "SSL verification failed. If your VPS is missing CA certificates, "
            "set runtime.verify_ssl to false in the config and try again.",
            file=sys.stderr,
        )
        print(str(exc), file=sys.stderr)
        return 1
    except requests.RequestException as exc:
        if not args.lookup_only and not args.dry_run:
            safe_notify_from_config(
                config,
                f"Pure booking run failed with network error.\n{type(exc).__name__}: {exc}",
            )
        print(f"Network error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    except (PureYogaError, json.JSONDecodeError) as exc:
        if not args.lookup_only and not args.dry_run:
            safe_notify_from_config(config, f"Pure booking run failed.\n{type(exc).__name__}: {exc}")
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
