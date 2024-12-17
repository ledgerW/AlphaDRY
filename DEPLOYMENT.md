# Deployment Safety Checklist

## Pre-Deployment Checks

1. **Environment Variables**
   - [ ] Verify DATABASE_URL is set correctly for production
   - [ ] Verify REPLIT_DEPLOYMENT=1 is set for production environment
   - [ ] Verify API_KEY is set correctly
   - [ ] Verify API_BASE_URL is set correctly

2. **Database Backup**
   - [ ] Create a backup of the production database before deployment
   ```sql
   pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

## Deployment Steps

1. **Update Database Schema**
   - [ ] Run the deployment safety SQL script:
   ```bash
   psql $DATABASE_URL < db/deployment_safety.sql
   ```

2. **Verify Database State**
   - [ ] Confirm all tables exist with correct prefixes:
   ```sql
   SELECT table_name 
   FROM information_schema.tables 
   WHERE table_schema = 'public' 
   AND table_name LIKE 'prod_%';
   ```

## Rollback Plan

If issues are encountered:

1. **Restore Database Backup**
   ```sql
   psql $DATABASE_URL < backup_[timestamp].sql
   ```

## Post-Deployment Verification

1. **Monitor System**
   - [ ] Monitor database performance
   - [ ] Verify API endpoints are responding correctly

2. **Data Integrity**
   - [ ] Verify existing data is intact
   - [ ] Confirm new records are being created correctly

## Notes

- The deployment script handles both development and production environments using the appropriate table prefixes
- All database operations are performed with transaction safety
- No data migration is needed as the changes only affect schema structure
