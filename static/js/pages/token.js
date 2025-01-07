import { fetchToken, runTokenAlphaScout } from '/static/js/api/alphaApi.js';
import { escapeHtml } from '/static/js/utils/formatting.js';

function createOpportunityHTML(opportunity) {
    // Create source links HTML if sources are available
    const sourceLinks = opportunity.sources ? opportunity.sources
        .filter(url => url) // Filter out null/empty URLs
        .map(url => `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(url)}</a>`)
        .join('<br>') : '';

    return `
        <div class="token-opportunity">
            <p><strong>Market Cap:</strong> ${opportunity.market_cap ? '$' + opportunity.market_cap.toLocaleString() : 'N/A'}</p>
            <p>${escapeHtml(opportunity.justification)}</p>
            ${sourceLinks ? `<div class="source-links"><strong>Sources:</strong><br>${sourceLinks}</div>` : ''}
            <p class="timestamp">${new Date(opportunity.created_at).toLocaleString()}</p>
        </div>
    `;
}

function createSocialPostHTML(socialPost) {
    const date = new Date(socialPost.timestamp);
    const formattedDate = date.toLocaleDateString();
    
    return `
        <div class="social-post">
            <img src="/static/warpcast.png" alt="Warpcast" class="warpcast-logo">
            <div class="social-post-header">
                <span>${formattedDate}</span>
            </div>
            <div class="social-post-content">${escapeHtml(socialPost.text)}</div>
            <div class="social-post-author">@${escapeHtml(socialPost.author_display_name)}</div>
            <div class="social-metrics">
                <div class="metric">
                    <span class="metric-icon">❤️</span>
                    ${socialPost.reactions_count || 0}
                </div>
                <div class="metric">
                    <span class="metric-icon">💬</span>
                    ${socialPost.replies_count || 0}
                </div>
                <div class="metric">
                    <span class="metric-icon">🔄</span>
                    ${socialPost.reposts_count || 0}
                </div>
            </div>
        </div>
    `;
}

function canRunAnalysis(lastAnalysisTime) {
    if (!lastAnalysisTime) {
        console.log('No previous analysis time found');
        return true;
    }
    const oneHour = 60 * 60 * 1000;
    const lastAnalysisUTC = new Date(lastAnalysisTime + 'Z');
    const currentUTC = new Date();
    const timeSinceLastAnalysis = currentUTC.getTime() - lastAnalysisUTC.getTime();
    console.log('Last analysis UTC:', lastAnalysisUTC.toISOString());
    console.log('Current time UTC:', currentUTC.toISOString());
    console.log('Time since analysis (ms):', timeSinceLastAnalysis);
    return timeSinceLastAnalysis >= oneHour;
}

function updateButtonState(lastAnalysisTime) {
    const button = document.getElementById('runAlphaScout');
    const messageEl = document.getElementById('timeMessage');
    
    if (!canRunAnalysis(lastAnalysisTime)) {
        const lastAnalysisUTC = new Date(lastAnalysisTime + 'Z');
        const currentUTC = new Date();
        const elapsedMs = currentUTC.getTime() - lastAnalysisUTC.getTime();
        const minutesElapsed = Math.floor(elapsedMs / (60 * 1000));
        const minutesLeft = 60 - minutesElapsed;
        const adjustedMinutes = Math.max(0, Math.min(60, minutesLeft));
        
        console.log('Button disabled - minutes remaining:', adjustedMinutes);
        button.disabled = true;
        messageEl.textContent = `Available in ${adjustedMinutes} minute${adjustedMinutes !== 1 ? 's' : ''}`;
    } else {
        console.log('Button enabled - analysis can be run');
        button.disabled = false;
        messageEl.textContent = '';
    }
}

