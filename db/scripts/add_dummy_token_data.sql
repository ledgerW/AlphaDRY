-- Get the token_id for our target token
WITH token_id AS (
    SELECT id FROM dev_tokens 
    WHERE LOWER(address) = LOWER('0x0578d8A44db98B23BF096A382e016e29a5Ce0ffe')
)

-- Insert dummy social media post
, inserted_post AS (
    INSERT INTO dev_social_media_posts (
        source, post_id, author_id, author_username, author_display_name,
        text, original_timestamp, timestamp, reactions_count, replies_count,
        reposts_count, raw_data, created_at
    )
    SELECT
        'warpcast',
        'dummy_post_' || NOW()::text,
        'dummy_author',
        'dummyuser',
        'Dummy User',
        'Just analyzed this interesting token. Looking promising with strong fundamentals. #crypto #analysis',
        NOW() - INTERVAL '2 days',
        NOW() - INTERVAL '2 days',
        42,
        15,
        7,
        '{"dummy": "data"}'::jsonb,
        NOW() - INTERVAL '2 days'
    RETURNING id
)

-- Insert token report linked to the social post and token
, inserted_report AS (
    INSERT INTO dev_token_reports (
        mentions_purchasable_token, token_symbol, token_chain, token_address,
        is_listed_on_dex, trading_pairs, confidence_score, reasoning,
        created_at, token_id
    )
    SELECT
        true,
        'TOKEN',
        'base',
        LOWER('0x0578d8A44db98B23BF096A382e016e29a5Ce0ffe'),
        true,
        '["TOKEN/ETH", "TOKEN/USDC"]'::jsonb,
        8,
        'Strong fundamentals with growing community engagement. Technical analysis shows bullish patterns.',
        NOW() - INTERVAL '2 days',
        t.id
    FROM token_id t
    RETURNING id
)

-- Update social_media_post with token_report_id
, update_post AS (
    UPDATE dev_social_media_posts sp
    SET token_report_id = tr.id
    FROM inserted_post ip, inserted_report tr
    WHERE sp.id = ip.id
)

-- Insert token opportunity
INSERT INTO dev_token_opportunities (
    name, chain, contract_address, market_cap,
    community_score, safety_score, justification,
    sources, recommendation, created_at,
    token_report_id, token_id
)
SELECT
    'Emerging DeFi Token',
    'base',
    LOWER('0x0578d8A44db98B23BF096A382e016e29a5Ce0ffe'),
    5000000.00,
    75,
    80,
    'Token shows strong potential with active development and growing community. Recent updates and partnerships indicate positive momentum.',
    '["on-chain-analysis", "social-metrics", "technical-analysis"]'::jsonb,
    'Buy',
    NOW() - INTERVAL '2 days',
    tr.id,
    t.id
FROM inserted_report tr, token_id t;

-- Add a second, older report for history
WITH token_id AS (
    SELECT id FROM dev_tokens 
    WHERE LOWER(address) = LOWER('0x0578d8A44db98B23BF096A382e016e29a5Ce0ffe')
)

-- Insert older social media post
, inserted_old_post AS (
    INSERT INTO dev_social_media_posts (
        source, post_id, author_id, author_username, author_display_name,
        text, original_timestamp, timestamp, reactions_count, replies_count,
        reposts_count, raw_data, created_at
    )
    SELECT
        'warpcast',
        'dummy_old_post_' || NOW()::text,
        'dummy_author_2',
        'cryptoanalyst',
        'Crypto Analyst',
        'Initial review of this token. Early stages but showing promise. Will keep monitoring. #crypto',
        NOW() - INTERVAL '5 days',
        NOW() - INTERVAL '5 days',
        35,
        12,
        5,
        '{"dummy": "old_data"}'::jsonb,
        NOW() - INTERVAL '5 days'
    RETURNING id
)

-- Insert older token report
, inserted_old_report AS (
    INSERT INTO dev_token_reports (
        mentions_purchasable_token, token_symbol, token_chain, token_address,
        is_listed_on_dex, trading_pairs, confidence_score, reasoning,
        created_at, token_id
    )
    SELECT
        true,
        'TOKEN',
        'base',
        LOWER('0x0578d8A44db98B23BF096A382e016e29a5Ce0ffe'),
        true,
        '["TOKEN/ETH"]'::jsonb,
        7,
        'Initial analysis shows promising fundamentals. Early stage but worth monitoring.',
        NOW() - INTERVAL '5 days',
        t.id
    FROM token_id t
    RETURNING id
)

-- Update old social_media_post with token_report_id
, update_old_post AS (
    UPDATE dev_social_media_posts sp
    SET token_report_id = tr.id
    FROM inserted_old_post ip, inserted_old_report tr
    WHERE sp.id = ip.id
)

-- Insert older token opportunity
INSERT INTO dev_token_opportunities (
    name, chain, contract_address, market_cap,
    community_score, safety_score, justification,
    sources, recommendation, created_at,
    token_report_id, token_id
)
SELECT
    'New DeFi Project',
    'base',
    LOWER('0x0578d8A44db98B23BF096A382e016e29a5Ce0ffe'),
    3000000.00,
    65,
    70,
    'Early stage token with good initial metrics. Development team appears competent. Community is growing.',
    '["on-chain-analysis", "social-metrics"]'::jsonb,
    'Hold',
    NOW() - INTERVAL '5 days',
    tr.id,
    t.id
FROM inserted_old_report tr, token_id t;
