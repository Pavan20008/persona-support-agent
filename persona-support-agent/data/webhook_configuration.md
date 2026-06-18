# Webhook Configuration

## Overview
Webhooks deliver real-time event notifications to your server when actions occur in Adsparkx.

## Setup Steps
1. Go to Dashboard > Developers > Webhooks.
2. Click "Add Endpoint" and enter your HTTPS URL.
3. Select events to subscribe to (e.g., `invoice.paid`, `user.created`).
4. Copy the signing secret for payload verification.

## Signature Verification

```python
import hmac
import hashlib

def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

## Retry Policy
Failed deliveries (non-2xx or timeout > 10s) retry at: 1min, 5min, 30min, 2hr, 6hr, 24hr.

## Testing
Use the "Send test event" button in the dashboard or the CLI:
`adsparkx webhooks test --endpoint https://your-server.com/hooks`
