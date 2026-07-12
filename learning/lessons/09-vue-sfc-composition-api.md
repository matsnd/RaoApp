# Lekcja 09 — Vue SFC + Composition API

> Plik bazowy: `frontend/src/views/MachinesListView.vue`
> Odpowiednik Angular: Angular component (3 pliki: .ts + .html + .css)

Vue 3 SFC (Single File Component) = jeden plik `.vue` z `<template>`, `<script setup>`, `<style>`. Composition API z `<script setup>` to nowszy, zwięzły sposób pisania komponentów — odpowiednik Angular standalone components z `inject`/signals.

## Realny snippet z repo

<ref_snippet file="C:/projects/repos/RaoApp_new/frontend/src/views/MachinesListView.vue" lines="1-120" />

## 1. SFC — 3 sekcje w jednym pliku

```vue
<template>
  <!-- HTML z dyrektywami Vue -->
</template>

<script setup lang="ts">
// TypeScript logika
</script>

<style scoped>
/* CSS tylko dla tego komponentu */
</style>
```

Angular: 3 pliki (`machines-list.component.ts`, `.html`, `.css`). Vue: 1 plik. Zaleta: wszystko razem, łatwiej nawigować. Wada: pliki mogą być duże (`ContractFormView.vue` = 129KB w tym repo).

`<style scoped>` — CSS z atrybutem `data-v-xxx`, nie wycieka. Odpowiednik Angular `encapsulation: ViewEncapsulation.Emulated` (default).

## 2. `<script setup>` — Composition API, bez `export default`

Angular component:
```typescript
@Component({ selector: 'app-machines-list', templateUrl: './machines-list.component.html' })
export class MachinesListComponent implements OnInit {
  search = '';
  constructor(private store: MachinesStore) {}
  ngOnInit() { this.store.fetchList(); }
}
```

Vue `<script setup>`:
```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useMachineStore } from '@/stores/machines'

const search = ref('')
const store = useMachineStore()

onMounted(() => {
  store.fetchList()
})
</script>
```

**Kluczowe:** `<script setup>` to cukier syntaktyczny. Nie ma `export default defineComponent({...})`. Wszystkie top-level deklaracje są **automatycznie dostępne w template**. `search`, `store` — w template używasz `{{ search }}`, `store.list` bez żadnego `this.`.

Odpowiednik Angular standalone component z `signals` (nowoczesny Angular). Vue Composition API było inspiracją dla Angular signals.

## 3. `ref()` — reactive state

```typescript
const search = ref('')
const categoryFilter = ref<number | string>('')
const selectedId = ref<number | null>(null)
```

`ref(value)` — tworzy reactive reference. W JS/script: `search.value` (z `.value`). W template: `search` (bez `.value` — Vue auto-unwrap).

Odpowiednik Angular:
- Stary Angular: `search = ''` (zwykłe pole, ChangeDetection wykrywa przez zone.js)
- Nowy Angular (signals): `search = signal('')` — `search()` w JS, `search` w template

**Vue `ref` ≈ Angular `signal`**. Vue miał to pierwszy (Composition API od Vue 3.0, 2020). Angular signals od Angular 16 (2023).

**Dlaczego `.value`?** `ref()` zwraca obiekt `{ value: T }`. Reaktywność przez Proxy. `.value` triggeruje track/notify. W template Vue auto-unwrap bo wie że to ref.

## 4. `computed()` — derived state

<ref_snippet file="C:/projects/repos/RaoApp_new/frontend/src/stores/auth.js" lines="11-16" />

```typescript
const isAuthenticated = computed(() => !!token.value)
const isAdmin = computed(() => !!token.value)
```

`computed(getter)` — wartość wyliczona, **cachowana**, przeliczana tylko gdy zależności się zmienią. Odpowiednik Angular `computed(() => ...)` z signals, albo pure pipe.

W `MachinesListView.vue` (zakładam, nie cytuję bo długi):
```typescript
const sortedMachines = computed(() => store.list.filter(...).sort(...))
const totalPages = computed(() => Math.ceil(store.total / perPage.value))
```

**Memoizacja:** `computed` przelicza się tylko gdy `store.list` lub `perPage.value` się zmieni. Jeśli nic się nie zmieni, zwraca cachowaną wartość. Odpowiednik Angular `computed` signal — dokładnie ten sam mechanizm.

## 5. `watch()` — side effects na zmianę

```typescript
watch(
  () => [props.dateFrom, props.dateTo],
  ([f, t]) => {
    range.value = [fromISO(f), fromISO(t)]
  },
)
```

`watch(source, callback)` — uruchom callback gdy source się zmieni. Source może być ref, computed, lub getter function `() => x`.

Odpowiednik Angular `effect(() => ...)` z signals, albo `ngOnChanges` (stary).

**Vue `watch` vs `effect`:** `watch` jest explicit (definiujesz source), `effect` auto-track. Vue ma też `watchEffect` (auto-track jak Angular effect). W tym repo `watch` z explicit source.

