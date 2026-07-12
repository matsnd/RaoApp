# Lekcja 10 — Pinia store vs Angular service

> Plik bazowy: `frontend/src/stores/articles.js`, `frontend/src/stores/auth.js`
> Odpowiednik Angular: Service + BehaviorSubject, albo NgRx Component Store

Pinia to oficjalny store Vue 3. Odpowiednik Angular service z `BehaviorSubject` + `@Injectable`, albo NgRx Component Store. Prostszy niż NgRx (brak actions/reducers/effects), podobny do Angular service ze stanem.

## Realny snippet z repo

<ref_snippet file="C:/projects/repos/RaoApp_new/frontend/src/stores/articles.js" lines="1-87" />

<ref_snippet file="C:/projects/repos/RaoApp_new/frontend/src/stores/auth.js" lines="1-62" />

## 1. `defineStore` — setup syntax

```typescript
export const useArticleStore = defineStore('articles', () => {
  const list = ref([])
  const total = ref(0)
  const loading = ref(false)

  async function fetchList(params = {}) { ... }

  return { list, total, loading, fetchList }
})
```

**Setup syntax** (function form) — jak `<script setup>` w komponencie. Zwraca obiekt z refami i funkcjami. To są "public API" store.

Druga forma (Options API):
```typescript
export const useArticleStore = defineStore('articles', {
  state: () => ({ list: [], total: 0 }),
  getters: { totalDoubled: (state) => state.total * 2 },
  actions: { async fetchList() { ... } },
})
```

W tym repo **setup syntax** wszędzie (nowszy, zwięzły, lepszy TypeScript).

Odpowiednik Angular:
```typescript
@Injectable({ providedIn: 'root' })
export class ArticlesStore {
  private _list = signal<Article[]>([]);
  readonly list = this._list.asReadonly();
  private _loading = signal(false);
  readonly loading = this._loading.asReadonly();

  async fetchList(params: any) {
    this._loading.set(true);
    try {
      const data = await api.get('/machines', { params });
      this._list.set(data);
    } finally {
      this._loading.set(false);
    }
  }
}
```

Pinia to to samo, ale z mniejszą boilerplate.

## 2. `ref()` w store = state

```typescript
const list = ref([])
const total = ref(0)
const current = ref(null)
const loading = ref(false)
```

`ref()` w store = reactive state. W komponencie używasz `store.list`, `store.loading` — **bez `.value`** (Pinia auto-unwrap w store, jak Vue w template).

Odpowiednik Angular `signal()` z `asReadonly()` — ale Pinia domyślnie pozwala mutować z zewnątrz (`store.list = [...]`). Angular signal readonly by default.

**Ważne:** Pinia auto-unwrap działa tylko przy dostępie przez `store.xxx`. Jeśli zrobisz `const { list } = store` i potem `list.value` — działa (bo to ref). Ale `list` bez `.value` w JS nie działa. Dlatego w komponentach często `const store = useStore()` i `store.list`.

## 3. `computed()` w store = getters

<ref_snippet file="C:/projects/repos/RaoApp_new/frontend/src/stores/auth.js" lines="11-16" />

```typescript
const isAuthenticated = computed(() => !!token.value)
const isAdmin = computed(() => !!token.value)
```

`computed()` w store = getter. W komponencie `store.isAuthenticated` — działa jak computed (memoizacja).

Odpowiednik Angular `computed(() => this._token() !== null)` z signals.

## 4. Funkcje w store = actions

```typescript
async function fetchList(params = {}) {
  loading.value = true
  try {
    const { data } = await api.get(ep, { params })
    list.value = Array.isArray(data) ? data : (data.items ?? [])
    total.value = Array.isArray(data) ? data.length : (data.total ?? 0)
  } finally {
    loading.value = false
  }
}
```

Funkcje zadeklarowane w store i zwrócone w `return` = actions. Wywołujesz `store.fetchList({...})`. Mogą być async.

**`loading.value = true`** — wewnątrz store używasz `.value` (bo to ref). Z zewnątrz `store.loading` (auto-unwrap).

Odpowiednik Angular metoda w service. Brak dispatch/reducer jak w NgRx — bezpośrednia mutacja stanu. Prostsze, mniej boilerplate.

## 5. `return` — public API store

```typescript
return { list, total, current, loading, fetchList, fetchOne, create, update, remove, duplicate, checkAvailability }
```

