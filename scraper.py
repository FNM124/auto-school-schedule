import requests
import pdfplumber
import io
import re
from datetime import datetime

# --- CONFIGURATION ---
URL = "https://sites.google.com/view/program-4lyk-ilioup/"
MY_CLASS = "ΒΑΝ1"

def run_scraper():
    # Greek Days mapping (Monday=0 ... Sunday=6)
    days_gr = ["ΔΕΥΤΕΡΑ", "ΤΡΙΤΗ", "ΤΕΤΑΡΤΗ", "ΠΕΜΠΤΗ", "ΠΑΡΑΣΚΕΥΗ", "ΣΑΒΒΑΤΟ", "ΚΥΡΙΑΚΗ"]
    today_num = datetime.now().weekday()
    
    # --- WEEKEND OVERRIDE ---
    is_weekend = False
    if today_num >= 5:     # If it's Saturday (5) or Sunday (6)
        today_num = 0      # Force the scanner to look at Monday (0)
        is_weekend = True
        
    today_name = days_gr[today_num]
    
    # Calculate the columns to scan based on the day
    # Monday: cols 1-7, Tuesday: cols 8-14, etc.
    day_start_col = 1 + (today_num * 7)
    day_end_col = day_start_col + 7

    # Add a little note if we are looking ahead
    display_day = f"{today_name} (Next Week)" if is_weekend else today_name
    print(f"Searching for {MY_CLASS} on {display_day}...")

    try:
        # Get PDF ID from Site
        headers = {'User-Agent': 'Mozilla/5.0'}
        raw_text = requests.get(URL, headers=headers).text.replace('\\/', '/')
        
        # Deep Scanner for Drive ID
        match = re.search(r'drive\.google\.com/file/d/([a-zA-Z0-9_-]{25,})', raw_text)
        if not match:
            with open("professors.txt", "w", encoding="utf-8") as f:
                f.write("Status: Could not find the PDF link on the site today.")
            return
            
        file_id = match.group(1)
        pdf_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        
        pdf_data = requests.get(pdf_url).content
        my_schedule = []

        # Read the Table
        with pdfplumber.open(io.BytesIO(pdf_data)) as pdf:
            table = pdf.pages[0].extract_table()
            if table:
                # Iterate through every row (every Professor)
                for row in table[2:]: # Skipping the top header rows to avoid junk text
                    # Make sure the row actually has data before checking
                    if not row or not row[0]:
                        continue
                        
                    professor_name = str(row[0]).strip() # Leftmost column
                    
                    # Scan ONLY the columns for the target day
                    # We use enumerate to keep track of the school hour (1st, 2nd, etc.)
                    day_columns = row[day_start_col:day_end_col]
                    for hour_idx, cell in enumerate(day_columns):
                        if cell and MY_CLASS in str(cell):
                            # hour_idx starts at 0, so we add 1 for the actual school hour
                            my_schedule.append(f"Hour {hour_idx + 1}: {professor_name}")

        # Save Today's (or Monday's) Personal Schedule
        with open("professors.txt", "w", encoding="utf-8") as f:
            f.write(f"--- {display_day} SCHEDULE FOR {MY_CLASS} ---\n")
            if my_schedule:
                # Sort alphabetically by the "Hour X" string so it's in chronological order
                for entry in sorted(my_schedule):
                    f.write(f"{entry}\n")
            else:
                f.write(f"No classes found for {MY_CLASS} on {display_day}.")

    except Exception as e:
        with open("professors.txt", "w", encoding="utf-8") as f:
            f.write(f"Error: {e}")

if __name__ == "__main__":
    run_scraper()
