# Lekcja 01 — Python basics for C# dev

> Plik bazowy: `backend/articles/schemas.py`
> Odpowiednik .NET: C# type system, async/await, records

Python w tym repo to **Python 3.14** z type hintingiem i async. Jeśli znasz C#, 80% semantyki już rozumiesz — różni się głównie składnia i kilka idiomów.

## Realny snippet z repo

<ref_snippet file="C:/projects/repos/RaoApp_new/backend/articles/schemas.py" lines="1-46" />

## 1. Indent-sensitivity — blok zamiast `{ }`

W C# blok definiujesz klamrami:
```csharp
public class Foo {
    public int Bar() {
        if (x > 0) {
            return x;
        }
        return 0;
    }
}
```

W Pythonie **indentacja JEST składnią**. Klamr nie ma:
```python
class Foo:
    def bar(self) -> int:
        if x > 0:
            return x
        return 0
```

**Kluczowe:** 4 spacje (nie tab!). Mieszanie tab + spaces = `IndentationError`. W tym repo jest to ustandaryzowane (black/ruff).

## 2. Type hints — `str | None` zamiast `string?`

C# 12 nullable reference types:
```csharp
string? name = null;        // może być null
string name = "x";          // nie-null (warning jeśli NRT włączone)
int? age = null;            // Nullable<int>
```

Python (PEP 604, Python 3.10+):
```python
name: str | None = None     # może być None (odpowiednik string?)
name: str = "x"             # nie oznacza "nie-null" — to tylko hint!
age: int | None = None      # odpowiednik int?
```

**Kluczowa różnica:** Python type hints są **opcjonalne i nieegzekwowane w runtime** (domyślnie). To dokumentacja + narzędzia (mypy, pyright). C# NRT są egzekwowane przez kompilator jako warningi.

W `schemas.py` widzisz:
```python
internal_number: str | None         # pole może być null
is_service: bool = False            # default False
replacement_value: Decimal | None   # Decimal = odpowiednik C# decimal
```

`Decimal` z Pythona = `decimal` z C# (precyzja finansowa, NIE `float`).

## 3. `class Config` i `from_attributes` (Pydantic-specific, ale warto tu)

W `schemas.py:45-46`:
```python
class Config:
    from_attributes = True
```

To Pydantic v2 sposób na "mapuj z obiektu po atrybutach" (ORM mode). Odpowiednik C# `MapFrom` w AutoMapper. Wrócimy do tego w lekcji 03.

## 4. `async` / `await` — Task → coroutine

C#:
```csharp
public async Task<User> GetUserAsync(int id)
{
    return await _db.Users.FindAsync(id);
}
```

Python:
```python
async def get_user(db: AsyncSession, user_id: int) -> User:
    return await db.get(User, user_id)
```

**Różnice pod spodem:**

| C# | Python |
|----|--------|
| `Task<T>` — obiekt reprezentujący przyszłą wartość | `Coroutine` — funkcja, którą trzeba `await`ować lub zaplanować |
| `async/await` kompiluje się do state machine | `async/await` kompiluje się do generatora (PEP 492) |
| ThreadPool / TaskScheduler | **Event loop** (asyncio) — single-threaded cooperative |
| `.Result`, `.Wait()` — sync-block (deadlock risk) | **Nie ma** — musisz `await`, nie da się sync-block |
| `Task.WhenAll` | `asyncio.gather` |
| `Task.Delay` | `asyncio.sleep` |

**Najważniejsze:** Python async jest **single-threaded cooperative**. Jeden event loop, jeden wątek. Brak preemptive scheduling. Jeśli zablokujesz event loop `time.sleep(5)` (zamiast `await asyncio.sleep(5)`), cały serwer stoi na 5s.

W FastAPI wszystkie endpointy są `async def` — FastAPI je planuje na event loopie. Jeśli zrobisz sync `def`, FastAPI wrzuci to do threadpoola (threadpool per request), ale to antywzorzec w tym repo.

## 5. `str | None` vs `Optional[str]` — dwa zapisy, to samo

```python
from typing import Optional
x: Optional[str] = None      # Python 3.5+

# PEP 604 (Python 3.10+):
x: str | None = None         # nowszy, czytelniejszy
```

W repo widać mieszankę — `Optional[str]` w starszym kodzie, `str | None` w nowszym. To **to samo**. `str | None` to cukier syntaktyczny dla `Union[str, None]`.

## 6. List/dict comprehensions — zamiast LINQ

C# LINQ:
```csharp
var ids = articles.Where(a => a.IsActive).Select(a => a.Id).ToList();
var map = articles.ToDictionary(a => a.Id, a => a.Name);
```

Python:
```python
ids = [a.id for a in articles if a.is_active]
map = {a.id: a.name for a in articles}
```

