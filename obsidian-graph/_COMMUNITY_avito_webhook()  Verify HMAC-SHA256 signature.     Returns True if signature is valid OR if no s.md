---
type: community
cohesion: 0.29
members: 10
---

# avito_webhook() / Verify HMAC-SHA256 signature.     Returns True if signature is valid OR if no s

**Cohesion:** 0.29 - loosely connected
**Members:** 10 nodes

## Members
- [[Avito webhook handler with signature verification and idempotency.  Modes (via]] - rationale - app\avito\webhook.py
- [[AvitoWebhookEvent]] - code - app\avito\schemas.py
- [[Handle Avito webhook with optional signature verification and rate limiting.]] - rationale - app\avito\webhook.py
- [[Verify HMAC-SHA256 signature.     Returns True if signature is valid OR if no s]] - rationale - app\avito\webhook.py
- [[avito_webhook()]] - code - app\avito\webhook.py
- [[notifier.py]] - code - app\telegram\notifier.py
- [[notify_new_avito_event()]] - code - app\telegram\notifier.py
- [[schemas.py]] - code - app\avito\schemas.py
- [[verify_signature()]] - code - app\avito\webhook.py
- [[webhook.py]] - code - app\avito\webhook.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/avito_webhook()_/_Verify_HMAC-SHA256_signature._____Returns_True_if_signature_is_valid_OR_if_no_s
SORT file.name ASC
```

## Connections to other communities
- 14 edges to [[_COMMUNITY_BookingStatus  Booking]]
- 1 edge to [[_COMMUNITY_str  settings.py]]
- 1 edge to [[_COMMUNITY_houses.py  HouseUpdate]]

## Top bridge nodes
- [[avito_webhook()]] - degree 7, connects to 2 communities
- [[AvitoWebhookEvent]] - degree 6, connects to 1 community
- [[Avito webhook handler with signature verification and idempotency.  Modes (via]] - degree 6, connects to 1 community
- [[Verify HMAC-SHA256 signature.     Returns True if signature is valid OR if no s]] - degree 6, connects to 1 community
- [[Handle Avito webhook with optional signature verification and rate limiting.]] - degree 6, connects to 1 community