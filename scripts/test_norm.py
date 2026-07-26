import unicodedata
s1 = 'Ładowarki Teleskopowe'
s2 = 'Ladowarki teleskopowe '
def norm(s):
    s = s.strip().lower()
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return s
print(f's1 norm: {norm(s1)!r}')
print(f's2 norm: {norm(s2)!r}')
print(f'Equal: {norm(s1) == norm(s2)}')
# Check Ł decomposition
print(f'Ł NFKD: {[hex(ord(c)) for c in unicodedata.normalize("NFKD", "Ł")]}')
print(f'L NFKD: {[hex(ord(c)) for c in unicodedata.normalize("NFKD", "L")]}')
# Manual replace
def norm2(s):
    s = s.strip().lower()
    s = s.replace('ł', 'l').replace('Ł', 'l')
    return s
print(f's1 norm2: {norm2(s1)!r}')
print(f's2 norm2: {norm2(s2)!r}')
print(f'Equal2: {norm2(s1) == norm2(s2)}')
