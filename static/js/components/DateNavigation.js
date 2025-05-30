import { formatDate } from '../../js/utils/date.js';

// Function to create date navigation
export function createDateNavigation(dates, currentDateIndex, container) {
    if (!container) {
        console.error('Container element not provided to createDateNavigation');
        return null;
    }

    const nav = document.createElement('div');
    nav.className = 'date-navigation';
    
    // Get the current date from URL or use today if not available
    const urlParams = new URLSearchParams(window.location.search);
    const currentUrlDate = urlParams.get('date') || new Date().toISOString().split('T')[0];
    
    let formattedDate;
    try {
        formattedDate = formatDate(currentUrlDate);
    } catch (error) {
        console.error('Error formatting date for navigation:', error);
        formattedDate = 'Invalid Date';
    }
    
    nav.innerHTML = `
        <button class="nav-btn" id="prevDay">←</button>
        <span class="current-date">${formattedDate}</span>
        <button class="nav-btn" id="nextDay">→</button>
    `;
    
    // Helper function to adjust date
    const adjustDate = (dateStr, days) => {
        const date = new Date(dateStr);
        date.setDate(date.getDate() + days);
        return date.toISOString().split('T')[0];
    };

    // Create click handlers
    const handlePrevClick = () => {
        const urlParams = new URLSearchParams(window.location.search);
        const currentDate = urlParams.get('date') || new Date().toISOString().split('T')[0];
        const newDate = adjustDate(currentDate, -1);
        
        const url = new URL(window.location);
        url.searchParams.set('date', newDate);
        window.location.href = url.toString();
    };
    
    const handleNextClick = () => {
        const urlParams = new URLSearchParams(window.location.search);
        const currentDate = urlParams.get('date') || new Date().toISOString().split('T')[0];
        const newDate = adjustDate(currentDate, 1);
        
        const url = new URL(window.location);
        url.searchParams.set('date', newDate);
        window.location.href = url.toString();
    };

    try {
        container.insertBefore(nav, container.firstChild);
        
        // Attach event listeners
        const prevBtn = nav.querySelector('#prevDay');
        const nextBtn = nav.querySelector('#nextDay');
        
        if (prevBtn) {
            prevBtn.onclick = handlePrevClick;
        }
        
        if (nextBtn) {
            nextBtn.onclick = handleNextClick;
        }
    } catch (error) {
        console.error('Error inserting navigation element:', error);
        return null;
    }
    
    // Create navigation object with element and update function
    const navigation = {
        element: nav,
        update: function(newDate) {
            const prevBtn = this.element.querySelector('#prevDay');
            const nextBtn = this.element.querySelector('#nextDay');
            const dateSpan = this.element.querySelector('.current-date');
            
            if (prevBtn && nextBtn && dateSpan) {
                try {
                    dateSpan.textContent = formatDate(newDate);
                } catch (error) {
                    console.error('Error updating date display:', error);
                    dateSpan.textContent = 'Invalid Date';
                }
                
                // Always enable buttons since we're using direct date navigation
                prevBtn.disabled = false;
                nextBtn.disabled = false;
                
                // Ensure click handlers are attached
                prevBtn.onclick = handlePrevClick;
                nextBtn.onclick = handleNextClick;
            }
        }
    };
    
    return navigation;
}
