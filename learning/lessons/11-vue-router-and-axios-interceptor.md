# Lekcja 11 — vue-router + Axios interceptor

> Plik bazowy: `frontend/src/router/index.js`, `frontend/src/composables/useApi.js`
> Odpowiednik Angular: Angular Router + HttpInterceptor

vue-router 4 to oficjalny router Vue 3. Axios to HTTP client (zamiast `fetch`). Interceptor Axios = HttpInterceptor Angular. Konceptualnie prawie identyczne.

## Realny snippet z repo — router

<ref_snippet file="C:/projects/repos/RaoApp_new/frontend/src/router/index.js" lines="1-50" />

<ref_snippet file="C:/projects/repos/RaoApp_new/frontend/src/router/index.js" lines="170-199" />

## Realny snippet z repo — Axios interceptor

<ref_snippet file="C:/projects/repos/RaoApp_new/frontend/src/composables/useApi.js" lines="1-32" />

## 1. Route config — lazy-loaded components

```typescript
const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),   // ← lazy
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    component: () => import('@/components/layout/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: 'home', name: 'Home', component: () => import('@/views/HomeView.vue') },
      { path: 'machines', name: 'MachinesList', component: () => import('@/views/MachinesListView.vue') },
      { path: 'machines/:id/edit', name: 'MachineEdit', component: () => import('@/views/MachineFormView.vue'), props: true },
    ],
  },
]
```

`component: () => import(...)` — **lazy loading**. Komponent ładowany przy pierwszej nawigacji. Odpowiednik Angular `loadComponent` / `loadChildren` (standalone).

`children: [...]` — zagnieżdżone route'y. `AppLayout` ma `<router-view>` gdzie renderują się dzieci. Odpowiednik Angular `router-outlet` + child routes.

`path: 'machines/:id/edit'` — path param `:id`. `props: true` — param przekazany jako prop do komponentu. Odpowiednik Angular `:id` + `withComponentInputBinding`.

`meta: { requiresAuth: false }` — metadane route. Używane w guard. Odpowiednik Angular `data: { requiresAuth: false }`.

## 2. `createRouter` + `createWebHistory`

```typescript
const router = createRouter({
  history: createWebHistory('/rao'),
  routes,
})
```

`createWebHistory('/rao')` — HTML5 history mode, base path `/rao`. URL: `/rao/machines`, `/rao/contracts/123/edit`. Bez `#`. Wymaga server config (fallback na index.html).

Odpowiednik Angular `provideRouter(routes, withInMemoryScrolling(...))` + `APP_BASE_HREF: '/rao'`.

Alternatywa: `createWebHashHistory()` — `#/machines` (hash routing, nie wymaga server config). W tym repo `createWebHistory` (czystsze URL).

## 3. `beforeEach` — navigation guard

<ref_snippet file="C:/projects/repos/RaoApp_new/frontend/src/router/index.js" lines="175-193" />

```typescript
router.beforeEach((to, from, next) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth !== false && !auth.isAuthenticated) {
    return next({ name: 'Login', query: { redirect: to.fullPath } })
  }
  if (to.name === 'Login' && auth.isAuthenticated) {
    return next('/')
  }
  next()
})
```

`beforeEach((to, from, next) => ...)` — guard uruchamiany przed każdą nawigacją. `next(...)` — kontynuuj lub przekieruj. Odpowiednik Angular `canActivate` guard (functional form w nowszym Angular).

**`to`** — route docelowy. **`from`** — route źródłowy. **`next`** — callback:
- `next()` — kontynuuj
- `next('/login')` — przekieruj
- `next(false)` — anuluj

W nowszym vue-router można `return` zamiast `next()`:
```typescript
router.beforeEach((to) => {
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'Login', query: { redirect: to.fullPath } }
  }
})
```

W tym repo stare `next()` style.

## 4. `meta` — metadane route

```typescript
meta: { requiresAuth: false }
meta: { requiresAuth: true }
meta: { requiresAdmin: true }
```

`meta` dowolny obiekt. W guard czytasz `to.meta.requiresAuth`. Odpowiednik Angular `data: { ... }` w route.

**Dziedziczenie:** `meta` dziecka merge'uje z `meta` rodzica. Jeśli rodzic `requiresAuth: true`, dzieci dziedziczą chyba że nadpiszą.

## 5. Programmatic navigation

```typescript
router.push({ name: 'MachineNew' })
router.push({ name: 'MachineEdit', params: { id: 123 } })
router.push('/machines')
```

`router.push(...)` — nawigacja. Odpowiednik Angular `router.navigate(['machines', id])` albo `routerLink`.

W template:
```html
<router-link :to="{ name: 'MachineEdit', params: { id: m.id } }}">Edytuj</router-link>
```

`<router-link>` — odpowiednik Angular `routerLink`.

