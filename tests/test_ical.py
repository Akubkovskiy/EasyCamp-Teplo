from datetime import date, datetime, timedelta, timezone

import pytest

from app.domain.ical import (
    AvailabilityEvent,
    ICalendarError,
    ICalendarRevisionConflict,
    ICalendarStatus,
    detect_interval_conflicts,
    export_ical,
    import_snapshot,
    parse_ical,
)


UTC = timezone.utc


def event(
    *,
    origin: str = "avito",
    uid: str = "booking-1@avito",
    start: date = date(2026, 9, 10),
    end: date = date(2026, 9, 13),
    sequence: int = 0,
    status: ICalendarStatus = ICalendarStatus.CONFIRMED,
    dtstamp: datetime = datetime(2026, 9, 3, 10, 0, tzinfo=UTC),
) -> AvailabilityEvent:
    return AvailabilityEvent(
        origin=origin,
        uid=uid,
        start=start,
        end=end,
        dtstamp=dtstamp,
        sequence=sequence,
        status=status,
    )


def calendar(*event_lines: str) -> str:
    return "\r\n".join(
        (
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Fixture//EN",
            *event_lines,
            "END:VCALENDAR",
            "",
        )
    )


class TestParseICalendar:
    def test_parses_lodging_dates_as_half_open_interval(self):
        payload = calendar(
            "BEGIN:VEVENT",
            "UID:booking-1@avito",
            "DTSTAMP:20260903T100000Z",
            "DTSTART;VALUE=DATE:20260910",
            "DTEND;VALUE=DATE:20260913",
            "SEQUENCE:2",
            "STATUS:CONFIRMED",
            "END:VEVENT",
        )

        parsed = parse_ical(payload, origin="avito")

        assert len(parsed) == 1
        assert parsed[0].start == date(2026, 9, 10)
        assert parsed[0].end == date(2026, 9, 13)
        assert parsed[0].sequence == 2
        assert parsed[0].key == ("avito", "booking-1@avito")

    def test_accepts_unambiguous_date_without_value_parameter(self):
        payload = calendar(
            "BEGIN:VEVENT",
            "UID:yandex-1",
            "DTSTAMP:20260903T100000Z",
            "DTSTART:20260910",
            "DTEND:20260913",
            "END:VEVENT",
        )

        parsed = parse_ical(payload, origin="yandex")

        assert parsed[0].start == date(2026, 9, 10)
        assert parsed[0].end == date(2026, 9, 13)

    def test_unfolds_content_lines(self):
        payload = calendar(
            "BEGIN:VEVENT",
            "UID:long-booking-",
            " 1@avito",
            "DTSTAMP:20260903T100000Z",
            "DTSTART;VALUE=DATE:20260910",
            "DTEND;VALUE=DATE:20260913",
            "END:VEVENT",
        )

        parsed = parse_ical(payload, origin="avito")

        assert parsed[0].uid == "long-booking-1@avito"

    @pytest.mark.parametrize(
        "event_lines, expected",
        [
            (
                (
                    "BEGIN:VEVENT",
                    "DTSTAMP:20260903T100000Z",
                    "DTSTART;VALUE=DATE:20260910",
                    "DTEND;VALUE=DATE:20260913",
                    "END:VEVENT",
                ),
                "UID",
            ),
            (
                (
                    "BEGIN:VEVENT",
                    "UID:booking-1",
                    "DTSTART;VALUE=DATE:20260910",
                    "DTEND;VALUE=DATE:20260913",
                    "END:VEVENT",
                ),
                "DTSTAMP",
            ),
            (
                (
                    "BEGIN:VEVENT",
                    "UID:booking-1",
                    "DTSTAMP:20260903T100000Z",
                    "DTSTART:20260910T120000Z",
                    "DTEND:20260913T120000Z",
                    "END:VEVENT",
                ),
                "DTSTART",
            ),
        ],
    )
    def test_rejects_missing_or_ambiguous_required_values(self, event_lines, expected):
        with pytest.raises(ICalendarError, match=expected):
            parse_ical(calendar(*event_lines), origin="avito")

    def test_rejects_recurrence_instead_of_guessing_occupancy(self):
        payload = calendar(
            "BEGIN:VEVENT",
            "UID:booking-1",
            "DTSTAMP:20260903T100000Z",
            "DTSTART;VALUE=DATE:20260910",
            "DTEND;VALUE=DATE:20260913",
            "RRULE:FREQ=DAILY;COUNT=3",
            "END:VEVENT",
        )

        with pytest.raises(ICalendarError, match="RRULE"):
            parse_ical(payload, origin="avito")

    def test_rejects_changed_duplicate_revision_atomically(self):
        payload = calendar(
            "BEGIN:VEVENT",
            "UID:booking-1",
            "DTSTAMP:20260903T100000Z",
            "DTSTART;VALUE=DATE:20260910",
            "DTEND;VALUE=DATE:20260913",
            "SEQUENCE:0",
            "END:VEVENT",
            "BEGIN:VEVENT",
            "UID:booking-1",
            "DTSTAMP:20260903T110000Z",
            "DTSTART;VALUE=DATE:20260911",
            "DTEND;VALUE=DATE:20260913",
            "SEQUENCE:0",
            "END:VEVENT",
        )

        with pytest.raises(ICalendarRevisionConflict):
            parse_ical(payload, origin="avito")


