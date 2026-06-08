"""Side-by-side comparison: old vs new PDFs."""
from PIL import Image
import pathlib

base = pathlib.Path(__file__).parent
old_dir = base / "old_refs"

PAIRS = [
    ("S129_2026_own", "verify-umowa-S", 3),
    ("S130_2026G_own", "verify-umowa-U", 2),
    ("PZO_S129_2026", "verify-protokol_zo-S", 1),
    ("PZO_S130_2026G", "verify-protokol_zo-U", 1),
]

for old_stem, new_stem, n in PAIRS:
    for i in range(1, n + 1):
        old = old_dir / f"{old_stem}-p{i}.png"
        new = base / f"{new_stem}-p{i}.png"
        if not old.exists() or not new.exists():
            print(f"SKIP: {old.name} or {new.name}")
            continue
        a = Image.open(old)
        b = Image.open(new)
        h = min(a.height, b.height, 1400)
        a_scaled = a.resize((int(a.width * h / a.height), h))
        b_scaled = b.resize((int(b.width * h / b.height), h))
        gap = 30
        merged = Image.new("RGB", (a_scaled.width + b_scaled.width + gap, h + 40), (240, 240, 240))
        merged.paste(a_scaled, (0, 40))
        merged.paste(b_scaled, (a_scaled.width + gap, 40))
        out = base / f"compare-{new_stem}-p{i}.png"
        merged.save(out)
        print(f"OK: {out.name}")

print("Done")
