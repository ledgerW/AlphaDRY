// Function to show loading state
export function showLoading() {
    const container = document.getElementById('alphaContainer');
    if (container) {
        container.innerHTML = `
            <div class="loading">Loading alpha reports...</div>
            <div class="skeleton"></div>
            <div class="skeleton"></div>
            <div class="skeleton"></div>
        `;
    }
}

// Function to submit the token report
export async function submitReport() {
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

        return result;
    } catch (error) {
        console.error('Error submitting report:', error);
        showError(`Failed to submit report: ${error.message}`);
        throw error;
    } finally {
        loadingIndicator.style.display = 'none';
    }
}

// Function to show error message
export function showError(message) {
    const errorMessage = document.getElementById('errorMessage');
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
}

// Function to fetch alpha reports
export async function fetchAlphaReports(date = null) {
    const url = date ? `/api/alpha_reports?date=${date}` : '/api/alpha_reports';
    const response = await fetch(url);
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}. ${errorText}`);
    }
    try {
        const text = await response.text();
        // Add missing commas between properties
        const fixedJson = text.replace(/}{"id"/g, '},{"id"')
                             .replace(/}{"name"/g, '},{"name"')
                             .replace(/"([^"]+)"(\d+|true|false)/g, '"$1":$2')
                             .replace(/"([^"]+)"\[/g, '"$1":[')
                             .replace(/}\[/g, '},[');
        return JSON.parse(fixedJson);
    } catch (error) {
        console.error('Error parsing JSON:', error);
        throw new Error(`Failed to parse API response: ${error.message}`);
    }
}
