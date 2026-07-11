import re
from collections import defaultdict

INPUT = r"C:\projects\repos\RaoApp_new\spec\technical\legacy_samples\extracted_all\sections_extracted_v2.txt"

# Read blocks
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

# Patterns
re_doba_simple = re.compile(r"(\d[\d\s,.]*),?\s*z[lł]\s*/\s*doba")
re_godz_simple = re.compile(r"(\d[\d\s,.]*),?\s*z[lł]\s*/\s*godz")
re_do_godz = re.compile(r"do\s+(\d+)\s+godzin\s*-\s*(\d[\d\s,.]*)", re.IGNORECASE)
re_każda = re.compile(r"ka[zż]da\s+kolejna\s*(\d[\d\s,.]*)", re.IGNORECASE)
re_dni_range = re.compile(r"(\d+)\s*-\s*(\d+)\s*dni\s*-\s*(\d[\d\s,.]*)\s*/\s*doba", re.IGNORECASE)
re_1dzien = re.compile(r"1\s+dzie[nń]\s*-\s*(\d[\d\s,.]*)\s*/\s*doba", re.IGNORECASE)
re_powyzej_dni = re.compile(r"powy[żz]ej\s+(\d+)\s*dni\s*-\s*(\d[\d\s,.]*)\s*/\s*doba", re.IGNORECASE)

stats = defaultdict(lambda: defaultdict(int))
examples = defaultdict(list)

def add_example(group, file, line, detail):
    if len(examples[group]) < 10:
        examples[group].append((file, line, detail))

for block in blocks:
    filename = block["file"]
    typ = detect_type(filename)
    content = "\n".join(block["lines"])
    norm = normalize(content)
    stats["total"][typ] += 1

    # flag patterns
    has_doba = bool(re_doba_simple.search(norm))
    has_godz = bool(re_godz_simple.search(norm))
    has_do_godz = bool(re_do_godz.search(norm))
    has_kazda = bool(re_każda.search(norm))
    has_dni_range = bool(re_dni_range.search(norm))
    has_1dzien = bool(re_1dzien.search(norm))
    has_powyzej_dni = bool(re_powyzej_dni.search(norm))

    # classify sub-pattern
    if typ == "N":
        if has_dni_range and has_powyzej_dni:
            pattern = "N_kaskadowa_doba"
        elif has_1dzien:
            pattern = "N_1dzien_doba"
        elif has_doba:
            pattern = "N_prosta_doba"
        else:
            pattern = "N_inny"
    elif typ == "U":
        if has_do_godz and has_kazda:
            pattern = "U_do_godzin_kazda_kolejna"
        elif has_godz:
            pattern = "U_prosta_godzina"
        elif has_do_godz:
            pattern = "U_do_godzin_bez_kazda"
        else:
            pattern = "U_inny"
    else:
        pattern = "?"

    stats["pattern"][pattern] += 1
    stats["pattern_by_type"][typ + "_" + pattern] += 1

    # extract values for more detail
    for m in re_doba_simple.finditer(norm):
        add_example("doba_simple", filename, m.group(0), None)
    for m in re_godz_simple.finditer(norm):
        add_example("godz_simple", filename, m.group(0), None)
    for m in re_do_godz.finditer(norm):
        add_example("do_godz", filename, m.group(0), None)
    for m in re_każda.finditer(norm):
        add_example("kazda", filename, m.group(0), None)
    for m in re_dni_range.finditer(norm):
        add_example("dni_range", filename, m.group(0), m.groups())
    for m in re_1dzien.finditer(norm):
        add_example("1dzien", filename, m.group(0), None)
    for m in re_powyzej_dni.finditer(norm):
        add_example("powyzej_dni", filename, m.group(0), m.groups())

# print summary
print("=== PODSUMOWANIE ===")
print(f"Liczba plikow: {len(blocks)}")
print("Po typie:")
for k, v in sorted(stats["total"].items()):
    print(f"  {k}: {v}")
print("\nPatterny:")
for k, v in sorted(stats["pattern"].items(), key=lambda x: -x[1]):
    print(f"  {k}: {v}")

print("\n=== PRZYKLADY ===")
for k, v in examples.items():
    print(f"\n{k}:")
    for ex in v[:5]:
        print(f"  {ex[0]}: {ex[1]}")
