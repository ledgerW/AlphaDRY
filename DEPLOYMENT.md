# Deployment Safety Checklist

## ⚠️ IMPORTANT: Database Backup is MANDATORY

The backup step is **NOT** optional. You **MUST** create a backup before proceeding with any deployment steps.

## Pre-Deployment Checks

1. **Environment Variables**
   - [ ] Verify DATABASE_URL is set correctly for production
   - [ ] Verify REPLIT_DEPLOYMENT=1 is set for production environment
   - [ ] Verify API_KEY is set correctly
   - [ ] Verify API_BASE_URL is set correctly

2. **Database Backup (REQUIRED)**
   ```sql
   # This step is MANDATORY - deployment will fail without today's backup
   pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

## Deployment Steps

1. **Update Database Schema**
   - [ ] Run the deployment safety SQL script:
   ```bash
   # This script will check for backup and prevent data loss
   psql $DATABASE_URL < db/deployment_safety.sql
   ```

2. **Verify Database State**
   - [ ] Confirm all tables exist with correct prefixes and data is intact:
   ```sql
   -- Check tables exist
   SELECT table_name 
   FROM information_schema.tables 
   WHERE table_schema = 'public' 
   AND table_name LIKE 'prod_%';

   -- Verify data counts
   SELECT 
       (SELECT COUNT(*) FROM prod_token_opportunities) as token_opportunities_count,
       (SELECT COUNT(*) FROM prod_alpha_reports) as alpha_reports_count,
       (SELECT COUNT(*) FROM prod_warpcasts) as warpcasts_count,
       (SELECT COUNT(*) FROM prod_social_media_posts) as social_posts_count,
       (SELECT COUNT(*) FROM prod_token_reports) as token_reports_count;
   ```

## Rollback Plan

If issues are encountered:

1. **Stop Deployment**
   - Immediately halt any ongoing deployment steps

2. **Restore Database Backup**
   ```sql
   psql $DATABASE_URL < backup_[timestamp].sql
   ```

3. **Verify Restoration**
   - Run the data count query above to confirm data was restored correctly
   - Check application functionality

## Post-Deployment Verification

1. **Monitor System**
   - [ ] Monitor database performance
   - [ ] Verify API endpoints are responding correctly
   - [ ] Check error logs for any issues

2. **Data Integrity**
   - [ ] Verify existing data is intact using the count query above
   - [ ] Confirm new records are being created correctly
   - [ ] Sample check a few records from each table

## Schema Changes

- All schema changes must be done through ALTER statements, not DROP/CREATE
- Always use IF EXISTS/IF NOT EXISTS clauses
- Test schema changes in development first
- Include rollback statements for each schema change

## Notes

- The deployment script now includes safety checks to prevent accidental data loss
- A backup from the current day is required for deployment to proceed
- Schema changes are applied safely without dropping tables
- Monitor the application during and after deployment for any issues
