import requests
from bs4 import BeautifulSoup
import pdfplumber
import io
from urllib.parse import urljoin

# ==========================================
# CONFIGURATION
# ==========================================
SCHOOL_PAGE_URL = "https://sites.google.com/view/program-4lyk-ilioup/"
PROF_COLUMN_INDEX = 2  # 0 is 1st column, 1 is 2nd, 2 is 3rd, etc.
# ==========================================

def run_ai():
    print(f"Starting AI search on: {SCHOOL_PAGE_URL}")
    
    # 1. FIND THE PDF LINK
    try:
        response = requests.get(SCHOOL_PAGE_URL, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        pdf_url = ""
        for link in soup.find_all('a', href=True):
            if link['href'].lower().endswith('.pdf'):
                pdf_url = urljoin(SCHOOL_PAGE_URL, link['href'])
                break
        
        if not pdf_url:
            print("AI Status: No PDF link found on the page.")
            return
    except Exception as e:
        print(f"Error visiting website: {e}")
        return

    # 2. EXTRACT PROFESSORS FROM TABLE
    print(f"PDF Found! Analyzing: {pdf_url}")
    profs = set() 
    
    try:
        pdf_content = requests.get(pdf_url).content
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    # We start at row 1 to skip the headers
                    for row in table[1:]: 
                        if len(row) > PROF_COLUMN_INDEX:
                            name = row[PROF_COLUMN_INDEX]
                            if name and len(name.strip()) > 2:
                                profs.add(name.strip())
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return

    # 3. SAVE THE LIST TO A FILE
    with open("professors.txt", "w") as f:
        f.write("--- LATEST PROFESSOR LIST ---\n")
        for p in sorted(list(profs)):
            f.write(f"{p}\n")
    
    print(f"Success! Found {len(profs)} professors.")

if __name__ == "__main__":
    run_ai()
