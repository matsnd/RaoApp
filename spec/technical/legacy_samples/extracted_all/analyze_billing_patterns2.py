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

re_doba_simple = re.compile(r"(\d[\d\s,.]*),?\s*z[lł]\s*/\s*doba")
re_godz_simple = re.compile(r"(\d[\d\s,.]*),?\s*z[lł]\s*/\s*godz")
re_do_godz = re.compile(r"do\s+(\d+)\s+godzin\s*-\s*(\d[\d\s,.]*)", re.IGNORECASE)
re_każda = re.compile(r"ka[zż]da\s+kolejna\s*(\d[\d\s,.]*)", re.IGNORECASE)
re_dni_range = re.compile(r"(\d+)\s*-\s*(\d+)\s*dni\s*-\s*(\d[\d\s,.]*)\s*/\s*doba", re.IGNORECASE)
re_1dzien = re.compile(r"1\s+dzie[nń]\s*-\s*(\d[\d\s,.]*)\s*/\s*doba", re.IGNORECASE)
re_powyzej_dni = re.compile(r"powy[żz]ej\s+(\d+)\s*dni\s*-\s*(\d[\d\s,.]*)\s*/\s*doba", re.IGNORECASE)

anomalies = []

for block in blocks:
    filename = block["file"]
    typ = detect_type(filename)
    content = "\n".join(block["lines"])
    norm = normalize(content)

    has_doba = bool(re_doba_simple.search(norm))
    has_godz = bool(re_godz_simple.search(norm))
    has_do_godz = bool(re_do_godz.search(norm))
    has_kazda = bool(re_każda.search(norm))
    has_dni_range = bool(re_dni_range.search(norm))
    has_1dzien = bool(re_1dzien.search(norm))
    has_powyzej_dni = bool(re_powyzej_dni.search(norm))

    if typ == "N":
        if not (has_doba or has_dni_range or has_1dzien or has_powyzej_dni):
            anomalies.append((filename, typ, content))
    elif typ == "U":
        if not (has_godz or has_do_godz):
            anomalies.append((filename, typ, content))

print(f"Liczba anomalii: {len(anomalies)}")
for f, t, c in anomalies:
    print(f"\n=== {f} ({t}) ===")
    print(c)
    print("---")
