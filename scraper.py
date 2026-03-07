import requests
import pdfplumber
import io
import re
from datetime import datetime, timedelta

# --- CONFIGURATION ---
URL = "https://sites.google.com/view/program-4lyk-ilioup/"
MY_CLASS = "ΒΑΝ1"

def run_scraper():
    days_gr = ["ΔΕΥΤΕΡΑ", "ΤΡΙΤΗ", "ΤΕΤΑΡΤΗ", "ΠΕΜΠΤΗ", "ΠΑΡΑΣΚΕΥΗ", "ΣΑΒΒΑΤΟ", "ΚΥΡΙΑΚΗ"]
    
    # 1. Determine "Next School Day"
    now = datetime.now()
    today_idx = now.weekday()
    
    # If Friday (4), Sat (5), or Sun (6) -> Target is Monday (0)
    if today_idx >= 4:
        target_idx = 0
        note = " (Monday/Next Week)"
    else:
        target_idx = today_idx + 1
        note = f" ({days_gr[target_idx]})"

    target_day_name = days_gr[target_idx]
    today_name = days_gr[today_idx]

    try:
        # 2. Get the PDF
        headers = {'User-Agent': 'Mozilla/5.0'}
        raw_text = requests.get(URL, headers=headers).text.replace('\\/', '/')
        match = re.search(r'drive\.google\.com/file/d/([a-zA-Z0-9_-]{25,})', raw_text)
        if not match:
            with open("professors.txt", "w", encoding="utf-8") as f:
                f.write("Status: Could not find the PDF link on the site.")
            return
            
        pdf_url = f"https://drive.google.com/uc?export=download&id={match.group(1)}"
        pdf_data = requests.get(pdf_url).content
        
        my_schedule = []
        found_target_day = False

        with pdfplumber.open(io.BytesIO(pdf_data)) as pdf:
            table = pdf.pages[0].extract_table()
            if table:
                # 3. Find exactly where the target day is in the PDF
                # We search the first 2 rows for the day name
                day_start_col = -1
                for r_idx in range(min(2, len(table))):
                    for c_idx, cell in enumerate(table[r_idx]):
                        if cell and target_day_name in str(cell).upper():
                            day_start_col = c_idx
                            found_target_day = True
                            break
                    if found_target_day: break

                # 4. Fallback Logic: If next day isn't found, check if only "today" is available
                final_target_name = target_day_name
                if not found_target_day:
                    print(f"{target_day_name} not found. Checking for {today_name}...")
                    for r_idx in range(min(2, len(table))):
                        for c_idx, cell in enumerate(table[r_idx]):
                            if cell and today_name in str(cell).upper():
                                day_start_col = c_idx
                                final_target_name = f"{today_name} (Next day not uploaded yet!)"
                                break
                
                if day_start_col == -1:
                    with open("professors.txt", "w", encoding="utf-8") as f:
                        f.write(f"Error: Could not find {target_day_name} or {today_name} in the PDF.")
                    return

                # 5. Extract data from the 7 hours of that day
                day_end_col = day_start_col + 7
                for row in table[2:]:
                    if not row or not row[0]: continue
                    professor_name = str(row[0]).strip()
                    
                    day_columns = row[day_start_col:day_end_col]
                    for hour_idx, cell in enumerate(day_columns):
                        if cell and MY_CLASS in str(cell):
                            my_schedule.append(f"Hour {hour_idx + 1}: {professor_name}")

        # 6. Final Save
        with open("professors.txt", "w", encoding="utf-8") as f:
            f.write(f"--- TARGET: {final_target_name} FOR {MY_CLASS} ---\n")
            if my_schedule:
                for entry in sorted(my_schedule):
                    f.write(f"{entry}\n")
            else:
                f.write(f"No classes found for {MY_CLASS} in the found section.")

    except Exception as e:
        with open("professors.txt", "w", encoding="utf-8") as f:
            f.write(f"Error: {e}")

if __name__ == "__main__":
    run_scraper()
