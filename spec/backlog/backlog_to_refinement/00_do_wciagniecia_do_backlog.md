Sa następujące historyjki i bugi dla product ownera do dodania

następnie zespół ma zrobic refinement, 
zweryfikować backlog i zadecydować o dodaniu

1. 
- Miejscowości w starej bazie są jako zlepek w stringu 
- Klient chce mieć możliwość wpisywać tak żeby było można było dopisywać różne rzeczy
- Podczas migracji starych danych użyj jakiegoś skryptu który zegzaminuje te dane i utworzy poprawne adresy z dodatkowymi polamii Kod pocztowy i miasto
-  podczas migracji ujednolić odpowiednie żeby był pod kod pocztowy jedno miasto
- podczas dodawania nowych umów, miejsce wykonania usługi ma się uzupełnić dokładnie w taki sposób (użyty ten sam skrypt który przygotujecie teamem do wyciągania z danych adresowych kodu pocztowego i miasta automatycznie, może to tez samemu edytować jakby się nie pobrało) 
-  po pierwszym dodaniu jakiegos kodu pocztowego slownikuj to i automatycznie miasto wpisuj zeby nie bylo rozjazdu
- przeanalizuj implementację statystyk i wszedzie niech nie bazuj na jakiś z dupy filtrach po calym adresie, maja byc wyrzucone po obecnym adresie (w ktorym sa wpisywane bajki przez klienta typu wjazd od bramy), Statystyki maja bazowac tlyko na twardym kod pocztowy + miasto 

2.![[Zrzut ekranu 2026-05-17 220919.png]]

3.![[Zrzut ekranu 2026-05-17 221011.png]]


4. ![[Zrzut ekranu 2026-05-17 221042.png]] zweryfikuj own jak wygląda w starej aplikacje znajdziesz w archiwach przykładowe pliki, sprawdz sam jak sie generuje i napraw
5. ![[Pasted image 20260517221341.png]] Brakuje klientowi tych uwag, przeszukaj jak to wygladało w aplikacji [c:\](c:\projects\repos\AppRao)
6. W raz zespołem trzeba obejrzeć wygenerowane pdf czy odpowiadają tym ze starego systemu 
7. ![[Pasted image 20260517221739.png]]**

Chciałabym zmienić wygląd protokołów. Zależy mi na dodaniu tabeli „Przy wydaniu / Przy odbiorze”, w której znalazłyby się puste pola do ręcznego uzupełnienia, takie jak:

·         data i godzina,

·         urządzenie i model,

·         stan paliwa,

·         ilość kluczyków,

·         stan wideł,

·         czystość maszyny,

·         dokumentacja zdjęciowa,

·         dodatkowe akcesoria,

·         uwagi.


8.  Zmień, że usługi dodatkowe mają być zestawem zesłownikowanym z usługami, migrując starą bazę ma to się utworzyć, czyli usługi dodatkowe to nie są jakieś zmyślone stringi tylko usługi zesłownikowane (artykuły=> usługi). Czyli tak jak jest w nowej aplikacji ze sa uslugi dodatkowe w zestawach, ale te zestawy maja byc zeslownikowane z uslugami w artykuly
9.  Musi być zakonczone 8 przed tym!!! dodaj nowy panel Rozliczenie umowy i tak będą wszystkie pozycje umowy (razem z uslugi dodatkowe) automatycznie sie to ma dodac po utworzeniu umowy i beda recznie do wpisania dane Koszty (zadanie dla PRODUCT OWNERA wymyslec odpowiednie nazwy, chodzi o koszty przedstawione na fakturze dla klienta i koszty jakie ponosi firma)
10. musi byc dokonczone 9 przed tym!!!!! Zrefactoryzuj system prowizyjny, zeby dla handlowca ustalal prowizje x% ale nie od kosztu umowy, tylko od realnego zarobku czyli (Koszty klienta - Koszt jakie ponosi toolsmart ) x%
   