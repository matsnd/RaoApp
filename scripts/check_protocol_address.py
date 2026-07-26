"""Check delivery_address in protocol PDF (P1-016 verification).

Generates protocol PDF for a contract and extracts text to verify
'miejsce dostawy' is present.
"""
import sys
import os
import requests

BASE = "http://localhost:8000/rao/api"


def login():
    r = requests.post(f"{BASE}/auth/login", json={"login": "admin", "password": "admin123"})
    r.raise_for_status()
    return r.json()["access_token"]


def gen_pdf(token, contract_id, report_type="protocol_zo"):
    r = requests.post(
        f"{BASE}/reports/contract/{contract_id}?type={report_type}",
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
    report_type = sys.argv[2] if len(sys.argv) > 2 else "protocol_zo"

    token = login()
    pdf = gen_pdf(token, contract_id, report_type)

    os.makedirs("../temp", exist_ok=True)
    out = f"../temp/check_protocol_{report_type}_{contract_id}.pdf"
    with open(out, "wb") as f:
        f.write(pdf)

    text = extract_text(pdf)

    report = []
    report.append(f"Protocol PDF: {out} ({len(pdf)} bytes)")
    report.append(f"Report type: {report_type}")
    report.append(f"Contract ID: {contract_id}")
    report.append("")

    # Check for delivery address markers
    has_miejsce = "miejsce dostawy" in text.lower()
    has_delivery = "Adres dostawy" in text
    has_magdalenka = "Magdalenka" in text  # S401/2026 delivery_address

    report.append(f"Has 'miejsce dostawy': {has_miejsce}")
    report.append(f"Has 'Adres dostawy': {has_delivery}")
    report.append(f"Has 'Magdalenka' (expected for S401): {has_magdalenka}")
    report.append("")

    # Show context around 'miejsce dostawy'
    if has_miejsce:
        idx = text.lower().find("miejsce dostawy")
        report.append(f"Context around 'miejsce dostawy':")
        report.append(text[max(0, idx-50):idx+200])
    else:
        report.append("'miejsce dostawy' NOT FOUND — checking full text for address-related content")
        # Show first 1500 chars
        report.append(f"\n--- First 1500 chars ---\n{text[:1500]}")

    report_text = "\n".join(report)
    with open("../temp/check_protocol_address_report.txt", "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"Report saved: ../temp/check_protocol_address_report.txt")
    print(f"Has 'miejsce dostawy': {has_miejsce}")
    print(f"Has 'Magdalenka': {has_magdalenka}")


if __name__ == "__main__":
    main()
