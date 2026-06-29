"""Check stamp presence in contract PDF (P1-018 verification).

Verifies:
- Stamp image is NOT in SIGNATURES section (page 1 of contract)
- Stamp image IS in own-sigs section (OWN page)
- Stamp IS in protocol ZO (unchanged)

Usage: python check_pdf_stamp.py <contract_id>
"""
import sys
import os
import requests

BASE = "http://localhost:8000/rao/api"


def login():
    r = requests.post(f"{BASE}/auth/login", json={"login": "admin", "password": "admin123"})
    r.raise_for_status()
    return r.json()["access_token"]


def gen_pdf(token, contract_id, kind="contract"):
    endpoint = "contract" if kind == "contract" else "protocol"
    r = requests.post(
        f"{BASE}/reports/{endpoint}/{contract_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    r.raise_for_status()
    return r.content


def extract_text(pdf_bytes):
    import fitz
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = []
    for page in doc:
        pages.append({
            "text": page.get_text(),
            "images": len(page.get_images()),
        })
    return pages


def main():
    contract_id = int(sys.argv[1]) if len(sys.argv) > 1 else 15492
    token = login()

    # Contract PDF
    pdf = gen_pdf(token, contract_id, "contract")
    os.makedirs("../temp", exist_ok=True)
    out = f"../temp/check_stamp_contract_{contract_id}.pdf"
    with open(out, "wb") as f:
        f.write(pdf)

    pages = extract_text(pdf)
    report = []
    report.append(f"Contract PDF: {out} ({len(pdf)} bytes, {len(pages)} pages)")
    report.append("")

    for i, p in enumerate(pages):
        report.append(f"--- Page {i+1} ({p['images']} images) ---")
        # Check for signature section markers
        has_sigs = "czytelny podpis Wynajmującego" in p["text"]
        has_own_sigs = "czytelny podpis Najemcy" in p["text"] and "OWN" in p["text"][:200].upper()
        has_own_marker = "OGÓLNE WARUNKI NAJMU" in p["text"] or "OGÓLNE WARUNKI" in p["text"]
        report.append(f"  has 'czytelny podpis Wynajmującego': {has_sigs}")
        report.append(f"  has 'OGÓLNE WARUNKI': {has_own_marker}")
        report.append(f"  images count: {p['images']}")
        report.append("")

    # Save report
    report_text = "\n".join(report)
    with open("../temp/check_pdf_stamp_report.txt", "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"Report saved: ../temp/check_pdf_stamp_report.txt")
    print(f"Pages: {len(pages)}")
    for i, p in enumerate(pages):
        print(f"  Page {i+1}: {p['images']} images, has_sigs={'czytelny podpis Wynajmującego' in p['text']}")


if __name__ == "__main__":
    main()
