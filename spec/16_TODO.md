## Status wykonania zadań

| # | Zadanie | Status | Commit | Uwagi |
|---|---------|--------|--------|-------|
| 1 | Wywalić legacy szablony | ✅ Done | `879fb45` | Usunięto tab + 6 endpointów `/service-fee-templates` |
| 2 | Naprawić generowanie raportów PDF | ✅ Done | `0cb3d13` | Playwright + Chromium zainstalowane |
| 3 | PDF parity ze starą aplikacją | ✅ Done | `5999394` | Ciemne tytuły, usunięto OWN str. 2, dodano legal footer, "Wydrukowano" w stopce, naprawiono merge conflicty |
| 4 | Raporty dla pracownika | ✅ Done | `f25979e` | 4 endpointy: expiring/overdue/deliveries-today/unprinted + WorkerView.vue |
| 5 | Mapowanie usług dodatkowych ze starej bazy | ⏳ In Progress | pending | step5b w migrate.py: parser OPLATY + contract_service_fees |
| 6 | Ponowna migracja ze starej bazy | ⏳ Pending | — | — |
| 7 | Plan testowania aplikacji | ⏳ Pending | — | — |
| 8 | System prowizji dla handlowców | ⏳ Pending | — | — |
| 9 | Przemyśl GUI/UX z całą ekipą | ⏳ Pending | — | — |
| 10 | Wydruki dla wszystkich raportów i statystyk | ⏳ Pending | — | — |

---

1. Wywalić legacy szablony
2. Naprawic generowanie raportów PDF nie działa po kliknięciu
3. Product owner ma docisnąc zespół, żeby PDF wyglądały dokłądnie tak samo jak w starej aplikacji
4. Są dodane w aplikacji raporty przydatne dla własciciela firmy, dodaj raporty dla pracownika, analityk biznesowy niech się spotka z tym pracownikiem, jako ten pracownik powiedz czego potzebujesz do ułatwienia pracy, czyli np. nadchodzące zakończenia umowy, ale jako ten pracownik pracujący na tej aplikacji odpowiedz na pytanie ekipie i wymyśl co jeszcze potrzebujesz, porozmawiajcie, dojdźcie do porozumienia
5. Delikatna sprawa precież te usługi dodatkowe w polu tekstowym w starej aplikacji powinny się zmapować na nowy model w nowej aplikacji, rozważ ekipa jak to najlepiej zrobić
6. Wykonaj ze starej bazy jeszcze raz migracje i sprawdź jak to się zmapowało
7. Zastanów się jaki masz pomysł na testowanie tej aplikacji 
8. Zaproponuj jakiś system obliczenia prowizji dla handlowców
9. Przemyśl ekipą jak lepiej by to można było rozłożyć w GUI, UIX designer niech się wykaże i doagadajcie sie z product ownerem i cała ekipą
10. Utwórz wydruki dla wszystkich raportów i statystyk jeśli brakuje w najlepiej rozmyślony sposób przez ekipę
11. Sprawdź czy czegoś nie brakuje w migracji na tym etapie aplikacji