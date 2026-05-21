"""Compare stamps in the repo root with extracted assets"""
import hashlib
import os

def main():
    extracted_dir = os.path.join(os.path.dirname(__file__), '../../../spec/archive/reference_extracted_assets')
    pzo_stamp = os.path.join(extracted_dir, 'PZO_S129_2026 (1)_p1_img1.png')
    
    repo_files = [
        "stamp_from_old_app.png",
        "stamp_image_raw.bin",
        "stamp_raw.dat"
    ]
    
    print("📋 Comparing PZO stamp with repo files:")
    if os.path.exists(pzo_stamp):
        with open(pzo_stamp, "rb") as f:
            pzo_bytes = f.read()
            pzo_hash = hashlib.sha256(pzo_bytes).hexdigest()
            print(f"  PZO stamp size: {len(pzo_bytes)} bytes, hash={pzo_hash[:12]}")
            
        for rfile in repo_files:
            rpath = os.path.join(os.path.dirname(__file__), '../../..', rfile)
            if os.path.exists(rpath):
                rsize = os.path.getsize(rpath)
                with open(rpath, "rb") as f:
                    rbytes = f.read()
                    rhash = hashlib.sha256(rbytes).hexdigest()
                print(f"  {rfile}: size={rsize} bytes, hash={rhash[:12]} → MATCH: {rhash == pzo_hash}")
            else:
                print(f"  {rfile} not found")
    else:
        print("  PZO stamp not found!")

if __name__ == "__main__":
    main()
