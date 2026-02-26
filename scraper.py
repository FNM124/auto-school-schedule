import requests
import pdfplumber
import io

# ==========================================
# CONFIGURATION: PASTE YOUR DIRECT PDF LINK HERE
# ==========================================
SCHOOL_PDF_URL = "https://example.com/path/to/your/schedule.pdf"
PROF_COLUMN_INDEX = 2  # 0 is 1st column, 1 is 2nd, etc.
# ==========================================

def run_ai():
    print(f"Directly accessing PDF at: {SCHOOL_PDF_URL}")
    profs = set() 
    
    try:
        # Download the PDF directly
        response = requests.get(SCHOOL_PDF_URL, timeout=20)
        response.raise_for_status()
        
        with pdfplumber.open(io.BytesIO(response.content)) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    # Skip the first row (headers)
                    for row in table[1:]: 
                        if len(row) > PROF_COLUMN_INDEX:
                            name = row[PROF_COLUMN_INDEX]
                            if name and len(str(name).strip()) > 2:
                                profs.add(str(name).strip())
        
        # Save the findings to the text file
        with open("professors.txt", "w") as f:
            if profs:
                f.write("--- LATEST PROFESSOR LIST ---\n")
                for p in sorted(list(profs)):
                    f.write(f"{p}\n")
                print(f"Success! Found {len(profs)} professors.")
            else:
                f.write("AI connected to PDF but found no names in that column.")
                print("Connected to PDF, but table was empty or wrong column.")

    except Exception as e:
        print(f"Error: {e}")
        # Create the file even on error so GitHub Actions doesn't crash
        with open("professors.txt", "w") as f:
            f.write(f"AI Error: {e}")

if __name__ == "__main__":
    run_ai()
    
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
