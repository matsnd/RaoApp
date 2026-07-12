#!/usr/bin/env python3
"""Learn-By-Code quiz CLI dla RAO.

Interaktywny quiz w terminalu — pyta, sprawdza, daje feedback z linkiem do pliku.

Użycie:
    python learning/quiz/quiz.py                      # 10 losowych pytań
    python learning/quiz/quiz.py --topic vue          # 10 pytań z tematu
    python learning/quiz/quiz.py --topic vue --n 5    # 5 pytań z tematu
    python learning/quiz/quiz.py --all                # wszystkie po kolei
    python learning/quiz/quiz.py --history            # historia wyników

Wymaga: pyyaml (dostępny w backend/.venv).
Uruchamiaj z venva backendu:
    .\\backend\\.venv\\Scripts\\python.exe learning\\quiz\\quiz.py
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import datetime
from pathlib import Path

# Windows console default encoding (cp1250/cp852) nie wspiera emoji.
# Reconfigure na UTF-8 żeby 🧠✅❌💡 działały bez PYTHONIOENCODING.
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

try:
    import yaml
except ImportError:
    print("Brak pyyaml. Użyj venva backendu:")
    print("  .\\backend\\.venv\\Scripts\\python.exe learning\\quiz\\quiz.py")
    print("Albo: pip install pyyaml")
    sys.exit(1)


HERE = Path(__file__).parent
QUESTIONS_FILE = HERE / "questions.yaml"
HISTORY_FILE = HERE / ".history.json"
REPO_ROOT = HERE.parent.parent  # C:/projects/repos/RaoApp_new

TOPICS = [
    "python", "sqlalchemy", "pydantic", "fastapi", "di", "async",
    "service", "migrations", "vue", "pinia", "router", "props",
]


def load_questions() -> list[dict]:
    with open(QUESTIONS_FILE, encoding="utf-8") as f:
        return yaml.safe_load(f)


def pick_questions(all_q: list[dict], topic: str | None, n: int, all_mode: bool) -> list[dict]:
    pool = [q for q in all_q if (topic is None or q["topic"] == topic)]
    if not pool:
        print(f"Brak pytań dla tematu '{topic}'. Dostępne: {', '.join(TOPICS)}")
        sys.exit(1)
    if all_mode:
        return pool
    if n >= len(pool):
        return pool
    return random.sample(pool, n)


def ask_one(q: dict, idx: int, total: int) -> bool:
    """Pytaj jedno pytanie. Zwróć True jeśli poprawnie."""
    print(f"\n{'='*70}")
    print(f"[{idx}/{total}] ({q['topic']}) {q['question']}")
    print(f"{'='*70}")
    letters = "ABCD"
    for i, opt in enumerate(q["options"]):
        print(f"  {letters[i]}) {opt}")

    while True:
        raw = input("\nTwoja odpowiedź (A/B/C/D, s=skip, q=quit): ").strip().upper()
        if raw == "Q":
            print("\nPrzerwano.")
            sys.exit(0)
        if raw == "S":
            print(f"\n  ⏭  Skip. Poprawna: {letters[q['answer']]}) {q['options'][q['answer']]}")
            print(f"  Wyjaśnienie: {q['explanation']}")
            if q.get("ref"):
                print(f"  📁 {q['ref']}")
            return False
        if raw in letters[: len(q["options"])]:
            chosen = letters.index(raw)
            break
        print("  Wpisz A/B/C/D/s/q.")

    correct = chosen == q["answer"]
    if correct:
        print(f"\n  ✅ Poprawnie! {letters[q['answer']]}) {q['options'][q['answer']]}")
    else:
        print(f"\n  ❌ Błąd. Twoja: {letters[chosen]}) {q['options'][chosen]}")
        print(f"  Poprawna: {letters[q['answer']]}) {q['options'][q['answer']]}")
    print(f"  💡 {q['explanation']}")
    if q.get("ref"):
        print(f"  📁 {q['ref']}")
    return correct


def save_history(score: int, total: int, topic: str | None) -> None:
    history = []
    if HISTORY_FILE.exists():
        try:
            history = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            history = []
    history.append({
        "date": datetime.now().isoformat(timespec="seconds"),
        "score": score,
        "total": total,
        "topic": topic or "all",
        "pct": round(score / total * 100, 1) if total else 0,
    })
    # keep last 100
    history = history[-100:]
    HISTORY_FILE.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")


def show_history() -> None:
    if not HISTORY_FILE.exists():
        print("Brak historii. Odpal quiz najpierw.")
        return
    history = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    if not history:
        print("Brak historii.")
        return
    print(f"\n{'='*60}\nHistoria wyników ({len(history)} ostatnich)\n{'='*60}")
    print(f"{'Data':<22}{'Temat':<10}{'Wynik':<10}{'%':<8}")
    print("-" * 60)
    for h in history[-20:]:
        date = h["date"][:19].replace("T", " ")
        print(f"{date:<22}{h['topic']:<10}{h['score']}/{h['total']:<6}{h['pct']}%")
    # aggregate
    all_scores = [h["pct"] for h in history]
    avg = sum(all_scores) / len(all_scores) if all_scores else 0
    print("-" * 60)
    print(f"Średni wynik: {avg:.1f}%  |  Sesji: {len(history)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Learn-By-Code quiz CLI dla RAO")
    parser.add_argument("--topic", choices=TOPICS + [None], default=None,
                        help="Tylko pytania z tematu")
    parser.add_argument("--n", type=int, default=10,
                        help="Liczba pytań w sesji (domyślnie 10)")
    parser.add_argument("--all", action="store_true",
                        help="Wszystkie pytania po kolei (ignoruje --n)")
    parser.add_argument("--history", action="store_true",
                        help="Pokaż historię wyników i wyjdź")
    args = parser.parse_args()

    if args.history:
        show_history()
        return

    questions = load_questions()
    picked = pick_questions(questions, args.topic, args.n, args.all)

    print(f"\n🧠 Learn-By-Code quiz — RAO")
    print(f"   Temat: {args.topic or 'wszystkie'} | Pytań: {len(picked)}")
    print(f"   (s=skip, q=quit)\n")

    score = 0
    for i, q in enumerate(picked, 1):
        if ask_one(q, i, len(picked)):
            score += 1

    pct = round(score / len(picked) * 100, 1) if picked else 0
    print(f"\n{'='*70}")
    print(f"  Wynik: {score}/{len(picked)}  ({pct}%)")
    print(f"{'='*70}")
    if pct == 100:
        print("  🏆 Perfekcyjnie!")
    elif pct >= 80:
        print("  🎉 Bardzo dobrze!")
    elif pct >= 60:
        print("  👍 OK, ale powtarzaj.")
    else:
        print("  📚 Przeczytaj lekcje i spróbuj jeszcze raz.")

    save_history(score, len(picked), args.topic)
    print(f"\n  Historia zapisana. Zobacz: python learning/quiz/quiz.py --history")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nPrzerwano.")
        sys.exit(0)
