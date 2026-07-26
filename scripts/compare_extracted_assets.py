"""Compare hashes of extracted assets with existing repo assets"""
import hashlib
import os

def sha256_hash(file_path):
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def main():
    extracted_dir = os.path.join(os.path.dirname(__file__), '../../../spec/archive/reference_extracted_assets')
    repo_assets = {
        "company_stamp.jpg": os.path.join(os.path.dirname(__file__), '../../../backend/reports/assets/company_stamp.jpg'),
        "stamp_from_old_app.png": os.path.join(os.path.dirname(__file__), '../../../stamp_from_old_app.png'),
    }
    
    repo_hashes = {}
    for name, path in repo_assets.items():
        if os.path.exists(path):
            h = sha256_hash(path)
            repo_hashes[h] = name
            print(f"📦 Repo asset: {name} → SHA256: {h[:12]}")
        else:
            print(f"⚠️ Repo asset not found: {path}")
            
    print("\n🔍 Comparing extracted assets:")
    for f in os.listdir(extracted_dir):
        fpath = os.path.join(extracted_dir, f)
        h = sha256_hash(fpath)
        match_name = repo_hashes.get(h, "NO MATCH")
        print(f"📄 {f} → SHA256: {h[:12]} → MATCH: {match_name}")

if __name__ == "__main__":
    main()
