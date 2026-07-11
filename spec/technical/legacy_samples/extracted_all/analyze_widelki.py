import re
from collections import defaultdict

INPUT = r"C:\projects\repos\RaoApp_new\spec\technical\legacy_samples\extracted_all\sections_extracted_v2.txt"

# Parse blocks
def parse_blocks(text):
    blocks = []
    current = None
    for line in text.splitlines():
        if line.startswith("=== ") and line.endswith(" ==="):
            if current:
                blocks.append(current)
            current = {"file": line[4:-4].strip(), "lines": []}
        elif current is not None:
            current["lines"].append(line)
    if current:
        blocks.append(current)
    return blocks

with open(INPUT, "r", encoding="utf-8") as f:
    text = f.read()

blocks = parse_blocks(text)

def detect_type(filename):
    if "_U" in filename:
        return "U"
    if "_N" in filename:
        return "N"
    return "?"

def normalize(line):
    return (
        line.lower()
        .replace("ó", "o").replace("ż", "z").replace("ź", "z")
        .replace("ć", "c").replace("ń", "n").replace("ś", "s")
        .replace("ł", "l").replace("ę", "e").replace("ą", "a")
    )

# Regex patterns for price extraction
price_re = r"[\d\s,.]+"
patterns = {
    "do_dni_godzin": re.compile(r"do\s+(\d+)\s*(dni|godzin|godz)?\s*-\s*(" + price_re + r")\s*(?:z[lł])?\s*(?:/\s*(doba|godzina|godz))?"),
    "od_do": re.compile(r"(\d+)\s*-\s*(\d+)\s*(dni|godzin|godz)\s*-\s*(" + price_re + r")\s*(?:z[lł])?\s*(?:/\s*(doba|godzina|godz))?"),
    "powyzej": re.compile(r"powy[żz]ej\s+(\d+)\s*(dni|godzin|godz)?\s*-\s*(" + price_re + r")\s*(?:z[lł])?\s*(?:/\s*(doba|godzina|godz))?"),
    "kazda_kolejna": re.compile(r"ka[zż]da\s+kolejna\s*(" + price_re + r")\s*(?:z[lł])?"),
    "prosta_stawka": re.compile(r"(" + price_re + r")\s*z[lł]\s*/\s*(doba|godzina|godz)"),
    "dni_1": re.compile(r"1\s+dzie[nń]\s*-\s*(" + price_re + r")\s*(?:z[lł])?\s*/\s*doba"),
}

stats = defaultdict(lambda: defaultdict(int))
classified = []
examples = defaultdict(list)

def add_example(group, file, line, detail):
    if len(examples[group]) < 15:
        examples[group].append((file, line, detail))

for block in blocks:
    filename = block["file"]
    typ = detect_type(filename)
    content = "\n".join(block["lines"])
    norm = normalize(content)
    lines = content.splitlines()

    found = {k: [] for k in patterns}
    for line in lines:
        ln = normalize(line)
        for name, pat in patterns.items():
            for m in pat.finditer(ln):
                found[name].append((line, m.groups()))

    has_prosta_doba = any(unit in ("doba",) for m in found["prosta_stawka"] for unit in [m[1]]) if found["prosta_stawka"] else False
    has_prosta_godz = any(unit in ("godzina", "godz") for m in found["prosta_stawka"] for unit in [m[1]]) if found["prosta_stawka"] else False
    has_do = len(found["do_dni_godzin"]) > 0
    has_od_do = len(found["od_do"]) > 0
    has_powyzej = len(found["powyzej"]) > 0
    has_kazda = len(found["kazda_kolejna"]) > 0
    has_1dzien = len(found["dni_1"]) > 0

    # determine detailed pattern
    if typ == "N":
        if has_od_do and has_powyzej:
            pattern = "N_kaskadowa_doba (od-do + powyzej)"
        elif has_1dzien:
            pattern = "N_1dzien_doba"
        elif has_prosta_doba:
            pattern = "N_prosta_doba"
        elif has_prosta_godz:
            pattern = "N_godzinowa (anomalia)"
        else:
            pattern = "N_brak_ceny"
    elif typ == "U":
        if has_od_do and has_powyzej:
            pattern = "U_kaskadowa_godzinowa (od-do + powyzej)"
        elif has_do and has_kazda:
            pattern = "U_do_godzin_kazda_kolejna"
        elif has_prosta_godz:
            pattern = "U_prosta_godzina"
        elif has_prosta_doba:
            pattern = "U_dobowa (anomalia)"
        elif has_do:
            pattern = "U_do_dni (anomalia)"
        else:
            pattern = "U_brak_ceny"
    else:
        pattern = "?"

    classified.append({
        "file": filename,
        "type": typ,
        "pattern": pattern,
        "found": found,
    })
    stats["by_pattern"][pattern] += 1
    stats["by_type"][typ] += 1

    for k, items in found.items():
        for line, groups in items:
            add_example(k, filename, line, groups)

# Print summary
print("=== PODSUMOWANIE WIDEŁEK ===")
print(f"Liczba plikow: {len(blocks)}")
print("\nPo typie:")
for k, v in sorted(stats["by_type"].items()):
    print(f"  {k}: {v}")
print("\nPatterny:")
for k, v in sorted(stats["by_pattern"].items(), key=lambda x: -x[1]):
    print(f"  {k}: {v}")

print("\n=== PRZYKŁADY ===")
for k, v in examples.items():
    print(f"\n{k} ({len(v)} przykladow):")
    for ex in v[:8]:
        print(f"  {ex[0]}: {ex[1].strip()}")
