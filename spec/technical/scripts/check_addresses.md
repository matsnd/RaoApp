# check_addresses.py

## Opis
Skrypt do weryfikacji przykładowych adresów dostawy z bazy danych. Używany podczas developmentu do analizy formatu adresów.

## Użycie

```bash
cd spec/technical/scripts
python check_addresses.py
```

## Wymagania
- Backend musi być skonfigurowany (`.env` z DB connection)
- Tabela `contract` musi istnieć w bazie

## Działanie
1. Łączy się z bazą danych przez `AsyncSessionLocal`
2. Wybiera 20 unikalnych adresów dostawy z tabeli `contract`
3. Wyświetla listę adresów

## Wynik
```
Przykładowe adresy z bazy:
1. ul. Krakowska 12, 00-123 Warszawa
2. al. Pokoju 15/2, 01-234 Kraków
...
```

## Użycie w RAO
- Development — analiza formatu adresów przed implementacją `extract_city()`
- Testing — weryfikacja danych w bazie
- Data analysis — szybki podgląd adresów dostawy

## Powiązane
- Script: `test_extract_city.py`
- Function: `backend/explorer/router.py::extract_city()`
- Table: `contract.delivery_address`