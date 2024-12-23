// Function to format market cap
export function formatMarketCap(marketCap) {
    if (!marketCap) return 'N/A';
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(marketCap);
}

// Function to get recommendation class
export function getRecommendationClass(recommendation) {
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

// Function to safely escape HTML
export function escapeHtml(unsafe) {
    if (typeof unsafe !== 'string') return unsafe;
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
