"""Inspect and extract images from stamp_old_contract.pdf"""
import fitz  # PyMuPDF
import os

def main():
    pdf_path = os.path.join(os.path.dirname(__file__), '../../../stamp_old_contract.pdf')
    if not os.path.exists(pdf_path):
        print("❌ stamp_old_contract.pdf not found")
        return
        
    print(f"📄 Inspecting: {pdf_path}")
    doc = fitz.open(pdf_path)
    print(f"Pages: {len(doc)}")
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        image_list = page.get_images()
        print(f"  Page {page_num + 1} has {len(image_list)} images")
        for img_idx, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            print(f"    Img {img_idx}: size={len(image_bytes)} bytes, ext={image_ext}")
            
            # Save it
            out_path = os.path.join(os.path.dirname(__file__), f"../../../extracted_stamp_old_contract_{img_idx}.{image_ext}")
            with open(out_path, "wb") as f:
                f.write(image_bytes)
            print(f"    Saved as: {out_path}")
    doc.close()

if __name__ == "__main__":
    main()
