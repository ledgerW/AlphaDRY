let nextCursor = null;
let isLoading = false;
let hasMoreTokens = true;
const TOKENS_PER_PAGE = 10;

// Get filter values
function getSelectedChains() {
    return Array.from(document.querySelectorAll('.chain-option input:checked'))
        .map(input => input.value)
        .join(',');
}

function getSelectedMarketCap() {
    const value = document.querySelector('input[name="market-cap"]:checked').value;
    return value === 'all' ? null : Number(value);
}

function getSortBy() {
    return document.getElementById('sort-select').value;
}

// Create intersection observer for infinite scroll
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting && !isLoading && hasMoreTokens) {
            loadMoreTokens();
        }
    });
}, { threshold: 0.1 });

function calculateKoiEvents(token) {
    if (!token.token_reports) return 0;
    
    // Count unique social media posts and their engagement
    const uniquePosts = new Map(); // Use Map to track unique posts by ID
    
    // Ensure we're working with an array of token_reports
    const allReports = Array.isArray(token.token_reports) ? token.token_reports : [];
    
    allReports.forEach(report => {
        if (!report.social_media_post) return;
        const post = report.social_media_post;
        
        // Only count each unique post once using post_id as the unique identifier
        if (!uniquePosts.has(post.post_id)) {
            uniquePosts.set(post.post_id, {
                reactions: post.reactions_count || 0,
                replies: post.replies_count || 0,
                reposts: post.reposts_count || 0
            });
        }
    });

    // Sum up all engagement from unique posts
    return Array.from(uniquePosts.values()).reduce((total, post) => {
        return total + 1 + post.reactions + post.replies + post.reposts;
    }, 0);
}

function getLatestOpportunity(token) {
    if (!token.token_opportunities || token.token_opportunities.length === 0) {
        return null;
    }
    
    // Sort opportunities by date and return the most recent one
    const sortedOpps = [...token.token_opportunities].sort((a, b) => 
        new Date(b.created_at) - new Date(a.created_at)
    );
    
    return sortedOpps[0];
}

function getLatestSocialPost(token) {
    if (!token.token_reports) return null;
    
    // Ensure we're working with an array of token_reports
    const allReports = Array.isArray(token.token_reports) ? token.token_reports : [];
    
    const postsWithDates = allReports
        .filter(report => report.social_media_post)
        .map(report => ({
            date: new Date(report.social_media_post.timestamp),
            post: report.social_media_post
        }));
    
    if (postsWithDates.length === 0) return null;
    
    return postsWithDates.reduce((latest, current) => 
        current.date > latest.date ? current : latest
    ).date;
}

async function fetchTokens(cursor = null) {
    try {
        // Build URL with filter parameters
        const params = new URLSearchParams({
            per_page: TOKENS_PER_PAGE,
            chains: getSelectedChains(),
            sort_by: getSortBy()
        });

        if (cursor) {
            params.append('cursor', cursor);
        }

        const marketCapMax = getSelectedMarketCap();
        if (marketCapMax !== null) {
            params.append('market_cap_max', marketCapMax);
        }

        const response = await fetch(`/api/tokens?${params}`);
        if (!response.ok) {
            throw new Error('Failed to fetch tokens');
        }
        const data = await response.json();
        
        hasMoreTokens = data.has_more;
        nextCursor = data.next_cursor;
        
        // Display tokens
        displayTokens(data.tokens, cursor !== null);
    } catch (error) {
        console.error('Error:', error);
        document.querySelector('.token-grid').innerHTML = `
            <div class="error-message">
                <p>Error loading tokens. Please try again later.</p>
            </div>
        `;
    }
}

async function loadMoreTokens() {
    if (isLoading || !hasMoreTokens || !nextCursor) return;
    
    isLoading = true;
    try {
        await fetchTokens(nextCursor);
    } finally {
        isLoading = false;
    }
}

