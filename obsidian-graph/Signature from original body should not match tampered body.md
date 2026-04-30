---
source_file: "tests\test_webhook.py"
type: "rationale"
community: "TestWebhookSignatureVerification / TestWebhookIdempotency"
location: "L50"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/TestWebhookSignatureVerification_/_TestWebhookIdempotency
---

# Signature from original body should not match tampered body

## Connections
- [[.test_tampered_body_detected()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/TestWebhookSignatureVerification_/_TestWebhookIdempotency