## 6. Lifecycle hooks

| Vue | Angular | Kiedy |
|-----|---------|-------|
| `onMounted` | `ngOnInit` / `ngAfterViewInit` | Po zamontowaniu w DOM |
| `onUnmounted` | `ngOnDestroy` | Przed zniszczeniem |
| `onUpdated` | `ngAfterViewChecked` | Po update DOM |
| `onBeforeMount` | `ngOnInit` | Przed mount |

W `MachinesListView.vue:102`: `import { ref, computed, onMounted, onUnmounted, watch } from 'vue'`

`onMounted(() => store.fetchList())` — fetch po zamontowaniu. Odpowiednik Angular `ngOnInit`.

`onUnmounted(() => clearInterval(...))` — cleanup. Odpowiednik `ngOnDestroy` / `takeUntilDestroyed`.

## 7. Template dyrektywy — `v-if`, `v-for`, `v-model`, `@click`

<ref_snippet file="C:/projects/repos/RaoApp_new/frontend/src/views/MachinesListView.vue" lines="38-67" />

| Vue | Angular | Co robi |
|-----|---------|---------|
| `v-if="cond"` | `*ngIf="cond"` | Warunkowy render (DOM tworzony/usuwany) |
| `v-else-if`, `v-else` | `*ngIf else` | Else branch |
| `v-for="x in list"` | `*ngFor="let x of list"` | Pętla |
| `:key="x.id"` | `[key]="x.id"` | Track-by dla v-for |
| `v-model="search"` | `[(ngModel)]="search"` | Two-way binding |
| `@click="fn"` | `(click)="fn()"` | Event binding |
| `:class="{ active: x }"` | `[class.active]="x"` | Class binding |
| `:value="x"` | `[value]="x"` | Property binding |
| `{{ x }}` | `{{ x }}` | Interpolation |

**`v-if` vs `v-show`:** `v-if` usuwa z DOM, `v-show` tylko `display:none`. `v-if` jest droższy przy przełączaniu, `v-show` przy initial render.

**`v-model`** to cukier dla `:value` + `@input`. W `MachinesListView.vue:13`: `v-model="search"` → input aktualizuje `search.value`.

## 8. `useRouter()` — programmatic navigation

```typescript
import { useRouter } from 'vue-router'
const router = useRouter()
// ...
router.push({ name: 'MachineNew' })
```

`useRouter()` — composable zwracający instancję routera. `router.push(...)` — nawigacja. Odpowiednik Angular `Router.navigate()` wstrzyknięty przez konstruktor.

## 9. `useStore()` — Pinia store

```typescript
import { useMachineStore } from '@/stores/machines'
const store = useMachineStore()
// store.list, store.total, store.loading, store.fetchList()
```

Pinia store przez composable. Odpowiednik Angular service wstrzyknięty przez DI. Więcej w lekcji 10.

## 10. Brak `this` — wszystko top-level

W `<script setup>` nie ma `this`. Wszystkie zmienne, funkcje, importy są top-level i automatycznie w template. W starym Vue Options API było `this.search`, `this.store` — teraz nie.

Odpowiednik Angular standalone z `inject()` — też nie ma `this` w `inject` pattern.

## Gotchas dla Angular deva

1. **`ref(x)` → `x.value` w JS, `x` w template.** Vue auto-unwrap w template.
2. **`<script setup>` nie ma `export default`.** Top-level = dostępne w template.
3. **`computed` = `signal` + memoization.** Przelicza się tylko gdy zależności zmienią.
4. **`watch` vs `watchEffect`.** `watch` explicit source, `watchEffect` auto-track.
5. **`v-if` usuwa DOM, `v-show` tylko display:none.** Wybieraj wg częstotliwości przełączania.
6. **`v-model` = `:value` + `@input`.** Two-way binding, odpowiednik `[(ngModel)]`.
7. **`:key` w `v-for` obowiązkowe.** Bez tego Vue ostrzega (i ma rację).
8. **Brak `this` w `<script setup>`.** Top-level deklaracje.
9. **Jeden plik `.vue`.** Template + script + style razem. Plusem: nawigacja. Minusem: duże pliki.
10. **`<style scoped>` = ViewEncapsulation.Emulated.** CSS nie wycieka.

## Quiz

1. Czym różni się `ref()` od zwykłej zmiennej? (reactive — triggeruje update, `.value` w JS)
2. Co robi `computed()`? (derived state, memoizacja, przelicza gdy zależności zmienią)
3. Czym jest `<script setup>`? (cukier dla Composition API, top-level = dostępne w template, brak export default)
4. `v-if` vs `v-show`? (v-if usuwa DOM, v-show display:none)
5. Czym jest `watch()`? (side effect na zmianę source — odpowiednik effect/ngOnChanges)

→ `python learning/quiz/quiz.py --topic vue --n 5`
