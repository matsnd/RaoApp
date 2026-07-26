#!/usr/bin/env python3
"""
Extract structured data from legacy RAO PDFs (WinForms/Crystal Reports output).

Parses ~400 PDF contracts (N=najem, U=usługa) into structured JSON:
  - Contract metadata (number, date, type, prepayment, dates, delivery address)
  - Contractor (najemca) data (name, address, NIP)
  - Positions (article name, rental_days, replacement_value, rate conditions)
  - Service fees ("Inne usługi")
  - Notes/Uwagi

Rate condition patterns recognized:
  1. Single rate:     "700,00zł / doba"
  2. Hourly rate:     "110,00zł / godzina"
  3. Tiered 2-step:   "1 - 3 dni - 800,00 / doba" + "powyżej 3 dni - 700,00 / doba"
  4. Tiered 3-step:   "1 - 2 dni - 1100,00" + "3 - 5 dni - 900,00" + "powyżej 5 dni - 800,00"
  5. Single day:      "1 dzień - 30,00 / doba"
  6. Flat rate (U):   "do 8 godzin - 4700,00zł"
  7. Base + addtl (U):"do 8 godzin - 4700,00zł" + "każda kolejna 300,00zł"

Usage:
  python extract_legacy_pdfs.py [PDF_DIR] [OUTPUT_JSON]
  Default: PDF_DIR=C:\\Temp\\legacy_pdfs, OUTPUT=extracted_contracts.json
"""

import fitz  # PyMuPDF
import os
import re
import json
import sys
from pathlib import Path
from collections import Counter


# ─── Regex patterns ──────────────────────────────────────────────

RE_CONTRACT_NUM = re.compile(r"Umowa (?:najmu|usługi) nr:\s*(.+)", re.IGNORECASE)
RE_CONTRACT_DATE = re.compile(r"Zawarta w dniu:\s*(.+)", re.IGNORECASE)
RE_NIP = re.compile(r"NIP:\s*(\d+)")
RE_PREPAYMENT = re.compile(r"Przedpłata:\s*([\d\s]+,[\d]+)\s*zł", re.IGNORECASE)
RE_PERIOD = re.compile(r"Przewidywany okres:\s*(\d{1,2}\.\d{1,2}\.\d{4})\s*-\s*(\d{1,2}\.\d{1,2}\.\d{4})", re.IGNORECASE)
RE_DELIVERY_DATE = re.compile(r"Termin (?:przekazania|prac):\s*(\d{1,2}\.\d{1,2}\.\d{4})", re.IGNORECASE)
RE_DELIVERY_ADDR = re.compile(r"Adres dostawy:\s*(.+)", re.IGNORECASE)
RE_WORKING_DAYS = re.compile(r"Ilość dni pracy w tygodniu:\s*(\d+)", re.IGNORECASE)

# Rate condition patterns
RE_SINGLE_RATE = re.compile(r"([\d\s]+,[\d]{2})\s*z[łl]\s*/\s*(doba|godzin[ay]*)", re.IGNORECASE)
RE_TIERED_RATE = re.compile(r"(\d+)\s*-\s*(\d+)\s* dni\s*-\s*([\d\s]+,[\d]{2})\s*/\s*(doba|godzin[ay]*)", re.IGNORECASE)
RE_POWYZEJ = re.compile(r"powy[żz]ej\s*(\d+)\s* dni\s*-\s*([\d\s]+,[\d]{2})\s*/\s*(doba|godzin[ay]*)", re.IGNORECASE)
RE_SINGLE_DAY = re.compile(r"1\s*dzie[ńn]\s*-\s*([\d\s]+,[\d]{2})\s*/\s*(doba|godzin[ay]*)", re.IGNORECASE)
RE_FLAT_RATE = re.compile(r"do\s*(\d+)\s*godzin\s*-\s*([\d\s]+,[\d]{2})\s*z[łl]\s*", re.IGNORECASE)
RE_KAZDA_KOLEJNA = re.compile(r"ka[żz]da\s*kolejna\s*([\d\s]+,[\d]{2})\s*z[łl]", re.IGNORECASE)

