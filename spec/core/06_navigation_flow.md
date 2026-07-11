# 06 — Navigation Flow & Routing

> **INSTRUKCJA DLA AGENTA:** Flow użytkownika musi być identyczny z WinForms.
> Użytkownicy nie mogą się "zgubić" — nawigacja 1:1.

## Flow Diagram

```mermaid
graph TD
    A["<b>Logowanie</b><br/>LoginView.vue<br/>/login"] -->|login OK| B["<b>Dashboard</b><br/>DashboardView.vue<br/>/dashboard/contracts"]

    B --> B1["Sidebar: <b>Umowy</b><br/>/dashboard/contracts"]
    B --> B2["Sidebar: <b>Kontrahenci</b><br/>/dashboard/contractors"]
    B --> B3["Sidebar: <b>Maszyny</b><br/>/machines (Faza 7 refaktor)"]
    B --> B3a["Sidebar: <b>Usługi</b><br/>/services (Faza 7 refaktor)"]
    B --> B3c["Sidebar: <b>Usługi dodatkowe</b><br/>/additional-services (Faza 7 refaktor)"]
    B --> B3b["Sidebar: <b>Rezerwacje</b><br/>/reservations (Phase 3)"]
    B --> B7["Sidebar: <b>📊 Statystyki</b><br/>/analytics (merge Stats+Reports, RAO-P2-063)"]
    B --> B6["Sidebar: <b>📦 Archiwum</b><br/>/archive (RAO-P2-062)"]
    B --> B5["Sidebar: <b>Ustawienia</b><br/>/settings"]

    B1 -->|"Toolbar [+] lub double-click"| C["<b>Formularz umowy</b><br/>ContractFormView.vue<br/>/contracts/new lub /contracts/:id/edit"]
    B1 -->|"Toolbar [-]"| D["ConfirmDialog → DELETE"]
    B1 -->|"Context: Wydruk"| E["POST /reports/contract/:id<br/>→ Nowa karta z PDF"]

    B2 -->|"Toolbar [+] lub double-click"| F["<b>Formularz kontrahenta</b><br/>ContractorFormView.vue<br/>/contractors/new lub /:id/edit"]
    B2 -->|"Context: Dodaj umowę"| C

    B3 -->|"Toolbar [+] lub double-click"| G["<b>Formularz maszyny</b><br/>MachineFormView.vue<br/>/machines/new lub /machines/:id/edit"]
    B3 -->|"Context: Duplikuj"| H["POST /machines/:id/duplicate<br/>→ reload lista"]

    B3a -->|"Toolbar [+] lub double-click"| G2["<b>Formularz usługi</b><br/>ServiceFormView.vue<br/>/services/new lub /services/:id/edit"]
    B3c -->|"Toolbar [+] lub double-click"| G3["<b>Formularz usługi dodatk.</b><br/>AdditionalServiceFormView.vue<br/>/additional-services/new lub /:id/edit"]

    C -->|"Btn Kontrahent"| I["<b>Picker kontrahenta</b><br/>ContractorPicker (modal)<br/>Lista kontrahentów z wyszukiwaniem"]
    C -->|"Pozycje [+]"| J["<b>Picker maszyny</b><br/>ArticlePicker (modal)<br/>Lista maszyn + data dostawy + dni"]
    C -->|"Warunki [+] lub double-click warunek"| K["<b>Warunki rozliczenia</b><br/>ConditionFormView (modal/panel)<br/>Konfiguracja stawek i progów"]
    C -->|"Btn Widok [w]"| E
    C -->|"Btn Zapisz"| L["PUT /contracts/:id → powrót do Dashboard"]

    I -->|Wybierz| M["Dane kontrahenta wypełnione w formularzu umowy"]
    J -->|Wybierz| N["Nowa pozycja dodana do gridu"]
    K -->|Zakończ| O["Warunki zapisane, powrót do umowy"]

    F -->|"Btn Zatwierdź"| P["POST/PUT /contractors/:id → powrót do Dashboard"]
    F -->|"Btn GUS"| Q["POST /integrations/gus-lookup<br/>→ auto-fill pól"]

    B5 --> R["<b>Konfiguracja</b><br/>SettingsView.vue<br/>/settings"]
    R -->|"Btn Zapisz"| S["PUT /settings/company + fees + salespeople"]
```