function displayTokens(tokens, append = false) {
    const tokenGrid = document.querySelector('.token-grid');
    
    if (!tokens || tokens.length === 0) {
        if (!append) {
            tokenGrid.innerHTML = `
                <div class="error-message">
                    <p>No tokens found.</p>
                </div>
            `;
        }
        return;
    }

    // Remove existing loading element if it exists
    const existingLoader = tokenGrid.querySelector('.loading');
    if (existingLoader) {
        existingLoader.remove();
    }

    // When appending, filter out tokens that are already displayed
    if (append) {
        const existingTokens = new Set(
            Array.from(tokenGrid.querySelectorAll('.token-link'))
                .map(el => el.getAttribute('href').split('=')[1])
        );
        tokens = tokens.filter(token => !existingTokens.has(encodeURIComponent(token.address)));
    }

    // Create tokens HTML
    const tokensHtml = tokens.map(token => `
        <a href="/token?address=${encodeURIComponent(token.address)}" class="token-link">
            <div class="token-card">
                <div class="token-top">
                    <img src="${token.image_url || '/static/IMG_2358.png'}" class="token-icon" alt="${escapeHtml(token.symbol)} icon" />
                    <div class="token-info">
                        <div class="token-symbol">${escapeHtml(token.symbol)}</div>
                        <div class="token-address">${truncateAddress(token.address)}</div>
                    </div>
                    <div class="token-chain">
                        <img src="/static/${token.chain === 'solana' ? 'solana_icon.svg' : 'base_icon.svg'}" 
                             alt="${escapeHtml(token.chain)} icon" 
                             class="chain-icon" />
                        ${escapeHtml(token.chain)}
                    </div>
                </div>
                <div class="token-details">
                    ${renderOpportunityDetails(token)}
                </div>
            </div>
        </a>
    `).join('');

    if (append) {
        // Remove the old loading indicator if it exists
        const oldLoader = tokenGrid.querySelector('.loading');
        if (oldLoader) {
            oldLoader.remove();
        }
        
        // Append new tokens
        tokenGrid.insertAdjacentHTML('beforeend', tokensHtml);
    } else {
        // Replace all content
        tokenGrid.innerHTML = tokensHtml;
    }

    // Add loading indicator if there are more tokens
    if (hasMoreTokens) {
        const loadingElement = document.createElement('div');
        loadingElement.className = 'loading';
        loadingElement.textContent = 'Loading more tokens...';
        tokenGrid.appendChild(loadingElement);

        // Observe the loading element
        observer.observe(loadingElement);
    }
}

function truncateAddress(address) {
    if (!address) return '';
    if (address.length <= 8) return address;
    return `${address.slice(0, 4)}...${address.slice(-4)}`;
}

function formatMarketCap(marketCap) {
    if (!marketCap) return 'N/A';
    if (marketCap >= 1e9) {
        return `$${(marketCap / 1e9).toFixed(2)}B`;
    }
    if (marketCap >= 1e6) {
        return `$${(marketCap / 1e6).toFixed(2)}M`;
    }
    return `$${marketCap.toLocaleString()}`;
}

function renderOpportunityDetails(token) {
    const latestOpp = getLatestOpportunity(token);
    const koiEvents = calculateKoiEvents(token);

    if (!latestOpp) {
        return `
            <div class="token-dates">
                <div><span class="date-label">Created:</span>${new Date(token.created_at).toLocaleDateString()}</div>
            </div>
            <div class="token-metrics">
                <div class="token-kol-events"><span class="metric-label">KOL Events:</span>${koiEvents.toLocaleString()}</div>
            </div>
        `;
    }

    return `
        <div class="token-dates">
            <div><span class="date-label">Created:</span>${new Date(token.created_at).toLocaleDateString()}</div>
            <div><span class="date-label">Last Update:</span>${new Date(latestOpp.created_at).toLocaleDateString()}</div>
        </div>
        <div class="token-metrics">
            <div class="token-market-cap"><span class="metric-label">Market Cap:</span>${formatMarketCap(latestOpp.market_cap)}</div>
            <div class="token-kol-events"><span class="metric-label">KOL Events:</span>${koiEvents.toLocaleString()}</div>
        </div>
    `;
}

function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Add event listener for Apply button
document.getElementById('apply-filters').addEventListener('click', () => {
    // Reset cursor when applying filters
    nextCursor = null;
    hasMoreTokens = true;
    fetchTokens(null);
});

// Initial load
fetchTokens(null);
