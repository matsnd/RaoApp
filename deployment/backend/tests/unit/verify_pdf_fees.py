#!/usr/bin/env python3
"""
Skrypt weryfikacji tekstu w PDF generowanym przez WeasyPrint.
Użycie:
    python verify_pdf_fees.py <sciezka_do_pdf> <oczekiwany_tekst>

Zwraca:
    PASS + szczegóły  — gdy tekst zostanie znaleziony w PDF
    FAIL + szczegóły  — gdy tekst nie zostanie znaleziony

Może być używany jako:
- standalone script z linii komend (CI/CD, lokalne testy)
- helper w testach pytest (import verify_pdf_fees + wywołanie funkcji)
"""

import sys
import os

# Dodaj root backend/ do sys.path żeby importować backendowe moduły
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


def extract_text_from_pdf(pdf_path: str) -> str:
    """Wyciąga cały tekst z PDF.

    RAO-P1-102: WeasyPrint 68.x embeds subsetted fonts without proper ToUnicode
    CMap mappings, so pdfplumber/pdfminer/pypdf return empty strings for body text.
    PyMuPDF (fitz) handles these PDFs correctly on Windows.
    Fallback: pdfplumber (for non-WeasyPrint PDFs or older versions).
    """
    # Primary: PyMuPDF (fitz) — handles WeasyPrint 68.x font subsetting
    try:
        import fitz
        doc = fitz.open(pdf_path)
        all_text = []
        for page in doc:
            text = page.get_text()
            if text:
                all_text.append(text)
        doc.close()
        return '\n'.join(all_text)
    except ImportError:
        pass

    # Fallback: pdfplumber (for non-WeasyPrint PDFs)
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("ani fitz (PyMuPDF) ani pdfplumber nie jest zainstalowany. Uruchom: pip install PyMuPDF")

    all_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                all_text.append(text)
    return '\n'.join(all_text)


def verify_pdf_contains(pdf_path: str, expected_text: str) -> dict:
    """
    Weryfikuje czy PDF zawiera oczekiwany tekst.

    Returns:
        dict: {status: 'PASS'|'FAIL', pdf_path, expected, found: bool, snippet: str}
    """
    if not os.path.exists(pdf_path):
        return {
            'status': 'FAIL',
            'pdf_path': pdf_path,
            'expected': expected_text,
            'found': False,
            'snippet': f'Plik nie istnieje: {pdf_path}',
        }

    content = extract_text_from_pdf(pdf_path)
    found = expected_text in content

    # Znajdź fragment okolic tekstu (dla debugowania)
    snippet = ''
    if found:
        idx = content.find(expected_text)
        start = max(0, idx - 60)
        end = min(len(content), idx + len(expected_text) + 60)
        snippet = f'...{content[start:end]}...'
    else:
        # Pokaż pierwsze 500 znaków żeby zobaczyć co jest w PDF
        snippet = content[:500].replace('\n', ' ')

    return {
        'status': 'PASS' if found else 'FAIL',
        'pdf_path': pdf_path,
        'expected': expected_text,
        'found': found,
        'snippet': snippet,
    }


def main():
    if len(sys.argv) < 3:
        print("Użycie: python verify_pdf_fees.py <sciezka_pdf> <oczekiwany_tekst>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    expected_text = sys.argv[2]

    result = verify_pdf_contains(pdf_path, expected_text)

    print(f"Status: {result['status']}")
    print(f"Plik:   {result['pdf_path']}")
    print(f"Szukano: '{result['expected']}'")
    print(f"Znaleziono: {result['found']}")
    if result['snippet']:
        print(f"Fragment: {result['snippet']}")

    sys.exit(0 if result['status'] == 'PASS' else 1)


if __name__ == '__main__':
    main()
