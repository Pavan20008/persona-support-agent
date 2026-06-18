# API Troubleshooting Guide

## Overview
This guide helps technical users diagnose common API integration failures in the Adsparkx platform.

## Authentication Errors (401 Unauthorized)

A 401 response indicates the bearer token is missing, expired, or invalid.

### Required Headers
Every authenticated API request must include:

```
Authorization: Bearer <your_api_key>
Content-Type: application/json
Accept: application/json
X-API-Version: 2024-01
```

### Common Causes
1. **Expired API key** — Production keys rotate every 90 days. Regenerate in Dashboard > Settings > API Keys.
2. **Wrong environment** — Sandbox keys (`sk_test_`) cannot access production endpoints.
3. **Whitespace in key** — Copy the key without trailing spaces or line breaks.
4. **Clock skew** — Ensure server NTP is synchronized; JWT validation fails if drift exceeds 5 minutes.

### Diagnostic Steps
1. Verify the key in `curl -H "Authorization: Bearer YOUR_KEY" https://api.adsparkx.io/v1/health`
2. Check response headers for `X-Request-Id` and search logs in the developer console.
3. Confirm IP allowlisting if enabled on your account.
4. Review rate limit headers: `X-RateLimit-Remaining`, `Retry-After`.

## 500 Internal Server Errors

Internal errors during database integration often trace to:
- Invalid connection string format
- SSL certificate mismatch on self-hosted databases
- Connection pool exhaustion (default max: 20 connections)

Enable debug logging with `ADSPARKX_LOG_LEVEL=debug` and attach trace IDs when opening a ticket.

## Webhook Delivery Failures

Webhooks require a publicly reachable HTTPS endpoint returning 2xx within 10 seconds. Failed deliveries retry with exponential backoff for 72 hours.

## Support Escalation
If errors persist after following this guide, provide: request ID, timestamp (UTC), endpoint, and sanitized request/response payloads.