Tylko to co w `return` jest dostępne z zewnątrz. Reszta (np. `_endpoint` w `articles.js:14`) jest "prywatne" (konwencja `_` prefix, ale JS nie enforce).

Odpowiednik Angular `public` / `private` — ale w JS nie enforce, konwencja.

## 6. Użycie w komponencie

```typescript
// w komponencie
import { useMachineStore } from '@/stores/machines'
const store = useMachineStore()

onMounted(() => store.fetchList())

// template:
// <tr v-if="store.loading">...</tr>
// <tr v-for="m in store.list" :key="m.id">...</tr>
```

`useMachineStore()` — zwraca instancję store. **Singleton per app** — ten sam store wszędzie. Odpowiednik Angular `@Injectable({ providedIn: 'root' })`.

## 7. Persystencja — `localStorage` ręcznie

<ref_snippet file="C:/projects/repos/RaoApp_new/frontend/src/stores/auth.js" lines="6-26" />

```typescript
const token = ref(localStorage.getItem('rao_token') || null)
// ...
localStorage.setItem('rao_token', data.access_token)
```

Pinia **nie persystuje** domyślnie. Ręcznie czytasz `localStorage` przy init i zapisujesz w action. Odpowiednik Angular — też ręcznie, albo `@ngrx/store-localstorage`.

Alternatywa: `pinia-plugin-persistedstate` — plugin. W tym repo ręcznie (prościej, mniej deps).

## 8. Brak devtools actions/reducers — prostota

NgRx: `actions` → `reducer` → `effect` → `actions`. Pinia: `action` → mutacja `ref`. To **prostsze** ale mniej strukturalne.

**Kiedy NgRx by był lepszy:**
- Złożony state z wielu źródeł
- Time-travel debugging
- Selectors komponowane
- Side effects izolowane

**Kiedy Pinia wystarcza (jak w RAO):**
- CRUD app, state per feature
- Mało cross-feature interactions
- Proste async (fetch, set)

## 9. Multi-store — feature-based

RAO ma osobne store per feature:
- `auth.js` — auth state
- `articles.js` — articles (legacy, deleguje do machines/services)
- `machines.js` — machines
- `contracts.js` — contracts
- `settings.js` — settings
- `analytics.ts` — analytics
- `archive.ts` — archive
- `reservations.ts` — reservations

Każdy store niezależny, importowany gdzie potrzeba. Odpowiednik Angular — osobny service per feature.

## 10. TypeScript vs JS w store

W tym repo mieszanka: `articles.js`, `auth.js` (JS) vs `analytics.ts`, `archive.ts`, `reservations.ts` (TS). TS daje type safety, JS jest zwięzły. Nowszy kod = TS.

W TS store:
```typescript
export const useReservationsStore = defineStore('reservations', () => {
  const list = ref<Reservation[]>([])
  // ...
})
```

`ref<Reservation[]>([])` — typ generic. Jak C# `List<Reservation>`.

## Gotchas dla Angular deva

1. **`ref()` w store = state.** `computed()` = getter. Funkcje = actions. Brak reducer/dispatch.
2. **`store.xxx` auto-unwrap.** Wewnątrz store `.value`, z zewnątrz bez.
3. **Setup syntax** (function form) — nowszy, zwięzły, lepszy TS. Options API istnieje ale nieużywane.
4. **`return` = public API.** Tylko to co w return dostępne z zewnątrz.
5. **Brak persystencji.** `localStorage` ręcznie albo plugin.
6. **Singleton per app.** `useStore()` zwraca tę samą instancję.
7. **Brak devtools time-travel.** Pinia ma devtools ale prostsze niż NgRx.
8. **Bezpośrednia mutacja.** `store.list = [...]` OK. Brak immutability requirement.
9. **Feature-based stores.** Jeden store per feature, jak Angular service.
10. **Mieszanka JS/TS.** Nowszy kod TS, starszy JS. Migracja stopniowa.

## Quiz

1. Czym jest `defineStore('articles', () => { ... })`? (setup syntax — function form store)
2. Czym różni się `ref()` w store od `computed()`? (ref=state mutable, computed=derived memoized)
3. Dlaczego `store.list` działa bez `.value`? (Pinia auto-unwrap przy dostępie przez store)
4. Czym jest `return { list, fetchList }` w store? (public API — tylko to dostępne z zewnątrz)
5. Dlaczego Pinia nie persystuje? (ręcznie localStorage albo plugin — brak built-in)

→ `python learning/quiz/quiz.py --topic pinia --n 5`
