# Oracle Database Connection Guide

Quick reference for connecting the Query Tuner Tool to your Oracle database.

---

## Step 1: Create Monitoring User in Oracle

Run this SQL script as SYSDBA or a user with DBA privileges:

```sql
-- Create monitoring user
CREATE USER query_tuner_monitor IDENTIFIED BY YourSecurePassword;

-- Grant connect privilege
GRANT CONNECT TO query_tuner_monitor;

-- Grant SELECT on V$ views (Real-time monitoring)
GRANT SELECT ON V_$SQL TO query_tuner_monitor;
GRANT SELECT ON V_$SQL_PLAN TO query_tuner_monitor;
GRANT SELECT ON V_$SESSION TO query_tuner_monitor;
GRANT SELECT ON V_$SESSION_WAIT TO query_tuner_monitor;
GRANT SELECT ON V_$ACTIVE_SESSION_HISTORY TO query_tuner_monitor;
GRANT SELECT ON V_$LOCK TO query_tuner_monitor;
GRANT SELECT ON V_$SESSTAT TO query_tuner_monitor;
GRANT SELECT ON V_$VERSION TO query_tuner_monitor;

-- Grant SELECT on DBA views (For AWR/ASH - requires Diagnostics Pack license)
GRANT SELECT ON DBA_HIST_SQLSTAT TO query_tuner_monitor;
GRANT SELECT ON DBA_HIST_SQL_PLAN TO query_tuner_monitor;
GRANT SELECT ON DBA_HIST_ACTIVE_SESS_HISTORY TO query_tuner_monitor;
GRANT SELECT ON DBA_HIST_SNAPSHOT TO query_tuner_monitor;
GRANT SELECT ON DBA_TAB_STATISTICS TO query_tuner_monitor;
GRANT SELECT ON DBA_IND_STATISTICS TO query_tuner_monitor;

-- Grant SELECT_CATALOG_ROLE for easier access
GRANT SELECT_CATALOG_ROLE TO query_tuner_monitor;

-- Verify grants
SELECT * FROM DBA_SYS_PRIVS WHERE GRANTEE = 'QUERY_TUNER_MONITOR';
SELECT * FROM DBA_TAB_PRIVS WHERE GRANTEE = 'QUERY_TUNER_MONITOR';
```

---

## Step 2: Test Connection from Command Line

Before configuring in the UI, test the connection:

```bash
# Using sqlplus
sqlplus query_tuner_monitor/YourSecurePassword@//hostname:1521/servicename

# Test a simple query
SQL> SELECT * FROM V$VERSION;
SQL> SELECT COUNT(*) FROM V$SQL;
```

If successful, you should see Oracle version and query count.

---

## Step 3: Configure Connection in Web UI

1. **Open the application:**
   ```
   http://localhost:3003
   ```

2. **Login** (or register if first time)

3. **Go to Connection Setup:**
   - Click "Manage Connections" in sidebar
   - Or navigate directly to connection setup page

4. **Enter Database Details:**
   ```
   Connection Name:  Production Oracle DB
   Database Type:    Oracle
   Host:             oracle-server.company.com
   Port:             1521
   Service Name:     PRODDB     (use this OR SID, not both)
   SID:              ORCL       (alternative to Service Name)
   Username:         query_tuner_monitor
   Password:         YourSecurePassword
   ```

5. **Test Connection:**
   - Click "Test Connection" button
   - Should see success message

6. **Save Connection:**
   - Click "Save" if test succeeded
   - Connection will be used for all queries

---

## Step 4: Verify Features Work

### Query Analysis
```
Navigate to: Query Analysis
Expected: See real queries from V$SQL
Test: Click on any SQL_ID
```

### Wait Events
```
Navigate to: Wait Events
Expected: See real wait events from V$SESSION_WAIT
Test: Check wait class breakdown
```

### Performance Reports (AWR)
```
Navigate to: Performance Reports
Expected: See AWR snapshots from DBA_HIST_SNAPSHOT
Test: Generate a report for a date range
Note: Requires Oracle Diagnostics Pack license
```

### Bug Detection
```
Navigate to: Bug Detection
Expected: Bug detection based on Oracle version
Test: Review detected issues
```

### Deadlock Detection
```
Navigate to: Deadlock Detection
Expected: Show deadlocks if any occurred
Test: May be empty if no recent deadlocks
```

