# Lekcja 12 — Props/emit + composables

> Plik bazowy: `frontend/src/composables/useSort.ts`, `frontend/src/components/shared/DateRangePicker.vue`
> Odpowiednik Angular: `@Input`/`@Output` + services / utility functions

Props i emit to komunikacja rodzic ↔ dziecko w Vue. Composables to wielokrotnego użytku logika (odpowiednik Angular services / utility functions / custom hooks).

## Realny snippet z repo — composable

<ref_snippet file="C:/projects/repos/RaoApp_new/frontend/src/composables/useSort.ts" lines="1-84" />

## Realny snippet z repo — props/emit

<ref_snippet file="C:/projects/repos/RaoApp_new/frontend/src/components/shared/DateRangePicker.vue" lines="27-66" />

## 1. `defineProps` — input do komponentu

Angular:
```typescript
@Input() dateFrom: string | null = null;
@Input() dateTo: string | null = null;
// nowszy Angular:
dateFrom = input<string | null>(null);
```

Vue `<script setup>`:
```typescript
const props = defineProps<{
  dateFrom: string | null
  dateTo: string | null
}>()
```

`defineProps<T>()` — generic z typem. TypeScript-only. W JS: `defineProps({ dateFrom: { type: String, default: null } })`.

**`props`** — obiekt tylko do odczytu. `props.dateFrom`, `props.dateTo`. Nie mutuj (jak Angular `@Input`).

W template: `{{ dateFrom }}` (auto-unwrap, bez `props.`).

## 2. `defineEmits` — output z komponentu

Angular:
```typescript
@Output() dateFromChange = new EventEmitter<string | null>();
// nowszy Angular:
dateFromChange = output<string | null>();
// emit:
this.dateFromChange.emit(value);
```

Vue:
```typescript
const emit = defineEmits<{
  (e: 'update:dateFrom', val: string | null): void
  (e: 'update:dateTo', val: string | null): void
}>()

// emit:
emit('update:dateFrom', newVal)
```

`defineEmits<T>()` — generic z typem eventów. Każdy event to `(e: 'eventName', ...args) => void`. W JS: `defineEmits(['update:dateFrom', 'update:dateTo'])`.

`emit('eventName', payload)` — wywołaj event. Rodzic słucha przez `@event-name="handler"`.

## 3. `update:xxx` — convention dla v-model

```typescript
emit('update:dateFrom', val)
emit('update:dateTo', val)
```

`update:propName` — konwencja Vue dla two-way binding. Rodzic:
```html
<DateRangePicker
  :date-from="form.date_from"
  :date-to="form.date_to"
  @update:date-from="form.date_from = $event"
  @update:date-to="form.date_to = $event"
/>
```

Albo skrót `v-model:date-from="form.date_from"`:
```html
<DateRangePicker v-model:date-from="form.date_from" v-model:date-to="form.date_to" />
```

`v-model:arg="x"` = `:arg="x"` + `@update:arg="x = $event"`. Odpowiednik Angular `[(dateFrom)]="form.date_from"` (banana-in-a-box).

**Standard `v-model`** (bez arg) = `:modelValue` + `@update:modelValue`. Dla jednego pola. Dla wielu pól — `v-model:arg` z argumentem.

## 4. `watch` na props — synchronizacja

<ref_snippet file="C:/projects/repos/RaoApp_new/frontend/src/components/shared/DateRangePicker.vue" lines="61-66" />

```typescript
watch(
  () => [props.dateFrom, props.dateTo] as [string | null, string | null],
  ([f, t]) => {
    range.value = [fromISO(f), fromISO(t)]
  },
)
```

`watch(() => [props.dateFrom, props.dateTo], ...)` — gdy props się zmieni, zsynchronizuj internal `range`. Source to getter function zwracająca array.

**Dlaczego nie bezpośrednio `computed`?** Bo `range` jest mutowany przez VueDatePicker (v-model). Musi być `ref`, nie `computed` (computed jest read-only). `watch` synchronizuje props → ref.

Odpowiednik Angular `ngOnChanges` albo `effect(() => this.range.set([fromISO(this.dateFrom()), ...]))`.

## 5. Composable — `useSort<T>`

<ref_snippet file="C:/projects/repos/RaoApp_new/frontend/src/composables/useSort.ts" lines="18-83" />

```typescript
export function useSort<T extends Record<string, unknown>>(
  initialKey: keyof T,
  initialDir: SortDir = 'desc',
) {
  const sortKey = ref<keyof T>(initialKey)
  const sortDir = ref<SortDir>(initialDir)

  function toggleSort(key: keyof T): void { ... }
  function sortedRows<U extends Record<string, unknown>>(rows: U[]): U[] { ... }

  return { sortKey, sortDir, toggleSort, sortedRows }
}
```

**Composable** = funkcja zwracająca reactive state + funkcje. Konwencja: nazwa `useXxx`. Używane w `<script setup>`:

```typescript
const { sortKey, sortDir, toggleSort, sortedRows } = useSort<Machine>('name', 'asc')
```

Odpowiednik Angular:
- **Service** z `@Injectable` — ale service jest singleton, composable tworzy nową instancję per komponent
- **Custom hook** (jeśli Angular miałby hooks)
- **Factory function** zwracająca signals

