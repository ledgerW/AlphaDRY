let tokensData = [];
let selectedChains = ['base', 'solana'];
let selectedMarketCap = 'all';

function calculateKoiEvents(token) {
    if (!token.token_reports) return 0;
    
    return token.token_reports.reduce((total, report) => {
        if (!report.social_media_post) return total;
        const post = report.social_media_post;
        return total + 1 + // Count the post itself
            (post.reactions_count || 0) +
            (post.replies_count || 0) +
            (post.reposts_count || 0);
    }, 0);
}

function getLatestOpportunity(token) {
    if (!token.token_opportunities || token.token_opportunities.length === 0) {
        return null;
    }
    return token.token_opportunities.reduce((latest, current) => {
        const latestDate = new Date(latest.created_at);
        const currentDate = new Date(current.created_at);
        return currentDate > latestDate ? current : latest;
    });
}

function handleChainFilter() {
    selectedChains = Array.from(document.querySelectorAll('.chain-option input:checked'))
        .map(input => input.value);
    applyFiltersAndSort();
}

function handleMarketCapFilter() {
    selectedMarketCap = document.querySelector('input[name="market-cap"]:checked').value;
    applyFiltersAndSort();
}

function handleSort(sortBy) {
    applyFiltersAndSort(sortBy);
}

function applyFiltersAndSort(sortBy = document.getElementById('sort-select').value) {
    if (!tokensData.length) return;

    let filteredTokens = tokensData.filter(token => {
        // Chain filter
        if (!selectedChains.includes(token.chain)) return false;

        // Market cap filter
        if (selectedMarketCap !== 'all') {
            const latestOpp = getLatestOpportunity(token);
            const marketCap = latestOpp?.market_cap || 0;
            if (marketCap > Number(selectedMarketCap)) return false;
        }

        return true;
    });

    const sortedTokens = [...filteredTokens];
    
    if (sortBy === 'recent_opportunity') {
        sortedTokens.sort((a, b) => {
            const aOpp = getLatestOpportunity(a);
            const bOpp = getLatestOpportunity(b);
            
            if (!aOpp && !bOpp) return 0;
            if (!aOpp) return 1;
            if (!bOpp) return -1;
            
            return new Date(bOpp.created_at) - new Date(aOpp.created_at);
        });
    } else if (sortBy === 'market_cap') {
        sortedTokens.sort((a, b) => {
            const aOpp = getLatestOpportunity(a);
            const bOpp = getLatestOpportunity(b);
            
            const aMarketCap = aOpp?.market_cap || 0;
            const bMarketCap = bOpp?.market_cap || 0;
            
            return bMarketCap - aMarketCap;
        });
    } else if (sortBy === 'kol_events') {
        sortedTokens.sort((a, b) => {
            const aEvents = calculateKoiEvents(a);
            const bEvents = calculateKoiEvents(b);
            return bEvents - aEvents;
        });
    } else if (sortBy === 'recent_social') {
        sortedTokens.sort((a, b) => {
            const aLatestPost = a.token_reports?.reduce((latest, report) => {
                if (!report.social_media_post) return latest;
                const postDate = new Date(report.social_media_post.created_at);
                return !latest || postDate > latest ? postDate : latest;
            }, null);
            
            const bLatestPost = b.token_reports?.reduce((latest, report) => {
                if (!report.social_media_post) return latest;
                const postDate = new Date(report.social_media_post.created_at);
                return !latest || postDate > latest ? postDate : latest;
            }, null);
            
            if (!aLatestPost && !bLatestPost) return 0;
            if (!aLatestPost) return 1;
            if (!bLatestPost) return -1;
            
            return bLatestPost - aLatestPost;
        });
    }

    displayTokens(sortedTokens);
}

async function fetchTokens() {
    try {
        const response = await fetch('/api/tokens');
        if (!response.ok) {
            throw new Error('Failed to fetch tokens');
        }
        tokensData = await response.json();
        handleSort('recent_opportunity');
    } catch (error) {
        console.error('Error:', error);
        document.querySelector('.token-grid').innerHTML = `
            <div class="error-message">
                <p>Error loading tokens. Please try again later.</p>
            </div>
        `;
    }
}

function displayTokens(tokens) {
    if (!tokens || tokens.length === 0) {
        document.querySelector('.token-grid').innerHTML = `
            <div class="error-message">
                <p>No tokens found.</p>
            </div>
        `;
        return;
    }

    const tokenGrid = document.querySelector('.token-grid');
    tokenGrid.innerHTML = tokens.map(token => `
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

// Load tokens when the page loads
fetchTokens();
