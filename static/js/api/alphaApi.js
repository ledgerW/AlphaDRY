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
        const apiKeyMeta = document.querySelector('meta[name="api-key"]');
        if (!apiKeyMeta) {
            throw new Error('API key meta tag not found');
        }
        const apiKey = apiKeyMeta.content;
        if (!apiKey) {
            throw new Error('API key is missing');
        }
        
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
// Function to fetch a specific token's details and latest report
export async function fetchToken(address) {
    const response = await fetch(`/api/token/${encodeURIComponent(address)}?include_latest_report=true`);
    if (!response.ok) {
        throw new Error(`Failed to fetch token: ${response.status}`);
    }
    const data = await response.json();
    
    // Add latest report if available
    if (data.token_reports && Array.isArray(data.token_reports) && data.token_reports.length > 0) {
        // Sort reports by date and get the latest
        const validReports = data.token_reports.filter(report => report && typeof report === 'object');
        
        if (validReports.length > 0) {
            validReports.sort((a, b) => {
                const dateA = new Date(b.created_at || b.timestamp || 0);
                const dateB = new Date(a.created_at || a.timestamp || 0);
                return dateA - dateB;
            });
            
            // Get the latest report and validate required fields
            const latestReport = validReports[0];
            const requiredFields = [
                'mentions_purchasable_token',
                'token_symbol',
                'token_chain',
                'token_address',
                'is_listed_on_dex',
                'confidence_score',
                'reasoning'
            ];

            const missingFields = requiredFields.filter(field => 
                latestReport[field] === undefined || latestReport[field] === null
            );

            if (missingFields.length === 0) {
                data.latest_report = latestReport;
            } else {
                console.warn('Latest report missing required fields:', missingFields);
            }
        }
    }
    return data;
}

export async function runTokenAlphaScout(tokenReport, tokenReportId) {
    try {
        const apiKey = document.querySelector('meta[name="api-key"]').content;
        const response = await fetch('/api/multi_agent_alpha_scout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-key': apiKey
            },
            body: JSON.stringify({
                token_report: {
                    mentions_purchasable_token: tokenReport.mentions_purchasable_token,
                    token_symbol: tokenReport.token_symbol,
                    token_chain: tokenReport.token_chain,
                    token_address: tokenReport.token_address,
                    is_listed_on_dex: tokenReport.is_listed_on_dex,
                    trading_pairs: tokenReport.trading_pairs || [],
                    confidence_score: tokenReport.confidence_score,
                    reasoning: tokenReport.reasoning
                },
                token_report_id: tokenReportId
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(errorText || 'Failed to run alpha scout');
        }

        const result = await response.json();
        console.log('Alpha scout response:', result);

        if (!result || typeof result !== 'object') {
            throw new Error('Invalid response from alpha scout');
        }

        // Ensure we have all required fields from TokenOpportunity model
        const requiredFields = ['name', 'chain', 'justification', 'sources', 'recommendation'];
        const missingFields = requiredFields.filter(field => !result[field]);
        
        if (missingFields.length > 0) {
            throw new Error(`Invalid response: missing required fields ${missingFields.join(', ')}`);
        }

        // Add a small delay to ensure database operations complete
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        return result;
    } catch (error) {
        console.error('Error running alpha scout:', error);
        throw error;
    }
}

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
        // First parse the raw JSON to handle any potential formatting issues
        let parsedData;
        try {
            parsedData = JSON.parse(text);
        } catch (parseError) {
            // If direct parsing fails, try to fix common JSON formatting issues
            const fixedJson = text.replace(/}{"id"/g, '},{"id"')
                                .replace(/}{"name"/g, '},{"name"')
                                .replace(/"([^"]+)"(\d+|true|false)/g, '"$1":$2')
                                .replace(/"([^"]+)"\[/g, '"$1":[')
                                .replace(/}\[/g, '},[');
            parsedData = JSON.parse(fixedJson);
        }

        // Clean up any colons in contract addresses
        const cleanData = (data) => {
            if (Array.isArray(data)) {
                return data.map(item => cleanData(item));
            }
            if (typeof data === 'object' && data !== null) {
                const cleaned = {};
                for (const [key, value] of Object.entries(data)) {
                    if (key === 'contract_address' && typeof value === 'string') {
                        cleaned[key] = value.replace(/^:/, '');
                    } else if (typeof value === 'object' && value !== null) {
                        cleaned[key] = cleanData(value);
                    } else {
                        cleaned[key] = value;
                    }
                }
                return cleaned;
            }
            return data;
        };

        return cleanData(parsedData);
    } catch (error) {
        console.error('Error parsing JSON:', error);
        throw new Error(`Failed to parse API response: ${error.message}`);
    }
}
