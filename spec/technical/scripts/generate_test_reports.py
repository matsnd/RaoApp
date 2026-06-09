"""Generate test PDFs and PNG screenshots for visual inspection"""
import asyncio
import os
import sys

# Ensure backend path is in Python path so we can import from it
backend_dir = os.path.join(os.path.dirname(__file__), '../../../backend')
sys.path.insert(0, backend_dir)

import fitz  # PyMuPDF
from sqlalchemy import select
from database import AsyncSessionLocal

# Import all models to register them in SQLAlchemy Base.metadata
import auth.models
import contractors.models
import categories.models
import articles.models
import settings.models
import settlements.models
import integrations.models
import reservations.models
import deliveries.models
import contract_costs.models
import audit.models
import integrations.fakturownia.models

from contracts.models import Contract
from reports.service import generate_pdf

def convert_pdf_to_pngs(pdf_data, pdf_name, output_dir):
    """Convert PDF bytes to PNG screenshots"""
    doc = fitz.open(stream=pdf_data, filetype="pdf")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    png_files = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for high quality
        png_path = os.path.join(output_dir, f"{pdf_name}_p{page_num + 1}.png")
        pix.save(png_path)
        png_files.append(png_path)
        print(f"      Page {page_num + 1} → {png_path}")
    doc.close()
    return png_files

async def main():
    print("🚀 Generating test reports from database...")
    print("=" * 60)
    
    reports_output_dir = os.path.join(os.path.dirname(__file__), '../../../spec/archive/generated_reports')
    screenshots_output_dir = os.path.join(os.path.dirname(__file__), '../../../spec/archive/generated_screenshots')
    
    os.makedirs(reports_output_dir, exist_ok=True)
    os.makedirs(screenshots_output_dir, exist_ok=True)
    
    async with AsyncSessionLocal() as db:
        # Find first machine contract (type 'S')
        s_res = await db.execute(select(Contract).where(Contract.contract_type == 'S').limit(1))
        s_contract = s_res.scalar_one_or_none()
        
        # Find first service contract (type 'U')
        u_res = await db.execute(select(Contract).where(Contract.contract_type == 'U').limit(1))
        u_contract = u_res.scalar_one_or_none()
        
        if not s_contract:
            # Fallback to any contract
            res = await db.execute(select(Contract).limit(1))
            s_contract = res.scalar_one_or_none()
            print("⚠️ No dedicated 'S' contract found, using fallback.")
            
        if not u_contract:
            print("⚠️ No dedicated 'U' contract found. We will use the fallback for testing.")
            u_contract = s_contract
            
        if not s_contract:
            print("❌ No contracts found in the database. Please create a contract first!")
            return
            
        print(f"✅ Found Machine Contract (ID: {s_contract.id}, Number: {s_contract.number}, Type: {s_contract.contract_type})")
        print(f"✅ Found Service Contract (ID: {u_contract.id}, Number: {u_contract.number}, Type: {u_contract.contract_type})")
        print("=" * 60)
        
        # Generate configurations
        generations = [
            # (contract_id, report_type, name)
            (s_contract.id, "contract", "contract_s_machine"),
            (s_contract.id, "protocol_zo", "protocol_s_machine_with_data"),
            (s_contract.id, "protocol_zo_nodata", "protocol_s_machine_nodata"),
        ]
        
        if u_contract and u_contract.contract_type == 'U':
            generations.extend([
                (u_contract.id, "contract", "contract_u_service"),
                (u_contract.id, "protocol_zo", "protocol_u_service_with_data"),
                (u_contract.id, "protocol_zo_nodata", "protocol_u_service_nodata"),
            ])
        else:
            # If no service contract is in the DB, generate S contract as contract_u to test layout
            generations.extend([
                (s_contract.id, "contract_u", "contract_u_service"),
                (s_contract.id, "protocol_zo_u", "protocol_u_service_with_data"),
                (s_contract.id, "protocol_zo_nodata_u", "protocol_u_service_nodata"),
            ])
            
        for cid, rtype, name in generations:
            print(f"📄 Generating {rtype} for contract ID {cid} as '{name}'...")
            try:
                pdf_bytes = await generate_pdf(db, cid, rtype)
                
                # Save PDF
                pdf_path = os.path.join(reports_output_dir, f"{name}.pdf")
                with open(pdf_path, "wb") as f:
                    f.write(pdf_bytes)
                print(f"   Saved PDF → {pdf_path}")
                
                # Convert to PNG
                convert_pdf_to_pngs(pdf_bytes, name, screenshots_output_dir)
            except Exception as e:
                import traceback
                print(f"❌ Failed to generate {rtype}: {e}")
                traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
