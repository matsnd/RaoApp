"""
Position value calculation engine.

Implements the algorithm from spec 04_BUSINESS_LOGIC.md:
- Type 1: one-time fee (unit_price × quantity)
- Type 2: tiered pricing (conditions sorted by period_count)
- Type 3: simple rate (rate1 × total_periods)

Source of truth: position_conditions.rate1 + contract_positions.rental_days
Old WinForms: FormU4.cs spaghetti → rozliczenie table (1 row/day)

RAO-P1-017: dodano aggregate_by_category() dla statystyk po kategoriach
RAO-P1-026: dodano aggregate_by_period() + rozszerzono poziomy sub2/sub3
"""
import re
import math
from collections import defaultdict
from decimal import Decimal


DAYS_PER_PERIOD = {
    "dziennie": 1,
    "dzienna": 1,
    "tygodniowo": 7,
    "dwutygodniowo": 14,
    "miesięcznie": 30,
    "miesieczne": 30,
    "godzinowo": 1,
    "jednorazowo": 1,
}


def get_days_per_period(billing_frequency: str | None) -> int:
    return DAYS_PER_PERIOD.get(billing_frequency or "dziennie", 1)


def calculate_position_value(
    rental_days: int | None,
    billing_frequency: str | None,
    unit_price: Decimal | None,
    quantity: int | None,
    conditions: list[dict],
) -> Decimal:
    """
    Calculate the value of a single position.

    Args:
        rental_days: number of rental days from contract_positions
        billing_frequency: e.g. 'dziennie', 'tygodniowo'
        unit_price: fallback if no conditions (usually NULL)
        quantity: fallback multiplier (usually 1)
        conditions: list of dicts with keys:
            rate1 (Decimal), rate2 (Decimal|None),
            period_count (int), minimum (int),
            rate_type_id (int)
    """
    if not conditions:
        if unit_price and quantity:
            return Decimal(str(unit_price)) * int(quantity)
        return Decimal("0.00")

    days = rental_days or 0
    if days <= 0:
        return Decimal("0.00")

    freq = billing_frequency or "dziennie"
    dpp = get_days_per_period(freq)
    total_periods = math.ceil(days / dpp) if dpp > 0 else 0

    # Apply minimum from first condition
    min_periods = conditions[0].get("minimum") or 0
    if total_periods < min_periods:
        total_periods = min_periods

    if total_periods <= 0:
        return Decimal("0.00")

    # Tiered calculation
    total_value = Decimal("0.00")
    remaining = total_periods

    for i, cond in enumerate(conditions):
        if remaining <= 0:
            break

        pc = cond.get("period_count") or remaining
        rate = Decimal(str(cond.get("rate1") or 0))

        if rate <= 0:
            continue

        if i == 0:
            periods_in_tier = min(remaining, pc)
        else:
            prev_pc = conditions[i - 1].get("period_count") or 0
            tier_size = (pc or 999) - prev_pc
            periods_in_tier = min(remaining, tier_size)

        total_value += rate * periods_in_tier
        remaining -= periods_in_tier

    # If remaining periods after all tiers, use last non-zero rate
    if remaining > 0:
        for cond in reversed(conditions):
            rate = Decimal(str(cond.get("rate1") or 0))
            if rate > 0:
                total_value += rate * remaining
                break

    return total_value


# ── RAO-P1-017: Agregacja po kategoriach ─────────────────────────────────────

_FALLBACK_CATEGORY = "(bez kategorii)"


_LEVEL_FIELDS = {
    "main": "category_main",
    "sub1": "category_sub1",
    "sub2": "category_sub2",
    "sub3": "category_sub3",
}


def aggregate_by_category(
    positions: list[dict],
    level: str = "main",
) -> list[dict]:
    """
    Agreguje dane pozycji wynajmu według poziomu kategorii (RAO-P1-017).

    Args:
        positions: lista dict-ów z _compute_position_revenues
                   (wymagane klucze: article_id, contract_id, revenue,
                    clamped_days, category_main, category_sub1,
                    category_sub2, category_sub3)
        level: "main"  → grupuje po category_main
               "sub1"  → grupuje po category_sub1
               "sub2"  → grupuje po category_sub2  (RAO-P1-026)
               "sub3"  → grupuje po category_sub3  (RAO-P1-026)

    Returns:
        lista dict-ów posortowanych malejąco po revenue:
            category_name, articles_count, rented_days, revenue, contracts_count
    """
    agg: dict[str, dict] = defaultdict(lambda: {
        "revenue": Decimal("0"),
        "days": 0,
        "contracts": set(),
        "articles": set(),
    })

    field = _LEVEL_FIELDS.get(level, "category_main")

    for p in positions:
        cat_name = p.get(field) or _FALLBACK_CATEGORY
        agg[cat_name]["revenue"] += p.get("revenue", Decimal("0"))
        agg[cat_name]["days"] += p.get("clamped_days", 0)
        agg[cat_name]["contracts"].add(p.get("contract_id"))
        agg[cat_name]["articles"].add(p.get("article_id"))

    return sorted(
        [
            {
                "category_name": cat,
                "articles_count": len(d["articles"]),
                "rented_days": d["days"],
                "revenue": d["revenue"],
                "contracts_count": len(d["contracts"]),
            }
            for cat, d in agg.items()
        ],
        key=lambda x: x["revenue"],
        reverse=True,
    )


# ── RAO-P1-026: Agregacja po okresach ────────────────────────────────────────

