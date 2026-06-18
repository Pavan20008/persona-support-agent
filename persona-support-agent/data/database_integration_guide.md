# Database Integration Guide

## Supported Databases
Adsparkx supports PostgreSQL 13+, MySQL 8.0+, and MongoDB 6.0+ as data warehouse connectors.

## Connection Setup
Navigate to Dashboard > Integrations > Database and provide:
- Host and port
- Database name
- Username with read-only permissions (recommended)
- SSL mode: `require` for production

## Common Internal Errors

### Error: "Connection refused (ECONNREFUSED)"
The database host is unreachable from Adsparkx IP ranges. Whitelist these IPs:
- 52.23.45.67
- 54.87.123.45
- 18.206.78.90

### Error: "SSL certificate verify failed"
Download the CA certificate from your provider and upload it under Advanced > SSL Certificate.

### Error: "Too many connections"
Reduce the connection pool size in integration settings (default: 10, max: 50).
Ensure idle connections are released by your database server.

## Sync Schedule
Initial sync may take 2-4 hours for databases over 10GB. Incremental syncs run every 15 minutes.

## Troubleshooting Checklist
1. Test connectivity with `telnet host port` from your network.
2. Verify the service account has SELECT on required tables.
3. Check sync logs in Dashboard > Integrations > Logs.
4. Restart the connector from the integration settings page.

## Escalation
Provide connector ID, last successful sync timestamp, and full error message from sync logs.
