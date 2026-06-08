"""Render generated PDFs to PNGs."""
import fitz, pathlib

base = pathlib.Path(__file__).parent

for pdf in base.glob("verify-*.pdf"):
    doc = fitz.open(pdf)
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=150)
        out = base / f"{pdf.stem}-p{i+1}.png"
        pix.save(out)
        print(f"{out.name}")
    doc.close()
    print(f"{pdf.name}: {len(doc)} stron")

print("Done")
