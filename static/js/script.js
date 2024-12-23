import { createAlphaCard } from '../js/components/AlphaCard.js';
import { createDateNavigation } from '../js/components/DateNavigation.js';
import { formatDate, groupOpportunitiesByDate, filterMostRecentPerToken } from '../js/utils/date.js';
import { showLoading, submitReport, showError, fetchAlphaReports } from '../js/api/alphaApi.js';

// Helper function to preserve navigation while clearing container
function preserveNavigationAndClear(container) {
    const existingNav = container.querySelector('.date-navigation');
    if (existingNav) {
        existingNav.remove();
    }
    container.innerHTML = '';
    if (existingNav) {
        container.insertBefore(existingNav, container.firstChild);
    }
}

// Helper function to update URL with date
function updateUrlWithDate(date) {
    if (date) {
        const url = new URL(window.location);
        url.searchParams.set('date', date);
        window.history.pushState({}, '', url);
    }
}

// Helper function to get date from URL
function getDateFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('date');
}

// Function to load alpha feed
async function loadAlphaFeed(dateIndex = null) {
    // Check URL for date parameter on initial load
    const urlDate = getDateFromUrl();
    try {
        const container = document.getElementById('alphaContainer');
        if (!container) {
            throw new Error('Alpha container element not found');
        }

        showLoading();
        
        // If dateIndex is provided, use it to fetch data for that specific date
        let data;
        if (dateIndex !== null) {
            const sortedDates = window.sortedDates || [];
            if (sortedDates[dateIndex]) {
                data = await fetchAlphaReports(sortedDates[dateIndex]);
                // Update URL with the selected date
                updateUrlWithDate(sortedDates[dateIndex]);
            } else {
                data = await fetchAlphaReports();
            }
        } else if (urlDate) {
            // If no dateIndex but URL has date parameter, fetch that date
            data = await fetchAlphaReports(urlDate);
        } else {
            data = await fetchAlphaReports();
        }
        
        console.log('Raw API response:', data);
        
        // Clear any existing error state and loading state
        preserveNavigationAndClear(container);
        
        // Extract opportunities from the response
        let allOpportunities = [];
        console.log('Parsing data:', JSON.stringify(data, null, 2));

        try {
            // Normalize the data structure
            if (data && typeof data === 'object') {
                if (Array.isArray(data)) {
                    // Handle array of reports
                    allOpportunities = data.flatMap(report => {
                        // Handle both direct opportunities and nested opportunities array
                        const opportunities = report.opportunities || [report];
                        if (Array.isArray(opportunities)) {
                            return opportunities.map(opp => {
                                // Try to extract token name from the opportunity's message first, then fall back to report
                                const tokenMatch = opp.message?.match(/\$([A-Z0-9_]+)/) || report.message?.match(/\$([A-Z0-9_]+)/);
                                return {
                                    name: (tokenMatch?.[1] || report.token_symbol || '').toUpperCase() || 'Unknown Token',
                                    created_at: opp.created_at || report.created_at,
                                    chain: report.token_chain || 'Unknown',
                                    contract_address: report.token_address,
                                    recommendation: 'hold',
                                    justification: opp.analysis || opp.message || report.analysis || report.message,
                                    ...opp
                                };
                            });
                        }
                        return [];
                    });
                } else if (typeof data === 'object') {
                    // Handle single report, with or without opportunities array
                    const opportunities = data.opportunities || [data];
                    if (Array.isArray(opportunities)) {
                        allOpportunities = opportunities.map(opp => {
                            // Try to extract token name from the opportunity's message first, then fall back to report
                            const tokenMatch = opp.message?.match(/\$([A-Z0-9_]+)/) || data.message?.match(/\$([A-Z0-9_]+)/);
                            return {
                                name: (tokenMatch?.[1] || data.token_symbol || '').toUpperCase() || 'Unknown Token',
                                created_at: opp.created_at || data.created_at,
                                chain: data.token_chain || 'Unknown',
                                contract_address: data.token_address,
                                recommendation: 'hold',
                                justification: opp.analysis || opp.message || data.analysis || data.message,
                                ...opp
                            };
                        });
                    }
                }
            }
            console.log('Initial opportunities count:', allOpportunities.length);
        } catch (error) {
            console.error('Error normalizing data:', error);
            throw new Error('Failed to normalize opportunities data');
        }

        console.log('Extracted opportunities:', allOpportunities);
        
        // Filter and validate opportunities
        allOpportunities = allOpportunities.filter(opp => {
            try {
                if (!opp || typeof opp !== 'object') {
                    console.log('Invalid opportunity object:', opp);
                    return false;
                }

                // Ensure required fields
                if (!opp.created_at || !opp.name) {
                    console.log('Missing required fields:', opp);
                    return false;
                }

                const date = new Date(opp.created_at.replace(/^:/, '').split('.')[0] + 'Z');
                if (isNaN(date.getTime())) {
                    console.log('Invalid date:', opp.created_at);
                    return false;
                }

                // Ensure all required fields have values
                opp.recommendation = opp.recommendation || 'hold';
                opp.chain = opp.chain || 'Unknown';
                opp.justification = opp.justification || 'No analysis provided.';
                opp.community_score = opp.community_score || 'N/A';
                opp.safety_score = opp.safety_score || 'N/A';

                return true;
            } catch (validationError) {
                console.error('Error validating opportunity:', validationError, opp);
                return false;
            }
        });

        console.log('Validated opportunities count:', allOpportunities.length);
        console.log('Processed opportunities:', allOpportunities);
        
        // Create navigation if it doesn't exist
        if (!window.navigation?.element) {
            window.navigation = createDateNavigation([], 0, container);
        }

        if (allOpportunities.length === 0) {
            // Clear container but preserve navigation
            preserveNavigationAndClear(container);
            
            // Update navigation with URL date or today's date
            if (window.navigation?.element) {
                window.navigation.update(urlDate || new Date().toISOString().split('T')[0]);
            }
            
            const noDataDiv = document.createElement('div');
            noDataDiv.className = 'no-data';
            noDataDiv.textContent = 'No alpha reports available for this date';
            container.appendChild(noDataDiv);
            return;
        }

        console.log('Processing opportunities...');
        
        // Group opportunities by date
        const groupedOpportunities = groupOpportunitiesByDate(allOpportunities);
        console.log('Grouped opportunities:', groupedOpportunities);
        
        // Get sorted dates (most recent first)
        const sortedDates = Object.keys(groupedOpportunities)
            .filter(date => groupedOpportunities[date].length > 0)
            .sort((a, b) => b.localeCompare(a));
            
        // Store dates globally for navigation
        window.sortedDates = sortedDates;
        console.log('Sorted dates:', sortedDates);
        
        if (sortedDates.length === 0) {
            // Clear container but preserve navigation
            preserveNavigationAndClear(container);
            const noDataDiv = document.createElement('div');
            noDataDiv.className = 'no-data';
            noDataDiv.textContent = 'No valid dates found in reports';
            container.appendChild(noDataDiv);
            return;
        }
        
        // If dateIndex is null or invalid, check URL date or use most recent
        if (dateIndex === null || dateIndex < 0 || dateIndex >= sortedDates.length) {
            if (urlDate) {
                // Find the index of the URL date in sortedDates
                dateIndex = sortedDates.indexOf(urlDate);
                // If date not found, default to most recent
                if (dateIndex === -1) {
                    dateIndex = 0;
                }
            } else {
                dateIndex = 0;
            }
        }
        
        // Store current index globally for navigation
        window.currentDateIndex = dateIndex;
        
        // Clear existing cards but keep navigation
        preserveNavigationAndClear(container);
        
        try {
            // Get opportunities for current date
            const currentDate = sortedDates[dateIndex];
            
            // Update navigation with current date
            if (window.navigation?.element) {
                window.navigation.update(currentDate);
            }
            if (currentDate && groupedOpportunities[currentDate]) {
                // Filter for most recent entry per token
                const filteredOpportunities = filterMostRecentPerToken(groupedOpportunities[currentDate]);
                
                // Sort by timestamp (most recent first)
                filteredOpportunities.sort((a, b) => 
                    new Date(b.created_at.replace(/^:/, '').split('.')[0] + 'Z') - new Date(a.created_at.replace(/^:/, '').split('.')[0] + 'Z')
                );
                
                // Create and append cards
                let cardsCreated = 0;
                filteredOpportunities.forEach(alpha => {
                    try {
                        console.log('Creating card for:', alpha);
                        const card = createAlphaCard(alpha);
                        container.appendChild(card);
                        cardsCreated++;
                    } catch (cardError) {
                        console.error('Error creating card:', cardError, 'Alpha:', JSON.stringify(alpha, null, 2));
                    }
                });
                console.log(`Created ${cardsCreated} cards out of ${filteredOpportunities.length} opportunities`);
            }
        } catch (renderError) {
            console.error('Error rendering content:', renderError);
            // Clear container but preserve navigation
            preserveNavigationAndClear(container);
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error';
            errorDiv.style.display = 'block';
            errorDiv.innerHTML = `
                Error displaying content: ${renderError.message}
                <br><br>
                <button onclick="loadAlphaFeed()">Try Again</button>
            `;
            container.appendChild(errorDiv);
        }
    } catch (error) {
        console.error('Error loading alpha feed:', error);
        if (container) {
            // Clear container but preserve navigation
            preserveNavigationAndClear(container);
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error';
            errorDiv.style.display = 'block';
            errorDiv.innerHTML = `
                Failed to load alpha feed: ${error.message}
                <br><br>
                <button onclick="loadAlphaFeed()">Try Again</button>
            `;
            container.appendChild(errorDiv);
        }
    }
}

// Make loadAlphaFeed and submitReport available globally
window.loadAlphaFeed = loadAlphaFeed;
window.submitReport = submitReport;

// Load alpha feed when page loads
document.addEventListener('DOMContentLoaded', () => {
    // Small delay to ensure all modules are loaded
    setTimeout(loadAlphaFeed, 100);
});
