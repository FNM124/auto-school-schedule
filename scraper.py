import requests
from bs4 import BeautifulSoup
import pdfplumber
import io
import re

# --- CONFIGURATION ---
URL = "https://sites.google.com/view/program-4lyk-ilioup/"
PROF_COLUMN = 2  # Column index for names (0 = 1st column, 1 = 2nd, 2 = 3rd)

def run_scraper():
    print(f"Starting daily extraction from: {URL}")
    
    # 1. Create file immediately to prevent GitHub Action Error 128
    with open("professors.txt", "w", encoding="utf-8") as f:
        f.write("Status: Initializing search...\n")

    try:
        # 2. Fetch the website content
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(URL, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 3. Hunt for the hidden Google Drive File ID
        file_id = None
        
        # Check iframes (windows) first
        for iframe in soup.find_all('iframe'):
            src = iframe.get('src', '')
            # Regex looks for standard Google Drive 25+ character IDs
            match = re.search(r'/d/([a-zA-Z0-9_-]{25,})', src) or re.search(r'id=([a-zA-Z0-9_-]{25,})', src)
            if match:
                file_id = match.group(1)
                break
                
        # Backup: Check standard links if no iframe had it
        if not file_id:
            for link in soup.find_all('a', href=True):
                href = link['href']
                match = re.search(r'/d/([a-zA-Z0-9_-]{25,})', href) or re.search(r'id=([a-zA-Z0-9_-]{25,})', href)
                if match:
                    file_id = match.group(1)
                    break

        if not file_id:
            msg = "Status: Could not find an embedded PDF window or Drive link on the site."
            print(msg)
            with open("professors.txt", "w", encoding="utf-8") as f:
                f.write(msg)
            return

        # 4. Construct Direct Download URL
        direct_pdf_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        print(f"Found PDF Document ID: {file_id}")
        
        # 5. Download and Parse the PDF
        pdf_response = requests.get(direct_pdf_url, timeout=20)
        pdf_response.raise_for_status()
        
        profs = set()
        with pdfplumber.open(io.BytesIO(pdf_response.content)) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    for row in table[1:]: # Skip header row
                        # Ensure row is long enough and cell isn't empty
                        if len(row) > PROF_COLUMN and row[PROF_COLUMN]:
                            name = str(row[PROF_COLUMN]).strip()
                            # Ignore empty spaces or glitchy short reads
                            if name and len(name) > 2 and name.lower() != "none":
                                profs.add(name)

        # 6. Save the final list
        with open("professors.txt", "w", encoding="utf-8") as f:
            if profs:
                f.write("--- LATEST PROFESSOR LIST ---\n")
                for p in sorted(profs):
                    f.write(f"{p}\n")
                print(f"Success! Extracted {len(profs)} professors.")
            else:
                f.write("Status: PDF read successfully, but no names found. Try changing PROF_COLUMN in the code.")
                print("Table extracted but column was empty.")

    except Exception as e:
        error_msg = f"Status: Error occurred during execution - {e}"
        print(error_msg)
        with open("professors.txt", "w", encoding="utf-8") as f:
            f.write(error_msg)

if __name__ == "__main__":
    run_scraper()