**Kluczowa różnica:** composable tworzy **nowy state per wywołanie**. Każdy komponent ma własny `sortKey`, `sortDir`. Angular service jest singleton (chyba że `providedIn: 'component'`).

## 6. Generic composable — `<T extends ...>`

```typescript
export function useSort<T extends Record<string, unknown>>(...)
```

Generic `T` — composable typowane per użycie. `useSort<Machine>('name')` — `sortKey` jest `keyof Machine`. TypeScript enforce'uje że `toggleSort('name')` OK, `toggleSort('foobar')` → error.

Odpowiednik Angular generic service `class SortService<T extends Record<string, unknown>>`. Ale w Angular service jest singleton — generic per injection token. W Vue composable — generic per wywołanie.

## 7. `ref<keyof T>` — ref z typem

```typescript
const sortKey = ref<keyof T>(initialKey)
```

`ref<keyof T>(initialKey)` — ref którego wartość jest kluczem typu `T`. `.value` ma typ `keyof T`. Odpowiednik Angular `signal<keyof T>(initialKey)`.

## 8. Composable zwraca obiekt z refs i funkcjami

```typescript
return { sortKey, sortDir, toggleSort, sortedRows }
```

Zwraca obiekt. W komponencie:
```typescript
const { sortKey, sortDir, toggleSort, sortedRows } = useSort<Machine>('name')
// sortKey.value, sortDir.value, toggleSort('name'), sortedRows(rows)
```

**Destructuring zachowuje reactivity** — `sortKey` to ref, `sortKey.value` reactive. Funkcje (`toggleSort`) są zwykłymi funkcjami.

**Uwaga:** jeśli zwrócisz `computed`, destructuring też zachowa reactivity (bo to ref pod spodem). Ale jeśli zwrócisz plain value (nie ref), straci reactivity. Dlatego composable zwraca refs, nie plain values.

## 9. Composable z lifecycle hooks

Composable może używać `onMounted`, `onUnmounted`, etc. — **tylko jeśli wywołane w `<script setup>`** (podczas setup komponentu). Vue trackuje "current instance" podczas setup.

```typescript
export function useFetch(url: string) {
  const data = ref(null)
  onMounted(async () => { data.value = await fetch(url) })
  return { data }
}
```

Odpowiednik Angular `effect` + `inject` w service — ale composable jest prostsze.

**Nie wywołuj composable poza setup** (np. w setTimeout) — lifecycle hooks nie zadziałają.

## 10. Composable vs Pinia store

| Composable | Pinia store |
|------------|-------------|
| Nowa instancja per komponent | Singleton per app |
| Stan lokalny komponentu | Stan globalny |
| `useSort()`, `useFileDownload()` | `useAuthStore()`, `useMachineStore()` |
| Brak devtools | Devtools |
| Generic per wywołanie | Brak generic |

**Reguła:** lokalny state komponentu → composable. Globalny state app → Pinia.

W RAO: `useSort`, `useFileDownload`, `usePdfFolders` — composables (lokalne). `auth`, `machines`, `contracts` — Pinia (globalne).

## Gotchas dla Angular deva

1. **`defineProps<T>()` = `@Input` / `input()`.** Tylko do odczytu, nie mutuj.
2. **`defineEmits<T>()` = `@Output` / `output()`.** `emit('event', payload)`.
3. **`update:propName` = v-model convention.** `v-model:arg="x"` = `:arg` + `@update:arg`.
4. **`watch` na props do sync internal state.** Jeśli props zmienia z zewnątrz.
5. **Composable = funkcja `useXxx`.** Nowa instancja per komponent (nie singleton).
6. **Composable zwraca refs + funkcje.** Destructuring zachowuje reactivity.
7. **Composable z lifecycle hooks tylko w setup.** Nie wywołuj poza `<script setup>`.
8. **Composable vs Pinia.** Lokalny → composable, globalny → Pinia.
9. **Generic composable `<T>`.** Typowane per wywołanie, jak factory function.
10. **`ref<keyof T>` = `signal<keyof T>`.** Reactive z typem.

## Quiz

1. Czym jest `defineProps<T>()`? (input do komponentu — odpowiednik @Input)
2. Co robi `emit('update:dateFrom', val)`? (emit event — convention dla v-model)
3. Czym jest composable `useSort`? (funkcja zwracająca reactive state + funkcje, nowa instancja per komponent)
4. Composable vs Pinia store — kiedy co? (lokalny state → composable, globalny → Pinia)
5. Dlaczego `watch` na props w DateRangePicker? (sync internal ref gdy props zmienia z zewnątrz)

→ `python learning/quiz/quiz.py --topic props --n 5`

---

## Co dalej?

Gratulacje — przeszedłeś 12 lekcji. Teraz:

1. **Odpal pełny quiz:** `python learning/quiz/quiz.py --all`
2. **Powtarzaj tematy:** `python learning/quiz/quiz.py --topic vue --n 10`
3. **Czytaj kod repo** — teraz powinieneś rozumieć 90% `backend/articles/` i `frontend/src/stores/`
4. **Modyfikuj ostrożnie** — drugie okno agenta pracuje, ale możesz czytać i eksperymentować na branchu

Powodzenia. Python i Vue są prostsze niż Ci się wydają — masz już 80% konceptów z .NET + Angular.
