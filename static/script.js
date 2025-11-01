// static/script.js (Final Version with Mobile UI Fix)

document.addEventListener('DOMContentLoaded', () => {

    // --- 1. GET ALL HTML ELEMENTS ---

    // Master View Elements
    const liveViewBtn = document.getElementById('btn-mode-live');
    const advancedViewBtn = document.getElementById('btn-mode-advanced');
    const liveViewContainer = document.getElementById('live-schedule-view');
    const advancedViewContainer = document.getElementById('advanced-view');

    // --- Master Mode 1 (Live) Elements ---
    const liveDaySelect = document.getElementById('day-select'); 
    const liveTimeSelect = document.getElementById('time-select'); 
    const liveShowBtn = document.getElementById('show-live-btn');
    const liveDisplayDiv = document.getElementById('live-schedule-display');
    const timeSlots = Array.from(liveTimeSelect.options).map(opt => opt.value).filter(Boolean);
    const daysOrder = Array.from(liveDaySelect.options).map(opt => opt.value).filter(Boolean);

    // --- Master Mode 2 (Advanced) Elements ---
    const modeSelect = document.getElementById('mode-select');
    const advDaySelectorContainer = document.getElementById('advanced-day-selector-container');
    const advDaySelect = document.getElementById('advanced-day-select'); 
    const classroomSelectorContainer = document.getElementById('classroom-selector-container');
    const subjectSelectorContainer = document.getElementById('subject-selector-container');
    const teacherSelectorContainer = document.getElementById('teacher-selector-container');
    const labSubjectSelectorContainer = document.getElementById('lab-subject-selector-container');
    const classroomSelect = document.getElementById('classroom-select');
    const subjectSelect = document.getElementById('subject-select');
    const teacherSelect = document.getElementById('teacher-select');
    const labSubjectSelect = document.getElementById('lab-subject-select');
    const advShowButton = document.getElementById('show-schedule-btn');
    const advDisplayDiv = document.getElementById('timetable-display');
    const buttonContainer = document.getElementById('button-container'); 
    
    // Shared Pagination Elements
    const tableNav = document.getElementById('table-nav');
    const btnPrev = document.getElementById('btn-prev');
    const btnNext = document.getElementById('btn-next');

    // Pagination State
    let currentPage = 0;
    let totalPages = 1;
    let tableWidth = 0;
    let containerWidth = 0;
    let currentTable = null;

    // --- 2. MASTER MODE TOGGLE LOGIC ---

    liveViewBtn.addEventListener('click', () => {
        liveViewContainer.style.display = 'block';
        advancedViewContainer.style.display = 'none';
        liveViewBtn.classList.add('active');
        advancedViewBtn.classList.remove('active');
        advDisplayDiv.innerHTML = '';
        tableNav.style.display = 'none';
    });

    advancedViewBtn.addEventListener('click', () => {
        liveViewContainer.style.display = 'none';
        advancedViewContainer.style.display = 'block';
        liveViewBtn.classList.remove('active');
        advancedViewBtn.classList.add('active');
        liveDisplayDiv.innerHTML = '';
    });

    // --- 3. MASTER MODE 1: "LIVE SCHEDULE" LOGIC ---

    const fetchLiveSchedule = async () => {
        const selectedDay = liveDaySelect.value;
        const selectedSlot = liveTimeSelect.value;

        if (!selectedDay || !selectedSlot) {
            liveDisplayDiv.innerHTML = '<p class="placeholder">Please select a day and a time slot.</p>';
            return;
        }
        
        liveDisplayDiv.innerHTML = '<p class="loading">Finding schedule...</p>';
        
        try {
            const url = `/get_live_schedule?day=${encodeURIComponent(selectedDay)}&slot=${encodeURIComponent(selectedSlot)}`;
            const response = await fetch(url);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: 'Could not fetch schedule.' }));
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            liveDisplayDiv.innerHTML = buildLiveScheduleHTML(data);
            
        } catch (error) {
            liveDisplayDiv.innerHTML = `<p class="error">Error: ${error.message}</p>`;
            console.error('Failed to fetch live schedule:', error);
        }
    };

    const buildLiveScheduleHTML = (data) => {
        let theoryHTML = '<h3>Theory Classes</h3>';
        if (!data.theory_classes || data.theory_classes.length === 0) {
            theoryHTML += '<p>No theory classes scheduled.</p>';
        } else {
            theoryHTML += '<div class="lab-list-container">'; 
            theoryHTML += '<ul class="lab-list">';
            data.theory_classes.forEach((item, index) => {
                const colorClass = `time-color-${index % 7}`;
                theoryHTML += `
                    <li class="lab-list-item ${colorClass}">
                        <span class="lab-subject">${item.subject} (${item.division})</span><br>
                        <span class="lab-details">Venue: ${item.room}</span> | 
                        <span class="lab-details">Teacher: ${item.teacher}</span>
                    </li>`;
            });
            theoryHTML += '</ul></div>';
        }

        let labHTML = '<h3>Lab Sessions (Ongoing)</h3>';
        if (!data.lab_classes || data.lab_classes.length === 0) {
            labHTML += '<p>No lab sessions scheduled.</p>';
        } else {
            labHTML += '<div class="lab-list-container">';
            labHTML += '<ul class="lab-list">';
            data.lab_classes.forEach((lab, index) => {
                const colorClass = `time-color-${(index + 2) % 7}`; 
                labHTML += `
                    <li class="lab-list-item ${colorClass}">
                        <span class="lab-subject">${lab.subject} (${lab.division})</span><br>
                        <span class="lab-details">Venue: ${lab.room}</span> | 
                        <span class="lab-details">Teacher: ${lab.teacher}</span> |
                        <span class="lab-details">Slot: ${lab.time}</span>
                    </li>`;
            });
            labHTML += '</ul></div>';
        }

        return `<h2>${data.title || 'Schedule'}</h2>${theoryHTML}<br>${labHTML}`;
    };

    // --- 4. MASTER MODE 2: "ADVANCED VIEW" LOGIC ---

    modeSelect.addEventListener('change', () => {
        const selectedMode = modeSelect.value;
        
        advDaySelectorContainer.style.display = 'none'; 
        classroomSelectorContainer.style.display = 'none';
        subjectSelectorContainer.style.display = 'none';
        teacherSelectorContainer.style.display = 'none';
        labSubjectSelectorContainer.style.display = 'none'; 
        
        if (buttonContainer) buttonContainer.style.display = 'none'; 

        advDisplayDiv.innerHTML = '';
        tableNav.style.display = 'none';
        advDisplayDiv.style.overflowX = 'auto'; 

        if (selectedMode === 'day') {
            advDaySelectorContainer.style.display = 'block'; 
            if (buttonContainer) buttonContainer.style.display = 'block';
        } else if (selectedMode === 'classroom') {
            classroomSelectorContainer.style.display = 'block';
            if (buttonContainer) buttonContainer.style.display = 'block';
        } else if (selectedMode === 'subject') {
            subjectSelectorContainer.style.display = 'block';
            if (buttonContainer) buttonContainer.style.display = 'block';
        } else if (selectedMode === 'labs') {
            labSubjectSelectorContainer.style.display = 'block';
            if (buttonContainer) buttonContainer.style.display = 'block';
        } else if (selectedMode === 'teacher') {
            teacherSelectorContainer.style.display = 'block';
            if (buttonContainer) buttonContainer.style.display = 'block';
        }
    });

    const fetchAdvancedSchedule = async () => {
        const mode = modeSelect.value;
        let endpoint = '';
        let selectedValue = '';
        let requiresValue = true;

        switch (mode) {
            case 'day': endpoint = '/get_by_day'; selectedValue = advDaySelect.value; break;
            case 'classroom': endpoint = '/get_by_classroom'; selectedValue = classroomSelect.value; break;
            case 'subject': endpoint = '/get_by_subject'; selectedValue = subjectSelect.value; break;
            case 'labs': endpoint = '/get_by_labs'; selectedValue = labSubjectSelect.value; break;
        case 'teacher': endpoint = '/get_by_teacher'; selectedValue = teacherSelect.value; break;
            default: advDisplayDiv.innerHTML = '<p class="placeholder">Please select a valid mode.</p>'; return;
        }

        if (requiresValue && !selectedValue) {
            advDisplayDiv.innerHTML = `<p class="placeholder">Please select an option.</p>`; return;
        }

        advDisplayDiv.innerHTML = '<p class="loading">Loading schedule...</p>';
        tableNav.style.display = 'none';

        try {
            const url = requiresValue ? `${endpoint}?value=${encodeURIComponent(selectedValue)}` : endpoint;
            const response = await fetch(url);
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: 'Could not fetch schedule.' }));
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }
            const data = await response.json();

            if (data.grid_type === 'hybrid_day_view') {
                advDisplayDiv.innerHTML = buildHybridDayViewHTML(data);
                // --- THIS IS THE FIX ---
                // ONLY run pagination for the Day View grid
                setupPagination(); 
                // --- END OF FIX ---
            } else {
                advDisplayDiv.innerHTML = buildGridHTML(data);
                // We do NOT run setupPagination() here
            }
            
            highlightAdvancedView(); 

        } catch (error) {
            advDisplayDiv.innerHTML = `<p class="error">Error: ${error.message}</p>`;
            console.error('Failed to fetch schedule:', error);
        }
    };

    // --- 5. HTML BUILDERS FOR ADVANCED VIEW ---

    const buildHybridDayViewHTML = (data) => {
        const gridHeaders = (data.columns || []).map(col => `<th>${col}</th>`).join('');
        const gridBodyRows = (data.rows || []).map(row => {
            const cells = (data.columns || []).map(col => {
                const cellContent = data.classroom_grid && data.classroom_grid[row] ? data.classroom_grid[row][col] || 'Free' : 'Free';
                return cellContent === 'Free' ? `<td data-label="${col}" class="free-slot">Free</td>` : `<td data-label="${col}">${cellContent}</td>`;
            }).join('');
            return `<tr><th class="time-slot">${row}</th>${cells}</tr>`;
        }).join('');
        
        // --- THIS IS THE FIX ---
        // Added the 'day-view-grid' class to the table
        const gridHTML = `
            <h3>Regular Classrooms</h3>
            <div id="table-nav-wrapper"></div> 
            <table class="timetable day-view-grid">
                <thead><tr><th>Time</th>${gridHeaders}</tr></thead>
                <tbody>${gridBodyRows}</tbody>
            </table>
        `;
        // --- END OF FIX ---

        let listHTML = '<h3>Scheduled Labs</h3>';
        const scheduledLabsList = data.scheduled_labs || [];

        if (!Array.isArray(scheduledLabsList) || scheduledLabsList.length === 0) {
            listHTML += '<p>No labs scheduled for this day.</p>';
        } else {
            const labsGroupedByTime = {};
            scheduledLabsList.forEach(lab => {
                const timeSlot = lab.time;
                if (!labsGroupedByTime[timeSlot]) {
                    labsGroupedByTime[timeSlot] = [];
                }
                labsGroupedByTime[timeSlot].push(lab);
            });

            listHTML += '<div class="lab-list-container">';
            
            const sortKey = (timeStr) => {
                const parts = (timeStr || '99:99').split('-')[0].split(':');
                try { 
                    if (parts.length >= 2) { 
                        let hour = parseInt(parts[0]);
                        const minute = parseInt(parts[1]);
                        if (hour < 8) hour += 12; 
                        return hour * 60 + minute; 
                    } return 9999; 
                } catch { return 9999; }
            };
            
            const sortedTimeSlots = Object.keys(labsGroupedByTime).sort((a, b) => sortKey(a) - sortKey(b));
            
            let labsDisplayed = false;
            sortedTimeSlots.forEach((timeSlot, index) => {
                if (labsGroupedByTime[timeSlot] && labsGroupedByTime[timeSlot].length > 0) {
                    labsDisplayed = true;
                    const colorClass = `time-color-${index % 7}`;
                    listHTML += `<h4 class="lab-timeslot-header ${colorClass}">${timeSlot}</h4>`;
                    listHTML += '<ul class="lab-list">';
                    labsGroupedByTime[timeSlot].forEach(lab => {
                        listHTML += `<li class="lab-list-item ${colorClass}"><span class="lab-subject">${lab.subject || 'N/A'} (${lab.division || 'N/A'})</span><br><span class="lab-details">Venue: ${lab.room || 'N/A'}</span> | <span class="lab-details">Teacher: ${lab.teacher || 'N/A'}</span></li>`;
                    });
                    listHTML += '</ul>';
                }
            });

            if (!labsDisplayed) { listHTML += '<p>No labs scheduled for this day.</p>'; }
            listHTML += '</div>';
        }

        return `<h2>${data.title || 'Schedule'}</h2>${gridHTML}<br>${listHTML}`;
    };


    const buildGridHTML = (data) => {
        const navHTML = `<div id="table-nav-wrapper"></div>`; 
        
        const headers = (data.columns || []).map(col => `<th>${col}</th>`).join('');
        const bodyRows = (data.rows || []).map(row => {
            const cells = (data.columns || []).map(col => {
                const cellContent = data.grid && data.grid[row] ? data.grid[row][col] || 'Free' : 'Free';
                return cellContent === 'Free' ? `<td data-label="${col}" class="free-slot">Free</td>` : `<td data-label="${col}">${cellContent}</td>`;
            }).join('');
            return `<tr><th class="time-slot">${row}</th>${cells}</tr>`;
        }).join('');
        
        return `
            <h2>${data.title || 'Schedule'}</h2>
            ${navHTML}
            <table class="timetable">
                <thead><tr><th>Time</th>${headers}</tr></thead>
                <tbody>${bodyRows}</tbody>
            </table>
        `;
    };

    // --- 6. PAGINATION LOGIC (Shared) ---
    
    function setupPagination() {
        // --- THIS IS THE FIX ---
        // Find the 'day-view-grid' table specifically
        currentTable = advDisplayDiv.querySelector('table.timetable.day-view-grid');
        // --- END OF FIX ---
        
        const navWrapper = advDisplayDiv.querySelector('#table-nav-wrapper'); 
        
        if (!currentTable || !navWrapper) {
            tableNav.style.display = 'none';
            return;
        }
        
        navWrapper.appendChild(tableNav);
        currentPage = 0;
        currentTable.style.transform = 'translateX(0)';
        
        setTimeout(() => {
            tableWidth = currentTable.scrollWidth;
            containerWidth = advDisplayDiv.clientWidth;
            
            if (tableWidth > containerWidth + 1) { 
                totalPages = Math.ceil(tableWidth / containerWidth);
                tableNav.style.display = 'flex';
                advDisplayDiv.style.overflowX = 'hidden';
            } else {
                totalPages = 1;
                tableNav.style.display = 'none';
                advDisplayDiv.style.overflowX = 'auto';
            }
            updateNavButtons();
        }, 100);
    }

    function updateNavButtons() {
        btnPrev.disabled = (currentPage === 0);
        btnNext.disabled = (currentPage >= totalPages - 1);
    }

    btnNext.addEventListener('click', () => {
        if (currentPage < totalPages - 1 && currentTable) {
            currentPage++;
            let moveAmount = currentPage * containerWidth;
            if (moveAmount + containerWidth > tableWidth) {
                moveAmount = tableWidth - containerWidth;
            }
            currentTable.style.transform = `translateX(-${moveAmount}px)`;
            updateNavButtons();
        }
    });

    btnPrev.addEventListener('click', () => {
        if (currentPage > 0 && currentTable) {
            currentPage--;
            const moveAmount = currentPage * containerWidth;
            currentTable.style.transform = `translateX(-${moveAmount}px)`;
            updateNavButtons();
        }
    });

    // --- 7. SHARED HELPER & ADVANCED VIEW HIGHLIGHTING ---
    
    const parseSlotRangeToDecimal = (slot_str) => {
        try {
            const [start_str, end_str] = slot_str.split('-');
            const [start_hour_str, start_min_str] = start_str.split(':');
            const [end_hour_str, end_min_str] = end_str.split(':');

            let start_hour = parseInt(start_hour_str);
            let end_hour = parseInt(end_hour_str);

            if (start_hour < 8) start_hour += 12;
            if (end_hour < 8) end_hour += 12;

            if (start_hour === 11 && end_hour === 12) {
                // 11:30-12:30
            } 
            else if (start_hour === 12 && end_hour === 1) {
                end_hour = 13; // 12:30-01:30
            }
            else if (end_hour < start_hour) {
                end_hour += 12;
            }

            const start_decimal = start_hour + parseInt(start_min_str) / 60;
            const end_decimal = end_hour + parseInt(end_min_str) / 60;

            return [start_decimal, end_decimal];
        } catch (e) {
            console.error("Could not parse time slot:", slot_str, e);
            return null;
        }
    };

    const highlightAdvancedView = () => {
        const now = new Date(); 
        const currentDay = now.toLocaleString('en-US', { weekday: 'long' });
        const currentHour = now.getHours() + now.getMinutes() / 60;
        const mode = modeSelect.value; 

        document.querySelectorAll('.timetable tbody tr').forEach(row => {
            const timeSlotEl = row.querySelector('th.time-slot');
            if (!timeSlotEl) return;
            
            const timeSlot = parseSlotRangeToDecimal(timeSlotEl.innerText);
            if (timeSlot && currentHour >= timeSlot[0] && currentHour < timeSlot[1]) {
                row.classList.add('active-row');
            }
        });

        if (mode !== 'day') {
            const dayHeaders = Array.from(document.querySelectorAll('.timetable thead th'));
            const dayIndex = dayHeaders.findIndex(th => th.innerText.trim() === currentDay);

            if (dayIndex > 0) { 
                document.querySelectorAll('.timetable tr').forEach(row => {
                    const cell = row.querySelector(`th:nth-child(${dayIndex + 1}), td:nth-child(${dayIndex + 1})`);
                    if (cell) cell.classList.add('active-day');
                });
            }
        }
        
        if (mode === 'day' && advDaySelect.value === currentDay) {
            document.querySelectorAll('.lab-timeslot-header').forEach(header => {
                const timeSlot = parseSlotRangeToDecimal(header.innerText);
                if (timeSlot && currentHour >= timeSlot[0] && currentHour < timeSlot[1]) {
                    header.classList.add('active-lab-header');
                    const list = header.nextElementSibling;
                    if (list && list.classList.contains('lab-list')) {
                        list.classList.add('active-lab-list');
                    }
                }
            });
        }
    };
    
    // --- 8. INITIAL PAGE LOAD LOGIC ---
    
    const initializeLiveView = () => {
        try {
            const now = new Date();
            const utc = now.getTime() + (now.getTimezoneOffset() * 60000);
            const istDate = new Date(utc + (330 * 60000));
            
            const currentDay = istDate.toLocaleString('en-US', { weekday: 'long' });
            const currentHour = istDate.getHours() + istDate.getMinutes() / 60; 

            if (daysOrder.includes(currentDay)) {
                liveDaySelect.value = currentDay;
            } else {
                liveDaySelect.value = daysOrder[0]; 
            }

            let currentSlotFound = false;
            if (daysOrder.includes(currentDay)) { 
                for (const slot of timeSlots) {
                    const [start, end] = parseSlotRangeToDecimal(slot); 
                    if (currentHour >= start && currentHour < end) {
                        liveTimeSelect.value = slot;
                        currentSlotFound = true;
                        break;
                    }
                }
            }

            if (currentSlotFound) {
                fetchLiveSchedule();
            } else {
                liveDisplayDiv.innerHTML = `<p class="placeholder">No classes Going on right now, try manually</p>`;
            }

        } catch(e) {
            console.error("Failed to initialize live view:", e);
            liveDisplayDiv.innerHTML = `<p class="error">No classes Going on right now, try manually</p>`;
        }
    };

    // Attach button listeners
    liveShowBtn.addEventListener('click', fetchLiveSchedule);
    advShowButton.addEventListener('click', fetchAdvancedSchedule);

    // Run the app!
    initializeLiveView(); // Run on page load
});