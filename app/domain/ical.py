"""Pure iCalendar primitives for availability synchronization.

This module deliberately has no database, scheduler, HTTP, or provider API
dependencies.  It parses complete snapshots, exports deterministic calendars,
merges revisions idempotently, and reports interval overlaps.  Persistence,
missing-event tombstones, delivery retries, and business conflict severity
belong to the future availability-ledger application layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from enum import Enum
from hashlib import sha256
from typing import Iterable, Mapping


EventKey = tuple[str, str]


class ICalendarError(ValueError):
    """Raised when an iCalendar snapshot violates the supported contract."""


class ICalendarRevisionConflict(ICalendarError):
    """Raised when one event revision contains contradictory semantics."""


class ICalendarStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    TENTATIVE = "TENTATIVE"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True, slots=True)
class AvailabilityEvent:
    """One source-owned availability event using a half-open date interval."""

    origin: str
    uid: str
    start: date
    end: date
    dtstamp: datetime
    sequence: int = 0
    status: ICalendarStatus = ICalendarStatus.CONFIRMED
    upstream_origin: str | None = None

    def __post_init__(self) -> None:
        _validate_identifier(self.origin, "origin")
        _validate_identifier(self.uid, "UID", max_length=512)
        if self.upstream_origin is not None:
            _validate_identifier(self.upstream_origin, "X-EASYCAMP-ORIGIN")
        if self.start >= self.end:
            raise ICalendarError("DTEND must be later than DTSTART")
        if self.dtstamp.tzinfo is None or self.dtstamp.utcoffset() is None:
            raise ICalendarError("DTSTAMP must be timezone-aware")
        if self.sequence < 0:
            raise ICalendarError("SEQUENCE must be a non-negative integer")

    @property
    def key(self) -> EventKey:
        return (self.origin, self.uid)

    @property
    def active(self) -> bool:
        return self.status is not ICalendarStatus.CANCELLED

    @property
    def semantic_fingerprint(self) -> str:
        """Stable semantic hash; intentionally excludes transport timestamp."""

        raw = "\x1f".join(
            (
                self.origin,
                self.uid,
                self.start.isoformat(),
                self.end.isoformat(),
                str(self.sequence),
                self.status.value,
                self.upstream_origin or "",
            )
        )
        return sha256(raw.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class SnapshotImportResult:
    """Result of an idempotent, non-destructive snapshot merge."""

    events: tuple[AvailabilityEvent, ...]
    added: tuple[EventKey, ...]
    updated: tuple[EventKey, ...]
    unchanged: tuple[EventKey, ...]
    stale: tuple[EventKey, ...]
    missing: tuple[EventKey, ...]


@dataclass(frozen=True, slots=True)
class IntervalConflict:
    """An overlap between two active events for the same availability unit."""

    left: EventKey
    right: EventKey
    start: date
    end: date


def parse_ical(payload: str | bytes, *, origin: str) -> tuple[AvailabilityEvent, ...]:
    """Parse a complete availability snapshot.

    The supported lodging profile requires VEVENT, UID, UTC DTSTAMP, DTSTART,
    and DTEND.  Occupancy values must be unambiguous DATE values.  Recurrences
    and timed occupancy are rejected instead of being guessed.
    """

    _validate_identifier(origin, "origin")
    text = _decode_payload(payload)
    lines = _unfold_lines(text)
    if len(lines) < 3 or lines[0] != "BEGIN:VCALENDAR" or lines[-1] != "END:VCALENDAR":
        raise ICalendarError("snapshot must contain exactly one VCALENDAR envelope")

    version_count = 0
    event_properties: list[tuple[str, Mapping[str, str], str]] | None = None
    events: list[AvailabilityEvent] = []

    for line in lines[1:-1]:
        name, params, value = _parse_content_line(line)
        if event_properties is None:
            if name == "BEGIN":
                if value != "VEVENT":
                    raise ICalendarError(f"unsupported calendar component: {value}")
                event_properties = []
            elif name == "END":
                raise ICalendarError(f"unexpected component end: {value}")
            elif name == "VERSION":
                version_count += 1
                if version_count > 1 or value != "2.0":
                    raise ICalendarError("VCALENDAR must declare VERSION:2.0 once")
            continue

        if name == "BEGIN":
            raise ICalendarError(f"nested component is not supported: {value}")
        if name == "END":
            if value != "VEVENT":
                raise ICalendarError(f"unexpected component end: {value}")
            events.append(_build_event(event_properties, origin=origin))
            event_properties = None
            continue
        event_properties.append((name, params, value))

    if event_properties is not None:
        raise ICalendarError("VEVENT is not closed")
    if version_count != 1:
        raise ICalendarError("VCALENDAR must declare VERSION:2.0 once")

    # Reject contradictory duplicate revisions before a caller can persist any
    # part of a snapshot. Exact retransmissions are safely collapsed.
    return tuple(_deduplicate_revisions(events).values())


def export_ical(
    events: Iterable[AvailabilityEvent],
    *,
    calendar_name: str = "EasyCamp availability",
    exclude_origin: str | None = None,
    product_id: str = "-//EasyCamp//Availability Ledger//EN",
) -> str:
    """Export deterministic, privacy-minimal iCalendar content.

    ``exclude_origin`` supports target-specific feeds: a target never receives
    the event that originally came from that same target.  Event descriptions
    and guest details are intentionally not accepted by this API.
    """

    _validate_text(calendar_name, "calendar_name")
    _validate_text(product_id, "product_id")
    if exclude_origin is not None:
        _validate_identifier(exclude_origin, "exclude_origin")

    selected = [event for event in events if event.origin != exclude_origin]
    selected.sort(key=lambda event: (event.start, event.end, event.origin, event.uid))

    content_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{_escape_text(product_id)}",
        "CALSCALE:GREGORIAN",
        f"X-WR-CALNAME:{_escape_text(calendar_name)}",
    ]
    for event in selected:
        content_lines.extend(
            (
                "BEGIN:VEVENT",
                f"UID:{_escape_text(event.uid)}",
                f"DTSTAMP:{_format_dtstamp(event.dtstamp)}",
                f"DTSTART;VALUE=DATE:{event.start:%Y%m%d}",
                f"DTEND;VALUE=DATE:{event.end:%Y%m%d}",
                f"SEQUENCE:{event.sequence}",
                f"STATUS:{event.status.value}",
                "TRANSP:OPAQUE",
                "SUMMARY:Unavailable",
                f"X-EASYCAMP-ORIGIN:{_escape_text(event.origin)}",
                "END:VEVENT",
            )
        )
    content_lines.append("END:VCALENDAR")
    return "\r\n".join(_fold_content_line(line) for line in content_lines) + "\r\n"


def import_snapshot(
    current: Iterable[AvailabilityEvent],
    incoming: Iterable[AvailabilityEvent],
) -> SnapshotImportResult:
    """Merge a complete snapshot without treating absence as cancellation.

    A producer must increase SEQUENCE when event semantics change.  Missing
    events are reported but retained.  A future reconciliation layer may turn
    repeated, successful absence into a tombstone according to source policy.
    """

    current_by_key = _deduplicate_revisions(current)
    incoming_by_key = _deduplicate_revisions(incoming)
    merged = dict(current_by_key)
    added: list[EventKey] = []
    updated: list[EventKey] = []
    unchanged: list[EventKey] = []
    stale: list[EventKey] = []

    for key, candidate in incoming_by_key.items():
        existing = current_by_key.get(key)
        if existing is None:
            merged[key] = candidate
            added.append(key)
            continue
        if candidate.sequence < existing.sequence:
            stale.append(key)
            continue
        if candidate.sequence == existing.sequence:
            if candidate.semantic_fingerprint != existing.semantic_fingerprint:
                raise ICalendarRevisionConflict(
                    f"event {key!r} changed without increasing SEQUENCE"
                )
            unchanged.append(key)
            # Keep the newer transport timestamp without recording a semantic
            # update. This remains idempotent and improves audit freshness.
            if candidate.dtstamp > existing.dtstamp:
                merged[key] = candidate
            continue
        merged[key] = candidate
        updated.append(key)

    missing = sorted(set(current_by_key) - set(incoming_by_key))
    return SnapshotImportResult(
        events=tuple(merged[key] for key in sorted(merged)),
        added=tuple(sorted(added)),
        updated=tuple(sorted(updated)),
        unchanged=tuple(sorted(unchanged)),
        stale=tuple(sorted(stale)),
        missing=tuple(missing),
    )


def detect_interval_conflicts(
    events: Iterable[AvailabilityEvent],
) -> tuple[IntervalConflict, ...]:
    """Return deterministic overlaps between active half-open intervals."""

    active = sorted(
        (event for event in events if event.active),
        key=lambda event: (event.start, event.end, event.origin, event.uid),
    )
    conflicts: list[IntervalConflict] = []
    for index, left in enumerate(active):
        for right in active[index + 1 :]:
            if right.start >= left.end:
                break
            overlap_start = max(left.start, right.start)
            overlap_end = min(left.end, right.end)
            if overlap_start < overlap_end:
                conflicts.append(
                    IntervalConflict(
                        left=left.key,
                        right=right.key,
                        start=overlap_start,
                        end=overlap_end,
                    )
                )
    return tuple(conflicts)


def _build_event(
    properties: Iterable[tuple[str, Mapping[str, str], str]], *, origin: str
) -> AvailabilityEvent:
    singleton: dict[str, tuple[Mapping[str, str], str]] = {}
    forbidden = {"DURATION", "RRULE", "RDATE", "EXDATE", "RECURRENCE-ID"}
    supported = {
        "UID",
        "DTSTAMP",
        "DTSTART",
        "DTEND",
        "SEQUENCE",
        "STATUS",
        "X-EASYCAMP-ORIGIN",
    }
    for name, params, value in properties:
        if name in forbidden:
            raise ICalendarError(f"{name} is not supported for availability events")
        if name not in supported:
            continue
        if name in singleton:
            raise ICalendarError(f"VEVENT contains duplicate {name}")
        singleton[name] = (params, value)

    missing = [name for name in ("UID", "DTSTAMP", "DTSTART", "DTEND") if name not in singleton]
    if missing:
        raise ICalendarError(f"VEVENT is missing required properties: {', '.join(missing)}")

    uid = _unescape_text(singleton["UID"][1])
    dtstamp = _parse_dtstamp(singleton["DTSTAMP"][0], singleton["DTSTAMP"][1])
    start = _parse_date_property("DTSTART", *singleton["DTSTART"])
    end = _parse_date_property("DTEND", *singleton["DTEND"])

    sequence = 0
    if "SEQUENCE" in singleton:
        params, raw_sequence = singleton["SEQUENCE"]
        if params:
            raise ICalendarError("SEQUENCE must not have parameters")
        try:
            sequence = int(raw_sequence)
        except ValueError as exc:
            raise ICalendarError("SEQUENCE must be a non-negative integer") from exc

    status = ICalendarStatus.CONFIRMED
    if "STATUS" in singleton:
        params, raw_status = singleton["STATUS"]
        if params:
            raise ICalendarError("STATUS must not have parameters")
        try:
            status = ICalendarStatus(raw_status.upper())
        except ValueError as exc:
            raise ICalendarError(f"unsupported VEVENT STATUS: {raw_status}") from exc

    upstream_origin = None
    if "X-EASYCAMP-ORIGIN" in singleton:
        params, raw_origin = singleton["X-EASYCAMP-ORIGIN"]
        if params:
            raise ICalendarError("X-EASYCAMP-ORIGIN must not have parameters")
        upstream_origin = _unescape_text(raw_origin)

    return AvailabilityEvent(
        origin=origin,
        uid=uid,
        start=start,
        end=end,
        dtstamp=dtstamp,
        sequence=sequence,
        status=status,
        upstream_origin=upstream_origin,
    )


def _deduplicate_revisions(
    events: Iterable[AvailabilityEvent],
) -> dict[EventKey, AvailabilityEvent]:
    result: dict[EventKey, AvailabilityEvent] = {}
    for event in events:
        existing = result.get(event.key)
        if existing is None or event.sequence > existing.sequence:
            result[event.key] = event
            continue
        if event.sequence < existing.sequence:
            continue
        if event.semantic_fingerprint != existing.semantic_fingerprint:
            raise ICalendarRevisionConflict(
                f"snapshot contains divergent revision for event {event.key!r}"
            )
        if event.dtstamp > existing.dtstamp:
            result[event.key] = event
    return result


def _decode_payload(payload: str | bytes) -> str:
    if isinstance(payload, bytes):
        try:
            text = payload.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ICalendarError("snapshot must be valid UTF-8") from exc
    elif isinstance(payload, str):
        text = payload.removeprefix("\ufeff")
    else:
        raise TypeError("payload must be str or bytes")
    if "\x00" in text:
        raise ICalendarError("snapshot contains NUL bytes")
    return text


def _unfold_lines(text: str) -> list[str]:
    physical = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    while physical and physical[-1] == "":
        physical.pop()
    unfolded: list[str] = []
    for line in physical:
        if line.startswith((" ", "\t")):
            if not unfolded:
                raise ICalendarError("snapshot starts with a folded continuation")
            unfolded[-1] += line[1:]
        else:
            unfolded.append(line)
    return unfolded


def _parse_content_line(line: str) -> tuple[str, dict[str, str], str]:
    if ":" not in line:
        raise ICalendarError(f"invalid content line without colon: {line!r}")
    head, value = line.split(":", 1)
    parts = head.split(";")
    name = parts[0].upper()
    if not name:
        raise ICalendarError("content line has an empty property name")
    params: dict[str, str] = {}
    for raw_param in parts[1:]:
        if "=" not in raw_param:
            raise ICalendarError(f"invalid parameter on {name}: {raw_param!r}")
        key, param_value = raw_param.split("=", 1)
        key = key.upper()
        if not key or not param_value or key in params:
            raise ICalendarError(f"invalid or duplicate parameter on {name}: {raw_param!r}")
        params[key] = param_value.upper()
    return name, params, value


def _parse_date_property(name: str, params: Mapping[str, str], value: str) -> date:
    if set(params) - {"VALUE"}:
        raise ICalendarError(f"{name} contains unsupported parameters")
    if params.get("VALUE", "DATE") != "DATE":
        raise ICalendarError(f"{name} must use a DATE value")
    if len(value) != 8 or not value.isdigit():
        raise ICalendarError(f"{name} must use YYYYMMDD lodging dates")
    try:
        return datetime.strptime(value, "%Y%m%d").date()
    except ValueError as exc:
        raise ICalendarError(f"{name} contains an invalid date: {value}") from exc


def _parse_dtstamp(params: Mapping[str, str], value: str) -> datetime:
    if params:
        raise ICalendarError("DTSTAMP must be a UTC DATE-TIME without parameters")
    try:
        parsed = datetime.strptime(value, "%Y%m%dT%H%M%SZ")
    except ValueError as exc:
        raise ICalendarError("DTSTAMP must use UTC YYYYMMDDTHHMMSSZ") from exc
    return parsed.replace(tzinfo=timezone.utc)


def _format_dtstamp(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ICalendarError("DTSTAMP must be timezone-aware")
    return value.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _validate_identifier(value: str, name: str, *, max_length: int = 100) -> None:
    _validate_text(value, name)
    if not value or len(value) > max_length:
        raise ICalendarError(f"{name} must contain 1..{max_length} characters")


def _validate_text(value: str, name: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise ICalendarError(f"{name} contains control characters")


def _escape_text(value: str) -> str:
    _validate_text(value, "iCalendar text")
    return value.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")


def _unescape_text(value: str) -> str:
    output: list[str] = []
    index = 0
    while index < len(value):
        char = value[index]
        if char != "\\":
            output.append(char)
            index += 1
            continue
        index += 1
        if index >= len(value):
            raise ICalendarError("text value ends with an incomplete escape")
        escaped = value[index]
        if escaped in ("\\", ";", ","):
            output.append(escaped)
        elif escaped in ("n", "N"):
            output.append("\n")
        else:
            raise ICalendarError(f"unsupported text escape: \\{escaped}")
        index += 1
    result = "".join(output)
    _validate_text(result, "iCalendar text")
    return result


def _fold_content_line(line: str, *, limit: int = 75) -> str:
    """Fold one content line without splitting a UTF-8 code point."""

    encoded = line.encode("utf-8")
    if len(encoded) <= limit:
        return line
    chunks: list[str] = []
    remaining = encoded
    first = True
    while remaining:
        capacity = limit if first else limit - 1
        split_at = min(capacity, len(remaining))
        while split_at > 0:
            try:
                chunk = remaining[:split_at].decode("utf-8")
                break
            except UnicodeDecodeError:
                split_at -= 1
        if split_at == 0:
            raise ICalendarError("unable to fold UTF-8 content line")
        chunks.append(chunk if first else " " + chunk)
        remaining = remaining[split_at:]
        first = False
    return "\r\n".join(chunks)
