import requests
import pdfplumber
import io
import re
from datetime import datetime

# --- CONFIGURATION ---
URL = "https://sites.google.com/view/program-4lyk-ilioup/"
MY_CLASS = "ΒΑΝ1"

def run_scraper():
    # Greek Days mapping
    days_gr = ["ΔΕΥΤΕΡΑ", "ΤΡΙΤΗ", "ΤΕΤΑΡΤΗ", "ΠΕΜΠΤΗ", "ΠΑΡΑΣΚΕΥΗ", "ΣΑΒΒΑΤΟ", "ΚΥΡΙΑΚΗ"]
    today_num = datetime.now().weekday()
    today_name = days_gr[today_num]
    
    # In your image, columns for each day are roughly:
    # Δευτέρα: cols 1-7, Τρίτη: cols 8-14, κλπ.
    day_start_col = 1 + (today_num * 7)
    day_end_col = day_start_col + 7

    print(f"Searching for {MY_CLASS} on {today_name}...")

    try:
        # Get PDF ID from Site
        headers = {'User-Agent': 'Mozilla/5.0'}
        raw_text = requests.get(URL, headers=headers).text.replace('\\/', '/')
        file_id = re.search(r'drive\.google\.com/file/d/([a-zA-Z0-9_-]{25,})', raw_text).group(1)
        pdf_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        
        pdf_data = requests.get(pdf_url).content
        my_schedule = []

        with pdfplumber.open(io.BytesIO(pdf_data)) as pdf:
            table = pdf.pages[0].extract_table()
            if table:
                # Iterate through every row (every Professor)
                for row in table:
                    professor_name = row[0] # Leftmost column
                    
                    # Scan only today's columns
                    for hour_idx, cell in enumerate(row[day_start_col:day_end_col]):
                        if cell and MY_CLASS in str(cell):
                            my_schedule.append(f"Hour {hour_idx + 1}: {professor_name}")

        with open("professors.txt", "w", encoding="utf-8") as f:
            f.write(f"--- {today_name} SCHEDULE FOR {MY_CLASS} ---\n")
            if my_schedule:
                # Sort by hour
                for entry in sorted(my_schedule):
                    f.write(f"{entry}\n")
            else:
                f.write("No classes found for today. Enjoy the break!")

    except Exception as e:
        with open("professors.txt", "w", encoding="utf-8") as f:
            f.write(f"Error: {e}")

if __name__ == "__main__":
    run_scraper()
