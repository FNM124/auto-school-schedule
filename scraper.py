import requests
import pdfplumber
import io
import re
from datetime import datetime

# --- CONFIGURATION ---
URL = "https://sites.google.com/view/program-4lyk-ilioup/"
CLASSES = ["Β3", "ΒΘ2"] # Priority list

def clean_text(text):
    """Normalizes Greek text for reliable header matching."""
    if not text: return ""
    text = str(text).replace(" ", "").replace(".", "").upper()
    replacements = {'Ά': 'Α', 'Έ': 'Ε', 'Ή': 'Η', 'Ί': 'Ι', 'Ό': 'Ο', 'Ύ': 'Υ', 'Ώ': 'Ω'}
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text

def update_web_html(schedule_text, target_day):
    """Generates the static HTML file for the website."""
    html_template = f"""
    <!DOCTYPE html>
    <html lang="el">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Schedule</title>
        <style>
            body {{ background: #0f0f0f; color: #00ff41; font-family: 'Courier New', monospace; padding: 20px; display: flex; justify-content: center; }}
            .terminal {{ background: #000; border: 2px solid #333; padding: 20px; border-radius: 8px; max-width: 500px; width: 100%; box-shadow: 0 0 20px rgba(0,255,65,0.2); }}
            pre {{ white-space: pre-wrap; font-size: 1.1rem; line-height: 1.5; margin: 0; }}
            .meta {{ color: #444; font-size: 0.7rem; margin-top: 15px; border-top: 1px solid #222; padding-top: 10px; }}
        </style>
    </head>
    <body>
        <div class="terminal">
            <pre>{schedule_text}</pre>
            <div class="meta">SYSTEM_READY | LAST_SYNC: {datetime.now().strftime('%H:%M:%S')}</div>
        </div>
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
            
            # 3. Verify Day Location
            for r_idx in range(min(3, len(table))):
                for c_idx, cell in enumerate(table[r_idx]):
                    if clean_text(target_day) in clean_text(cell):
                        found_column = c_idx
                        break
                if found_column != -1: break

            if found_column == -1:
                error_msg = f"ALERT: Could not verify {target_day} in the current PDF.\nThe school likely hasn't updated for the next day."
                # Save to text and html
                with open("professors.txt", "w", encoding="utf-8") as f:
                    f.write(error_msg)
                update_web_html(error_msg, target_day)
                return

            # 4. Priority Search Logic (With 2-hour merged cell support)
            ongoing_classes = {} # Maps row_index -> class_name to handle carry-overs

            for h in range(7):
                col_idx = found_column + h
                
                explicit_b3_teacher = None
                explicit_bth2_teacher = None
                carried_b3_teacher = None
                carried_bth2_teacher = None

                for r_idx, row in enumerate(table[2:]):
                    raw_cell = row[col_idx] if len(row) > col_idx else None
                    cell_str = str(raw_cell).strip() if raw_cell is not None else ""
                    
                    if cell_str != "" and cell_str != "None":
                        # Explicit text found in the cell
                        if CLASSES[0] in cell_str:
                            ongoing_classes[r_idx] = CLASSES[0]
                            if not explicit_b3_teacher: explicit_b3_teacher = row[0]
                        elif CLASSES[1] in cell_str:
                            ongoing_classes[r_idx] = CLASSES[1]
                            if not explicit_bth2_teacher: explicit_bth2_teacher = row[0]
                        else:
                            # They are teaching a different class; reset their status
                            ongoing_classes[r_idx] = None
                    else:
                        # Cell is empty (possible merged cell for a 2-hour block)
                        prev_class = ongoing_classes.get(r_idx)
                        if prev_class == CLASSES[0]:
                            if not carried_b3_teacher: carried_b3_teacher = row[0]
                        elif prev_class == CLASSES[1]:
                            if not carried_bth2_teacher: carried_bth2_teacher = row[0]
                            
                        # Immediately clear the carry-over so it doesn't bleed into a 3rd hour
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

        # --- 5. OUTPUT SECTION ---
        # Build the final text block
        schedule_string = f"--- VERIFIED {target_day} SCHEDULE ---\n" + "\n".join(final_schedule)
        
        # Save to backend database (professors.txt)
        with open("professors.txt", "w", encoding="utf-8") as f:
            f.write(schedule_string)
            
        # Bake into frontend website (index.html)
        update_web_html(schedule_string, target_day)

    except Exception as e:
        # Safety net: Show errors on the website too
        error_msg = f"System Error: {e}"
        with open("professors.txt", "w", encoding="utf-8") as f:
            f.write(error_msg)
        update_web_html(f"CRITICAL ERROR:\n{error_msg}", "ERROR")

if __name__ == "__main__":
    run_scraper()
