import requests
import pdfplumber
import io
import re
import json
from datetime import datetime

# --- CONFIGURATION ---
URL = "https://sites.google.com/view/program-4lyk-ilioup/"

# Add or modify all the classes available in your school here
ALL_CLASSES = [
    "Α1", "Α2", "Α3", "Α4", "Α5",
    "Β1", "Β2", "Β3", "Β4", "ΒΘ1", "ΒΘ2", "ΒΑΝ1", "ΒΑΝ2",
    "Γ1", "Γ2", "Γ3", "Γ4", "ΓΟΠ1", "ΓΟΠ2", "ΓΘ1", "ΓΘ2", "ΓΥΓ"
]

def clean_text(text):
    """Accurate Greek normalization to prevent mismatch errors."""
    if not text: return ""
    text = str(text).strip().upper()
    replacements = {
        'Ά': 'Α', 'Έ': 'Ε', 'Ή': 'Η', 'Ί': 'Ι', 'Ό': 'Ο', 'Ύ': 'Υ', 'Ώ': 'Ω',
        'Ϊ': 'Ι', 'Ϋ': 'Υ', 'ΐ': 'Ι', 'ΰ': 'Υ'
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    text = re.sub(r'[^\w\s]', '', text)
    return text.replace(" ", "")

def update_web_html(schedule_data, target_day):
    """Generates the interactive HTML file with embedded JSON data."""
    current_year = datetime.now().year
    
    # Convert our python dictionary to a JSON string for JavaScript
    json_data = json.dumps(schedule_data, ensure_ascii=False)
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="el">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>School Schedule</title>
        <style>
            body {{ background: #050505; color: #fff; font-family: 'Inter', sans-serif; padding: 20px; display: flex; justify-content: center; }}
            .card {{ background: #111; border: 1px solid #333; border-radius: 12px; width: 100%; max-width: 450px; padding: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }}
            
            /* Header & Main UI */
            .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 2px solid #00ff41; padding-bottom: 10px; }}
            .day-name {{ font-size: 1.4rem; font-weight: 800; text-transform: uppercase; color: #00ff41; }}
            .class-badge {{ font-size: 0.8rem; color: #fff; background: #222; padding: 6px 12px; border-radius: 8px; cursor: pointer; border: 1px solid #444; transition: 0.2s; }}
            .class-badge:hover {{ background: #333; border-color: #00ff41; }}
            
            /* Schedule Rows */
            .row {{ display: flex; align-items: center; padding: 12px; border-bottom: 1px solid #222; }}
            .row:last-child {{ border-bottom: none; }}
            .hour-circle {{ width: 35px; height: 35px; border-radius: 50%; border: 1px solid #00ff41; display: flex; justify-content: center; align-items: center; margin-right: 15px; font-weight: bold; font-family: monospace; color: #00ff41; flex-shrink: 0; }}
            .details {{ flex-grow: 1; font-size: 1rem; color: #eee; }}
            .empty {{ color: #444; font-style: italic; }}
            
            /* Footer */
            .sync-info {{ text-align: center; margin-top: 20px; font-size: 0.6rem; color: #444; letter-spacing: 1px; }}
            .copyright {{ text-align: center; margin-top: 5px; font-size: 0.6rem; color: #222; }}
            
            /* Setup Screen UI */
            #setup-screen {{ text-align: center; padding: 30px 10px; }}
            #setup-screen h2 {{ color: #00ff41; margin-top: 0; }}
            select {{ width: 100%; padding: 12px; margin: 20px 0; background: #222; color: #fff; border: 1px solid #444; border-radius: 8px; font-size: 1.1rem; outline: none; }}
            button {{ background: #00ff41; color: #000; font-weight: bold; border: none; padding: 12px 30px; border-radius: 8px; font-size: 1.1rem; cursor: pointer; width: 100%; }}
            button:hover {{ background: #00cc33; }}
        </style>
    </head>
    <body>
        
        <div class="card" id="setup-screen" style="display: none;">
            <h2>Καλωσήρθες!</h2>
            <p style="color: #bbb; font-size: 0.9rem;">Επίλεξε το τμήμα σου για να βλέπεις αυτόματα το πρόγραμμά σου.</p>
            <select id="class-select">
                <option value="" disabled selected>Επιλογή Τμήματος...</option>
            </select>
            <button onclick="saveClass()">Αποθήκευση</button>
        </div>

        <div class="card" id="main-screen" style="display: none;">
            <div class="header">
                <span class="day-name">{target_day}</span>
                <button class="class-badge" onclick="resetClass()" id="display-class">⚙️ Τμήμα</button>
            </div>
            <div id="list"></div>
            <div class="sync-info">LAST_REFRESH: {datetime.now().strftime('%H:%M:%S')}</div>
            <div class="copyright">© FNM124 {current_year} All rights reserved.</div>
        </div>

        <script>
            // The JSON data injected directly from Python
            const scheduleData = {json_data};
            
            // DOM Elements
            const setupScreen = document.getElementById('setup-screen');
            const mainScreen = document.getElementById('main-screen');
            const classSelect = document.getElementById('class-select');
            const listContainer = document.getElementById('list');
            const displayClass = document.getElementById('display-class');

            // Find classes that actually have hours assigned today to populate the dropdown cleanly
            const activeClasses = Object.keys(scheduleData).filter(c => 
                scheduleData[c].some(teacher => teacher !== "")
            );
            
            // Populate Dropdown
            activeClasses.forEach(c => {{
                const option = document.createElement('option');
                option.value = c;
                option.textContent = c;
                classSelect.appendChild(option);
            }});

            // App Initialization
            function initApp() {{
                const savedClass = localStorage.getItem('mySchoolClass');
                if (savedClass && scheduleData[savedClass]) {{
                    renderSchedule(savedClass);
                    setupScreen.style.display = 'none';
                    mainScreen.style.display = 'block';
                }} else {{
                    setupScreen.style.display = 'block';
                    mainScreen.style.display = 'none';
                }}
            }}

            // Save user choice
            function saveClass() {{
                const selected = classSelect.value;
                if (selected) {{
                    localStorage.setItem('mySchoolClass', selected);
                    initApp();
                }}
            }}

            // Reset user choice
            function resetClass() {{
                localStorage.removeItem('mySchoolClass');
                initApp();
            }}

            // Render the specific class schedule
            function renderSchedule(className) {{
                displayClass.textContent = "⚙️ " + className;
                listContainer.innerHTML = ''; // Clear previous
                
                const hours = scheduleData[className];
                
                hours.forEach((teacher, index) => {{
                    const num = index + 1;
                    const text = teacher ? teacher.trim() : "";
                    
                    const div = document.createElement('div');
                    div.className = 'row';
                    div.innerHTML = `<div class="hour-circle">${{num}}</div><div class="details ${{text ? '' : 'empty'}}">${{text || 'Κενό / No Class'}}</div>`;
                    listContainer.appendChild(div);
                }});
            }}

            // Start the app
            initApp();
        </script>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)

def run_scraper():
    days_gr = ["ΔΕΥΤΕΡΑ", "ΤΡΙΤΗ", "ΤΕΤΑΡΤΗ", "ΠΕΜΠΤΗ", "ΠΑΡΑΣΚΕΥΗ", "ΣΑΒΒΑΤΟ", "ΚΥΡΙΑΚΗ"]
    now = datetime.now()
    today_idx = now.weekday()
    target_idx = 0 if today_idx >= 4 else today_idx + 1
    target_day = days_gr[target_idx]
    
    print(f"Status: Verifying PDF for {target_day}...")

    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        raw_text = requests.get(URL, headers=headers).text.replace('\\/', '/')
        file_id = re.search(r'drive\.google\.com/file/d/([a-zA-Z0-9_-]{25,})', raw_text).group(1)
        pdf_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        pdf_data = requests.get(pdf_url).content
        
        found_column = -1

        with pdfplumber.open(io.BytesIO(pdf_data)) as pdf:
            table = pdf.pages[0].extract_table()
            
            # Verify Day Location
            target_clean = clean_text(target_day)
            for r_idx, row in enumerate(table[:5]):
                if not row: continue
                for c_idx, cell in enumerate(row):
                    if cell and target_clean in clean_text(cell):
                        found_column = c_idx
                        break
                if found_column != -1: break

            if found_column == -1:
                # Fallback empty schedule if day is missing
                update_web_html({c: [""]*7 for c in ALL_CLASSES}, target_day)
                raise ValueError(f"SYSTEM_ERROR: Could not find header '{target_day}'.")

            # Initialize a dictionary mapping every class to an array of 7 empty hours
            schedule_data = {c: [""] * 7 for c in ALL_CLASSES}

            for h in range(7):
                col_idx = found_column + h
                ongoing_classes = {} # Track merged cells vertically

                for r_idx, row in enumerate(table[2:]):
                    # Safely get teacher name (Column 0)
                    teacher = row[0].replace('\n', ' ').strip() if row[0] else ""
                    
                    # Safely get the target cell
                    raw_cell = row[col_idx] if len(row) > col_idx else "" 
                    cell_str = str(raw_cell).strip().upper() if raw_cell is not None else ""
                    
                    if raw_cell is not None and cell_str != "":
                        # Look for which classes are mentioned in this specific cell
                        found_in_cell = [c for c in ALL_CLASSES if c in cell_str]
                        ongoing_classes[r_idx] = found_in_cell
                        
                        for c in found_in_cell:
                            schedule_data[c][h] = teacher
                            
                    elif raw_cell is None:
                        # MERGED CELL (Carried over from the row above)
                        carried_classes = ongoing_classes.get(r_idx, [])
                        for c in carried_classes:
                            schedule_data[c][h] = teacher
                    else:
                        ongoing_classes[r_idx] = []

        # Generate the interactive HTML
        update_web_html(schedule_data, target_day)
        
        # Save a debug JSON to github just to track changes
        with open("professors.txt", "w", encoding="utf-8") as f:
            json.dump(schedule_data, f, ensure_ascii=False, indent=4)

    except Exception as e:
        error_msg = f"System Error: {e}"
        # Fallback in case of error
        empty_data = {c: [error_msg]*7 for c in ALL_CLASSES}
        update_web_html(empty_data, "ERROR")

if __name__ == "__main__":
    run_scraper()
