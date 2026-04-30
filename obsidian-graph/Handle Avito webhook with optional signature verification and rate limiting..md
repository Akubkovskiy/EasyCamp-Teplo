---
source_file: "app\avito\webhook.py"
type: "rationale"
community: "avito_webhook() / Verify HMAC-SHA256 signature.     Returns True if signature is valid OR if no s"
location: "L43"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/avito_webhook()_/_Verify_HMAC-SHA256_signature._____Returns_True_if_signature_is_valid_OR_if_no_s
---

# Handle Avito webhook with optional signature verification and rate limiting.

## Connections
- [[AvitoBookingPayload]] - `uses` [INFERRED]
- [[AvitoWebhookEvent]] - `uses` [INFERRED]
- [[Booking]] - `uses` [INFERRED]
- [[BookingService]] - `uses` [INFERRED]
- [[BookingSource]] - `uses` [INFERRED]
- [[avito_webhook()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/avito_webhook()_/_Verify_HMAC-SHA256_signature._____Returns_True_if_signature_is_valid_OR_if_no_s