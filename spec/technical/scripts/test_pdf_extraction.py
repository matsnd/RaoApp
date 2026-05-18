"""Test PDF extraction libraries on Windows"""
import fitz  # PyMuPDF
import os

def test_pdfplumber():
    """Test pdfplumber library"""
    try:
        import pdfplumber
        print("✅ pdfplumber is available")
        import pdfplumber
        print(f"   Version: {pdfplumber.__version__}")
        return True
    except ImportError:
        print("❌ pdfplumber is NOT available")
        return False

def test_fitz():
    """Test fitz (PyMuPDF) library"""
    try:
        import fitz
        print("✅ fitz (PyMuPDF) is available")
        print(f"   Version: {fitz.__version__}")
        return True
    except ImportError:
        print("❌ fitz (PyMuPDF) is NOT available")
        return False

def test_wand():
    """Test wand library"""
    try:
        import wand
        print("✅ wand is available")
        return True
    except ImportError:
        print("❌ wand is NOT available")
        return False

def extract_images_with_fitz(pdf_path):
    """Extract images from PDF using fitz"""
    doc = fitz.open(pdf_path)
    images = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        image_list = page.get_images()

        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]

            images.append({
                "page": page_num + 1,
                "index": img_index,
                "ext": image_ext,
                "size": len(image_bytes),
                "xref": xref
            })

    doc.close()
    return images

def main():
    print("🧪 Testing PDF extraction libraries on Windows")
    print("=" * 60)

    # Test libraries
    pdfplumber_available = test_pdfplumber()
    fitz_available = test_fitz()
    wand_available = test_wand()

    print("=" * 60)

    # Test extraction with fitz on reference PDFs
    if fitz_available:
        reference_dir = os.path.join(os.path.dirname(__file__), '../../../spec/archive/reference_reports')
        if os.path.exists(reference_dir):
            print(f"\n📁 Extracting images from reference PDFs in: {reference_dir}")
            print("=" * 60)

            total_images = 0
            pdf_files = [f for f in os.listdir(reference_dir) if f.endswith('.pdf')]

            for pdf_file in pdf_files:
                pdf_path = os.path.join(reference_dir, pdf_file)
                images = extract_images_with_fitz(pdf_path)
                print(f"📄 {pdf_file}: {len(images)} images extracted")
                for img in images:
                    print(f"   Page {img['page']}, Image {img['index']}: {img['ext']} ({img['size']} bytes)")
                total_images += len(images)

            print("=" * 60)
            print(f"📊 Total images extracted: {total_images} from {len(pdf_files)} PDFs")
        else:
            print(f"⚠️ Reference directory not found: {reference_dir}")
    else:
        print("⚠️ fitz not available, skipping extraction test")

if __name__ == "__main__":
    main()