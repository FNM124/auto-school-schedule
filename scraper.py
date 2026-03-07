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
                with open("professors.txt", "w", encoding="utf-8") as f:
                    f.write(f"ALERT: Could not verify {target_day} in the current PDF.\n")
                    f.write("The school likely hasn't updated for the next day.")
                return

            # 4. Priority Search Logic
            for h in range(7):
                hour_match = ""
                col_idx = found_column + h
                
                # Check for Priority 1 (Β3)
                for row in table[2:]:
                    cell = str(row[col_idx]) if len(row) > col_idx else ""
                    if CLASSES[0] in cell:
                        hour_match = f"Hour {h+1}: {row[0]} ({CLASSES[0]})"
                        break
                
                # If no Β3, Check for Priority 2 (ΒΘ2)
                if not hour_match:
                    for row in table[2:]:
                        cell = str(row[col_idx]) if len(row) > col_idx else ""
                        if CLASSES[1] in cell:
                            hour_match = f"Hour {h+1}: {row[0]} ({CLASSES[1]})"
                            break
                
                # If neither, leave blank
                final_schedule.append(hour_match if hour_match else f"Hour {h+1}: ")

        # 5. Output
        with open("professors.txt", "w", encoding="utf-8") as f:
            f.write(f"--- VERIFIED {target_day} SCHEDULE ---\n")
            for line in final_schedule:
                f.write(line + "\n")

    except Exception as e:
        with open("professors.txt", "w", encoding="utf-8") as f:
            f.write(f"System Error: {e}")

if __name__ == "__main__":
    run_scraper()
