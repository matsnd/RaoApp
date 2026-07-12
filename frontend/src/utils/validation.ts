/**
 * Utility do parsowania błędów walidacji z backendu (Pydantic v2 / FastAPI).
 *
 * Błędy 422 z FastAPI mają format:
 *   detail: [{ type, loc, msg, input, ctx }]
 *
 * Pydantic v2 dodaje techniczne prefixy ("Value error, ", "Field required"),
 * które są nieczytelne dla użytkownika. Ten utility:
 *  1. Czyści techniczne prefixy
 *  2. Tłumaczy comune komunikaty Pydantic na polski
 *  3. Mapuje nazwy pól na polskie
 */

// Mapowanie nazw pól (API → polski)
const FIELD_MAP: Record<string, string> = {
  // Umowy
  date_from: 'Data rozpoczęcia',
  date_to: 'Data zakończenia',
  contract_type: 'Typ umowy',
  contractor_id: 'Kontrahent',
  delivery_address: 'Adres dostawy',
  city: 'Miasto',
  postal_code: 'Kod pocztowy',
  contact_person1: 'Osoba kontaktowa',
  contact_phone1: 'Telefon kontaktowy',
  salesperson_id: 'Handlowiec',
  number: 'Numer',
  // Pozycje
  machine_id: 'Maszyna',
  service_id: 'Usługa',
  quantity: 'Ilość',
  rental_days: 'Dni wynajmu',
  // Warunki
  rate1: 'Stawka 1',
  rate2: 'Stawka 2',
  period_count: 'Liczba okresów',
  period_from: 'Okres od',
  period_to: 'Okres do',
  billing_label: 'Etykieta rozliczenia',
  rate_type_id: 'Typ stawki',
  // Opłaty
  amount_from: 'Kwota od',
  amount_to: 'Kwota do',
  description: 'Opis',
  is_active: 'Aktywna',
  additional_service_id: 'Usługa dodatkowa',
  // Kontrahent
  name: 'Nazwa',
  nip: 'NIP',
  // Maszyna/Artykuł
  internal_number: 'Numer wewnętrzny',
  serial_no: 'Numer seryjny',
  brand: 'Marka',
  model: 'Model',
  replacement_value: 'Wartość odtworzeniowa',
  category_main: 'Kategoria główna',
  category_id: 'Kategoria',
  power_type: 'Zasilanie',
  // Rezerwacje
  reserved_from: 'Data rezerwacji od',
  reserved_to: 'Data rezerwacji do',
  machine_number: 'Maszyna',
  // Auth
  login: 'Login',
  password: 'Hasło',
  email: 'E-mail',
  new_password: 'Nowe hasło',
  // Ustawienia
  commission_rate: 'Prowizja',
}

// Tłumaczenia comune komunikatów Pydantic v2
const MSG_TRANSLATIONS: Record<string, string> = {
  'Field required': 'To pole jest wymagane',
  'field required': 'To pole jest wymagane',
  'String should have at least 1 character': 'To pole jest wymagane',
  'String should have at least {min_length} characters': 'Wymagane minimum {min_length} znaków',
  'String should have at most {max_length} characters': 'Maksymalnie {max_length} znaków',
  'Input should be greater than or equal to {ge}': 'Wartość musi być większa lub równa {ge}',
  'Input should be less than or equal to {le}': 'Wartość musi być mniejsza lub równa {le}',
  'Input should be a valid number': 'Wymagana liczba',
  'Input should be a valid integer': 'Wymagana liczba całkowita',
  'Input should be a valid string': 'Wymagany tekst',
  'Input should be a valid date': 'Wymagana data',
  'Input should be a valid boolean': 'Wymagana wartość logiczna (tak/nie)',
  'String should match pattern {pattern}': 'Nieprawidłowy format',
  'value is not a valid email address': 'Nieprawidłowy adres e-mail',
  'Input should be a valid list': 'Wymagana lista',
}

// Czyści techniczne prefixy Pydantic v2
function cleanMessage(msg: string): string {
  if (!msg) return ''
  // Usuń prefix "Value error, " (dodawany przez Pydantic v2 dla raise ValueError)
  let cleaned = msg.replace(/^Value error,\s*/i, '')
  // Tłumacz comune komunikaty
  if (MSG_TRANSLATIONS[cleaned]) return MSG_TRANSLATIONS[cleaned]
  // Spróbuj dopasować z parametrami (np. "String should have at least 5 characters")
  for (const [pattern, translation] of Object.entries(MSG_TRANSLATIONS)) {
    if (pattern.includes('{')) {
      const regex = new RegExp('^' + pattern.replace(/\{[^}]+\}/g, '(\\d+)') + '$')
      const match = cleaned.match(regex)
      if (match) {
        return translation.replace(/\{[^}]+\}/g, match[1])
      }
    }
  }
  return cleaned
}

// Mapuje nazwę pola z API na polską
function translateField(field: string): string {
  return FIELD_MAP[field] || field
}

export interface ParsedValidationError {
  field: string
  message: string
  full: string
}

/**
 * Parsuje odpowiedź błędu z backendu (FastAPI/Pydantic v2).
 *
 * @param detail - `e.response.data.detail` (string lub lista błędów Pydantic)
 * @returns Lista przystępnych komunikatów po polsku
 */
export function parseValidationErrors(detail: unknown): string[] {
  if (!detail) return []
  if (typeof detail === 'string') return [detail]
  if (!Array.isArray(detail)) return [String(detail)]
  return detail.map((err: any) => {
    const rawField = err.loc?.[err.loc.length - 1] || err.loc?.[0] || 'pole'
    const field = translateField(String(rawField))
    const message = cleanMessage(err.msg || 'Błąd walidacji')
    return `${field}: ${message}`
  })
}

/**
 * Wyciąga czytelny komunikat błędu z odpowiedzi HTTP (używane w formularzach).
 *
 * @param error - obiekt błędu z axios (e.response.data.detail)
 * @param fallback - komunikat domyślny
 * @returns Pojedynczy string z czytelnym komunikatem
 */
export function extractErrorMessage(error: any, fallback = 'Błąd zapisu'): string {
  const detail = error?.response?.data?.detail
  if (!detail) return error?.message || fallback
  const messages = parseValidationErrors(detail)
  return messages.length > 0 ? messages.join(', ') : fallback
}
