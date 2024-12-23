// Function to format date for display
export function formatDate(dateStr) {
    try {
        // Create date and set to noon to avoid timezone issues
        const [year, month, day] = dateStr.split('-').map(Number);
        const date = new Date(year, month - 1, day, 12, 0, 0);
        if (isNaN(date.getTime())) {
            console.error('Invalid date:', dateStr);
            return 'Invalid Date';
        }
        
        const now = new Date();
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 12, 0, 0);
        const dateObj = date;
        
        // If it's today, show "Today"
        if (dateObj.getTime() === today.getTime()) {
            return 'Today';
        }
        
        // If it's yesterday, show "Yesterday"
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);
        if (dateObj.getTime() === yesterday.getTime()) {
            return 'Yesterday';
        }
        
        // Otherwise show the full date
        return date.toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    } catch (error) {
        console.error('Error formatting date:', error);
        return 'Invalid Date';
    }
}

// Function to get date key for grouping
export function getDateKey(dateStr) {
    try {
        // Handle microseconds format and remove any leading colon
        const cleanDateStr = dateStr.replace(/^:/, '').split('.')[0] + 'Z';
        const date = new Date(cleanDateStr);
        if (isNaN(date.getTime())) {
            console.error('Invalid date:', dateStr);
            return null;
        }
        // Convert to YYYY-MM-DD format
        return date.toISOString().split('T')[0];
    } catch (error) {
        console.error('Error getting date key:', error);
        return null;
    }
}

// Function to group opportunities by date
export function groupOpportunitiesByDate(opportunities) {
    const groups = {};
    opportunities.forEach(alpha => {
        if (!alpha.created_at) {
            console.error('Missing created_at for alpha:', alpha);
            return;
        }
        
        const dateKey = getDateKey(alpha.created_at);
        if (!dateKey) return;
        
        if (!groups[dateKey]) {
            groups[dateKey] = [];
        }
        groups[dateKey].push(alpha);
    });
    return groups;
}

// Function to get most recent entry per token per day
export function filterMostRecentPerToken(opportunities) {
    const tokenMap = new Map();
    opportunities.forEach(alpha => {
        const key = alpha.name;
        if (!tokenMap.has(key) || new Date(alpha.created_at) > new Date(tokenMap.get(key).created_at)) {
            tokenMap.set(key, alpha);
        }
    });
    return Array.from(tokenMap.values());
}