## Mapowanie WinForms Form → Vue Route

| WinForms Form | Vue Route | Typ nawigacji |
|---------------|-----------|---------------|
| `Logowanie.cs` | `/login` | Pełna strona |
| `Form2.cs` (Umowy tab) | `/dashboard/contracts` | Sidebar + content |
| `Form2.cs` (Kontrahenci tab) | `/dashboard/contractors` | Sidebar + content |
| `Form2.cs` (Artykuły tab) | `/dashboard/articles` (DEPRECATED) → `/machines` | Sidebar + content |
| `FormA.cs` | `/machines/new` lub `/machines/:id/edit` (Faza 7 refaktor) | Pełna strona (replace content) |
| `FormA.cs` (usługi) | `/services/new` lub `/services/:id/edit` (Faza 7) | Pełna strona |
| `FormA.cs` (usługi dodatk.) | `/additional-services/new` lub `/:id/edit` (Faza 7) | Pełna strona |
| `ReservationsView` (Phase 3) | `/reservations` | Sidebar + content (kalendarz + lista + modal CRUD) |
| `Form2.cs` (Raporty tab) | `/analytics` (merge Stats+Reports, RAO-P2-063) | Sidebar + content |
| `FormK.cs` | `/contractors/:id/edit` lub `/new` | Pełna strona (replace content) |
| `FormU4.cs` | `/contracts/:id/edit` lub `/new` | Pełna strona (replace content) |
| `FormA.cs` | Dialog (modal) | Overlay na Dashboard |
| `FormAwybor.cs` | Dialog (modal) w kontekście FormU4 | Overlay na ContractForm |
| `FormW.cs` | Dialog/Panel w kontekście FormU4 | Overlay lub side-panel |
| `Konfiguracjacs.cs` | `/settings` | Pełna strona |
| `FormU.cs` (Crystal Report) | Nowa karta z PDF | window.open() |

## Pełna tabela routes (router/index.js)

| Route | Name | View | Auth | Opis |
|-------|------|------|------|------|
| `/login` | `Login` | `LoginView.vue` | nie | Strona logowania |
| `/reset-password` | `ResetPassword` | `ResetPasswordView.vue` | nie | Reset hasła z tokenu (query: `?token=...`) |
| `/` | — | — | tak | Redirect → `/home` |
| `/home` | `Home` | `HomeView.vue` | tak | KPI Dashboard, quick actions |
| `/dashboard/:section` | `Dashboard` | `DashboardView.vue` | tak | Listy (contracts/contractors) — `articles` DEPRECATED (→ `/machines`), `reports` usunięte (merge do `/analytics`) |
| `/contractors/new` | `ContractorNew` | `ContractorFormView.vue` | tak | Nowy kontrahent |
| `/contractors/:id/edit` | `ContractorEdit` | `ContractorFormView.vue` | tak | Edycja kontrahenta |
| `/articles/new` | `ArticleNew` | `ArticleFormView.vue` | tak | DEPRECATED (Faza 7) — backward compat shim → `/machines/new` |
| `/articles/:id/edit` | `ArticleEdit` | `ArticleFormView.vue` | tak | DEPRECATED (Faza 7) — backward compat shim → `/machines/:id/edit` |
| `/machines` | `MachinesList` | `MachinesListView.vue` | tak | Lista maszyn (Faza 7 refaktor — zastępuje /dashboard/articles) |
| `/machines/new` | `MachineNew` | `MachineFormView.vue` | tak | Nowa maszyna (Faza 7) |
| `/machines/:id/edit` | `MachineEdit` | `MachineFormView.vue` | tak | Edycja maszyny (Faza 7) |
| `/services` | `ServicesList` | `ServicesListView.vue` | tak | Lista usług zwykłych (Faza 7) |
| `/services/new` | `ServiceNew` | `ServiceFormView.vue` | tak | Nowa usługa (Faza 7) |
| `/services/:id/edit` | `ServiceEdit` | `ServiceFormView.vue` | tak | Edycja usługi (Faza 7) |
| `/additional-services` | `AdditionalServicesList` | `AdditionalServicesListView.vue` | tak | Lista usług dodatkowych (Faza 7) |
| `/additional-services/new` | `AdditionalServiceNew` | `AdditionalServiceFormView.vue` | tak | Nowa usługa dodatkowa (Faza 7) |
| `/additional-services/:id/edit` | `AdditionalServiceEdit` | `AdditionalServiceFormView.vue` | tak | Edycja usługi dodatkowej (Faza 7) |
| `/reservations` | `Reservations` | `ReservationsView.vue` | tak | Rezerwacje maszyn — kalendarz + lista + modal CRUD (Phase 3) |
| `/contracts/new` | `ContractNew` | `ContractFormView.vue` | tak | Nowa umowa |
| `/contracts/:id/edit` | `ContractEdit` | `ContractFormView.vue` | tak | Edycja umowy |
| `/worker` | `Worker` | `WorkerView.vue` | tak | Pulpit operacyjny (kończące, dostawy) |
| `/stats` | — | redirect → `/analytics` | tak | Backward compat (bookmarki) — RAO-P2-063 |
| `/analytics` | `Analytics` | `AnalyticsView.vue` | tak | Statystyki (Flota teraz + Wynajem w okresie + Eksplorator) — merge Stats+Reports (RAO-P2-063) |
| `/commissions` | `Commissions` | `CommissionView.vue` | tak | Raporty prowizji handlowców |
| `/settings` | `Settings` | `SettingsView.vue` | tak | Konfiguracja firmy/szablonów/handlowców |
| `/password` | `ChangePassword` | `ChangePasswordView.vue` | tak | Zmiana własnego hasła |
| `/admin` | `Admin` | `AdminView.vue` | tak + admin | Panel administracyjny (CRUD użytkowników) |

