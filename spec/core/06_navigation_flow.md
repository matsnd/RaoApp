# 06 — Navigation Flow & Routing

> **INSTRUKCJA DLA AGENTA:** Flow użytkownika musi być identyczny z WinForms.
> Użytkownicy nie mogą się "zgubić" — nawigacja 1:1.

## Flow Diagram

```mermaid
graph TD
    A["<b>Logowanie</b><br/>LoginView.vue<br/>/login"] -->|login OK| B["<b>Dashboard</b><br/>DashboardView.vue<br/>/dashboard/contracts"]

    B --> B1["Sidebar: <b>Umowy</b><br/>/dashboard/contracts"]
    B --> B2["Sidebar: <b>Kontrahenci</b><br/>/dashboard/contractors"]
    B --> B3["Sidebar: <b>Artykuły</b><br/>/dashboard/articles"]
    B --> B4["Sidebar: <b>Raporty</b><br/>/dashboard/reports"]
    B --> B6["Sidebar: <b>📦 Archiwum</b><br/>/archive (RAO-P2-062)"]
    B --> B7["Sidebar: <b>📊 Statystyki</b><br/>/stats (RAO-P2-060 Faza 2)"]
    B --> B5["Sidebar: <b>Ustawienia</b><br/>/settings"]

    B1 -->|"Toolbar [+] lub double-click"| C["<b>Formularz umowy</b><br/>ContractFormView.vue<br/>/contracts/new lub /contracts/:id/edit"]
    B1 -->|"Toolbar [-]"| D["ConfirmDialog → DELETE"]
    B1 -->|"Context: Wydruk"| E["POST /reports/contract/:id<br/>→ Nowa karta z PDF"]

    B2 -->|"Toolbar [+] lub double-click"| F["<b>Formularz kontrahenta</b><br/>ContractorFormView.vue<br/>/contractors/new lub /:id/edit"]
    B2 -->|"Context: Dodaj umowę"| C

    B3 -->|"Toolbar [+] lub double-click"| G["<b>Dialog artykuł</b><br/>ArticleFormView (modal)"]
    B3 -->|"Context: Duplikuj"| H["POST /articles/:id/duplicate<br/>→ reload lista"]

    C -->|"Btn Kontrahent"| I["<b>Picker kontrahenta</b><br/>ContractorPicker (modal)<br/>Lista kontrahentów z wyszukiwaniem"]
    C -->|"Pozycje [+]"| J["<b>Picker artykułu</b><br/>ArticlePicker (modal)<br/>Lista artykułów + data dostawy + dni"]
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
| `Form2.cs` (Artykuły tab) | `/dashboard/articles` | Sidebar + content |
| `Form2.cs` (Raporty tab) | `/dashboard/reports` | Sidebar + content |
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
| `/dashboard/:section` | `Dashboard` | `DashboardView.vue` | tak | Listy (contracts/contractors/articles/reports) |
| `/contractors/new` | `ContractorNew` | `ContractorFormView.vue` | tak | Nowy kontrahent |
| `/contractors/:id/edit` | `ContractorEdit` | `ContractorFormView.vue` | tak | Edycja kontrahenta |
| `/articles/new` | `ArticleNew` | `ArticleFormView.vue` | tak | Nowy artykuł |
| `/articles/:id/edit` | `ArticleEdit` | `ArticleFormView.vue` | tak | Edycja artykułu |
| `/contracts/new` | `ContractNew` | `ContractFormView.vue` | tak | Nowa umowa |
| `/contracts/:id/edit` | `ContractEdit` | `ContractFormView.vue` | tak | Edycja umowy |
| `/worker` | `Worker` | `WorkerView.vue` | tak | Pulpit operacyjny (kończące, dostawy) |
| `/stats` | `Stats` | `StatsView.vue` | tak | Statystyki (Flota teraz + Wynajem w okresie) (RAO-P2-060) |
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

### 4. Toolbar [?]
W sekcji Umowy: otwiera podgląd szczegółów zaznaczonej umowy (dialog z danymi).
W sekcji Artykuły: otwiera dialog z informacjami o artykule.

### 5. Auth Guard
Każda route z `meta.requiresAuth = true` sprawdza token w localStorage.
Brak tokena → redirect do `/login`.
Token wygasły → refresh lub redirect do `/login`.

### 6. Sortowanie
Kliknięcie nagłówka kolumny w DataGrid → sortowanie ASC/DESC (client-side).
Domyślne sortowanie:
- Umowy: po `number` DESC (najnowsze na górze)
- Kontrahenci: po `name` ASC
- Artykuły: po `name` ASC

### 7. Wydruki (PDF)
W WinForms: Crystal Reports → window dialog.
W Vue: `POST /reports/contract/{id}?type=contract` → zwraca URL → `window.open(url, '_blank')`.
Typy wydruków:
- `contract` → Umowa (pełna)
- `protocol_zo` → Protokół zdawczo-odbiorczy
- `protocol_zo_nodata` → Protokół ZO bez danych (puste pola)
