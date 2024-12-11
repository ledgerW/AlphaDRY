// Function to format market cap
function formatMarketCap(marketCap) {
    if (!marketCap) return 'N/A';
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximaxFractionDigits: 0
    }).format(marketCap);
}

// Function to get recommendation class
function getRecommendationClass(recommendation) {
    switch (recommendation.toLowerCase()) {
        case 'buy':
            return 'recommendation-buy';
        case 'sell':
            return 'recommendation-sell';
        case 'hold':
            return 'recommendation-hold';
        default:
            return 'recommendation-hold';
    }
}

// Function to create an alpha card element
function createAlphaCard(alpha) {
    const alphaDiv = document.createElement('div');
    alphaDiv.className = 'alpha-card';

    alphaDiv.innerHTML = `
        <div class="alpha-header">
            <span class="token-name">${alpha.name}</span>
            <span class="recommendation ${getRecommendationClass(alpha.recommendation)}">${alpha.recommendation}</span>
        </div>
        <div class="alpha-details">
            <div class="detail-item">
                <div class="detail-label">Chain:</div>
                <div class="detail-value">${alpha.chain}</div>
            </div>
            ${alpha.contract_address ? `
                <div class="detail-item">
                    <div class="detail-label">Contract:</div>
                    <div class="detail-value">${alpha.contract_address}</div>
                </div>
            ` : ''}
            ${alpha.market_cap ? `
                <div class="detail-item">
                    <div class="detail-label">Market Cap:</div>
                    <div class="detail-value">${formatMarketCap(alpha.market_cap)}</div>
                </div>
            ` : ''}
            <div class="detail-item score-item">
                <div class="detail-label">Community:</div>
                <div class="detail-value">
                    <span class="score-value">${alpha.community_score}/10</span>
                </div>
            </div>
            <div class="detail-item score-item">
                <div class="detail-label">Safety:</div>
                <div class="detail-value">
                    <span class="score-value">${alpha.safety_score}/10</span>
                </div>
            </div>
        </div>
        <div class="justification">
            <strong>Analysis:</strong><br>
            ${alpha.justification}
        </div>
        ${alpha.sources && alpha.sources.length > 0 ? `
            <div class="sources">
                <strong>Sources:</strong>
                <ul>
                    ${alpha.sources.map(source => `<li>${source}</li>`).join('')}
                </ul>
            </div>
        ` : ''}
        ${alpha.created_at ? `
            <div class="timestamp">
                ${new Date(alpha.created_at).toLocaleString()}
            </div>
        ` : ''}
    `;
    
    return alphaDiv;
}

// Function to load alpha feed
async function loadAlphaFeed() {
    try {
        const response = await fetch('/api/alpha_reports');
        const reports = await response.json();
        
        const container = document.getElementById('alphaContainer');
        container.innerHTML = ''; // Clear existing cards
        
        // Create array of all opportunities with their timestamps
        const allOpportunities = reports.flatMap(report => {
            return report.opportunities.map(alpha => {
                // Use created_at from the opportunity itself
                return alpha;
            });
        });

        // Sort opportunities by timestamp (most recent first)
        allOpportunities.sort((a, b) => {
            const timeA = a.created_at ? new Date(a.created_at).getTime() : 0;
            const timeB = b.created_at ? new Date(b.created_at).getTime() : 0;
            return timeB - timeA; // Reverse sort (newest first)
        });
        
        // Create and append cards
        allOpportunities.forEach(alpha => {
            container.appendChild(createAlphaCard(alpha));
        });
    } catch (error) {
        console.error('Error loading alpha feed:', error);
        showError('Failed to load alpha feed. Please try again later.');
    }
}

// Function to submit the token report
async function submitReport() {
    const loadingIndicator = document.getElementById('loadingIndicator');
    const errorMessage = document.getElementById('errorMessage');
    
    // Get form values
    const mentionsPurchasableToken = document.getElementById('mentionsPurchasableToken').checked;
    const tokenSymbol = document.getElementById('tokenSymbol').value.trim();
    const tokenChain = document.getElementById('tokenChain').value.trim();
    const tokenAddress = document.getElementById('tokenAddress').value.trim();
    const isListedOnDex = document.getElementById('isListedOnDex').checked;
    const tradingPairs = document.getElementById('tradingPairs').value.trim()
        ? document.getElementById('tradingPairs').value.trim().split(',').map(pair => pair.trim())
        : null;
    const confidenceScore = parseInt(document.getElementById('confidenceScore').value);
    const reasoning = document.getElementById('reasoning').value.trim();

    // Validate required fields
    if (!reasoning) {
        showError('Reasoning is required');
        return;
    }
    if (confidenceScore < 1 || confidenceScore > 10) {
        showError('Confidence score must be between 1 and 10');
        return;
    }

    try {
        loadingIndicator.style.display = 'block';
        errorMessage.style.display = 'none';
        
        // Get API key from meta tag
        const apiKey = document.querySelector('meta[name="api-key"]').content;
        
        // Create IsTokenReport object matching the Pydantic model
        const tokenReport = {
            mentions_purchasable_token: mentionsPurchasableToken,
            token_symbol: tokenSymbol || null,
            token_chain: tokenChain || null,
            token_address: tokenAddress || null,
            is_listed_on_dex: isListedOnDex,
            trading_pairs: tradingPairs,
            confidence_score: confidenceScore,
            reasoning: reasoning
        };

        const response = await fetch('/api/multi_agent_alpha_scout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-key': apiKey
            },
            body: JSON.stringify(tokenReport)
        });

        if (!response.ok) {
            const error = await response.text();
            throw new Error(error);
        }

        const result = await response.json();

        // Clear form
        document.getElementById('mentionsPurchasableToken').checked = false;
        document.getElementById('tokenSymbol').value = '';
        document.getElementById('tokenChain').value = '';
        document.getElementById('tokenAddress').value = '';
        document.getElementById('isListedOnDex').checked = false;
        document.getElementById('tradingPairs').value = '';
        document.getElementById('confidenceScore').value = '5';
        document.getElementById('reasoning').value = '';

        // Refresh alpha feed
        await loadAlphaFeed();
    } catch (error) {
        console.error('Error submitting report:', error);
        showError(`Failed to submit report: ${error.message}`);
    } finally {
        loadingIndicator.style.display = 'none';
    }
}

// Function to show error message
function showError(message) {
    const errorMessage = document.getElementById('errorMessage');
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
}

// Load alpha feed when page loads
document.addEventListener('DOMContentLoaded', loadAlphaFeed);
