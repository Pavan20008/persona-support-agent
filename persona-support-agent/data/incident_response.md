# Incident Response for Production Outages

## Severity Levels
- **SEV-1**: Complete API outage — response within 15 minutes
- **SEV-2**: Partial degradation — response within 1 hour
- **SEV-3**: Non-critical issues — response within 4 hours

## What to Provide
When reporting production issues, include:
1. Account ID and affected environment (production/sandbox)
2. Error codes and timestamps (UTC)
3. Request IDs from response headers
4. Steps to reproduce

## Communication
Status updates posted to https://status.adsparkx.io every 30 minutes during SEV-1 incidents.
Enterprise customers receive direct email and Slack notifications if configured.

## Post-Incident
Root cause analysis (RCA) documents are shared within 5 business days for SEV-1 and SEV-2 events.