## Zachowania specjalne

### 1. Powrót z formularza
Po zapisie kontrahenta lub umowy → `router.push({ name: 'Dashboard', params: { section: previousSection } })`

### 2. Otwarcie umowy z kontekstu kontrahenta
Kliknięcie "Dodaj umowę" w context menu kontrahentów → `router.push({ name: 'ContractNew', query: { contractor_id: selectedItem.id } })`
Formularz umowy automatycznie wypełnia kontrahenta.

### 3. Kalendarz
Kliknięcie na dzień w kalendarzu → filtruje listę umów do tych z `data_od <= dzień AND data_do >= dzień`.
Dni z umowami są podświetlone (background color).

### 3b. Rezerwacje (Phase 3)
Widok `/reservations` — kalendarz month-view + lista + modal CRUD.
- Klik na dniu kalendarza → modal dodawania rezerwacji z preustawioną datą.
- Klik na kropce (event) → modal edycji (rezerwacja) lub info read-only (umowa).
- Ctrl+N NIE otwiera formularza dla sekcji reservations (widok ma własny modal).

### 4. Toolbar [?]
W sekcji Umowy: otwiera podgląd szczegółów zaznaczonej umowy (dialog z danymi).
W sekcji Maszyny: otwiera dialog z informacjami o maszynie. (Refaktor: było "Artykuły")

### 5. Auth Guard
Każda route z `meta.requiresAuth = true` sprawdza token w localStorage.
Brak tokena → redirect do `/login`.
Token wygasły → refresh lub redirect do `/login`.

### 6. Sortowanie
Kliknięcie nagłówka kolumny w DataGrid → sortowanie ASC/DESC (client-side).
Domyślne sortowanie:
- Umowy: po `number` DESC (najnowsze na górze)
- Kontrahenci: po `name` ASC
- Artykuły: po `name` ASC (DEPRECATED — patrz MachinesListView: po `name` ASC)

### 7. Wydruki (PDF)
W WinForms: Crystal Reports → window dialog.
W Vue: `POST /reports/contract/{id}?type=contract` → zwraca URL → `window.open(url, '_blank')`.
Typy wydruków:
- `contract` → Umowa (pełna)
- `protocol_zo` → Protokół zdawczo-odbiorczy
- `protocol_zo_nodata` → Protokół ZO bez danych (puste pola)
