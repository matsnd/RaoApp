"""Check images per page in contract PDF (P1-018 verification)."""
import sys
import fitz

doc = fitz.open(sys.argv[1] if len(sys.argv) > 1 else "../temp/check_stamp_contract_15492.pdf")
for i, page in enumerate(doc):
    infos = page.get_image_info()
    print(f"Page {i+1}: {len(infos)} images")
    for img in infos:
        w, h = img["width"], img["height"]
        bbox = img["bbox"]
        print(f"  w={w} h={h} bbox=({bbox[0]:.0f},{bbox[1]:.0f},{bbox[2]:.0f},{bbox[3]:.0f})")
