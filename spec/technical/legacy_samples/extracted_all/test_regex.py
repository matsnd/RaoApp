import re
lines = [
    "230,00zł / doba",
    "700,00zł / doba",
    "1 dzień - 630,00 / doba",
    "1 - 3 dni - 800,00 / doba",
    "powyżej 3 dni - 700,00 / doba",
    "do 8 godzin - 4700,00zł",
    "każda kolejna 300,00zł",
    "110,00zł / godzina",
]

def normalize(line):
    return (
        line.lower()
        .replace("ó", "o").replace("ż", "z").replace("ź", "z")
        .replace("ć", "c").replace("ń", "n").replace("ś", "s")
        .replace("ł", "l").replace("ę", "e").replace("ą", "a")
    )

price_re = r"[\d\s,.]+"
prosta = re.compile(r"(" + price_re + r")\s*z[lł]\s*/\s*(doba|godzina|godz)")
do_pat = re.compile(r"do\s+(\d+)\s*(dni|godzin|godz)?\s*-\s*(" + price_re + r")\s*(?:z[lł])?\s*(?:/\s*(doba|godzina|godz))?")
oddo = re.compile(r"(\d+)\s*-\s*(\d+)\s*(dni|godzin|godz)\s*-\s*(" + price_re + r")\s*(?:z[lł])?\s*(?:/\s*(doba|godzina|godz))?")
powyzej = re.compile(r"powy[żz]ej\s+(\d+)\s*(dni|godzin|godz)?\s*-\s*(" + price_re + r")\s*(?:z[lł])?\s*(?:/\s*(doba|godzina|godz))?")

with open('test_regex_out2.txt', 'w', encoding='utf-8') as out:
    for line in lines:
        ln = normalize(line)
        out.write(repr(line) + " -> " + repr(ln) + "\n")
        out.write("  prosta: " + str(prosta.search(ln)) + "\n")
        out.write("  do: " + str(do_pat.search(ln)) + "\n")
        out.write("  od-do: " + str(oddo.search(ln)) + "\n")
        out.write("  powyzej: " + str(powyzej.search(ln)) + "\n")
