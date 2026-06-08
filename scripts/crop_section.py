"""Crop specific section for detailed comparison."""
from PIL import Image
import pathlib

base = pathlib.Path(__file__).parent

img = Image.open(base / "verify-umowa-S-p2.png")
# Crop right column section 3
right_col = img.crop((410, 100, 810, 550))
right_col.save(base / "compare-my-S-p2-right.png")

print("OK")
