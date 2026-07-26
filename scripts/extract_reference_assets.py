"""Extract images from reference PDFs and save them to assets directory"""
import fitz  # PyMuPDF
import os

def extract_images_from_pdf(pdf_path, output_dir):
    doc = fitz.open(pdf_path)
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        image_list = page.get_images()
        
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            
            out_filename = f"{pdf_name}_p{page_num + 1}_img{img_index}.{image_ext}"
            out_path = os.path.join(output_dir, out_filename)
            with open(out_path, "wb") as f:
                f.write(image_bytes)
            print(f"   Saved: {out_path} ({len(image_bytes)} bytes)")
            
    doc.close()

def main():
    reference_dir = os.path.join(os.path.dirname(__file__), '../../../spec/archive/reference_reports')
    output_dir = os.path.join(os.path.dirname(__file__), '../../../spec/archive/reference_extracted_assets')
    os.makedirs(output_dir, exist_ok=True)
    
    pdf_files = [f for f in os.listdir(reference_dir) if f.endswith('.pdf')]
    for f in pdf_files:
        print(f"📄 Processing: {f}")
        extract_images_from_pdf(os.path.join(reference_dir, f), output_dir)

if __name__ == "__main__":
    main()
