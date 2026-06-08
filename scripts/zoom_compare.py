"""Zoomed crop of OWN section for pixel-perfect comparison."""
from PIL import Image
import pathlib

base = pathlib.Path(__file__).parent

old = Image.open(base / "old_refs" / "S129_2026_own-p2.png")
crop_old = old.crop((450, 80, 890, 600))
crop_old = crop_old.resize((crop_old.width * 2, crop_old.height * 2))
crop_old.save(base / "zoom-old-S-p2-r.png")

new = Image.open(base / "verify-umowa-S-p2.png")
crop_new = new.crop((410, 80, 810, 600))
crop_new = crop_new.resize((crop_new.width * 2, crop_new.height * 2))
crop_new.save(base / "zoom-new-S-p2-r.png")

print("OK")
