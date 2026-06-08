# /// script
# requires-python = ">=3.8"
# dependencies = ["pymupdf"]
#
import fitz

doc = fitz.open("contract_15458.pdf")
for page_num in range(len(doc)):
    page = doc[page_num]
    pix = page.get_pixmap()
    pix.save(f"contract_15458_page{page_num + 1}.png")
print(f"Converted {len(doc)} pages to PNG")
# ///
