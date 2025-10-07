// static/script.js (Master Version)

document.addEventListener('DOMContentLoaded', () => {

    // --- 1. GET ALL HTML ELEMENTS ---
    const modeSelect = document.getElementById('mode-select');
    const daySelectorContainer = document.getElementById('day-selector-container');
    const classroomSelectorContainer = document.getElementById('classroom-selector-container');
    const subjectSelectorContainer = document.getElementById('subject-selector-container');
    const daySelect = document.getElementById('day-select');
    const classroomSelect = document.getElementById('classroom-select');
    const subjectSelect = document.getElementById('subject-select');
    const showButton = document.getElementById('show-schedule-btn');
    const displayDiv = document.getElementById('timetable-display');

    
    // --- 2. MANAGE UI CHANGES (SHOW/HIDE DROPDOWNS) ---
    modeSelect.addEventListener('change', () => {
        const selectedMode = modeSelect.value;

        // Hide all secondary dropdowns first
        daySelectorContainer.style.display = 'none';
        classroomSelectorContainer.style.display = 'none';
        subjectSelectorContainer.style.display = 'none';
        displayDiv.innerHTML = ''; // Clear the previous table

        // Show the relevant dropdown based on the selected mode
        if (selectedMode === 'day') {
            daySelectorContainer.style.display = 'block';
        } else if (selectedMode === 'classroom') {
            classroomSelectorContainer.style.display = 'block';
        } else if (selectedMode === 'subject') {
            subjectSelectorContainer.style.display = 'block';
        }
    });

    
    // --- 3. FETCH DATA WHEN BUTTON IS CLICKED ---
    const fetchAndDisplaySchedule = async () => {
        const mode = modeSelect.value;
        let endpoint = '';
        let selectedValue = '';
        let placeholderText = '';

        // Determine which API to call and which value to send
        if (mode === 'day') {
            endpoint = '/get_by_day';
            selectedValue = daySelect.value;
            placeholderText = 'Please select a day.';
        } else if (mode === 'classroom') {
            endpoint = '/get_by_classroom';
            selectedValue = classroomSelect.value;
            placeholderText = 'Please select a classroom.';
        } else if (mode === 'subject') {
            endpoint = '/get_by_subject';
            selectedValue = subjectSelect.value;
            placeholderText = 'Please select a subject.';
        }

        if (!mode || !selectedValue) {
            displayDiv.innerHTML = `<p class="placeholder">${placeholderText || 'Please select a mode and an option.'}</p>`;
            return;
        }

        displayDiv.innerHTML = '<p class="loading">Loading schedule...</p>';

        try {
            const response = await fetch(`${endpoint}?value=${selectedValue}`);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Could not fetch schedule.');
            }
            const data = await response.json();
            displayDiv.innerHTML = buildTableHTML(data);
        } catch (error) {
            displayDiv.innerHTML = `<p class="error">Error: ${error.message}</p>`;
            console.error('Failed to fetch schedule:', error);
        }
    };

    
    // --- 4. BUILD THE HTML TABLE (UNIVERSAL FUNCTION) ---
    const buildTableHTML = (data) => {
        const headers = data.columns.map(col => `<th>${col}</th>`).join('');
        
        const bodyRows = data.rows.map(row => {
            const cells = data.columns.map(col => {
                const cellContent = data.grid[row][col];
                
                if (cellContent === 'Free') {
                    return '<td class="free-slot">Free</td>';
                }
                
                return `<td>${cellContent}</td>`;
            }).join('');
            
            return `<tr><th class="time-slot">${row}</th>${cells}</tr>`;
        }).join('');

        return `
            <h2>${data.title}</h2>
            <table class="timetable">
                <thead>
                    <tr>
                        <th>Time</th>
                        ${headers}
                    </tr>
                </thead>
                <tbody>
                    ${bodyRows}
                </tbody>
            </table>
        `;
    };

    // --- 5. ATTACH EVENT LISTENER TO THE BUTTON ---
    showButton.addEventListener('click', fetchAndDisplaySchedule);
});