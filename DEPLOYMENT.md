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

1. **Update Database Triggers**
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
   
   - [ ] Verify trigger is correctly installed:
   ```sql
   SELECT tgname, tgrelid::regclass
   FROM pg_trigger
   WHERE tgname = 'token_report_created';
   ```

3. **Test Listener Service**
   - [ ] Restart the listener service
   - [ ] Create a test token report to verify notifications
   ```sql
   INSERT INTO prod_token_reports (
       mentions_purchasable_token,
       token_symbol,
       token_chain,
       token_address,
       is_listed_on_dex,
       trading_pairs,
       confidence_score,
       reasoning
   ) VALUES (
       true,
       'TEST',
       'ethereum',
       '0xtest',
       true,
       ARRAY['TEST/ETH'],
       9,
       'Deployment test'
   );
   ```

## Rollback Plan

If issues are encountered:

1. **Restore Database Backup**
   ```sql
   psql $DATABASE_URL < backup_[timestamp].sql
   ```

2. **Verify Listener Service**
   - [ ] Stop the listener service
   - [ ] Clear any pending notifications
   ```sql
   UNLISTEN *;
   ```
   - [ ] Restart the listener service

## Post-Deployment Verification

1. **Monitor System**
   - [ ] Check listener service logs for any errors
   - [ ] Verify notifications are being processed
   - [ ] Monitor database performance

2. **Data Integrity**
   - [ ] Verify existing data is intact
   - [ ] Confirm new records are being created correctly
   - [ ] Validate trigger notifications are working

## Notes

- The deployment script handles both development and production environments using the appropriate table prefixes
- All database operations are performed with transaction safety
- The listener service continues to use the same notification channel name ("token_report_created")
- No data migration is needed as the changes only affect triggers and not table structure