class TestExportICalendar:
    def test_exports_required_fields_and_round_trips(self):
        source = event()

        payload = export_ical([source])
        parsed = parse_ical(payload, origin="easycamp-export")

        assert payload.endswith("\r\n")
        assert "UID:booking-1@avito\r\n" in payload
        assert "DTSTAMP:20260903T100000Z\r\n" in payload
        assert "DTSTART;VALUE=DATE:20260910\r\n" in payload
        assert "DTEND;VALUE=DATE:20260913\r\n" in payload
        assert "SUMMARY:Unavailable\r\n" in payload
        assert parsed[0].uid == source.uid
        assert parsed[0].upstream_origin == "avito"

    def test_excludes_target_origin_and_never_accepts_guest_details(self):
        avito_event = event(origin="avito", uid="avito-1")
        yandex_event = event(origin="yandex", uid="yandex-1")

        payload = export_ical([yandex_event, avito_event], exclude_origin="avito")

        assert "UID:avito-1" not in payload
        assert "UID:yandex-1" in payload
        assert "guest" not in payload.lower()

    def test_output_is_deterministic_for_input_order(self):
        first = event(origin="site", uid="site-1")
        second = event(origin="yandex", uid="yandex-1", start=date(2026, 10, 1), end=date(2026, 10, 2))

        assert export_ical([first, second]) == export_ical([second, first])


class TestSnapshotImport:
    def test_same_snapshot_is_idempotent(self):
        current = ()
        incoming = (event(),)

        for _ in range(100):
            result = import_snapshot(current, incoming)
            current = result.events

        assert len(current) == 1
        assert result.added == ()
        assert result.unchanged == (("avito", "booking-1@avito"),)

    def test_higher_sequence_updates_and_lower_sequence_is_stale(self):
        old = event(sequence=1)
        updated = event(sequence=2, end=date(2026, 9, 14))

        update_result = import_snapshot([old], [updated])
        stale_result = import_snapshot(update_result.events, [old])

        assert update_result.updated == (old.key,)
        assert update_result.events[0].end == date(2026, 9, 14)
        assert stale_result.stale == (old.key,)
        assert stale_result.events[0].end == date(2026, 9, 14)

    def test_same_sequence_with_changed_dates_is_a_conflict(self):
        old = event(sequence=1)
        divergent = event(sequence=1, end=date(2026, 9, 14))

        with pytest.raises(ICalendarRevisionConflict):
            import_snapshot([old], [divergent])

    def test_missing_event_is_reported_but_not_deleted(self):
        existing = event()

        result = import_snapshot([existing], [])

        assert result.missing == (existing.key,)
        assert result.events == (existing,)

    def test_newer_cancelled_revision_deactivates_event(self):
        existing = event(sequence=1)
        cancelled = event(sequence=2, status=ICalendarStatus.CANCELLED)

        result = import_snapshot([existing], [cancelled])

        assert result.events[0].active is False

    def test_semantically_same_newer_dtstamp_is_not_an_update(self):
        existing = event()
        retransmitted = event(dtstamp=event().dtstamp + timedelta(minutes=5))

        result = import_snapshot([existing], [retransmitted])

        assert result.unchanged == (existing.key,)
        assert result.updated == ()
        assert result.events[0].dtstamp == retransmitted.dtstamp


class TestConflictDetection:
    def test_detects_overlap_but_not_checkout_adjacency(self):
        first = event(origin="avito", uid="avito-1")
        overlapping = event(
            origin="yandex",
            uid="yandex-1",
            start=date(2026, 9, 12),
            end=date(2026, 9, 15),
        )
        adjacent = event(
            origin="site",
            uid="site-1",
            start=date(2026, 9, 13),
            end=date(2026, 9, 16),
        )

        conflicts = detect_interval_conflicts([first, overlapping, adjacent])

        assert len(conflicts) == 2
        assert conflicts[0].start == date(2026, 9, 12)
        assert conflicts[0].end == date(2026, 9, 13)
        assert all(conflict.left != conflict.right for conflict in conflicts)

    def test_cancelled_event_does_not_conflict(self):
        active = event(origin="avito", uid="active")
        cancelled = event(
            origin="yandex",
            uid="cancelled",
            status=ICalendarStatus.CANCELLED,
        )

        assert detect_interval_conflicts([active, cancelled]) == ()
