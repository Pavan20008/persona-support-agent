# Rate Limiting

## Default Limits
| Plan | Requests/min | Burst |
|------|-------------|-------|
| Free | 60 | 10 |
| Pro | 600 | 50 |
| Enterprise | 6000 | 200 |

## Response Headers
```
X-RateLimit-Limit: 600
X-RateLimit-Remaining: 587
X-RateLimit-Reset: 1704067200
Retry-After: 30
```

## Handling 429 Too Many Requests
1. Read the `Retry-After` header (seconds to wait)
2. Implement exponential backoff in your client
3. Batch requests where possible
4. Contact sales for limit increases on Enterprise plans

## Best Practices
- Cache read-heavy responses locally
- Use webhooks instead of polling for state changes
- Spread batch jobs across time windows
