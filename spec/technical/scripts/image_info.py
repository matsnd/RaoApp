"""Get dimensions of extracted and repo assets"""
import fitz  # PyMuPDF
import os

def main():
    extracted_dir = os.path.join(os.path.dirname(__file__), '../../../spec/archive/reference_extracted_assets')
    print("🖼️ Extracted assets info:")
    for f in os.listdir(extracted_dir):
        fpath = os.path.join(extracted_dir, f)
        try:
            doc = fitz.open(fpath)
            # Since it's an image, fitz can open it and give us page 0 dimensions
            pix = doc[0].get_pixmap()
            print(f"  {f}: width={pix.width}, height={pix.height}, size={os.path.getsize(fpath)} bytes")
            doc.close()
        except Exception as e:
            print(f"  Failed to read {f}: {e}")

if __name__ == "__main__":
    main()
