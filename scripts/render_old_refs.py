"""Render old reference PDFs to PNGs for visual comparison."""
import fitz, pathlib, sys

base = pathlib.Path(__file__).parent.parent / "spec" / "archive" / "reference_reports"
out = pathlib.Path(__file__).parent / "old_refs"
out.mkdir(exist_ok=True)

files = [
    ("S129_2026_own (1).pdf", "S129_2026_own"),
    ("S130_2026G_own (1).pdf", "S130_2026G_own"),
    ("PZO_S129_2026 (1).pdf", "PZO_S129_2026"),
    ("PZO_S130_2026G (1).pdf", "PZO_S130_2026G"),
]

for fname, stem in files:
    src = base / fname
    if not src.exists():
        print(f"SKIP: {fname} not found")
        continue
    doc = fitz.open(src)
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=150)
        dst = out / f"{stem}-p{i+1}.png"
        pix.save(dst)
        print(f"OK: {dst.name}")
    doc.close()

print("Done")
