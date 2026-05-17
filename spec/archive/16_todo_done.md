## Status wykonania zadań

> **Ostatnia aktualizacja:** 2026-04-07 | Aktualny backlog z pozostałymi zadaniami → `19_BACKLOG.md`

| # | Zadanie | Status | Commit | Uwagi |
|---|---------|--------|--------|-------|
| 1 | Wywalić legacy szablony | ✅ Done | `879fb45` | Usunięto tab + 6 endpointów `/service-fee-templates` |
| 2 | Naprawić generowanie raportów PDF | ✅ Done | `0cb3d13` | Playwright + Chromium zainstalowane |
| 3 | PDF parity ze starą aplikacją | ✅ Done | `5999394` | Ciemne tytuły, usunięto OWN str. 2, dodano legal footer, "Wydrukowano" w stopce, naprawiono merge conflicty |
| 4 | Raporty dla pracownika | ✅ Done | `f25979e` | 4 endpointy: expiring/overdue/deliveries-today/unprinted + WorkerView.vue |
| 5 | Mapowanie usług dodatkowych ze starej bazy | ✅ Done | `534340a` | step5b w migrate.py: parser OPLATY → 2345 wierszy z 413 umów |
| 6 | Ponowna migracja ze starej bazy | ✅ Done | `534340a` | Migracja OK: 516 umów, 875 warunków, 2345 usług dodatkowych, 531 kontrahentów |
| 7 | Plan testowania aplikacji | ✅ Done | `d9122cb` | spec/17_TESTING_PLAN.md + 32 testy jednostkowe (calc + fee parser) |
| 8 | System prowizji dla handlowców | ✅ Done | `f2de66f` | commission_rate w Salesperson, GET /stats/commissions, CommissionView.vue |
| 9 | Przemyśl GUI/UX z całą ekipą | ✅ Done | `2cbcb54` | spec/18_UX_IMPROVEMENTS.md, kolorowanie wierszy umów, chip dni do końca |
| 10 | Wydruki dla wszystkich raportów i statystyk | ✅ Done | `f7dbaf2` | @media print CSS, przyciski Drukuj w WorkerView/CommissionView/ReportsSection |
| 11 | Sprawdź czy czegoś nie brakuje w migracji | ✅ Done | `0987a22` | DB OK: 516 umów, 614 pozycji, 875 warunków, costs+commission_rate w DB |
| 12 | U5: UI warunków cenowych w formularzu umowy | ✅ Done | `0987a22` | ConditionPanel.vue już był wpięty (v-if="selectedPosId && isEdit") |
| 13 | U6: Auto-kalkulacja wartości umowy po zapisie | ✅ Done | `0987a22` | recalcTotal() wywoływane po savePosition() + onConditionValueChanged() |
| 14 | U7: pole costs + pozostałe pola w modalu pozycji | ✅ Done | `0987a22` | costs dodane do posForm, PositionCreate schema i szablonu modalu |
| 15 | U8-U12: P2 — GUS auto-adres, landline, PDF preview, edit/delete settings | ✅ Done | `0987a22` | U8/U9/U10 już były; U11 PDF w nowej karcie; U12 inline edit kat/rate-types |
| 16 | PDF czcionki na Linux (produkcja) | ✅ Done | — | Roboto bundled w backend/reports/fonts/, @font-face w CSS |
| 17 | Dashboard: Niewydrukowane + Nieaktualne wydruki | ✅ Done | — | HomeView + WorkerView, endpoints /stats/unprinted + /stats/stale-print-contracts |
| 18 | Logika biznesowa niewydrukowanych/nieaktualnych | ✅ Done | — | active OR last 60/30 days, backend stats/router.py |
| 19 | Responsywność formularzy (grid layout) | ✅ Done | — | forms.css form-row-2/3/4 display:grid + responsive breakpoints, max-width w ContractFormView |

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