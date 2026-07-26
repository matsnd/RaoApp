#!/usr/bin/env python3
"""Test script for the enhanced extract_city function"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

from explorer.router import extract_city

def test_extract_city():
    """Test various address formats"""

    test_cases = [
        # Standard formats with postal codes
        ("00-123 Warszawa, ul. Krakowska 12", "Warszawa"),
        ("01-234 Kraków, al. Pokoju 15/2", "Kraków"),
        ("10-567 Wrocław, pl. Solny 1", "Wrocław"),

        # City before street
        ("Warszawa ul. Marszałkowska 1", "Warszawa"),
        ("Gdańsk al. Zwycięstwa 23", "Gdańsk"),
        ("Poznań pl. Wolności 5", "Poznań"),

        # Complex addresses
        ("Warszawa-Ursus, ul. Ryżowa 12/34 m. 5", "Warszawa Ursus"),
        ("Warszawa, Wola, ul. Karolkowa 15", "Warszawa"),
        ("m. st. Warszawa, ul. Jana Pawła II 42", "Warszawa"),

        # Different formats
        ("ul. Krakowska 12, 00-123 Warszawa", "Warszawa"),
        ("Krakowska 12/34, Warszawa", "Warszawa"),
        ("Warszawa, Krakowska 12, bud. A", "Warszawa"),

        # Edge cases
        ("", "Nieznane"),
        ("ul. Krakowska 12", "Nieznane"),
        ("12/34", "Nieznane"),
        ("Budynek A, Warszawa", "Warszawa"),

        # Known cities in text
        ("Niedaleko Warszawy, ul. Krakowska 12", "Warszawy"),
        ("Transport do Gdańska, ul. Długa 1", "Gdańska"),

        # Multi-word cities
        ("Bielsko-Biała, ul. 1 Maja 1", "Bielsko-Biała"),
        ("Gorzów Wielkopolski, ul. Warszawska 1", "Gorzów Wielkopolski"),

        # Districts/areas
        ("Warszawa Praga-Północ, ul. Targowa 1", "Warszawa Praga Północ"),
        ("Łódź Widzew, ul. Piotrkowska 1", "Łódź Widzew"),
    ]

    print("🧪 Testowanie funkcji extract_city():")
    print("=" * 60)

    passed = 0
    failed = 0

    for address, expected in test_cases:
        result = extract_city(address)
        status = "✅" if result == expected else "❌"

        if result == expected:
            passed += 1
        else:
            failed += 1

        print(f"{status} Input: {address[:40]:<40}")
        print(f"   Expected: {expected:<20} Got: {result}")
        print()

    print("=" * 60)
    print(f"📊 Wyniki: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 Wszystkie testy przeszły!")
    else:
        print(f"⚠️  {failed} testów nie przeszło")

if __name__ == "__main__":
    test_extract_city()