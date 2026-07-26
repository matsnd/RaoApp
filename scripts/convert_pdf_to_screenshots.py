"""Convert PDF pages to PNG screenshots for Vision AI analysis"""
import fitz  # PyMuPDF
import os

def convert_pdf_to_pngs(pdf_path, output_dir):
    """Convert each page of PDF to PNG"""
    doc = fitz.open(pdf_path)
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    png_files = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better quality

        png_path = os.path.join(output_dir, f"{pdf_name}_p{page_num + 1}.png")
        pix.save(png_path)
        png_files.append(png_path)

        print(f"✅ Page {page_num + 1} → {png_path}")

    doc.close()
    return png_files

def main():
    print("🖼️ Converting PDF pages to PNG for Vision AI analysis")
    print("=" * 60)

    reference_dir = os.path.join(os.path.dirname(__file__), '../../../spec/archive/reference_reports')
    output_dir = os.path.join(os.path.dirname(__file__), '../../../spec/archive/reference_screenshots')

    if not os.path.exists(reference_dir):
        print(f"❌ Reference directory not found: {reference_dir}")
        return

    pdf_files = [f for f in os.listdir(reference_dir) if f.endswith('.pdf')]

    if not pdf_files:
        print(f"❌ No PDF files found in: {reference_dir}")
        return

    print(f"📁 Found {len(pdf_files)} PDF files in: {reference_dir}")
    print(f"📁 Output directory: {output_dir}")
    print("=" * 60)

    total_pngs = 0

    for pdf_file in pdf_files:
        pdf_path = os.path.join(reference_dir, pdf_file)
        print(f"\n📄 Converting: {pdf_file}")
        png_files = convert_pdf_to_pngs(pdf_path, output_dir)
        total_pngs += len(png_files)

    print("=" * 60)
    print(f"📊 Total PNG files created: {total_pngs}")
    print(f"📁 Saved in: {output_dir}")

if __name__ == "__main__":
    main()