# Safe Database Deployment Guide

## Pre-Deployment Steps

1. Always ensure the deployment safety SQL has been run:
   ```sql
   \i db/deployment_safety.sql
   ```
   This will:
   - Create backups of all production tables
   - Set up safety checks and rollback functions
   - Clean up old backups (keeps last 3 days)

2. Verify the current database state:
   ```bash
   alembic current
   ```

## Running Migrations

1. Before running migrations, ensure you're in production mode:
   ```bash
   export REPLIT_DEPLOYMENT=1
   ```

2. Run migrations with the following command:
   ```bash
   alembic upgrade head
   ```

The deployment safety system will:
- Automatically create backups before migrations
- Verify data integrity after migrations
- Automatically rollback if data loss is detected

## Troubleshooting

If a migration fails or data loss is detected:

1. The system will automatically rollback to the last backup
2. Check the postgres logs for details about what went wrong
3. Fix the migration scripts as needed
4. Re-run the deployment process

## Manual Rollback

If needed, you can manually trigger a rollback:

```sql
SELECT rollback_to_backup();
```

## Backup Management

- Backups are automatically created before migrations
- Backups are kept for 3 days
- You can view existing backups:
  ```sql
  SELECT tablename, pg_size_pretty(pg_total_relation_size(tablename::text)) 
  FROM pg_tables 
  WHERE tablename LIKE 'backup_prod_%';