W `service.py:49-51` widzisz realny przykład:
```python
article_ids = [a.id for a in articles]
category_ids = {a.category_id for a in articles if a.category_id}  # set comprehension
owner_ids = {a.owner_id for a in articles if a.owner_id}
```

`{...}` to **set comprehension** (kolekcja unikalnych). `[...]` to list comprehension. `{k: v for ...}` to dict comprehension.

## 7. f-strings — zamiast `$"..."` / string interpolation

C#:
```csharp
$"Hello {name}, age {age + 1}"
```

Python:
```python
f"Hello {name}, age {age + 1}"
```

W `service.py:33`:
```python
stmt = stmt.where(Article.name.ilike(f"%{search}%"))
```

f-string = string z prefixem `f`, wyrażenia w `{}`. Działa od Python 3.6.

## 8. `self` zamiast `this` — i musi być jawny

C#:
```csharp
class Foo {
    private int _x;
    public void Bar() { _x = 5; }   // this niejawne
}
```

Python:
```python
class Foo:
    def __init__(self) -> None:
        self.x = 0          # instancja, MUSI być self.
    def bar(self) -> None:
        self.x = 5          # self jawny
```

`self` to pierwszy parametr każdej metody instancji. **Nie da się pominąć** (w przeciwieństwie do `this` w C#). To konwencja, nie keyword — możesz nazwać `this`, ale nikt tak nie robi.

`__init__` to konstruktor (odpowiednik C# ctor). Nie ma overloadingu — jeden konstruktor per klasa.

## 9. `__init__.py` — co to jest?

Widzisz puste `__init__.py` w każdym folderze `backend/<feature>/`. To **marker pakietu**. W C# namespace jest implikowany przez folder, w Pythonie pakiet = folder z `__init__.py`.

Od Python 3.3+ puste `__init__.py` nie jest wymagane (implicit namespace packages), ale w tym repo jest dla jasności.

Import:
```python
from articles.models import Article      # articles/models.py → class Article
from articles.schemas import ArticleCreate
```

Odpowiednik C# `using Articles.Models;` — ale w Pythonie importujesz **konkretne symbole**, nie całą przestrzeń.

## 10. `if __name__ == "__main__":` — entry point

C# ma `static void Main()`. Python:
```python
if __name__ == "__main__":
    uvicorn.run(main:app, port=8000)
```

`__name__` to string. Jeśli plik uruchomiony bezpośrednio (`python main.py`), `__name__ == "__main__"`. Jeśli zaimportowany, `__name__ == "main"` (nazwa modułu). To pozwala plikowi być zarówno skryptem, jak i modułem importowanym.

FastAPI w tym repo jest uruchamiany przez `uvicorn main:app` — `main` to moduł, `app` to obiekt FastAPI w nim. Nie wchodzi w `if __name__` blok.

## Gotchas dla .NET deva

1. **`None` nie jest `null`.** `None` to singleton obiektu `NoneType`. `is None` zamiast `== None` (PEP 8).
2. **`True`/`False` z wielkiej litery.** Nie `true`/`false`.
3. **Brak overloadingu metod.** Używa się default args: `def foo(a, b=10, c=None)`.
4. **`len(x)` zamiast `x.Length`/`x.Count`.** `len()` to wbudowana funkcja.
5. **`dict` = `Dictionary`, ale składnia `{k: v}`.** `list` = `List`, składnia `[...]`.
6. **`for x in coll:` zamiast `foreach`.** `for (int i...)` → `for i in range(10):`.
7. **Nie ma `interface`!** Python ma duck typing + ABC (abstract base class) opcjonalnie. W repo nie ma interfejsów — kontrakty przez konwencję.
8. **`mutability`:** `list` jest mutable, `tuple` immutable. `dict` mutable, `frozendict` (3.12+) / `MappingProxyType` immutable.
9. **`==` vs `is`:** `==` porównuje wartość, `is` tożsamość obiektu. `a == b` może być True gdy `a is b` False. Dla `None` zawsze `is None`.
10. **GIL (Global Interpreter Lock):** Python threads nie mogą równolegle wykonywać Python bytecode. Dlatego async (cooperative) > threads dla I/O. CPU-bound → multiprocessing.

## Quiz (znajdziesz w `quiz.py`)

1. Czym jest `str | None` w Pythonie? (odp: składnia PEP 604 dla `Union[str, None]` / `Optional[str]`)
2. Czym różni się Python async od C# async? (odp: single-threaded event loop, brak `.Result`)
3. Co robi `if __name__ == "__main__":`? (odp: kod uruchamiany tylko gdy plik jest skryptem, nie importem)
4. Czym jest `self`? (odp: jawny pierwszy parametr metody instancji, odpowiednik niejawnego `this`)
5. Dlaczego `time.sleep(5)` w async endpoint jest katastrofą? (odp: blokuje event loop, cały serwer stoi)

→ `python learning/quiz/quiz.py --topic python --n 5`
