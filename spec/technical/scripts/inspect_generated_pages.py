"""Inspect text of generated PDF pages to find why there are so many pages"""
import fitz  # PyMuPDF
import os

def inspect_pdf(pdf_path):
    print(f"\n🔍 Inspecting: {pdf_path}")
    doc = fitz.open(pdf_path)
    print(f"Total pages: {len(doc)}")
    for i, page in enumerate(doc):
        text = page.get_text().strip()
        print(f"--- Page {i + 1} ({len(text)} chars) ---")
        first_line = text.split('\n')[0] if text else "(Empty)"
        last_line = text.split('\n')[-1] if text else "(Empty)"
        print(f"  First line: {first_line}")
        print(f"  Last line:  {last_line}")
    doc.close()

def main():
    generated_dir = os.path.join(os.path.dirname(__file__), '../../../spec/archive/generated_reports')
    pdf_files = [f for f in os.listdir(generated_dir) if f.endswith('.pdf')]
    for f in pdf_files:
        inspect_pdf(os.path.join(generated_dir, f))

if __name__ == "__main__":
    main()
