import requests
from bs4 import BeautifulSoup
import PyPDF2
import io

# 1. The main school page where the PDF is listed
BASE_URL = "https://sites.google.com/view/program-4lyk-ilioup/"

def find_and_check_pdf():
    try:
        # Visit the page
        response = requests.get(BASE_URL, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for any link ending in .pdf
        pdf_link = None
        for link in soup.find_all('a', href=True):
            if link['href'].endswith('.pdf'):
                pdf_link = link['href']
                break
        
        if not pdf_link:
            print("Status: No PDF found on the page yet.")
            return

        # Handle relative links (if the link is just '/file.pdf')
        if not pdf_link.startswith('http'):
            from urllib.parse import urljoin
            pdf_link = urljoin(BASE_URL, pdf_link)

        # Download and Count Lines
        print(f"Found PDF at: {pdf_link}")
        pdf_req = requests.get(pdf_link)
        pdf_file = io.BytesIO(pdf_req.content)
        reader = PyPDF2.PdfReader(pdf_file)
        
        total_lines = 0
        for page in reader.pages:
            text = page.extract_text()
            if text:
                total_lines += len(text.split('\n'))
        
        print(f"Success! PDF has {total_lines} lines.")
        
    except Exception as e:
        print(f"AI Error: {e}")

if __name__ == "__main__":
    find_and_check_pdf()
