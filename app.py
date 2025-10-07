# app.py (Master Version)

from flask import Flask, render_template, request, jsonify
import csv
import os

app = Flask(__name__)

# --- CONFIGURATION ---
CSV_FILENAME = 'ultimate_tt.csv' # Updated to your new CSV file
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CSV_PATH = os.path.join(BASE_DIR, CSV_FILENAME)

# --- CONSTANTS ---
DAYS_ORDER = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
TIME_SLOTS = [
    '08:30-09:30', '09:30-10:30', '10:30-11:30', '11:30-12:30',
    '12:30-01:30', '01:30-02:30', '02:30-03:30', '03:30-04:30',
    '04:30-05:30', '05:30-06:30'
]

# --- DATA LOADING ---
def load_schedule_from_csv(path):
    """Loads the schedule data from the new CSV with the Teacher column."""
    schedule = []
    try:
        with open(path, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                schedule.append({
                    'subject': row['Subject'].strip(),
                    'teacher': row['Teacher'].strip(), # New 'Teacher' field added
                    'division': row['Division'].strip(),
                    'day': row['Day'].strip().capitalize(),
                    'time': row['Time'].strip(),
                    'room': row['Room'].strip()
                })
        return schedule
    except FileNotFoundError:
        print(f"ERROR: The file {path} was not found.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# Load all data once when the app starts
SCHEDULE_DATA = load_schedule_from_csv(CSV_PATH)

# Create lists for all three dropdown menus
if SCHEDULE_DATA:
    UNIQUE_ROOMS = sorted(set(entry['room'] for entry in SCHEDULE_DATA))
    UNIQUE_SUBJECTS = sorted(set(entry['subject'] for entry in SCHEDULE_DATA))
else:
    UNIQUE_ROOMS = []
    UNIQUE_SUBJECTS = []


# --- HELPER FUNCTIONS FOR EACH MODE ---

def build_classroom_grid(selected_room):
    """Builds the Day x Time grid for a selected classroom."""
    grid = {time: {day: 'Free' for day in DAYS_ORDER} for time in TIME_SLOTS}
    for entry in SCHEDULE_DATA:
        if entry['room'] == selected_room:
            grid[entry['time']][entry['day']] = f"{entry['subject']}<br>{entry['division']}<br>{entry['teacher']}"
    return grid

def build_day_grid(selected_day):
    """Builds the Classroom x Time grid for a selected day."""
    grid = {time: {room: 'Free' for room in UNIQUE_ROOMS} for time in TIME_SLOTS}
    for entry in SCHEDULE_DATA:
        if entry['day'] == selected_day:
            grid[entry['time']][entry['room']] = f"{entry['subject']}<br>{entry['division']}<br>{entry['teacher']}"
    return grid

def build_subject_grid(selected_subject):
    """Builds the Day x Time grid for a selected subject."""
    grid = {time: {day: 'Free' for day in DAYS_ORDER} for time in TIME_SLOTS}
    for entry in SCHEDULE_DATA:
        if entry['subject'] == selected_subject:
            # If multiple divisions have the same subject at the same time, append them
            current_content = grid[entry['time']][entry['day']]
            new_content = f"{entry['division']}<br>{entry['room']}<br>{entry['teacher']}"
            if current_content == 'Free':
                grid[entry['time']][entry['day']] = new_content
            else:
                grid[entry['time']][entry['day']] += f"<hr>{new_content}"
    return grid


# --- FLASK ROUTES (API) ---

@app.route('/')
def index():
    """Renders the main page, providing the lists for all three dropdowns."""
    if SCHEDULE_DATA is None:
        return "Error: Timetable data could not be loaded. Check file name and path.", 500
    return render_template('index.html', days=DAYS_ORDER, rooms=UNIQUE_ROOMS, subjects=UNIQUE_SUBJECTS)

@app.route('/get_by_classroom', methods=['GET'])
def get_by_classroom():
    """API endpoint for the 'Classroom View'."""
    selected_room = request.args.get('value')
    if not selected_room or selected_room not in UNIQUE_ROOMS:
        return jsonify({'error': 'Please select a valid classroom.'}), 400
    grid = build_classroom_grid(selected_room)
    return jsonify({
        'grid_type': 'classroom_view',
        'columns': DAYS_ORDER,
        'rows': TIME_SLOTS,
        'grid': grid,
        'title': f"Schedule for Classroom: {selected_room}"
    })

@app.route('/get_by_day', methods=['GET'])
def get_by_day():
    """API endpoint for the 'Day View'."""
    selected_day = request.args.get('value')
    if not selected_day or selected_day not in DAYS_ORDER:
        return jsonify({'error': 'Please select a valid day.'}), 400
    grid = build_day_grid(selected_day)
    return jsonify({
        'grid_type': 'day_view',
        'columns': UNIQUE_ROOMS,
        'rows': TIME_SLOTS,
        'grid': grid,
        'title': f"Schedule for: {selected_day}"
    })

@app.route('/get_by_subject', methods=['GET'])
def get_by_subject():
    """API endpoint for the 'Subject View'."""
    selected_subject = request.args.get('value')
    if not selected_subject or selected_subject not in UNIQUE_SUBJECTS:
        return jsonify({'error': 'Please select a valid subject.'}), 400
    grid = build_subject_grid(selected_subject)
    return jsonify({
        'grid_type': 'subject_view',
        'columns': DAYS_ORDER,
        'rows': TIME_SLOTS,
        'grid': grid,
        'title': f"Schedule for Subject: {selected_subject}"
    })

# --- MAIN EXECUTION ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)