---

## Troubleshooting

### Connection Failed
**Error:** "ORA-12541: TNS:no listener"
- **Solution:** Check hostname and port are correct
- Verify Oracle listener is running: `lsnrctl status`

**Error:** "ORA-01017: invalid username/password"
- **Solution:** Verify credentials are correct
- Check if user is unlocked: `SELECT username, account_status FROM dba_users WHERE username = 'QUERY_TUNER_MONITOR';`

**Error:** "ORA-12154: TNS:could not resolve the connect identifier"
- **Solution:** Check service name or SID is correct
- Try using SID instead of Service Name or vice versa

### Insufficient Privileges
**Error:** "ORA-00942: table or view does not exist"
- **Solution:** Grant missing privileges
- Run the privilege script again as SYSDBA

**Missing AWR Data:**
- **Issue:** No snapshots visible
- **Solution:** Check if AWR is enabled: `SELECT * FROM DBA_HIST_SNAPSHOT;`
- Verify Diagnostics Pack is licensed

### Network Issues
**Error:** "Connection timeout"
- **Solution:** Check firewall rules
- Verify network connectivity: `telnet hostname 1521`
- Check Oracle network ACLs

---

## Connection String Formats

### Service Name (Recommended)
```
hostname:port/servicename
oracle-server.company.com:1521/PRODDB
```

### SID (Legacy)
```
hostname:port:SID
oracle-server.company.com:1521:ORCL
```

### Full TNS Format
```
(DESCRIPTION=
  (ADDRESS=(PROTOCOL=TCP)(HOST=hostname)(PORT=1521))
  (CONNECT_DATA=(SERVICE_NAME=servicename))
)
```

---

## Security Best Practices

1. **Use Strong Passwords**
   - Minimum 12 characters
   - Mix of upper, lower, numbers, symbols

2. **Limit Privileges**
   - Only grant SELECT on necessary views
   - Do NOT grant DML privileges (INSERT, UPDATE, DELETE)

3. **Monitor Access**
   - Review audit logs periodically
   - Track monitoring user activity

4. **Network Security**
   - Use Oracle Native Network Encryption
   - Consider Oracle Wallet for credentials
   - Restrict access via firewall

5. **Regular Reviews**
   - Audit privileges quarterly
   - Rotate passwords regularly
   - Review connection logs

---

## Oracle Licensing Note

**⚠️ Important:** The Performance Reports (AWR/ASH) features require the **Oracle Diagnostics Pack** license. If you don't have this license:

- Do NOT use AWR/ASH features
- Use only real-time V$ views (Query Analysis, Wait Events)
- Contact Oracle for licensing information

Basic features (Query Analysis, Wait Events, Execution Plans) work with **Standard Edition** and do not require additional licenses.

---

## Quick Reference

### Minimum Privileges (No AWR)
```sql
GRANT CONNECT TO query_tuner_monitor;
GRANT SELECT ON V_$SQL TO query_tuner_monitor;
GRANT SELECT ON V_$SQL_PLAN TO query_tuner_monitor;
GRANT SELECT ON V_$SESSION TO query_tuner_monitor;
GRANT SELECT ON V_$SESSION_WAIT TO query_tuner_monitor;
```

### Full Privileges (With AWR)
```sql
GRANT CONNECT TO query_tuner_monitor;
GRANT SELECT_CATALOG_ROLE TO query_tuner_monitor;
GRANT SELECT ON DBA_HIST_SQLSTAT TO query_tuner_monitor;
GRANT SELECT ON DBA_HIST_SQL_PLAN TO query_tuner_monitor;
GRANT SELECT ON DBA_HIST_SNAPSHOT TO query_tuner_monitor;
```

### Test Queries
```sql
-- Test V$ access
SELECT COUNT(*) FROM V$SQL;

-- Test AWR access (requires Diagnostics Pack)
SELECT COUNT(*) FROM DBA_HIST_SNAPSHOT;

-- Check version
SELECT * FROM V$VERSION;
```

---

## Support

If you encounter issues:

1. Check backend logs: `/Users/abdul/dev/query_tuner_tool/backend/logs/`
2. Check frontend console in browser (F12)
3. Verify Oracle listener is running
4. Test connection with sqlplus first
5. Review Oracle alert log for errors

---

**Last Updated:** February 12, 2026
