# Canonical Availability Ledger

Status: accepted architecture, implementation boundary approved 2026-09-03

Scope: EasyCamp, Teplo site, Avito Travel, Yandex Travel/Extranet

Runtime status: specification and local iCalendar primitives only; no production integration is enabled

## 1. Product outcome

For every accommodation unit, EasyCamp must present one explainable effective
availability view assembled from source-owned facts. A reservation or manual
closure from any accepted source closes the interval. Reopening is allowed only
when the configured availability owner or the owner of the original closure
provides an unambiguous release event.

The product must prefer a visible unavailable state over an unverified available
state. It must never claim that a request is a confirmed booking before an
atomic local hold or a source confirmation exists.

## 2. Capability facts and system limit

- Yandex Extranet supports per-unit bidirectional iCalendar import/export and
  multiple calendar links. Removing a link does not automatically reopen dates
  previously closed by that calendar.
- The public Yandex Travel partner API is a hotel storefront/order API. It is
  not a documented Extranet inventory-management API.
- Yandex supports approved channel managers for inventory management.
- Avito supports calendar import/export and publicly states that Avito booking
  updates may take up to one hour.
- The public Yandex iCalendar documentation does not publish a refresh bound.
- iCalendar is polling-based eventual convergence. It cannot provide a hard
  guarantee that every marketplace closes immediately.

Therefore a strict no-race business guarantee requires one of these operating
modes:

1. only one instant-booking channel per unit; all other channels are
   request-to-book; or
2. an approved real-time channel manager with measured delivery and
   acknowledgement behavior.

References:

- <https://yandex.ru/support/travel-partners/ru/extranet/sync-calendar>
- <https://yandex.ru/dev/travel-partners-api/doc/ru/>
- <https://yandex.ru/dev/travel-partners-api/doc/ru/methods>
- <https://yandex.ru/support/travel-partners/ru/extranet-managers>
- <https://yandex.ru/support/travel-partners/ru/extranet/bookings>
- <https://t.me/s/avito/5634>
- <https://datatracker.ietf.org/doc/html/rfc5545>

## 3. Architecture decision

The system uses a hybrid `many closers, one opener` model. EasyCamp is the
canonical convergence ledger and the availability API for the Teplo site, but
it is not automatically the owner of every external booking.

### 3.1 Authority is explicit

Each unit has exactly one `base_availability_owner`. Only that owner may open
base inventory. The owner is configuration, not a global hard-coded platform;
it may be EasyCamp or an approved channel manager.

Each reservation keeps its own lifecycle owner:

| Reservation origin | Lifecycle authority | Allowed local action |
|---|---|---|
| EasyCamp/site/Telegram/manual | EasyCamp | create, confirm, cancel under local policy |
| Avito | Avito | project state; request external action through a verified adapter |
| Yandex | Yandex | project state; never pretend a local cancellation cancelled Yandex |
| Channel manager | Channel manager | project acknowledged state |

Any accepted source may add a closure. A source may release only its own
closure. Removing one closure never overrides another active closure.

### 3.2 Effective availability

For a unit and date interval:

```text
effective_available = base_owner_open
                      AND no active reservation block
                      AND no active maintenance/manual/hold block
                      AND all critical source snapshots are fresh
```

Intervals are always half-open: `[check_in, check_out)`. A checkout on 13
September and a new check-in on 13 September are adjacent, not overlapping.

### 3.3 Topology

All synchronization is a star through the ledger:

```text
Avito ─────┐
Yandex ────┼──> source adapters ──> append-only event log
Site ──────┤                              │
Telegram ──┘                              ├──> availability projection
                                          ├──> conflict cases
                                          └──> transactional outbox
                                                   ├──> Avito target feed
                                                   └──> Yandex target feed
```

Do not create simultaneous Avito-to-Yandex and ledger-to-channel calendar
links. A mesh loses event origin and creates feedback loops.

