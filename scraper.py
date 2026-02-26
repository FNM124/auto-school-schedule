import requests
from bs4 import BeautifulSoup
import pdfplumber
import io
from urllib.parse import urljoin

# CONFIGURATION
SCHOOL_PAGE_URL = "https://sites.google.com/view/program-4lyk-ilioup/"
PROF_COLUMN_INDEX = 2  # Change this (0 is first column, 1 is second, etc.)

def run_ai():
    # 1. Find PDF
    response = requests.get(SCHOOL_PAGE_URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    pdf_url = ""
    for link in soup.find_all('a', href=True):
        if link['href'].lower().endswith('.pdf'):
            pdf_url = urljoin(SCHOOL_PAGE_URL, link['href'])
            break
    
    if not pdf_url:
        print("No PDF found.")
        return

    # 2. Extract Professors
    pdf_data = requests.get(pdf_url).content
    profs = set() # Use a set to avoid duplicates
    
    with pdfplumber.open(io.BytesIO(pdf_data)) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                for row in table[1:]: # Skip header row
                    if len(row) > PROF_COLUMN_INDEX:
                        name = row[PROF_COLUMN_INDEX]
                        if name: profs.add(name.strip())

    # 3. Save the List
    with open("professors.txt", "w") as f:
        f.write("AI GENERATED PROFESSOR LIST:\n")
        for p in sorted(profs):
            f.write(f"- {p}\n")
    print(f"Success! Saved {len(profs)} professors to professors.txt")

if __name__ == "__main__":
    run_ai()
