"""Check if phone numbers appear in contract PDF.

Usage: python check_pdf_phone.py <contract_id>
Saves PDF to temp/ and extracts text via PyMuPDF.
"""
import sys
import requests

BASE = "http://localhost:8000/rao/api"


def login():
    r = requests.post(f"{BASE}/auth/login", json={"login": "admin", "password": "admin123"})
    r.raise_for_status()
    return r.json()["access_token"]


def gen_pdf(token, contract_id):
    r = requests.post(
        f"{BASE}/reports/contract/{contract_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    r.raise_for_status()
    return r.content


def extract_text(pdf_bytes):
    import fitz
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    return "\n".join(page.get_text() for page in doc)


def main():
    contract_id = int(sys.argv[1]) if len(sys.argv) > 1 else 15492
    token = login()
    pdf = gen_pdf(token, contract_id)

    # Save for manual inspection
    import os
    os.makedirs("../temp", exist_ok=True)
    out = f"../temp/check_contract_{contract_id}.pdf"
    with open(out, "wb") as f:
        f.write(pdf)

    text = extract_text(pdf)
    phone_patterns = ["nr tel", "nr tel:", "telefon klienta"]
    found = [p for p in phone_patterns if p in text]

    # Save full report to file
    report = []
    report.append(f"PDF saved: {out} ({len(pdf)} bytes)")
    report.append(f"\n--- Phone pattern check ---")
    report.append(f"Patterns searched: {phone_patterns}")
    report.append(f"Found: {found}")
    if found:
        report.append("[FAIL] phone-related text still in PDF")
    else:
        report.append("[OK] no phone label in PDF")

    # 'uzupełnij' section context
    if "uzupełnij" in text.lower():
        idx = text.lower().find("uzupełnij")
        report.append(f"\n--- 'uzupełnij' section context ---")
        report.append(text[idx:idx+500])
    else:
        report.append("\n'uzupełnij' NOT FOUND in text")

    # Full text dump
    report.append(f"\n--- FULL EXTRACTED TEXT ({len(text)} chars) ---")
    report.append(text)

    report_text = "\n".join(report)
    with open("../temp/check_pdf_phone_report.txt", "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"Report saved: ../temp/check_pdf_phone_report.txt")
    print(f"Phone patterns found: {found}")


if __name__ == "__main__":
    main()
