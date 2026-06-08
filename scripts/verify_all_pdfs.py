"""Generate all PDF types for verification."""
import requests, pathlib, sys, json

base = pathlib.Path(__file__).parent
host = "http://localhost:8000"

TESTS = [
    ("/rao/api/reports/contracts/15446/pdf", "verify-umowa-S.pdf"),
    ("/rao/api/reports/contracts/15458/pdf", "verify-umowa-U.pdf"),
    ("/rao/api/reports/contracts/15446/protocol-zo/pdf", "verify-protokol_zo-S.pdf"),
    ("/rao/api/reports/contracts/15458/protocol-zo/pdf", "verify-protokol_zo-U.pdf"),
    ("/rao/api/reports/contracts/15446/protocol-zo-nodata/pdf", "verify-protokol_zo_nodata-S.pdf"),
    ("/rao/api/reports/contracts/15458/protocol-zo-nodata/pdf", "verify-protokol_zo_nodata-U.pdf"),
]

for endpoint, outname in TESTS:
    url = f"{host}{endpoint}"
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            dst = base / outname
            dst.write_bytes(r.content)
            size = len(r.content)
            pages = "?"
            try:
                import fitz
                doc = fitz.open(stream=r.content, filetype="pdf")
                pages = len(doc)
                doc.close()
            except:
                pass
            print(f"  OK: {outname} ({size} B, {pages} pages)")
        else:
            print(f"  ERR: {outname} HTTP {r.status_code}")
    except Exception as e:
        print(f"  ERR: {outname} {e}")

print("\nDone")
