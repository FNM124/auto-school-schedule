import requests
import pdfplumber
import io
import re

# --- CONFIGURATION ---
URL = "https://sites.google.com/view/program-4lyk-ilioup/"
PROF_COLUMN = 2  

def run_scraper():
    print(f"Starting Deep Scanner on: {URL}")
    with open("professors.txt", "w", encoding="utf-8") as f:
        f.write("Status: Initializing Deep Scanner...\n")

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(URL, headers=headers, timeout=15)
        response.raise_for_status()
        
        # 1. Clean the raw site code so hidden URLs are readable
        raw_text = response.text.replace('\\/', '/')
        
        file_id = None
        pdf_url = None
        
        # 2. Aggressive search for ANY Google Drive file ID in the raw code
        drive_matches = re.findall(r'drive\.google\.com/file/d/([a-zA-Z0-9_-]{25,})', raw_text)
        if not drive_matches:
            # Check for alternate Drive formats hidden in the Javascript
            drive_matches = re.findall(r'docs\.google\.com/viewer\?.*?id=([a-zA-Z0-9_-]{25,})', raw_text)
            
        if drive_matches:
            file_id = drive_matches[0] # Grab the first ID it finds
            print(f"Deep Scanner found hidden Drive ID: {file_id}")
            pdf_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            
        # 3. Backup: Look for direct .pdf links in the raw code
        if not pdf_url:
            pdf_matches = re.findall(r'(https?://[^\s"\'<>]+\.pdf)', raw_text)
            if pdf_matches:
                pdf_url = pdf_matches[0]
                print(f"Deep Scanner found hidden PDF link: {pdf_url}")

        if not pdf_url:
            msg = "Status: Deep Scanner failed. The file ID is completely masked by Google Sites."
            print(msg)
            with open("professors.txt", "w", encoding="utf-8") as f:
                f.write(msg)
            return

        # 4. Download and Read
        print(f"Downloading PDF from: {pdf_url}")
        pdf_response = requests.get(pdf_url, timeout=20)
        pdf_response.raise_for_status()
        
        profs = set()
        with pdfplumber.open(io.BytesIO(pdf_response.content)) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    for row in table[1:]: 
                        if len(row) > PROF_COLUMN and row[PROF_COLUMN]:
                            name = str(row[PROF_COLUMN]).strip()
                            if name and len(name) > 2 and name.lower() != "none":
                                profs.add(name)

        # 5. Save the List
        with open("professors.txt", "w", encoding="utf-8") as f:
            if profs:
                f.write("--- LATEST PROFESSOR LIST ---\n")
                for p in sorted(profs):
                    f.write(f"{p}\n")
                print(f"Success! Extracted {len(profs)} professors.")
            else:
                f.write("Status: PDF read successfully, but no names found. Try changing PROF_COLUMN.")

    except Exception as e:
        error_msg = f"Status: Error occurred - {e}"
        print(error_msg)
        with open("professors.txt", "w", encoding="utf-8") as f:
            f.write(error_msg)

if __name__ == "__main__":
    run_scraper()