## 6. Axios — HTTP client

```typescript
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/rao/api',
  timeout: 30000,
})
```

`axios.create(config)` — instancja z konfiguracją. `baseURL` — prefix dla wszystkich requestów. `timeout` — 30s. Odpowiednik Angular `HttpClient` z `interceptors`, albo C# `HttpClient` z `BaseAddress`.

`import.meta.env.VITE_API_URL` — env var z Vite. Odpowiednik Angular `environment.ts` / `environment.prod.ts`. Vite czyta `.env` / `.env.production`.

## 7. Request interceptor — dodaj token

<ref_snippet file="C:/projects/repos/RaoApp_new/frontend/src/composables/useApi.js" lines="9-15" />

```typescript
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('rao_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
```

`interceptors.request.use(onFulfilled)` — modyfikuj config przed wysłaniem. Tu: dodaj `Authorization: Bearer <token>` jeśli jest. Odpowiednik Angular `HttpInterceptor`:

```typescript
intercept(req: HttpRequest<any>, next: HttpHandler) {
  const token = localStorage.getItem('rao_token');
  if (token) {
    req = req.clone({ setHeaders: { Authorization: `Bearer ${token}` } });
  }
  return next.handle(req);
}
```

Axios: jeden interceptor przez `interceptors.request.use`. Angular: klasa `HttpInterceptor` + rejestracja w `provideHttpClient(withInterceptors([...]))`.

## 8. Response interceptor — global error handling

<ref_snippet file="C:/projects/repos/RaoApp_new/frontend/src/composables/useApi.js" lines="17-30" />

```typescript
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const isAuthEndpoint = error.config?.url?.startsWith('/auth/')
    if (error.response?.status === 401 && !isAuthEndpoint) {
      localStorage.removeItem('rao_token')
      localStorage.removeItem('rao_user')
      const current = window.location.pathname + window.location.search
      window.location.href = `/rao/login?redirect=${encodeURIComponent(current)}`
    }
    return Promise.reject(error)
  }
)
```

`interceptors.response.use(onFulfilled, onRejected)` — dwa callbacki. `onFulfilled` — modyfikuj response (tu: passthrough). `onRejected` — global error handling.

Tu: jeśli 401 (i nie auth endpoint) → wyczyść token, przekieruj na login. Odpowiednik Angular `HttpInterceptor` sprawdzający `401` w `HttpResponseError`.

**`Promise.reject(error)`** — przekaż error dalej (żeby `.catch` w komponencie go dostał). Jeśli nie `reject`, error "zjedzony".

## 9. Użycie `api` w store/componencie

```typescript
import api from '@/composables/useApi'

const { data } = await api.get('/machines', { params: { search: 'foo' } })
const { data } = await api.post('/machines', payload)
await api.delete(`/machines/${id}`)
```

`api.get/post/put/delete` — odpowiednik Angular `httpClient.get/post/...`. Zwraca `Promise<AxiosResponse<T>>`. `data` — body response.

`{ params: { search: 'foo' } }` — query params. Axios serializuje do `?search=foo`.

## 10. `export default api` — singleton

```typescript
const api = axios.create({ ... })
api.interceptors.request.use(...)
api.interceptors.response.use(...)
export default api
```

`api` tworzone raz przy imporcie modułu. Wszyscy importują tę samą instancję (z interceptorami). Odpowiednik Angular `HttpClient` z `provideHttpClient()` — singleton.

## Gotchas dla Angular deva

1. **`component: () => import(...)` = lazy.** Jak Angular `loadComponent`.
2. **`children` + `<router-view>` = nested routes.** Jak Angular `router-outlet` + child.
3. **`meta` = `data`.** Metadane route, czytane w guard.
4. **`beforeEach` = `canActivate`.** Functional guard w nowszym Angular.
5. **`next()` stare, `return` nowe.** vue-router 4 wspiera oba.
6. **Axios interceptor = HttpInterceptor.** Request i response, jeden obiekt.
7. **`Promise.reject(error)` obowiązkowe.** Inaczej error zjedzony.
8. **`api` singleton przez `export default`.** Jedna instancja z interceptorami.
9. **`import.meta.env.VITE_API_URL` = environment.ts.** Vite env vars.
10. **`createWebHistory` wymaga server fallback.** Bez tego refresh na `/machines` → 404.

## Quiz

1. Co robi `component: () => import(...)` w route? (lazy loading komponentu)
2. Czym jest `beforeEach`? (navigation guard — odpowiednik canActivate)
3. Co robi request interceptor w useApi.js? (dodaje Authorization: Bearer token)
4. Czym jest `meta: { requiresAuth: true }`? (metadane route, czytane w guard)
5. Dlaczego `Promise.reject(error)` w response interceptor? (przekaż error dalej do .catch)

→ `python learning/quiz/quiz.py --topic router --n 5`