## 4. Planned canonical data contract

This section defines a future additive schema. It does not authorize a database
migration.

### `availability_units`

- immutable internal unit ID and existing `house_id` binding;
- business timezone;
- `base_availability_owner`;
- monotonic projection version;
- availability mode: `instant`, `request_only`, or `closed`.

### `channel_unit_bindings`

- unit ID, channel and exact external unit ID;
- import/export capability and criticality;
- source-specific observation window and freshness SLO;
- secret reference or token hash, never a raw credential;
- enabled state and last verified timestamp.

Mappings are exact and unique. Names, fuzzy matching, or fallback to the first
house are forbidden.

### `availability_events`

Append-only facts containing:

- origin channel and external unit ID;
- external event ID/UID and source revision or normalized payload hash;
- event kind: reservation, hold, maintenance, manual closure, base inventory;
- action/status: active, cancelled, superseded;
- `[start_date, end_date)`;
- source timestamp and observed timestamp;
- correlation, causation and expected-echo identifiers;
- privacy-safe payload fingerprint.

Required uniqueness:

```text
(origin_channel, external_unit_id, external_event_id, source_revision_or_hash)
```

### `availability_blocks`

Current projection of active closing facts. A block points to its source event
and optionally the existing operational `Booking`. It is not a second booking
state machine.

### `availability_outbox`

An outbound intent written in the same transaction as the accepted local event:
target, projection generation, idempotency key, attempt count, next attempt,
last error and acknowledgement state.

### `sync_cursors`

Per binding: ETag, Last-Modified, last complete snapshot hash, observation
window, last attempt, last success and last semantic change.

### `conflict_cases`

Immutable evidence plus mutable resolution state for confirmed overlaps,
divergent revisions, stale feeds, mapping failures, unexpected reopens and
unmatched delivery echoes.

The existing `Booking` table remains the operational reservation record. A
future migration must add database-enforced uniqueness for non-null
`(source, external_id)` and link a booking to its availability block.

## 5. Transaction and idempotency rules

1. Local availability check, booking/hold creation, event append, block update
   and outbox append are one transaction.
2. With SQLite, the future write path must use a single-writer transaction such
   as `BEGIN IMMEDIATE` or a version compare-and-swap. An in-process lock alone
   is insufficient when multiple processes are possible.
3. External network calls never run inside that transaction. The outbox retries
   them after commit with the same idempotency key.
4. Replaying the same source event any number of times produces one semantic
   event and one active block.
5. A higher `SEQUENCE` may update an event. A lower revision is stale. Changed
   semantics at the same revision are quarantined as a divergent revision.
6. Absence from one complete snapshot is reported but never interpreted as an
   immediate cancellation.

## 6. iCalendar profile

The local primitive is `app/domain/ical.py`. It is intentionally disconnected
from HTTP, persistence, scheduler and provider credentials.

Supported import profile:

- UTF-8 VCALENDAR 2.0;
- unfolded content lines;
- VEVENT with required `UID`, UTC `DTSTAMP`, `DTSTART`, `DTEND`;
- lodging `DATE` values in `YYYYMMDD` form;
- optional non-negative `SEQUENCE`;
- status `CONFIRMED`, `TENTATIVE`, or `CANCELLED`;
- optional `X-EASYCAMP-ORIGIN` as an untrusted loop-correlation hint.

Timed events, recurrence rules, duration-only events, malformed dates, nested
components and contradictory revisions are rejected rather than guessed.

Export profile:

- CRLF and RFC-style line folding;
- stable UID and source DTSTAMP;
- `DTSTART;VALUE=DATE` and non-inclusive `DTEND;VALUE=DATE`;
- privacy-neutral `SUMMARY:Unavailable`;
- no guest name, phone, price, comment or booking details;
- one target-specific feed, excluding events whose origin is that target.