def aggregate_by_period(
    positions: list[dict],
    granularity: str = "month",
    category_main_filter: list[str] | None = None,
) -> list[dict]:
    """
    Agreguje pozycje per (period, category_name) (RAO-P1-026).

    Args:
        positions: lista dict-ów z _compute_position_revenues
                   (wymagane klucze: contract_date_from, revenue,
                    clamped_days, contract_id, category_main)
        granularity: "month" → period = "YYYY-MM"
                     "year"  → period = "YYYY"
        category_main_filter: gdy podany → osobna seria per kategorię;
                              gdy None/pusty → jedna seria "__all__"

    Returns:
        lista dict-ów posortowanych rosnąco po (period, category_name):
            period, category_name, revenue, rented_days, contracts_count
    """
    _FALLBACK = "(bez kategorii)"

    agg: dict[tuple, dict] = defaultdict(lambda: {
        "revenue": Decimal("0"),
        "days": 0,
        "contracts": set(),
    })

    for p in positions:
        dt = p.get("contract_date_from")
        if not dt:
            continue
        period = f"{dt.year}-{dt.month:02d}" if granularity == "month" else str(dt.year)

        if category_main_filter:
            cat = p.get("category_main") or _FALLBACK
        else:
            cat = "__all__"

        key = (period, cat)
        agg[key]["revenue"] += p.get("revenue", Decimal("0"))
        agg[key]["days"] += p.get("clamped_days", 0)
        agg[key]["contracts"].add(p.get("contract_id"))

    return sorted(
        [
            {
                "period": k[0],
                "category_name": k[1],
                "revenue": v["revenue"],
                "rented_days": v["days"],
                "contracts_count": len(v["contracts"]),
            }
            for k, v in agg.items()
        ],
        key=lambda x: (x["period"], x["category_name"]),
    )


# City extraction for location reports
# Priority list of Polish cities (top 20 by population)
KNOWN_CITIES = [
    "Warszawa", "Kraków", "Łódź", "Wrocław", "Poznań", "Gdańsk", "Szczecin", "Bydgoszcz",
    "Lublin", "Białystok", "Katowice", "Gdynia", "Częstochowa", "Radom", "Sosnowiec",
    "Toruń", "Kielce", "Gliwice", "Zabrze", "Olsztyn", "Bielsko-Biała", "Bytom",
    "Zgierz", "Rzeszów", "Ruda Śląska", "Rybnik", "Tychy", "Dąbrowa Górnicza",
    "Opole", "Elbląg", "Płock", "Wałbrzych", "Włocławek", "Gorzów Wielkopolski",
    "Tarnów", "Chorzów", "Kalisz", "Koszalin", "Jelenia Góra", "Lublin", "Sopot",
    "Jastrzębie-Zdrój", "Nowy Sącz", "Jaworzno", "Jastrzębie Zdrój", "Piła", "Siedlce"
]

# Patterns to ignore (delivery instructions)
IGNORE_PATTERNS = [
    r'dojezd[^\w]*', r'instrukcja[^\w]*', r'zobacz[^\w]*', r'prosz[^\w]*',
    r'proszę', r'bardzo', r'dziękuję', r'pozdrawiam', r'z poważaniem',
    r'z góry', r'z dołu', r'z lewej', r'z prawej', r'na rogu',
    r'przy budowie', r'na budowie', r'obok', r'naprzeciwko', r'w pobliżu'
]


def extract_city(address: str | None) -> str:
    """
    Extract city name from delivery address with priority for known cities.
    
    Strategy:
    1. Check for known cities first (priority)
    2. Extract using patterns (postal code + city, city after comma)
    3. Ignore delivery instructions
    4. Return empty string if no city found
    
    Args:
        address: Delivery address string (multiline or single line)
    
    Returns:
        Extracted city name or empty string
    """
    if not address:
        return ""
    
    # Normalize address: remove extra whitespace, convert to single line
    normalized = ' '.join(address.split()).strip()
    
    # Step 1: Check for known cities (priority)
    for city in KNOWN_CITIES:
        if city.lower() in normalized.lower():
            return city
    
    # Step 2: Extract postal code + city pattern (XX-XXX City)
    postal_pattern = r'(\d{2}-\d{3})\s*([A-ZŚĆŹŁ][a-ząćęłńóśźż]+)'
    match = re.search(postal_pattern, normalized)
    if match:
        return match.group(2)
    
    # Step 3: Extract city after comma (typical Polish address format)
    # Pattern: "ul. Street 1, 00-001 City, Country" or "Street 1, City"
    comma_pattern = r',\s*([A-ZŚĆŹŁ][a-ząćęłńóśźż]+(?:\s+[A-ZŚĆŹŁ][a-ząćęłńóśźż]+)*)'
    matches = re.findall(comma_pattern, normalized)
    if matches:
        # Return the last match (usually city before country)
        city_candidate = matches[-1].strip()
        # Filter out common non-city words
        non_city_words = ['ulica', 'ul.', 'osiedle', 'os.', 'budowa', 'budynek', 'pokój', 'p.', 'mieszkanie', 'm.']
        for word in non_city_words:
            if city_candidate.lower().startswith(word.lower()):
                continue
        return city_candidate
    
    # Step 4: Extract from end of address (last word before instructions)
    words = normalized.split()
    for i, word in enumerate(reversed(words)):
        # Check if word looks like a city (starts with capital letter)
        if re.match(r'^[A-ZŚĆŹŁ][a-ząćęłńóśźż]+$', word):
            # Check if it's not an instruction
            is_instruction = any(re.search(pattern, word.lower()) for pattern in IGNORE_PATTERNS)
            if not is_instruction:
                return word
    
    return ""
