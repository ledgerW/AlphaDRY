import { formatMarketCap, getRecommendationClass, escapeHtml } from '../../js/utils/formatting.js';

// Function to create an alpha card element
export function createAlphaCard(alpha) {
    const alphaDiv = document.createElement('div');
    alphaDiv.className = 'alpha-card collapsed';

    // Create the always-visible header with timestamp
    const headerHtml = `
        <div class="alpha-header">
            <div class="alpha-header-content">
                <div class="header-left">
                    <span class="recommendation ${getRecommendationClass(alpha.recommendation)}">${escapeHtml(alpha.recommendation)}</span>
                    <span class="token-name">${escapeHtml(alpha.name)}</span>
                </div>
                <div class="header-right">
                    <span class="timestamp">${new Date(alpha.created_at.replace(/^:/, '').split('.')[0] + 'Z').toLocaleString()}</span>
                </div>
            </div>
            <span class="collapse-indicator">▼</span>
        </div>
    `;

    // Create the collapsible content
    const contentHtml = `
        <div class="alpha-content">
            <div class="alpha-details">
                <div class="detail-item">
                    <div class="detail-label">Chain:</div>
                    <div class="detail-value">${escapeHtml(alpha.chain)}</div>
                </div>
                ${alpha.contract_address ? `
                    <div class="detail-item">
                        <div class="detail-label">Contract:</div>
                        <div class="detail-value">${escapeHtml(alpha.contract_address)}</div>
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
                        <span class="score-value">${alpha.community_score || 'N/A'}</span>
                    </div>
                </div>
                <div class="detail-item score-item">
                    <div class="detail-label">Safety:</div>
                    <div class="detail-value">
                        <span class="score-value">${alpha.safety_score || 'N/A'}</span>
                    </div>
                </div>
            </div>
            <div class="justification">
                <strong>Analysis:</strong><br>
                ${escapeHtml(alpha.justification)}
            </div>
            ${alpha.sources && alpha.sources.length > 0 ? `
                <div class="sources">
                    <strong>Sources:</strong>
                    <ul>
                        ${alpha.sources.map(source => `<li>${escapeHtml(source)}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
        </div>
    `;

    alphaDiv.innerHTML = headerHtml + contentHtml;

    // Add click handler for collapsing/expanding
    const header = alphaDiv.querySelector('.alpha-header');
    header.addEventListener('click', () => {
        alphaDiv.classList.toggle('collapsed');
    });

    return alphaDiv;
}