`X-EASYCAMP-ORIGIN` is only a hint. A provider may remove or rewrite it. Loop
prevention must primarily use target-specific feeds, expected-echo records and
stable interval/event fingerprints.

## 7. Snapshot and cancellation policy

An import is accepted only after the whole snapshot parses successfully. An
HTTP error, timeout, truncated body, invalid event, empty response outside a
declared empty-feed contract, or unknown unit leaves the last good projection
unchanged.

An explicit valid `STATUS:CANCELLED` with a current revision is a release fact.
Disappearance may become a tombstone only when all are true:

1. the source has delivered at least two consecutive complete successful
   snapshots;
2. the missing UID falls inside the source's declared observation window;
3. a source-specific grace period has elapsed;
4. no other active block is released by that action.

## 8. Conflicts

Overlapping closures are not automatically errors: a maintenance block may
legitimately overlap a reservation. The reconciliation layer classifies the
event kinds.

Policy order:

1. a confirmed/paid external reservation beats a local unconfirmed hold;
2. an active block always beats a request to open;
3. two confirmed reservations on the same unit and dates create a P0 conflict;
4. a P0 conflict closes the affected interval everywhere possible and requires
   a human decision; the software must not auto-cancel either reservation;
5. an unknown mapping quarantines the event and closes instant booking for the
   affected binding until reviewed.

## 9. Lag, reconciliation and alerts

Initial internal targets, subject to provider rate limits and measured UAT:

- poll imports every 5 minutes with jitter and exponential backoff;
- Avito expected external reflection: up to 60 minutes; warn at 75 minutes and
  escalate at 90 minutes;
- Yandex external reflection: unpublished; use a provisional two-hour stale
  boundary until a controlled test measures it;
- adapter/outbox health every 5-10 minutes;
- projection-to-source reconciliation hourly;
- owner digest daily, anomalies only.

Immediate alerts:

- confirmed overlap;
- stale critical source;
- parse or mapping failure;
- divergent revision;
- unexpected reopen;
- outbound intent beyond its acknowledgement SLO;
- unmatched echo or suspected loop.

If any critical inbound source is stale, the site must fail closed or switch the
unit to clearly labelled request-only mode. It must not present stale dates as
instantaneously bookable.

## 10. MVP delivery gates

1. This specification and the manual runbook are reviewed.
2. Local parser/exporter/import/conflict tests pass without network access.
3. An additive schema proposal is reviewed separately.
4. Backup, restore and rollback are tested against a copy of the real schema.
5. Shadow import reads fixtures or later approved test feeds and produces a
   reconciliation report without changing bookings.
6. Exact unit mappings are reviewed manually.
7. Target-specific feeds are tested locally for stable UIDs and loop exclusion.
8. One non-critical test unit is connected only under a separate production
   change approval.
9. Provider write APIs or webhooks remain disabled until official access,
   scopes, signatures, retry rules and cancellation behavior pass contract UAT.

## 11. MVP acceptance criteria

- The same incoming event replayed 100 times yields one event/block.
- Adjacent `[10, 13)` and `[13, 16)` stays do not conflict.
- A semantic change without a revision increase is rejected atomically.
- A higher revision updates; a lower revision cannot revert state.
- A missing UID is reported and retained, not deleted.
- A valid cancellation releases only its source contribution.
- A target feed excludes events originating from that target.
- Generated UIDs remain stable and generated calendars contain no PII.
- Ten import/export cycles create no new semantic events or loops.
- An invalid, empty or partial critical feed never reopens dates.
- Two concurrent local booking attempts can accept at most one interval.
- The outbox survives restart and retries without duplicate effects.
- Stale source, unknown mapping and confirmed overlap generate alerts.
- Restore with sync paused reproduces the same effective availability before
  outbound work resumes.

The local primitives cover the format, replay, revision, missing-event and
interval portions of these criteria. Concurrency, persistence, outbox, alerting
and provider UAT remain deliberately outside the current implementation.
