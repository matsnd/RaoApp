import re
from collections import defaultdict

INPUT = r"C:\projects\repos\RaoApp_new\spec\technical\legacy_samples\extracted_all\sections_extracted_v2.txt"
OUTPUT = r"C:\projects\repos\RaoApp_new\spec\technical\legacy_samples\extracted_all\widelki_v3_summary.txt"

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
    if len(examples[group]) < 20:
        examples[group].append((file, line, detail))

out_lines = []

for block in blocks:
    filename = block["file"]
    typ = detect_type(filename)
    content = "\n".join(block["lines"])
    lines = content.splitlines()

    found = {k: [] for k in patterns}
    for line in lines:
        ln = normalize(line)
        for name, pat in patterns.items():
            for m in pat.finditer(ln):
                found[name].append((line, m.groups()))

    # helpers
    def unit_in(name, units):
        for m in found[name]:
            groups = m[1]
            if name == "prosta_stawka":
                u = groups[1]
            elif name == "od_do":
                u = groups[2]  # dni/godzin/godz
            elif name == "do_dni_godzin":
                u = groups[1]  # may be None
            elif name == "powyzej":
                u = groups[1]
            else:
                u = None
            if u in units:
                return True
        return False

    has_prosta_doba = unit_in("prosta_stawka", ("doba",))
    has_prosta_godz = unit_in("prosta_stawka", ("godzina", "godz"))
    has_od_do_dni = unit_in("od_do", ("dni",))
    has_od_do_godz = unit_in("od_do", ("godzin", "godz"))
    has_do_dni = unit_in("do_dni_godzin", ("dni",))
    has_do_godz = unit_in("do_dni_godzin", ("godzin", "godz"))
    has_do_bez_jedn = any(m[1][1] is None for m in found["do_dni_godzin"])
    has_powyzej_dni = unit_in("powyzej", ("dni",))
    has_powyzej_godz = unit_in("powyzej", ("godzin", "godz"))
    has_kazda = len(found["kazda_kolejna"]) > 0
    has_1dzien = len(found["dni_1"]) > 0

    # determine detailed pattern
    if typ == "N":
        if (has_od_do_dni or has_1dzien) and has_powyzej_dni:
            pattern = "N_kaskadowa_doba (od-do lub 1dzien + powyzej)"
        elif has_od_do_dni:
            pattern = "N_od_do_dni (bez powyzej)"
        elif has_1dzien:
            pattern = "N_1dzien_doba"
        elif has_prosta_doba:
            pattern = "N_prosta_doba"
        elif has_prosta_godz:
            pattern = "N_godzinowa (anomalia)"
        else:
            pattern = "N_brak_ceny"
    elif typ == "U":
        if (has_od_do_godz or has_do_godz) and has_powyzej_godz:
            pattern = "U_kaskadowa_godzinowa (od-do/do + powyzej)"
        elif has_do_godz and has_kazda:
            pattern = "U_do_godzin_kazda_kolejna"
        elif has_do_godz:
            pattern = "U_do_godzin_bez_kazda"
        elif has_prosta_godz:
            pattern = "U_prosta_godzina"
        elif has_prosta_doba:
            pattern = "U_dobowa (anomalia)"
        elif has_do_dni or has_do_bez_jedn:
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

# Build output
out_lines.append("=== PODSUMOWANIE WIDEŁEK ===")
out_lines.append(f"Liczba plikow: {len(blocks)}")
out_lines.append("\nPo typie:")
for k, v in sorted(stats["by_type"].items()):
    out_lines.append(f"  {k}: {v}")
out_lines.append("\nPatterny:")
for k, v in sorted(stats["by_pattern"].items(), key=lambda x: -x[1]):
    out_lines.append(f"  {k}: {v}")

out_lines.append("\n=== WERYFIKACJA HIPOTEZY: 'od do i powyzej' ===")
# Files with od-do + powyzej
cascade_files = [c for c in classified if "od-do" in c["pattern"] or "kaskadowa" in c["pattern"]]
out_lines.append(f"Plikow z kaskadowym od-do + powyzej: {len(cascade_files)}")
for c in cascade_files[:20]:
    out_lines.append(f"  {c['file']} ({c['type']}): {c['pattern']}")

out_lines.append("\n=== ANOMALIE ===")
# anomalies: N with godz, U with doba/dni, empty prices
anomalies = [c for c in classified if "anomalia" in c["pattern"] or "brak" in c["pattern"]]
out_lines.append(f"Liczba anomalii: {len(anomalies)}")
for c in anomalies[:30]:
    out_lines.append(f"  {c['file']} ({c['type']}): {c['pattern']}")

out_lines.append("\n=== PRZYKŁADY ===")
for k, v in examples.items():
    out_lines.append(f"\n{k} ({len(v)} przykladow):")
    for ex in v[:8]:
        out_lines.append(f"  {ex[0]}: {ex[1].strip()}")

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write("\n".join(out_lines))

print("DONE")
