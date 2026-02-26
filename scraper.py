import requests
from bs4 import BeautifulSoup
import pdfplumber
import io
from urllib.parse import urljoin

# Your school's Google Site
URL = "https://sites.google.com/view/program-4lyk-ilioup/"

def run_ai():
    print(f"Starting AI search on: {URL}")
    
    # Create the file immediately to prevent Error 128
    with open("professors.txt", "w") as f:
        f.write("Starting search...")

    try:
        # 1. Look for the PDF link on the page
        response = requests.get(URL, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        pdf_url = ""
        for link in soup.find_all('a', href=True):
            href = link['href']
            # Look for common PDF or Google Drive file patterns
            if '.pdf' in href.lower() or 'drive.google.com/file' in href.lower():
                pdf_url = urljoin(URL, href)
                break
        
        if not pdf_url:
            print("No PDF found. Make sure the PDF is linked on the site!")
            with open("professors.txt", "w") as f:
                f.write("AI reached the site but couldn't find a PDF link.")
            return

        # 2. Download and read the PDF
        print(f"PDF Found! Reading: {pdf_url}")
        pdf_response = requests.get(pdf_url)
        profs = set()
        
        with pdfplumber.open(io.BytesIO(pdf_response.content)) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    for row in table[1:]: # Skip header
                        # Assuming professor name is in the 3rd column (index 2)
                        if len(row) > 2 and row[2]:
                            profs.add(str(row[2]).strip())

        # 3. Save the final list
        with open("professors.txt", "w") as f:
            f.write("--- LATEST PROFESSOR LIST ---\n")
            for p in sorted(list(profs)):
                f.write(f"{p}\n")
        print(f"Success! Found {len(profs)} professors.")

    except Exception as e:
        print(f"Error: {e}")
        with open("professors.txt", "w") as f:
            f.write(f"AI Error: {e}")

if __name__ == "__main__":
    run_ai()