# Service fee patterns
RE_SERVICE_FEE = re.compile(r"-\s*(.+?):\s*([\d.,\s]+z[łl](?:\s*/\s*h)?(?:\s*-\s*[\d.,\s]+z[łl](?:\s*/\s*h)?)?)", re.IGNORECASE)


def parse_amount(s: str) -> float:
    """Parse Polish amount string: '3 259,50' → 3259.50"""
    s = s.strip().replace(" ", "").replace("\xa0", "")
    s = s.replace("zł", "").replace("zl", "").strip()
    if "," in s:
        parts = s.rsplit(",", 1)
        return float(parts[0] + "." + parts[1])
    return float(s) if s else 0.0


def parse_date_pl(s: str) -> str:
    """Parse Polish date: '13.01.2026' → '2026-01-13', '2026.01.13' → '2026-01-13'"""
    s = s.strip()
    # DD.MM.YYYY
    m = re.match(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", s)
    if m:
        d, mo, y = m.groups()
        return f"{y}-{int(mo):02d}-{int(d):02d}"
    # YYYY.MM.DD
    m = re.match(r"(\d{4})\.(\d{1,2})\.(\d{1,2})", s)
    if m:
        y, mo, d = m.groups()
        return f"{y}-{int(mo):02d}-{int(d):02d}"
    return s


def extract_blocks(pdf_path: str) -> list[dict]:
    """Extract text blocks with coordinates from PDF."""
    doc = fitz.open(pdf_path)
    blocks_data = []
    for page_num, page in enumerate(doc):
        blocks = page.get_text("blocks")
        for i, b in enumerate(blocks):
            blocks_data.append({
                "page": page_num,
                "index": i,
                "x0": round(b[0], 1),
                "y0": round(b[1], 1),
                "x1": round(b[2], 1),
                "y1": round(b[3], 1),
                "text": b[4].strip(),
            })
    doc.close()
    return blocks_data


def parse_rate_conditions(text: str) -> list[dict]:
    """Parse rate condition lines into structured conditions.

    Returns list of condition dicts:
      {rate1, rate2, billing_label, period_from, period_to, is_flat_rate, pattern_type}
    """
    conditions = []
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # Check for U-type flat rate pattern: "do N godzin - X,XXzł" + optional "każda kolejna Y,YYzł"
    flat_match = RE_FLAT_RATE.search(text)
    if flat_match:
        hours = int(flat_match.group(1))
        rate1 = parse_amount(flat_match.group(2))
        kolejna_match = RE_KAZDA_KOLEJNA.search(text)
        rate2 = parse_amount(kolejna_match.group(1)) if kolejna_match else None
        conditions.append({
            "rate1": rate1,
            "rate2": rate2,
            "billing_label": f"do {hours} godzin",
            "period_from": None,
            "period_to": None,
            "is_flat_rate": True,
            "pattern_type": "flat_hourly" if kolejna_match else "flat_rate",
        })
        return conditions

    # N-type patterns
    # Check for tiered rates: "N - M dni - X,XX / doba"
    tiered_matches = RE_TIERED_RATE.findall(text)
    powyzej_matches = RE_POWYZEJ.findall(text)

    if tiered_matches:
        for pf, pt, rate, unit in tiered_matches:
            conditions.append({
                "rate1": parse_amount(rate),
                "rate2": None,
                "billing_label": unit.lower(),
                "period_from": int(pf),
                "period_to": int(pt),
                "is_flat_rate": False,
                "pattern_type": "tiered",
            })
        # Add "powyżej" tiers
        for pt_above, rate, unit in powyzej_matches:
            conditions.append({
                "rate1": parse_amount(rate),
                "rate2": None,
                "billing_label": unit.lower(),
                "period_from": int(pt_above) + 1,
                "period_to": None,
                "is_flat_rate": False,
                "pattern_type": "tiered_above",
            })
        return conditions

    # Check for single day: "1 dzień - X,XX / doba"
    single_day_match = RE_SINGLE_DAY.search(text)
    if single_day_match:
        rate, unit = single_day_match.group(1), single_day_match.group(2)
        conditions.append({
            "rate1": parse_amount(rate),
            "rate2": None,
            "billing_label": unit.lower(),
            "period_from": 1,
            "period_to": 1,
            "is_flat_rate": False,
            "pattern_type": "single_day",
        })
        # Check for powyżej after single day
        for pt_above, rate2, unit2 in RE_POWYZEJ.findall(text):
            conditions.append({
                "rate1": parse_amount(rate2),
                "rate2": None,
                "billing_label": unit2.lower(),
                "period_from": int(pt_above) + 1,
                "period_to": None,
                "is_flat_rate": False,
                "pattern_type": "tiered_above",
            })
        return conditions

    # Check for powyżej only (without tiered)
    if powyzej_matches and not conditions:
        for pt_above, rate, unit in powyzej_matches:
            conditions.append({
                "rate1": parse_amount(rate),
                "rate2": None,
                "billing_label": unit.lower(),
                "period_from": int(pt_above) + 1,
                "period_to": None,
                "is_flat_rate": False,
                "pattern_type": "above_only",
            })
        return conditions

    # Check for single rate: "X,XXzł / doba"
    single_match = RE_SINGLE_RATE.search(text)
    if single_match:
        rate, unit = single_match.group(1), single_match.group(2)
        conditions.append({
            "rate1": parse_amount(rate),
            "rate2": None,
            "billing_label": unit.lower(),
            "period_from": None,
            "period_to": None,
            "is_flat_rate": False,
            "pattern_type": "single_rate",
        })
        return conditions

    # Fallback: try to find any rate-like pattern
    generic_rate = re.search(r"([\d\s]+,[\d]{2})\s*(?:z[łl])?\s*/?\s*(doba|godzin[ay]*|h)?", text)
    if generic_rate:
        conditions.append({
            "rate1": parse_amount(generic_rate.group(1)),
            "rate2": None,
            "billing_label": (generic_rate.group(2) or "").lower(),
            "period_from": None,
            "period_to": None,
            "is_flat_rate": False,
            "pattern_type": "generic",
        })

    return conditions


def split_inne_uslugi(text: str) -> tuple[str, str]:
    """Split block text on 'Inne usługi' — returns (position_part, service_fees_part)."""
    for marker in ["Inne usługi", "Inne uslugi", "inne usługi", "inne uslugi"]:
        idx = text.find(marker)
        if idx >= 0:
            return text[:idx].strip(), text[idx:]
    return text.strip(), ""


def parse_position_block(text: str, contract_type: str = "N") -> dict | None:
    """Parse a single position block text into a position dict.

    N-type: row_num → article_name → rental_days → replacement_value → rate_conditions
    U-type: row_num → rate_conditions → article_name (no rental_days/value)
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if not lines or not re.match(r"^\d+$", lines[0]):
        return None

    row_num = int(lines[0])
    remaining = lines[1:]

    if contract_type == "U":
        # U-type: row_num → rate_text → article_name
        rate_lines = []
        article_lines = []
        for line in remaining:
            if any(kw in line.lower() for kw in ["godzin", "kolejna", "zł", "zl", "/ doba", "/ godzina", "/ h"]):
                if not article_lines:
                    rate_lines.append(line)
                else:
                    article_lines.append(line)
            else:
                article_lines.append(line)

        article_name = " ".join(article_lines).strip()
        rate_text = "\n".join(rate_lines)
        conditions = parse_rate_conditions(rate_text)

        return {
            "row_number": row_num,
            "article_name": article_name,
            "rental_days": None,
            "replacement_value": None,
            "rate_text": rate_text,
            "conditions": conditions,
        }
    else:
        # N-type: row_num → article_name → rental_days → replacement_value → rate_conditions
        article_lines = []
        rental_days = None
        replacement_value = None
        rate_lines = []
        phase = "article"

        for line in remaining:
            if re.match(r"^\d+$", line) and phase == "article" and len(line) <= 3:
                rental_days = int(line)
                phase = "value"
            elif re.match(r"^[\d\s]+,[\d]{2}$", line) and phase == "value":
                replacement_value = parse_amount(line)
                phase = "rates"
            elif re.match(r"^[\d\s]+,[\d]{2}$", line) and phase == "article":
                replacement_value = parse_amount(line)
                phase = "days_then_rates"
            elif re.match(r"^\d+$", line) and phase == "days_then_rates" and len(line) <= 3:
                rental_days = int(line)
                phase = "rates"
            elif phase == "rates" or phase == "days_then_rates":
                rate_lines.append(line)
            else:
                article_lines.append(line)

        article_name = " ".join(article_lines).strip()
        rate_text = "\n".join(rate_lines)
        conditions = parse_rate_conditions(rate_text)

        return {
            "row_number": row_num,
            "article_name": article_name,
            "rental_days": rental_days,
            "replacement_value": replacement_value,
            "rate_text": rate_text,
            "conditions": conditions,
        }


def parse_positions(blocks: list[dict], contract_type: str = "N") -> list[dict]:
    """Parse position blocks from the table area.

    Uses block boundaries (Y-coordinates) to identify positions.
    Handles 'Inne usługi' embedded in the same block as position data.
    """
    positions = []

    # Find table header block
    table_header_idx = None
    inne_uslugi_idx = None

    for i, b in enumerate(blocks):
        text_lower = b["text"].lower()
        if ("rozliczenie" in text_lower and ("przedmiot najmu" in text_lower or "usługa" in text_lower or "usluga" in text_lower)):
            table_header_idx = i
        if "inne usługi" in text_lower or "inne uslugi" in text_lower:
            inne_uslugi_idx = i
            break

    if table_header_idx is None:
        return positions

    end_idx = inne_uslugi_idx if inne_uslugi_idx is not None else len(blocks)

    # Parse each block between table header and "Inne usługi"
    for i in range(table_header_idx + 1, end_idx):
        b = blocks[i]
        text = b["text"].strip()
        if not text:
            continue

        # Split on "Inne usługi" if embedded in this block
        pos_part, _ = split_inne_uslugi(text)
        if pos_part:
            pos = parse_position_block(pos_part, contract_type)
            if pos:
                positions.append(pos)

    # Also check the "Inne usługi" block — might have position data before the marker
    if inne_uslugi_idx is not None:
        b = blocks[inne_uslugi_idx]
        pos_part, _ = split_inne_uslugi(b["text"])
        if pos_part:
            pos = parse_position_block(pos_part, contract_type)
            if pos:
                positions.append(pos)

    return positions


def parse_contractor(block_text: str) -> dict:
    """Parse contractor (najemca) block text.

    Example:
      'TECHLINES LEWANDOWSKI SPÓŁKA \nKOMANDYTOWA\nul. Trakt 31 , 87-140 Chełmża\nNIP: 8792757756\n'
    """
    lines = [l.strip() for l in block_text.split("\n") if l.strip()]
    nip_match = RE_NIP.search(block_text)
    nip = nip_match.group(1) if nip_match else None

    # Find address line (contains "ul." or street + postal code)
    address_line = None
    name_lines = []
    for line in lines:
        if line.startswith("NIP:"):
            continue
        if "ul." in line.lower() or re.search(r"\d{2}-\d{3}", line):
            address_line = line
        else:
            name_lines.append(line)

    name = " ".join(name_lines).strip()

    # Parse address
    postal_code = None
    city = None
    street = None
    if address_line:
        # Pattern: "ul. Trakt 31 , 87-140 Chełmża"
        m = re.match(r"ul\.?\s*(.+?)\s*,\s*(\d{2}-\d{3})\s+(.+)", address_line, re.IGNORECASE)
        if m:
            street = m.group(1).strip()
            postal_code = m.group(2)
            city = m.group(3).strip()
        else:
            # Try without "ul."
            m = re.match(r"(.+?)\s*,\s*(\d{2}-\d{3})\s+(.+)", address_line)
            if m:
                street = m.group(1).strip()
                postal_code = m.group(2)
                city = m.group(3).strip()

    return {
        "name": name,
        "nip": nip,
        "street": street,
        "postal_code": postal_code,
        "city": city,
        "raw": block_text.strip(),
    }


def parse_service_fees(block_text: str) -> list[dict]:
    """Parse 'Inne usługi' service fees block.

    Example:
      '- Transport: 500.00 zł dostawa / 500.00 zł odbiór
       - Czyszczenie maszyny po wynajmie (zabrudzenia drobne): 150.00 zł - 400.00 zł
       - Usługa tankowania: 200.00 zł (plus koszt paliwa)'
    """
    fees = []
    lines = [l.strip() for l in block_text.split("\n") if l.strip()]

    for line in lines:
        if not line.startswith("-"):
            continue
        # Remove leading "-"
        content = line[1:].strip()

        # Split name and amount
        m = re.match(r"(.+?):\s*(.+)", content)
        if m:
            name = m.group(1).strip()
            amount_text = m.group(2).strip()
            fees.append({
                "name": name,
                "amount_text": amount_text,
            })
        else:
            # No colon — whole line is the fee description
            fees.append({
                "name": content,
                "amount_text": None,
            })

    return fees


def extract_contract(pdf_path: str, filename: str) -> dict:
    """Extract all data from a single legacy PDF contract."""
    blocks = extract_blocks(pdf_path)
    full_text = "\n".join(b["text"] for b in blocks)

    # Determine contract type from filename
    if "_U" in filename:
        contract_type = "U"
        doc_type = "usługa"
    elif "_N" in filename:
        contract_type = "N"
        doc_type = "najem"
    else:
        contract_type = "?"
        doc_type = "unknown"

    # Contract number
    num_match = RE_CONTRACT_NUM.search(full_text)
    contract_number = num_match.group(1).strip() if num_match else None

    # Contract date
    date_match = RE_CONTRACT_DATE.search(full_text)
    contract_date = parse_date_pl(date_match.group(1)) if date_match else None

    # Find contractor (najemca) block — the one with NIP that's NOT TOOLSMART
    contractor = None
    for b in blocks:
        if "NIP:" in b["text"] and "9512598092" not in b["text"]:
            contractor = parse_contractor(b["text"])
            break

    # Prepayment
    prepay_match = RE_PREPAYMENT.search(full_text)
    prepayment = parse_amount(prepay_match.group(1)) if prepay_match else None

    # Date range (N-type)
    period_match = RE_PERIOD.search(full_text)
    date_from = parse_date_pl(period_match.group(1)) if period_match else None
    date_to = parse_date_pl(period_match.group(2)) if period_match else None

    # Delivery date / work date
    delivery_date_match = RE_DELIVERY_DATE.search(full_text)
    delivery_date = parse_date_pl(delivery_date_match.group(1)) if delivery_date_match else None

    # If no period (U-type), use delivery date as date_from
    if not date_from and delivery_date:
        date_from = delivery_date

    # Delivery address
    addr_match = RE_DELIVERY_ADDR.search(full_text)
    delivery_address = addr_match.group(1).strip() if addr_match else None

    # Working days per week
    wd_match = RE_WORKING_DAYS.search(full_text)
    working_days = int(wd_match.group(1)) if wd_match else 6

    # Positions
    positions = parse_positions(blocks, contract_type)

    # Service fees
    service_fees = []
    for b in blocks:
        if "inne usługi" in b["text"].lower() or "inne uslugi" in b["text"].lower():
            # This block might contain just the header, the next block has the fees
            break

    # Find the block after "Inne usługi" that starts with "-"
    for i, b in enumerate(blocks):
        if "inne usługi" in b["text"].lower() or "inne uslugi" in b["text"].lower():
            # Check if the fees are in the same block or the next one
            if b["text"].count("-") > 1:
                service_fees = parse_service_fees(b["text"])
            elif i + 1 < len(blocks):
                service_fees = parse_service_fees(blocks[i + 1]["text"])
            break

    # Determine rate pattern type for categorization
    pattern_types = set()
    for pos in positions:
        for cond in pos["conditions"]:
            pattern_types.add(cond["pattern_type"])

    return {
        "filename": filename,
        "contract_number": contract_number,
        "contract_type": contract_type,
        "doc_type": doc_type,
        "contract_date": contract_date,
        "date_from": date_from,
        "date_to": date_to,
        "delivery_date": delivery_date,
        "delivery_address": delivery_address,
        "prepayment": prepayment,
        "working_days_per_week": working_days,
        "contractor": contractor,
        "positions": positions,
        "service_fees": service_fees,
        "pattern_types": sorted(pattern_types),
        "positions_count": len(positions),
        "conditions_count": sum(len(p["conditions"]) for p in positions),
        "text_length": len(full_text),
    }


def main():
    pdf_dir = sys.argv[1] if len(sys.argv) > 1 else r"C:\Temp\legacy_pdfs"
    output_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(pdf_dir, "extracted_contracts.json")

    pdf_files = sorted([f for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf")])
    print(f"Found {len(pdf_files)} PDF files in {pdf_dir}")

    results = []
    errors = []

    for i, fname in enumerate(pdf_files, 1):
        path = os.path.join(pdf_dir, fname)
        try:
            contract = extract_contract(path, fname)
            results.append(contract)
        except Exception as e:
            errors.append({"file": fname, "error": str(e)})
            print(f"  ERROR {fname}: {e}")

        if i % 50 == 0:
            print(f"  Processed {i}/{len(pdf_files)}")

    # Save full results
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # Summary statistics
    print(f"\n{'='*60}")
    print(f"EXTRACTION COMPLETE: {len(results)} contracts, {len(errors)} errors")
    print(f"Output: {output_path}")

    # Pattern type distribution
    pattern_counter = Counter()
    for r in results:
        for pt in r["pattern_types"]:
            pattern_counter[pt] += 1

    print(f"\nPattern type distribution:")
    for pt, count in pattern_counter.most_common():
        print(f"  {pt}: {count}")

    # Contract type distribution
    type_counter = Counter(r["contract_type"] for r in results)
    print(f"\nContract type distribution:")
    for t, count in type_counter.most_common():
        print(f"  {t}: {count}")

    # Positions count distribution
    pos_counter = Counter(r["positions_count"] for r in results)
    print(f"\nPositions per contract:")
    for n, count in sorted(pos_counter.items()):
        print(f"  {n} positions: {count} contracts")

    # Conditions count distribution
    cond_counter = Counter(r["conditions_count"] for r in results)
    print(f"\nConditions per contract:")
    for n, count in sorted(cond_counter.items()):
        print(f"  {n} conditions: {count} contracts")

    # Unique contractors
    contractors = set()
    for r in results:
        if r["contractor"] and r["contractor"]["nip"]:
            contractors.add(r["contractor"]["nip"])
    print(f"\nUnique contractors (by NIP): {len(contractors)}")

    # Unique articles
    articles = set()
    for r in results:
        for p in r["positions"]:
            if p["article_name"]:
                articles.add(p["article_name"].lower().strip())
    print(f"Unique article names: {len(articles)}")

    if errors:
        print(f"\nErrors ({len(errors)}):")
        for e in errors[:10]:
            print(f"  {e['file']}: {e['error']}")


if __name__ == "__main__":
    main()
