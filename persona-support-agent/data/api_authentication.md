# API Authentication Reference

## Bearer Token Implementation

Adsparkx uses OAuth 2.0 client credentials for server-to-server integrations and personal API keys for developer access.

### Header Parameter Requirements

| Header | Required | Description |
|--------|----------|-------------|
| Authorization | Yes | Format: `Bearer <token>` |
| Content-Type | Yes | Must be `application/json` for POST/PUT |
| Accept | Yes | Must be `application/json` |
| X-API-Version | Recommended | API version date, e.g. `2024-01` |
| X-Request-Id | Optional | UUID for idempotency and log correlation |

### Example Request

```http
POST /v1/events HTTP/1.1
Host: api.adsparkx.io
Authorization: Bearer sk_live_abc123xyz
Content-Type: application/json
Accept: application/json
X-API-Version: 2024-01

{
  "event": "user.signup",
  "properties": {
    "plan": "enterprise"
  }
}
```

### Token Scopes
- `read:analytics` — Read-only dashboard data
- `write:events` — Send tracking events
- `admin:keys` — Manage API keys (requires admin role)

### Token Lifecycle
Access tokens expire after 3600 seconds. Use the `/oauth/token` endpoint with your client_id and client_secret to refresh.

```bash
curl -X POST https://api.adsparkx.io/oauth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=YOUR_ID&client_secret=YOUR_SECRET"
```
