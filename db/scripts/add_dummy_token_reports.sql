-- Add token reports first
INSERT INTO dev_token_reports (
    token_id, mentions_purchasable_token,
    token_symbol, token_chain, token_address, is_listed_on_dex,
    trading_pairs, confidence_score, reasoning, created_at
)
SELECT 
    t.id,
    true,
    t.symbol,
    t.chain,
    t.address,
    true,
    '["USDC"]'::json,
    0.85,
    'Strong social signals and growing community interest',
    NOW() - INTERVAL '2 days'
FROM dev_tokens t
WHERE t.symbol = 'ALPHA'
UNION ALL
SELECT 
    t.id,
    true,
    t.symbol,
    t.chain,
    t.address,
    true,
    '["USDC", "ETH"]'::json,
    0.90,
    'Active development and positive community sentiment',
    NOW() - INTERVAL '1 day'
FROM dev_tokens t
WHERE t.symbol = 'BETA'
UNION ALL
SELECT 
    t.id,
    true,
    t.symbol,
    t.chain,
    t.address,
    true,
    '["USDC"]'::json,
    0.95,
    'Innovative product with strong market potential',
    NOW() - INTERVAL '12 hours'
FROM dev_tokens t
WHERE t.symbol = 'GAMMA'
UNION ALL
SELECT 
    t.id,
    true,
    t.symbol,
    t.chain,
    t.address,
    true,
    '["USDC", "ETH"]'::json,
    0.88,
    'Continued positive development and growing metrics',
    NOW() - INTERVAL '6 hours'
FROM dev_tokens t
WHERE t.symbol = 'ALPHA';

-- Now add social media posts with token_report_id references
INSERT INTO dev_social_media_posts (
    source, post_id, author_id, author_username, author_display_name,
    text, original_timestamp, timestamp, reactions_count, replies_count, reposts_count,
    created_at, token_report_id, raw_data
)
VALUES 
    ('warpcast', 'post1', 'user1', 'alpha_finder', 'Alpha Finder',
     'Just found a great new token $ALPHA on Base! Looks promising with strong fundamentals.',
     NOW() - INTERVAL '2 days', NOW() - INTERVAL '2 days', 150, 25, 45,
     NOW() - INTERVAL '2 days',
     (SELECT id FROM dev_token_reports WHERE token_symbol = 'ALPHA' AND created_at = NOW() - INTERVAL '2 days'),
     '{}'::jsonb),
    ('warpcast', 'post2', 'user2', 'token_hunter', 'Token Hunter',
     'Deep dive into $BETA - solid team, great roadmap, and growing community! #Base',
     NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day', 200, 35, 60,
     NOW() - INTERVAL '1 day',
     (SELECT id FROM dev_token_reports WHERE token_symbol = 'BETA' AND created_at = NOW() - INTERVAL '1 day'),
     '{}'::jsonb),
    ('warpcast', 'post3', 'user3', 'crypto_scout', 'Crypto Scout',
     'New Solana gem alert! $GAMMA launching soon with innovative tokenomics.',
     NOW() - INTERVAL '12 hours', NOW() - INTERVAL '12 hours', 300, 50, 80,
     NOW() - INTERVAL '12 hours',
     (SELECT id FROM dev_token_reports WHERE token_symbol = 'GAMMA' AND created_at = NOW() - INTERVAL '12 hours'),
     '{}'::jsonb),
    ('warpcast', 'post4', 'user1', 'alpha_finder', 'Alpha Finder',
     'Second look at $ALPHA - the metrics are even better than expected! #DeFi',
     NOW() - INTERVAL '6 hours', NOW() - INTERVAL '6 hours', 180, 30, 55,
     NOW() - INTERVAL '6 hours',
     (SELECT id FROM dev_token_reports WHERE token_symbol = 'ALPHA' AND created_at = NOW() - INTERVAL '6 hours'),
     '{}'::jsonb);

-- Add some token opportunities to test market cap filtering and sorting
INSERT INTO dev_token_opportunities (
    token_id, name, chain, contract_address, market_cap,
    community_score, safety_score, justification, sources,
    recommendation, created_at
)
SELECT 
    t.id,
    t.symbol || ' Token Opportunity',
    t.chain,
    t.address,
    CASE 
        WHEN t.symbol = 'ALPHA' THEN 5000000  -- $5M
        WHEN t.symbol = 'BETA' THEN 15000000  -- $15M
        WHEN t.symbol = 'GAMMA' THEN 2000000  -- $2M
        ELSE 1000000  -- $1M default
    END,
    0.85,
    0.90,
    'Strong fundamentals and growing community',
    '["twitter", "telegram", "discord"]'::json,
    'Buy',
    NOW() - INTERVAL '1 day'
FROM dev_tokens t
WHERE t.symbol IN ('ALPHA', 'BETA', 'GAMMA');
