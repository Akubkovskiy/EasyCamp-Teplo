---
type: community
cohesion: 0.08
members: 24
---

# TestWebhookSignatureVerification / TestWebhookIdempotency

**Cohesion:** 0.08 - loosely connected
**Members:** 24 nodes

## Members
- [[.test_duplicate_detection_by_id()]] - code - tests\test_webhook.py
- [[.test_invalid_json_raises()]] - code - tests\test_webhook.py
- [[.test_invalid_signature_rejected()]] - code - tests\test_webhook.py
- [[.test_new_booking_not_duplicate()]] - code - tests\test_webhook.py
- [[.test_parse_valid_payload()]] - code - tests\test_webhook.py
- [[.test_response_for_duplicate()]] - code - tests\test_webhook.py
- [[.test_tampered_body_detected()]] - code - tests\test_webhook.py
- [[.test_valid_signature_matches()]] - code - tests\test_webhook.py
- [[Duplicate webhook should return already_processed status]] - rationale - tests\test_webhook.py
- [[Invalid JSON should raise exception]] - rationale - tests\test_webhook.py
- [[Invalid signature should not match]] - rationale - tests\test_webhook.py
- [[New booking ID should not be detected as duplicate]] - rationale - tests\test_webhook.py
- [[Same avito_booking_id should be detected as duplicate]] - rationale - tests\test_webhook.py
- [[Signature from original body should not match tampered body]] - rationale - tests\test_webhook.py
- [[Test HMAC signature verification logic]] - rationale - tests\test_webhook.py
- [[Test idempotency logic for duplicate webhook prevention]] - rationale - tests\test_webhook.py
- [[Test webhook payload parsing]] - rationale - tests\test_webhook.py
- [[TestWebhookIdempotency]] - code - tests\test_webhook.py
- [[TestWebhookPayloadParsing]] - code - tests\test_webhook.py
- [[TestWebhookSignatureVerification]] - code - tests\test_webhook.py
- [[Tests for Avito webhook functionality (unit tests)]] - rationale - tests\test_webhook.py
- [[Valid payload should parse correctly]] - rationale - tests\test_webhook.py
- [[Valid signature should match expected]] - rationale - tests\test_webhook.py
- [[test_webhook.py]] - code - tests\test_webhook.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/TestWebhookSignatureVerification_/_TestWebhookIdempotency
SORT file.name ASC
```
