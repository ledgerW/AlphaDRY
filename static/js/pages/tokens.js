let tokensData = [];
let selectedChains = ['base', 'solana'];
let selectedMarketCap = 'all';
let currentPage = 0;
let isLoading = false;
let hasMoreTokens = true;
const TOKENS_PER_PAGE = 10;

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

function handleChainFilter() {
    selectedChains = Array.from(document.querySelectorAll('.chain-option input:checked'))
        .map(input => input.value);
    currentPage = 0;
    hasMoreTokens = true;
    applyFiltersAndSort();
}

function handleMarketCapFilter() {
    selectedMarketCap = document.querySelector('input[name="market-cap"]:checked').value;
    currentPage = 0;
    hasMoreTokens = true;
    applyFiltersAndSort();
}

function handleSort(sortBy) {
    currentPage = 0;
    hasMoreTokens = true;
    applyFiltersAndSort(sortBy, false);
}

function applyFiltersAndSort(sortBy = document.getElementById('sort-select').value, loadMore = false) {
    if (!tokensData.length) return;

    // Create a Map to ensure unique tokens by address while merging token_reports
    const uniqueTokens = new Map();
    tokensData.forEach(token => {
        if (!uniqueTokens.has(token.address)) {
            // Initialize the token with its data
            uniqueTokens.set(token.address, {
                ...token,
                token_reports: [],
                token_opportunities: []
            });
        }
        
        // Get the existing token from the Map
        const existingToken = uniqueTokens.get(token.address);
        
        // Merge token_reports if they exist
        if (token.token_reports) {
            existingToken.token_reports = existingToken.token_reports.concat(token.token_reports);
        }
        
        // Merge token_opportunities if they exist
        if (token.token_opportunities) {
            existingToken.token_opportunities = existingToken.token_opportunities.concat(token.token_opportunities);
        }
    });

    let filteredTokens = Array.from(uniqueTokens.values()).filter(token => {
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
            const aLatestPost = getLatestSocialPost(a);
            const bLatestPost = getLatestSocialPost(b);
            
            if (!aLatestPost && !bLatestPost) return 0;
            if (!aLatestPost) return 1;
            if (!bLatestPost) return -1;
            
            return bLatestPost - aLatestPost;
        });
    }

    // Calculate start and end indices for pagination
    const startIndex = loadMore ? currentPage * TOKENS_PER_PAGE : 0;
    const endIndex = startIndex + TOKENS_PER_PAGE;
    
    // Update current page
    if (!loadMore) {
        currentPage = 0;
    }
    
    // Get the subset of tokens to display
    const tokensToDisplay = sortedTokens.slice(startIndex, endIndex);
    
    // Check if we have more tokens to load
    hasMoreTokens = endIndex < sortedTokens.length;
    
    // If loading more, increment the page counter
    if (loadMore) {
        currentPage++;
    }
    
    // Display the tokens
    displayTokens(tokensToDisplay, loadMore);
}

async function fetchTokens() {
    try {
        const response = await fetch('/api/tokens');
        if (!response.ok) {
            throw new Error('Failed to fetch tokens');
        }
        tokensData = await response.json();
        currentPage = 0;
        hasMoreTokens = true;
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

function loadMoreTokens() {
    if (isLoading || !hasMoreTokens) return;
    
    isLoading = true;
    const sortBy = document.getElementById('sort-select').value;
    applyFiltersAndSort(sortBy, true);
    isLoading = false;
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

// Load tokens when the page loads
fetchTokens();
