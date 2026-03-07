import requests
import pdfplumber
import io
import re
from datetime import datetime

# --- CONFIGURATION ---
URL = "https://sites.google.com/view/program-4lyk-ilioup/"
MY_CLASS = "ΒΑΝ1"

def clean_text(text):
    """Removes spaces and common Greek accents for better matching."""
    if not text: return ""
    # Remove spaces, dots, and convert to upper case
    text = str(text).replace(" ", "").replace(".", "").upper()
    # Basic normalization for Greek accents
    replacements = {'Ά': 'Α', 'Έ': 'Ε', 'Ή': 'Η', 'Ί': 'Ι', 'Ό': 'Ο', 'Ύ': 'Υ', 'Ώ': 'Ω'}
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text

def run_scraper():
    # 1. Determine Target Day
    days_gr = ["ΔΕΥΤΕΡΑ", "ΤΡΙΤΗ", "ΤΕΤΑΡΤΗ", "ΠΕΜΠΤΗ", "ΠΑΡΑΣΚΕΥΗ", "ΣΑΒΒΑΤΟ", "ΚΥΡΙΑΚΗ"]
    now = datetime.now()
    today_idx = now.weekday()
    
    # Logic: Next Day, but skip to Monday if it's the weekend
    target_idx = 0 if today_idx >= 4 else today_idx + 1
    target_day = days_gr[target_idx]
    
    print(f"Bot Goal: Find {target_day} in the PDF...")

    try:
        # 2. Get the PDF
        headers = {'User-Agent': 'Mozilla/5.0'}
        raw_text = requests.get(URL, headers=headers).text.replace('\\/', '/')
        file_id = re.search(r'drive\.google\.com/file/d/([a-zA-Z0-9_-]{25,})', raw_text).group(1)
        pdf_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        pdf_data = requests.get(pdf_url).content
        
        my_schedule = []
        found_column = -1

        with pdfplumber.open(io.BytesIO(pdf_data)) as pdf:
            table = pdf.pages[0].extract_table()
            if not table:
                raise Exception("Could not find a table in the PDF.")

            # 3. VERIFY THE DAY
            # We check the top 3 rows for the target day name
            for r_idx in range(min(3, len(table))):
                for c_idx, cell in enumerate(table[r_idx]):
                    cleaned_cell = clean_text(cell)
                    if clean_text(target_day) in cleaned_cell:
                        found_column = c_idx
                        print(f"Match found! {target_day} is at column {c_idx}")
                        break
                if found_column != -1: break

            if found_column == -1:
                # If we didn't find the target, see what IS there to tell the user
                current_pdf_day = clean_text(table[0][1]) if len(table[0]) > 1 else "Unknown"
                with open("professors.txt", "w", encoding="utf-8") as f:
                    f.write(f"ALERT: I was looking for {target_day}, but the PDF header seems to show {current_pdf_day}.\n")
                    f.write("The school likely hasn't updated the file for the next day yet.")
                return

            # 4. SCRAPE THE DATA
            # Once verified, we look at the 7 columns for that day
            day_range = range(found_column, found_column + 7)
            for row in table:
                if not row or not row[0]: continue
                prof = str(row[0]).strip()
                
                for i, col_idx in enumerate(day_range):
                    if col_idx < len(row) and MY_CLASS in str(row[col_idx]):
                        my_schedule.append(f"Hour {i+1}: {prof}")

        # 5. SAVE
        with open("professors.txt", "w", encoding="utf-8") as f:
            f.write(f"--- VERIFIED SCHEDULE FOR {target_day} ({MY_CLASS}) ---\n")
            if my_schedule:
                for entry in sorted(my_schedule): f.write(f"{entry}\n")
            else:
                f.write("No classes found in the verified section.")

    except Exception as e:
        with open("professors.txt", "w", encoding="utf-8") as f:
            f.write(f"Error: {e}")

if __name__ == "__main__":
    run_scraper()
