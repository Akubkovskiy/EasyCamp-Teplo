# Availability Ledger: Manual Operations Runbook

Status: design-time runbook; no production ledger or scheduler is enabled

Audience: owner/operator and engineer on duty

## 1. Safety rules

1. Treat EasyCamp booking data and every external calendar as production state.
2. Never solve a disagreement by bulk-opening dates.
3. A stale, unavailable or malformed source keeps its last good closures.
4. Only the configured base availability owner may open base inventory.
5. A channel may release only the closure it owns.
6. Never delete or edit the live SQLite file directly.
7. Never paste calendar URLs, tokens, credentials, guest data or raw feed
   contents into tickets or chat. Calendar URLs are bearer secrets.
8. Pause import/export jobs before a restore or bulk mapping change.

## 2. Information required for every incident

Record privacy-safe evidence before taking action:

- internal unit ID and exact channel binding;
- affected half-open interval `[check_in, check_out)`;
- source event key `(origin, external_event_id)` and revision/hash;
- last successful source snapshot and its observation window;
- projection generation;
- pending/failed outbox intent IDs;
- expected echo and acknowledgement deadline;
- active blocks contributing to the final closed state.

Do not include guest PII in the availability incident record. Operators can use
the channel's native booking screen when identity is genuinely necessary.

## 3. Alert triage

| Alert | Severity | Immediate safe state | First check |
|---|---:|---|---|
| Two confirmed reservations overlap | P0 | close affected interval; stop instant selling for unit | verify exact unit and both source booking IDs |
| Unknown or ambiguous unit mapping | P0/P1 | quarantine event; request-only/closed unit | compare immutable external IDs, never names |
| Unexpected reopen | P0 | restore last known closure locally; pause opener | identify which authority emitted release |
| Critical feed stale | P1 | retain last good blocks; site fail-closed/request-only | transport status and last complete snapshot |
| Invalid/partial/empty feed | P1 | reject entire snapshot | encoding, envelope, event validation |
| Outbox acknowledgement late | P1 | retain local block; retry idempotently | target, idempotency key, provider lag bound |
| Divergent same revision | P1 | quarantine snapshot | compare interval/status and producer revision |
| Suspected calendar loop | P1 | pause affected outbound target | origin, expected echo and target-specific feed |

## 4. Confirmed overlap procedure

1. Do not cancel either reservation automatically.
2. Confirm that both events refer to the same immutable unit, not similarly
   named units.
3. Confirm the intervals using checkout-exclusive semantics.
4. Keep the union of both intervals closed in every reachable channel.
5. Switch the unit to request-only or closed until the conflict is resolved.
6. Open a conflict case with both source IDs and timestamps.
7. Contact the source-channel support/owner according to lifecycle authority.
   Yandex reservations must not be represented as cancelled by a local-only
   action.
8. After the business decision, ingest or create an explicit source-owned
   cancellation/release event.
9. Reconcile all active blocks before restoring instant booking.

## 5. Stale or broken inbound calendar

1. Keep the last complete successful snapshot and its active blocks.
2. Reject the new snapshot as a whole; never partially apply valid-looking
   events from it.
3. Mark the binding stale after its configured threshold.
4. Put the site/unit into fail-closed or clearly labelled request-only mode.
5. Retry with backoff and jitter. Do not create a second poller.
6. If the source recovers, compare the first good snapshot in shadow mode before
   allowing any inferred disappearance to release dates.
7. Two successful snapshots plus the source grace policy are required before a
   missing UID may become a tombstone.

## 6. Late outbound reflection

1. Verify the local block and outbox intent are committed.
2. Verify the idempotency key did not change between attempts.
3. Compare elapsed time with the provider-specific acknowledgement SLO.
4. Retry the same intent; do not create a replacement booking or a new event ID.
5. Keep the site interval closed while delivery is uncertain.
6. If the target later exports the same interval, correlate it with the expected
   echo. Do not fan it out as a new source event.
7. Escalate after the target SLO; for Avito iCalendar use the measured policy
   based on its public one-hour update statement.

## 7. Cancellation or disappeared event

For explicit `STATUS:CANCELLED` or a verified provider cancellation:

1. verify origin, UID and non-stale revision;
2. supersede only the matching source block;
3. recompute effective availability from every remaining active block;
4. open dates only if the base owner allows them and no other closure remains;
5. deliver the new target projections through the same outbox mechanism.

For disappearance from a snapshot:

1. report the UID as missing but retain it;
2. ensure the snapshot is complete and the UID is inside the declared window;
3. wait for the second complete successful absence and grace period;
4. inspect pending expected echoes and provider retention behavior;
5. create an auditable tombstone rather than deleting history.

## 8. Mapping failure

1. Quarantine the event.
2. Do not use object name, fuzzy search, display order, or "first house" as a
   substitute.
3. Pause instant booking for the affected binding if the unit cannot be proven.
4. Obtain the immutable external unit ID through an approved account workflow.
5. Review the proposed one-to-one binding.
6. Replay the quarantined event only after the mapping is accepted.

## 9. Planned restore procedure

This section supplements, but does not replace, `ops/backup.md` and
`ops/restore.md` after a ledger schema is approved.

1. Stop all import, reconciliation and outbox workers.
2. Identify the exact database path and code revision.
3. Create and verify a recoverable pre-restore backup.
4. Restore the booking database together with ledger events, projection,
   cursors and outbox. Restoring only part of that state is invalid.
5. Start in shadow/read-only mode.
6. Rebuild the projection from the event log and compare its version/hash with
   the stored projection.
7. Fetch no external state until credentials, mappings and observation windows
   are confirmed for that environment.
8. Run reconciliation and inspect conflicts/unacknowledged intents.
9. Resume one importer, then reconciliation, then outbound delivery. Never
   overlap duplicate pollers for one binding.
10. Keep the pre-restore backup until post-restore acceptance is complete.

## 10. Change and rollback gates

Before connecting a real unit or enabling a provider adapter:

- approved architecture and schema;
- current verified backup and tested rollback;
- exact unit mapping;
- provider capability and credential scope confirmed from official sources or
  the authorized account;
- fixture and contract tests passing;
- shadow diff reviewed;
- alert destination tested;
- one bounded canary unit and explicit observation window;
- documented switch back to request-only/closed mode.

Rollback means disabling the new adapter/feed for the bounded unit, preserving
ledger evidence and last known closures, and returning the unit to a safe
request-only/closed mode. Rollback must not bulk-open external calendars.
