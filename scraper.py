import requests
import pdfplumber
import io
import re
from datetime import datetime

# --- CONFIGURATION ---
URL = "https://sites.google.com/view/program-4lyk-ilioup/"
CLASSES = ["Β3", "ΒΘ2"] # Priority list

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

def update_web_html(schedule_text, target_day):
    # Get the current year for the copyright
    current_year = datetime.now().year
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="el">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>School Schedule</title>
        <style>
            body {{ background: #050505; color: #fff; font-family: 'Inter', sans-serif; padding: 20px; display: flex; justify-content: center; min-height: 100vh; flex-direction: column; align-items: center; }}
            .card {{ background: #111; border: 1px solid #333; border-radius: 12px; width: 100%; max-width: 450px; padding: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); margin-bottom: 20px; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 2px solid #00ff41; padding-bottom: 10px; }}
            .day-name {{ font-size: 1.4rem; font-weight: 800; text-transform: uppercase; color: #00ff41; }}
            
            .row {{ display: flex; align-items: center; padding: 12px; border-bottom: 1px solid #222; }}
            .row:last-child {{ border-bottom: none; }}
            .hour-circle {{ width: 35px; height: 35px; border-radius: 50%; border: 1px solid #00ff41; display: flex; justify-content: center; align-items: center; margin-right: 15px; font-weight: bold; font-family: monospace; color: #00ff41; flex-shrink: 0; }}
            .details {{ flex-grow: 1; font-size: 1rem; color: #eee; }}
            .empty {{ color: #444; font-style: italic; }}
            
            .sync-info {{ text-align: center; font-size: 0.6rem; color: #333; letter-spacing: 1px; margin-bottom: 10px; }}
            .copyright {{ text-align: center; font-size: 0.6rem; color: #222; font-family: monospace; text-transform: uppercase; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="header">
                <span class="day-name">{target_day}</span>
                <span style="font-size: 0.7rem; color: #666;">B3 / BTH2</span>
            </div>
            <div id="list"></div>
        </div>
        
        <div class="sync-info">LAST_REFRESH: {datetime.now().strftime('%H:%M:%S')}</div>
        <div class="copyright">© FNM124 {current_year} | ALL RIGHTS RESERVED</div>

        <script>
            const raw = `{schedule_text}`;
            const container = document.getElementById('list');
            raw.split('\\n').forEach(line => {{
                if (!line.includes('Hour')) return;
                const [hr, info] = line.split(':');
                const num = hr.replace('Hour', '').trim();
                const text = info ? info.trim() : "";
                
                const div = document.createElement('div');
                div.className = 'row';
                div.innerHTML = `<div class="hour-circle">${{num}}</div><div class="details ${{text ? '' : 'empty'}}">${{text || 'No Class'}}</div>`;
                container.appendChild(div);
            }});
        </script>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)

def run_scraper():
    # 1. Target Next School Day
    days_gr = ["ΔΕΥΤΕΡΑ", "ΤΡΙΤΗ", "ΤΕΤΑΡΤΗ", "ΠΕΜΠΤΗ", "ΠΑΡΑΣΚΕΥΗ", "ΣΑΒΒΑΤΟ", "ΚΥΡΙΑΚΗ"]
    now = datetime.now()
    today_idx = now.weekday()
    
    # Fri/Sat/Sun -> Monday; otherwise -> Tomorrow
    target_idx = 0 if today_idx >= 4 else today_idx + 1
    target_day = days_gr[target_idx]
    
    print(f"Status: Verifying PDF for {target_day}...")

    try:
        # 2. Extract PDF ID
        headers = {'User-Agent': 'Mozilla/5.0'}
        raw_text = requests.get(URL, headers=headers).text.replace('\\/', '/')
        file_id = re.search(r'drive\.google\.com/file/d/([a-zA-Z0-9_-]{25,})', raw_text).group(1)
        pdf_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        pdf_data = requests.get(pdf_url).content
        
        final_schedule = []
        found_column = -1

        with pdfplumber.open(io.BytesIO(pdf_data)) as pdf:
            table = pdf.pages[0].extract_table()
            
            # 3. Verify Day Location with enhanced flexibility
            target_clean = clean_text(target_day)
            for r_idx, row in enumerate(table[:5]): # Scan first 5 rows
                if not row: continue
                for c_idx, cell in enumerate(row):
                    if cell and target_clean in clean_text(cell):
                        found_column = c_idx
                        break
                if found_column != -1: break

            if found_column == -1:
                error_report = f"SYSTEM_ERROR: Could not find header '{target_day}' in PDF."
                update_web_html(error_report, target_day)
                raise ValueError(error_report)

            # 4. Search Logic
            ongoing_classes = {} 

            for h in range(7):
                col_idx = found_column + h
                
                explicit_b3_teacher = None
                explicit_bth2_teacher = None
                carried_b3_teacher = None
                carried_bth2_teacher = None

                for r_idx, row in enumerate(table[2:]):
                    raw_cell = row[col_idx] if len(row) > col_idx else "" 
                    cell_str = str(raw_cell).strip() if raw_cell is not None else ""
                    
                    if raw_cell is not None and cell_str != "":
                        # EXPLICIT TEXT found
                        if CLASSES[0] in cell_str:
                            ongoing_classes[r_idx] = CLASSES[0]
                            if not explicit_b3_teacher: explicit_b3_teacher = row[0]
                        elif CLASSES[1] in cell_str:
                            ongoing_classes[r_idx] = CLASSES[1]
                            if not explicit_bth2_teacher: explicit_bth2_teacher = row[0]
                        else:
                            ongoing_classes[r_idx] = None
                            
                    elif raw_cell is None:
                        # MERGED CELL (Double hour shadow)
                        prev_class = ongoing_classes.get(r_idx)
                        if prev_class == CLASSES[0]:
                            if not carried_b3_teacher: carried_b3_teacher = row[0]
                        elif prev_class == CLASSES[1]:
                            if not carried_bth2_teacher: carried_bth2_teacher = row[0]
                        ongoing_classes[r_idx] = None
                    else:
                        # STANDARD GAP
                        ongoing_classes[r_idx] = None

                # Priority Resolution
                final_teacher = None
                final_class = None
                
                if explicit_b3_teacher:
                    final_teacher, final_class = explicit_b3_teacher, CLASSES[0]
                elif carried_b3_teacher:
                    final_teacher, final_class = carried_b3_teacher, CLASSES[0]
                elif explicit_bth2_teacher:
                    final_teacher, final_class = explicit_bth2_teacher, CLASSES[1]
                elif carried_bth2_teacher:
                    final_teacher, final_class = carried_bth2_teacher, CLASSES[1]
                    
                if final_teacher:
                    final_schedule.append(f"Hour {h+1}: {final_teacher} ({final_class})")
                else:
                    final_schedule.append(f"Hour {h+1}: ")

        # --- 5. OUTPUT ---
        schedule_string = f"--- VERIFIED {target_day} SCHEDULE ---\n" + "\n".join(final_schedule)
        
        with open("professors.txt", "w", encoding="utf-8") as f:
            f.write(schedule_string)
            
        update_web_html(schedule_string, target_day)

    except Exception as e:
        error_msg = f"System Error: {e}"
        with open("professors.txt", "w", encoding="utf-8") as f:
            f.write(error_msg)
        update_web_html(f"CRITICAL ERROR:\n{error_msg}", "ERROR")

if __name__ == "__main__":
    run_scraper()
