"""Ekstraktuje tekst z legacy PDFów (PZO + umowy) do analizy usług dodatkowych.

RAO-P2-059: analiza starych dokumentów dla migracji plain-text → per-artikel.
"""
import fitz  # PyMuPDF
import pathlib
import json

SRC_DIR = pathlib.Path("c:/projects/repos/RaoApp/spec/technical/legacy_samples/pzo_umowy")
OUT_DIR = pathlib.Path("c:/projects/repos/RaoApp/spec/technical/legacy_samples/pzo_umowy_extracted")
OUT_DIR.mkdir(parents=True, exist_ok=True)

pdfs = sorted(SRC_DIR.glob("*.pdf"))
print(f"Znaleziono {len(pdfs)} PDFów")

summary = {}
for pdf_path in pdfs:
    doc = fitz.open(pdf_path)
    pages_text = []
    for page_num, page in enumerate(doc, 1):
        text = page.get_text("text")
        pages_text.append(f"\n=== STRONA {page_num} ===\n{text}")
    doc.close()

    full_text = "\n".join(pages_text)
    out_txt = OUT_DIR / f"{pdf_path.stem}.txt"
    out_txt.write_text(full_text, encoding="utf-8")
    summary[pdf_path.name] = {
        "pages": len(pages_text),
        "chars": len(full_text),
        "out_file": str(out_txt),
    }
    print(f"  {pdf_path.name}: {len(pages_text)} stron, {len(full_text)} znaków → {out_txt.name}")

summary_path = OUT_DIR / "_summary.json"
summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\nSummary: {summary_path}")