async function loadTokenData() {
    const urlParams = new URLSearchParams(window.location.search);
    const urlTokenAddress = urlParams.get('address');
    const tokenGrid = document.querySelector('.token-grid');
    
    if (!urlTokenAddress) {
        tokenGrid.innerHTML = `
            <div class="error-message">
                <p>Error: No token address provided</p>
                <p>Please access this page through a token link from the home page.</p>
            </div>`;
        return;
    }

    try {
        const token = await fetchToken(urlTokenAddress);

        if (!token) {
            tokenGrid.innerHTML = `
                <div class="error-message">
                    <p>No opportunities found for token address:</p>
                    <p class="token-address">${escapeHtml(urlTokenAddress)}</p>
                    <p>This token may not have been analyzed yet.</p>
                </div>`;
            return;
        }

        // Update header with token details
        if (token.image_url) {
            const tokenImage = document.querySelector('.token-image');
            tokenImage.src = token.image_url;
            tokenImage.alt = `${token.name} logo`;
        }

        document.querySelector('.token-name').textContent = token.name;
        document.querySelector('.token-chain').innerHTML = `
            <img src="/static/${token.chain.toLowerCase() === 'solana' ? 'solana_icon.svg' : 'base_icon.svg'}" 
                alt="${escapeHtml(token.chain)} icon" 
                class="chain-icon" />
            ${escapeHtml(token.chain)}
        `;

        const addressElement = document.querySelector('.token-address');
        addressElement.textContent = token.address ? `${token.address.slice(0, 4)}...${token.address.slice(-4)}` : '';
        addressElement.onclick = () => copyAddress(token.address);
        document.querySelector('.copy-icon').onclick = () => copyAddress(token.address);

        const tokenUrls = document.querySelector('.token-urls');
        tokenUrls.innerHTML = `
            ${token.website_url ? `
                <a href="${escapeHtml(token.website_url)}" target="_blank" rel="noopener noreferrer" class="token-url" title="Website">
                    <svg viewBox="0 0 24 24">
                        <path fill="#00ff88" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zM4 12c0-1.95.7-3.74 1.87-5.13L9 10v2h2v2h2v3h2v-3h1c1.1 0 2-.9 2-2v-2c0-1.1-.9-2-2-2h-3V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 4.41-3.59 8-8 8s-8-3.59-8-8z"/>
                    </svg>
                </a>
            ` : ''}
            ${token.warpcast_url ? `
                <a href="${escapeHtml(token.warpcast_url)}" target="_blank" rel="noopener noreferrer" class="token-url" title="Warpcast">
                    <img src="/static/warpcast.png" alt="Warpcast">
                </a>
            ` : ''}
            ${token.twitter_url ? `
                <a href="${escapeHtml(token.twitter_url)}" target="_blank" rel="noopener noreferrer" class="token-url" title="Twitter">
                    <img src="/static/twitter.svg" alt="Twitter">
                </a>
            ` : ''}
            ${token.telegram_url ? `
                <a href="${escapeHtml(token.telegram_url)}" target="_blank" rel="noopener noreferrer" class="token-url" title="Telegram">
                    <img src="/static/Telegram_logo.svg" alt="Telegram">
                </a>
            ` : ''}
            ${token.signal_url ? `
                <a href="${escapeHtml(token.signal_url)}" target="_blank" rel="noopener noreferrer" class="token-url" title="Signal">
                    <i>📞</i>
                </a>
            ` : ''}
            ${token.chain.toLowerCase() === 'base' ? `
                <a href="https://dexscreener.com/base/${token.address}" target="_blank" rel="noopener noreferrer" class="token-url" title="DEX Screener">
                    <img src="/static/dex_screener.png" alt="DEX Screener">
                </a>
            ` : ''}
        `;

        // Sort opportunities by date
        const opportunities = token.token_opportunities.sort((a, b) => 
            new Date(b.created_at) - new Date(a.created_at)
        );

        // Clear loading message and create content sections
        tokenGrid.innerHTML = `
            <div style="padding: 0 20px; margin-bottom: 30px;">
                <div style="display: flex; flex-direction: column; gap: 15px; align-items: center;">
                    <h2 class="section-header" style="margin: 0;">Token Analysis</h2>
                    <div class="button-container">
                        <button id="runAlphaScout" class="action-button">
                            🚀 🔬 Run Alpha Analysis
                        </button>
                        <div id="timeMessage"></div>
                    </div>
                </div>
            </div>
            ${opportunities.length > 0 
                ? createOpportunityHTML(opportunities[0])
                : '<p style="text-align: center;">No opportunities found for this token.</p>'
            }
            
            ${opportunities.length > 1 ? `
                <button class="collapsible">Past Analysis</button>
                <div class="content">
                    <div id="historical-opportunities"></div>
                    <div class="pagination"></div>
                </div>
            ` : ''}

            <h2 class="section-header">Related Social Posts</h2>
            <div id="social-posts"></div>
        `;

        if (opportunities.length > 1) {
            // Set up collapsible functionality
            const collapsible = document.querySelector('.collapsible');
            collapsible.addEventListener('click', function() {
                this.classList.toggle('active');
                const content = this.nextElementSibling;
                content.classList.toggle('active');
            });

            // Set up pagination for historical opportunities
            const itemsPerPage = 10;
            const historicalOpps = opportunities.slice(1);
            const totalPages = Math.ceil(historicalOpps.length / itemsPerPage);
            let currentPage = 1;

            function displayHistoricalOpportunities(page) {
                const start = (page - 1) * itemsPerPage;
                const end = start + itemsPerPage;
                const pageOpps = historicalOpps.slice(start, end);
                
                document.getElementById('historical-opportunities').innerHTML = 
                    pageOpps.map(opp => createOpportunityHTML(opp)).join('');
                
                document.querySelector('.pagination').innerHTML = `
                    <button ${page === 1 ? 'disabled' : ''} onclick="window.changePage(${page - 1})">Previous</button>
                    <span>Page ${page} of ${totalPages}</span>
                    <button ${page === totalPages ? 'disabled' : ''} onclick="window.changePage(${page + 1})">Next</button>
                `;
            }

            window.changePage = function(page) {
                currentPage = page;
                displayHistoricalOpportunities(page);
            };

            displayHistoricalOpportunities(1);
        }

        // Set up alpha scout button handler
        const lastAnalysisTime = opportunities.length > 0 ? opportunities[0].created_at : null;
        updateButtonState(lastAnalysisTime);

        // Update time message every minute
        setInterval(() => updateButtonState(lastAnalysisTime), 60000);

        document.getElementById('runAlphaScout').addEventListener('click', async function() {
            try {
                this.disabled = true;
                this.textContent = '🚀 🔬 Running Analysis...';
                this.style.animation = 'pulse 1.5s infinite';
                
                if (!token.latest_report) {
                    throw new Error('Cannot run analysis: No previous token report available. Please create an initial token report first.');
                }

                console.log('Using latest report:', token.latest_report);

                const formattedReport = {
                    mentions_purchasable_token: token.latest_report.mentions_purchasable_token,
                    token_symbol: token.latest_report.token_symbol,
                    token_chain: token.latest_report.token_chain,
                    token_address: token.latest_report.token_address,
                    is_listed_on_dex: token.latest_report.is_listed_on_dex,
                    trading_pairs: token.latest_report.trading_pairs || [],
                    confidence_score: token.latest_report.confidence_score,
                    reasoning: token.latest_report.reasoning
                };

                const result = await runTokenAlphaScout(formattedReport, token.latest_report.id);
                
                if (result) {
                    window.location.reload();
                } else {
                    throw new Error('Failed to get analysis result');
                }
            } catch (error) {
                console.error('Error running alpha scout:', error);
                alert('Failed to run alpha analysis: ' + error.message);
                this.disabled = false;
                this.textContent = '🚀 🔬 Run Alpha Analysis';
                this.style.animation = 'none';
            }
        });

        // Get social posts from token reports
        const socialPosts = token.token_reports
            .filter(report => report.social_media_post)
            .map(report => report.social_media_post);

        document.getElementById('social-posts').innerHTML = 
            socialPosts.length > 0
                ? socialPosts.map(post => createSocialPostHTML(post)).join('')
                : '<p style="text-align: center;">No social posts found for this token.</p>';

    } catch (error) {
        console.error('Error loading token data:', error);
        tokenGrid.innerHTML = 
            '<p>Error loading token data. Please try again later.</p>';
    }
}

// Add copy feedback element
const feedbackEl = document.createElement('div');
feedbackEl.className = 'copy-feedback';
feedbackEl.textContent = 'Address copied!';
document.body.appendChild(feedbackEl);

// Copy address function
window.copyAddress = function(address) {
    navigator.clipboard.writeText(address).then(() => {
        feedbackEl.classList.add('show');
        setTimeout(() => {
            feedbackEl.classList.remove('show');
        }, 2000);
    });
};

// Initialize
document.addEventListener('DOMContentLoaded', loadTokenData);
