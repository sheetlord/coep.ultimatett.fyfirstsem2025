from flask import Flask, render_template, request, jsonify, send_from_directory
import csv
import os
from collections import defaultdict

app = Flask(__name__)

# --- CONFIGURATION ---
CSV_FILENAME = 'ultimate_tt.csv'
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CSV_PATH = os.path.join(BASE_DIR, CSV_FILENAME)

# --- CONSTANTS ---
DAYS_ORDER = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
TIME_SLOTS = [
    '08:30-09:30', '09:30-10:30', '10:30-11:30', '11:30-12:30',
    '12:30-01:30', '01:30-02:30', '02:30-03:30', '03:30-04:30',
    '04:30-05:30', '05:30-06:30'
]
LAB_TIME_SLOTS = [
    '08:30-10:30', '10:30-12:30', '01:30-03:30', '03:30-05:30', '04:30-06:30'
]
LAB_PREFIX_CHECK = 'LAB BATCH'

# --- DATA LOADING ---
def load_schedule_from_csv(path):
    schedule = []
    line_num = 0
    try:
        with open(path, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            essential_keys = ['Subject', 'Division', 'Day', 'Time', 'Room']
            all_keys = ['Subject', 'Teacher', 'Division', 'Day', 'Time', 'Room']
            for row in reader:
                line_num += 1
                if not all(key in row for key in all_keys):
                    print(f"Skipping row {line_num} due to missing keys: {row}")
                    continue
                if all(row.get(key, '').strip() for key in essential_keys):
                        schedule.append({
                            'subject': row['Subject'].strip(),
                            'teacher': row.get('Teacher', '').strip(),
                            'division': row['Division'].strip(),
                            'day': row['Day'].strip().capitalize(),
                            'time': row['Time'].strip(),
                            'room': row['Room'].strip()
                        })
        print(f"Successfully loaded {len(schedule)} schedule entries.")
        return schedule
    except FileNotFoundError:
        print(f"ERROR: The file {path} was not found.")
        return None
    except Exception as e:
        print(f"An error occurred during CSV loading (around line {line_num}): {e}")
        return None

SCHEDULE_DATA = load_schedule_from_csv(CSV_PATH)

if SCHEDULE_DATA:
    ignored_rooms = ['TBD', 'SC07 Civil Department', 'Lang Lab'] 

    UNIQUE_SUBJECTS = sorted(list(set(
        e['subject'] for e in SCHEDULE_DATA 
        if e.get('subject') and not e['subject'].upper().startswith(LAB_PREFIX_CHECK)
    )))
    CLASSROOMS = sorted(list(set(
        e['room'] for e in SCHEDULE_DATA 
        if e.get('room') and \
            e.get('subject') and \
            not e['subject'].upper().startswith(LAB_PREFIX_CHECK) and \
            e['room'] not in ignored_rooms
    )))
    UNIQUE_TEACHERS = sorted(list(set(e['teacher'] for e in SCHEDULE_DATA if e.get('teacher'))))
    
    lab_subjects_set = set()
    for entry in SCHEDULE_DATA:
        subject_name = entry.get('subject', '')
        if subject_name.upper().startswith(LAB_PREFIX_CHECK):
            parts = subject_name.split('-', 1) 
            if len(parts) > 1:
                lab_subject_raw = parts[1].strip()
                lab_subject_clean = lab_subject_raw.split('(', 1)[0].strip()
                if lab_subject_clean:
                    lab_subjects_set.add(lab_subject_clean)
    UNIQUE_LAB_SUBJECTS = sorted(list(lab_subjects_set))

else:
    UNIQUE_SUBJECTS = []
    CLASSROOMS = []
    UNIQUE_TEACHERS = []
    UNIQUE_LAB_SUBJECTS = [] 
    print("Warning: SCHEDULE_DATA is empty or failed to load.")


# --- HELPER FUNCTIONS ---

# --- NEW HELPER 1: Lab Slot String Getter (used in multiple places) ---
def get_lab_slot_string(time_str):
    if not time_str or ':' not in time_str: return None
    try:
        if time_str.startswith('08:30') or time_str.startswith('09:30'): return '08:30-10:30'
        if time_str.startswith('10:30') or time_str.startswith('11:30'): return '10:30-12:30'
        if time_str.startswith('12:30'): return None 
        if time_str.startswith('01:30') or time_str.startswith('02:30'): return '01:30-03:30'
        if time_str.startswith('03:30'): return '03:30-05:30'
        if time_str.startswith('04:30') or time_str.startswith('05:30'): return '04:30-06:30'
    except Exception as e:
         print(f"[get_lab_slot_string] Error processing time '{time_str}': {e}")
         return None
    return None

# --- NEW HELPER 2: Time Slot to Decimal Converter ---
def parse_time_to_decimal(time_str):
    """Converts a time string like '08:30' or '01:30' to a decimal (8.5, 13.5)"""
    try:
        parts = time_str.split(':')
        if len(parts) >= 2:
            hour, minute = int(parts[0]), int(parts[1])
            if hour < 8: # Convert PM hours (1, 3, 4, 5, 6) to 24-hour
                hour += 12
            return hour + (minute / 60.0)
        return None
    except Exception:
        return None

# --- NEW HELPER 3: Time Slot Range to Decimals ---
def parse_slot_range_to_decimal(slot_str):
    """Converts a slot string '08:30-09:30' to decimal start/end (8.5, 9.5)"""
    try:
        start_str, end_str = slot_str.split('-')
        start_decimal = parse_time_to_decimal(start_str)
        end_decimal = parse_time_to_decimal(end_str)
        
        # Handle 12:30-01:30 (12.5 -> 13.5)
        if start_decimal and end_decimal:
             if start_decimal == 12.5 and end_decimal == 1.5:
                end_decimal = 13.5 # Fix for 01:30 PM
        
        # Handle 11:30-12:30 (11.5 -> 12.5)
        if start_decimal == 11.5 and end_decimal == 12.5:
            pass # This is correct

        # Handle 05:30-06:30 (17.5 -> 18.5)
        if end_decimal and end_decimal < start_decimal:
            end_decimal += 12

        if start_decimal and end_decimal:
            return start_decimal, end_decimal
        
        return None, None
    except Exception:
        return None, None

# --- NEW HELPER 4: Sort Key for 24-hour time ---
def sort_key_by_time(entry):
    time_str = entry.get('time', '99:99')
    parts = time_str.split('-')[0].split(':')
    try:
        if len(parts) >= 2: 
            hour, minute = int(parts[0]), int(parts[1])
            if hour < 8: # 24-hour conversion
                hour += 12
            return hour * 60 + minute
        else: return 9999
    except: return 9999

# --- NEW HELPER 5: The "Live Schedule" Logic ---
def get_live_schedule(selected_day, selected_1hr_slot):
    if not SCHEDULE_DATA or not selected_day or not selected_1hr_slot:
        return [], []

    theory_classes = []
    lab_classes = []
    
    # Get the user's 1-hour time range (e.g., 16.5 to 17.5 for '04:30-05:30')
    user_start, user_end = parse_slot_range_to_decimal(selected_1hr_slot)
    if user_start is None:
        print(f"Could not parse user slot: {selected_1hr_slot}")
        return [], []

    print(f"Finding schedule for {selected_day} @ {selected_1hr_slot} ({user_start} to {user_end})")

    # --- Find Theory Classes ---
    for entry in SCHEDULE_DATA:
        if entry.get('day') == selected_day and \
           entry.get('time') == selected_1hr_slot and \
           not entry.get('subject', '').upper().startswith(LAB_PREFIX_CHECK):
            
            theory_classes.append({
                'subject': entry.get('subject', 'N/A'),
                'division': entry.get('division', 'N/A'),
                'room': entry.get('room', 'N/A'),
                'teacher': entry.get('teacher', 'N/A').strip() or 'N/A',
                'time': entry.get('time') # Store the 1-hour slot
            })

    # --- Find Lab Classes ---
    processed_lab_sessions = set()
    lab_entries_today = []
    
    # 1. Find all raw lab entries for the day
    for entry in SCHEDULE_DATA:
         if entry.get('day') == selected_day and \
            entry.get('subject', '').upper().startswith(LAB_PREFIX_CHECK):
            lab_entries_today.append(entry)

    # 2. De-duplicate and check for overlap
    for entry in lab_entries_today:
        session_key = (entry.get('subject'), entry.get('division'), entry.get('room'), entry.get('teacher', ''))
        if session_key not in processed_lab_sessions:
            
            # Get the full 2-hour slot (e.g., '03:30-05:30')
            lab_slot_2hr = get_lab_slot_string(entry.get('time'))
            
            if lab_slot_2hr:
                # Convert 2-hour slot to decimals (e.g., 15.5 to 17.5)
                lab_start, lab_end = parse_slot_range_to_decimal(lab_slot_2hr)
                
                if lab_start is None:
                    print(f"Could not parse lab slot: {lab_slot_2hr}")
                    continue
                
                # *** THE OVERLAP CHECK ***
                # if user's slot [user_start, user_end]
                # and lab's slot [lab_start, lab_end]
                # overlap if (user_start < lab_end) and (user_end > lab_start)
                
                if (user_start < lab_end) and (user_end > lab_start):
                    lab_classes.append({
                        'subject': entry.get('subject', 'N/A'),
                        'division': entry.get('division', 'N/A'),
                        'room': entry.get('room', 'N/A'),
                        'teacher': entry.get('teacher', 'N/A').strip() or 'N/A',
                        'time': lab_slot_2hr # Store the 2-hour slot
                    })
                    processed_lab_sessions.add(session_key)

    # Sort the final lists
    theory_classes.sort(key=lambda x: (x['subject'], x['division']))
    lab_classes.sort(key=sort_key_by_time) # Sort by the start time of the lab

    return theory_classes, lab_classes


# --- (Existing Helper Functions - Unchanged) ---

def build_classroom_grid(selected_room):
    grid = {time: defaultdict(lambda: 'Free') for time in TIME_SLOTS}
    if not SCHEDULE_DATA: return {t: dict(g) for t, g in grid.items()}
    for entry in SCHEDULE_DATA:
        if all(k in entry for k in ['room', 'time', 'day', 'subject', 'division', 'teacher']):
            if entry['room'] == selected_room:
                if entry['time'] in grid and entry['day'] in DAYS_ORDER:
                    grid[entry['time']][entry['day']] = f"{entry['subject']}<br>{entry['division']}<br>{entry['teacher']}"
    return {t: dict(g) for t, g in grid.items()}

def build_day_view(selected_day):
    print(f"\n--- Building Day View for: {selected_day} ---")
    classroom_grid = {time: defaultdict(lambda: 'Free') for time in TIME_SLOTS}
    if SCHEDULE_DATA:
        for entry in SCHEDULE_DATA:
            subject_upper = entry.get('subject', '').strip().upper()
            if entry.get('day') == selected_day and \
                not subject_upper.startswith(LAB_PREFIX_CHECK) and \
                entry.get('time') in classroom_grid and \
                entry.get('room') in CLASSROOMS and \
                entry.get('day') in DAYS_ORDER:
                    classroom_grid[entry['time']][entry['room']] = f"{entry.get('subject', 'N/A')}<br>{entry.get('division', 'N/A')}<br>{entry.get('teacher', 'N/A')}"
    
    # Uses the global helper function now
    _get_lab_slot_string = get_lab_slot_string 

    labs_today = []
    lab_count_found = 0
    if SCHEDULE_DATA:
        print(f"Processing {len(SCHEDULE_DATA)} entries for labs on {selected_day}. Checking prefix '{LAB_PREFIX_CHECK}'...")
        for i, entry in enumerate(SCHEDULE_DATA):
            if entry.get('day') == selected_day:
                subject_original = entry.get('subject', None)
                if subject_original is not None:
                    subject_stripped = subject_original.strip()
                    subject_upper = subject_stripped.upper()
                    if subject_upper.startswith(LAB_PREFIX_CHECK):
                            if all(entry.get(k, '').strip() for k in ['subject', 'division', 'room', 'time']): 
                                labs_today.append(entry)
                                lab_count_found += 1
        print(f"Found {lab_count_found} raw entries matching prefix criteria for {selected_day}.")
    
    final_scheduled_labs = []
    processed_sessions = set()
    for entry in labs_today:
        session_key = (entry.get('subject'), entry.get('division'), entry.get('room'), entry.get('teacher', ''))
        if session_key not in processed_sessions:
            lab_slot_2hr = _get_lab_slot_string(entry.get('time'))
            if lab_slot_2hr:
                lab_info = {
                    'subject': entry.get('subject', 'N/A'), 'division': entry.get('division', 'N/A'),
                    'room': entry.get('room', 'N/A'), 'teacher': entry.get('teacher', 'N/A'),
                    'time': lab_slot_2hr
                }
                final_scheduled_labs.append(lab_info)
                processed_sessions.add(session_key)
    print(f"Created {len(final_scheduled_labs)} final unique lab entries with merged time.")

    final_scheduled_labs.sort(key=sort_key_by_time)
    
    final_classroom_grid = {t: dict(g) for t, g in classroom_grid.items()}
    print(f"Returning grid and {len(final_scheduled_labs)} sorted labs.")
    return final_classroom_grid, final_scheduled_labs

def build_subject_grid(selected_subject):
    grid_data = {time: defaultdict(list) for time in TIME_SLOTS}
    
    if SCHEDULE_DATA:
        for entry in SCHEDULE_DATA:
            if all(k in entry for k in ['subject', 'time', 'day', 'division', 'room']):
                if entry['subject'] == selected_subject and entry['time'] in grid_data:
                    if entry['day'] in DAYS_ORDER:
                        grid_data[entry['time']][entry['day']].append(entry)

    final_grid = {time: defaultdict(lambda: 'Free') for time in TIME_SLOTS}
    for time, days in grid_data.items():
        for day, entries in days.items():
            count = len(entries)
            
            if count == 0:
                continue 
            
            elif count == 1:
                entry = entries[0]
                teacher = entry.get('teacher', 'N/A').strip() or 'N/A'
                final_grid[time][day] = f"{entry['division']}<br>{entry['room']}<br>{teacher}"
            
            else:
                html_output = '<div class="multi-class-container">'
                for entry in entries:
                    teacher = entry.get('teacher', 'N/A').strip() or 'N/A'
                    html_output += f'<span class="multi-class-item">{entry["division"]}, {entry["room"]} ({teacher})</span>'
                html_output += '</div>'
                final_grid[time][day] = html_output

    return {t: dict(g) for t, g in final_grid.items()}

def build_teacher_grid(selected_teacher):
    grid = {time: defaultdict(lambda: 'Free') for time in TIME_SLOTS}
    if not SCHEDULE_DATA: return {t: dict(g) for t, g in grid.items()}
    for entry in SCHEDULE_DATA:
         if all(k in entry for k in ['teacher', 'time', 'day', 'subject', 'division', 'room']):
             if entry['teacher'] == selected_teacher and entry['time'] in grid:
                    if entry['day'] in DAYS_ORDER:
                        current_content = grid[entry['time']][entry['day']]
                        new_content = f"{entry['subject']}<br>{entry['division']}<br>{entry['room']}"
                        if current_content == 'Free':
                            grid[entry['time']][entry['day']] = new_content
                        else:
                            grid[entry['time']][entry['day']] += f"<hr>{new_content}"
    return {t: dict(g) for t, g in grid.items()}

def build_labs_grid(selected_lab_subject):
    grid_data = {time: defaultdict(list) for time in LAB_TIME_SLOTS}
    
    if not SCHEDULE_DATA or not selected_lab_subject:
        return {t: dict(g) for t, g in grid_data.items()}

    # Uses the global helper function now
    _get_lab_slot_string = get_lab_slot_string

    for entry in SCHEDULE_DATA:
        essential_lab_keys = ['subject', 'time', 'day', 'division', 'room']
        if all(k in entry and entry[k] for k in essential_lab_keys):
            subject_name = entry.get('subject', '').strip()
            
            if subject_name.upper().startswith(LAB_PREFIX_CHECK):
                parts = subject_name.split('-', 1)
                if len(parts) > 1:
                    current_lab_subject_raw = parts[1].strip()
                    current_lab_subject_clean = current_lab_subject_raw.split('(', 1)[0].strip()
                    
                    if current_lab_subject_clean != selected_lab_subject:
                        continue
                else:
                    continue

                lab_slot_2hr = _get_lab_slot_string(entry.get('time'))
                if lab_slot_2hr and lab_slot_2hr in grid_data:
                    if entry['day'] in DAYS_ORDER:
                        grid_data[lab_slot_2hr][entry['day']].append(entry)

    final_grid = {time: defaultdict(lambda: 'Free') for time in LAB_TIME_SLOTS}
    placed_labs = set() 

    for time, days in grid_data.items():
        for day, entries in days.items():
            count = len(entries)
            if count == 0:
                continue
            
            unique_sessions_in_slot = {}
            for entry in entries:
                session_key = (entry['subject'], entry['division'], entry['room'])
                if session_key not in placed_labs:
                    unique_sessions_in_slot[session_key] = entry
                    placed_labs.add(session_key) 
            
            final_entries = list(unique_sessions_in_slot.values())
            final_count = len(final_entries)

            if final_count == 0:
                continue

            elif final_count == 1:
                entry = final_entries[0]
                teacher = entry.get('teacher', 'N/A').strip() or 'N/A'
                final_grid[time][day] = f"{entry['subject']}<br>{entry['division']}<br>{entry['room']}<br>{teacher}"

            else:
                html_output = '<div class="multi-class-container">'
                for entry in final_entries:
                    teacher = entry.get('teacher', 'N/A').strip() or 'N/A'
                    html_output += f'<span class="multi-class-item">{entry["subject"]}, {entry["division"]}, {entry["room"]}</span>'
                html_output += '</div>'
                final_grid[time][day] = html_output

    return {t: dict(g) for t, g in final_grid.items()}


# --- FLASK ROUTES (API) ---

# --- UPDATED / ROUTE ---
@app.route('/')
def index():
    if SCHEDULE_DATA is None:
        return render_template('index.html', days=[], time_slots=[], rooms=[], subjects=[], teachers=[], lab_subjects=[])
    return render_template('index.html',
                            days=DAYS_ORDER or [],
                            time_slots=TIME_SLOTS or [], # <-- Added 1-hour slots
                            rooms=CLASSROOMS or [],
                            subjects=UNIQUE_SUBJECTS or [],
                            teachers=UNIQUE_TEACHERS or [],
                            lab_subjects=UNIQUE_LAB_SUBJECTS or []) 

# --- NEW /get_live_schedule ROUTE ---
@app.route('/get_live_schedule', methods=['GET'])
def get_live_schedule_route():
    selected_day = request.args.get('day')
    selected_slot = request.args.get('slot')
    
    if not selected_day or selected_day not in DAYS_ORDER:
        return jsonify({'error': 'Please select a valid day.'}), 400
    if not selected_slot or selected_slot not in TIME_SLOTS:
        return jsonify({'error': 'Please select a valid time slot.'}), 400
        
    theory, labs = get_live_schedule(selected_day, selected_slot)
    
    return jsonify({
        'title': f"Schedule for {selected_day}, {selected_slot}",
        'theory_classes': theory,
        'lab_classes': labs
    })


# --- (Existing API Routes - Unchanged) ---

@app.route('/get_by_classroom', methods=['GET'])
def get_by_classroom():
    selected_room = request.args.get('value')
    if not selected_room or selected_room not in (CLASSROOMS or []):
        return jsonify({'error': 'Please select a valid classroom.'}), 400
    grid = build_classroom_grid(selected_room)
    return jsonify({'columns': DAYS_ORDER or [], 'rows': TIME_SLOTS or [], 'grid': grid or {}, 'title': f"Schedule for Classroom: {selected_room}"})

@app.route('/get_by_day', methods=['GET'])
def get_by_day():
    selected_day = request.args.get('value')
    if not selected_day or selected_day not in (DAYS_ORDER or []):
        return jsonify({'error': 'Please select a valid day.'}), 400
    classroom_grid, scheduled_labs = build_day_view(selected_day)
    return jsonify({'grid_type': 'hybrid_day_view',
                    'columns': CLASSROOMS or [], 
                    'rows': TIME_SLOTS or [],
                    'classroom_grid': classroom_grid or {},
                    'scheduled_labs': scheduled_labs if isinstance(scheduled_labs, list) else [],
                    'title': f"Schedule for {selected_day}"})

@app.route('/get_by_subject', methods=['GET'])
def get_by_subject():
    selected_subject = request.args.get('value')
    if not selected_subject or selected_subject not in (UNIQUE_SUBJECTS or []):
        return jsonify({'error': 'Please select a valid subject.'}), 400
    grid = build_subject_grid(selected_subject)
    return jsonify({'columns': DAYS_ORDER or [], 'rows': TIME_SLOTS or [], 'grid': grid or {}, 'title': f"Schedule for Subject: {selected_subject}"})

@app.route('/get_by_teacher', methods=['GET'])
def get_by_teacher():
    selected_teacher = request.args.get('value')
    if not selected_teacher or selected_teacher not in (UNIQUE_TEACHERS or []):
        return jsonify({'error': 'Please select a valid teacher.'}), 400
    grid = build_teacher_grid(selected_teacher)
    return jsonify({'columns': DAYS_ORDER or [], 'rows': TIME_SLOTS or [], 'grid': grid or {}, 'title': f"Schedule for {selected_teacher}"})

@app.route('/get_by_labs', methods=['GET'])
def get_by_labs():
    selected_lab_subject = request.args.get('value')
    if not selected_lab_subject or selected_lab_subject not in (UNIQUE_LAB_SUBJECTS or []):
        return jsonify({'error': 'Please select a valid lab subject.'}), 400
        
    grid = build_labs_grid(selected_lab_subject)
    return jsonify({
        'grid_type': 'labs_view', 
        'columns': DAYS_ORDER or [], 
        'rows': LAB_TIME_SLOTS or [], 
        'grid': grid or {}, 
        'title': f"Lab Schedule for {selected_lab_subject}"
    })


# --- MAIN EXECUTION ---
if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        print(f"Failed to start Flask server: {e}")