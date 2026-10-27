"""Зведення прайсів постачальників в один Excel-файл.

Використання:
    python merge_prices.py                 — взяти прайси з папки input/, результат у output/
    python merge_prices.py --rate USD=41.5 — вказати курс вручну (без запиту до НБУ)
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from merger.core import merge
from merger.nbu import get_rates
from merger.readers import find_file, read_supplier
from merger.writer import write_report

# Папка програми: поруч з .exe (якщо зібрано PyInstaller) або поруч зі скриптом
BASE = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent


def load_config(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.exit(f"❌ Не знайдено {path}. Скопіюйте config.example.json у config.json і налаштуйте постачальників.")
    except json.JSONDecodeError as e:
        sys.exit(f"❌ Помилка в {path.name}, рядок {e.lineno}: {e.msg}")


def run(base: Path, manual_rates: dict | None = None, fetch=None) -> Path:
    cfg = load_config(base / "config.json")
    input_dir = base / cfg.get("input_folder", "input")
    output_dir = base / cfg.get("output_folder", "output")
    output_dir.mkdir(parents=True, exist_ok=True)

    results, missing = [], []
    for sup in cfg["suppliers"]:
        path = find_file(input_dir, sup["file"])
        if path is None:
            missing.append(f"{sup['name']} (шаблон {sup['file']})")
            continue
        res = read_supplier(path, sup)
        results.append(res)
        status = f"{len(res.items)} позицій" + (f", пропущено {res.skipped}" if res.skipped else "")
        print(f"  ✓ {sup['name']}: {path.name} — {status}")
        for e in res.errors:
            print(f"    ⚠ {e}")
    for m in missing:
        print(f"  ✗ {m}: файл не знайдено в {input_dir.name}/")
    items = [it for r in results for it in r.items]
    if not items:
        sys.exit("❌ Немає жодної позиції для зведення. Перевірте папку input/ і config.json.")

    rates_manual = {**cfg.get("manual_rates", {}), **(manual_rates or {})}
    kwargs = {"fetch": fetch} if fetch else {}
    rates, sources = get_rates({it.currency for it in items}, rates_manual, **kwargs)
    for cur, r in rates.items():
        if cur != "UAH":
            print(f"  💱 {cur}: {r:.4f} грн ({sources[cur]})")

    markup = float(cfg.get("markup_percent", 0))
    positions = merge(items, rates, markup)
    out = output_dir / f"Зведений_прайс_{datetime.now():%Y-%m-%d_%H-%M}.xlsx"
    write_report(out, positions, [s["name"] for s in cfg["suppliers"]], results, rates, sources, markup)
    multi = sum(1 for p in positions if len(p.offers) > 1)
    print(f"\n✅ Готово: {len(positions)} унікальних позицій ({multi} — у кількох постачальників)\n   {out}")
    return out


def main():
    ap = argparse.ArgumentParser(description="Зведення прайсів постачальників")
    ap.add_argument("--rate", action="append", default=[], help="Курс вручну, напр. --rate USD=41.5")
    args = ap.parse_args()
    manual = {}
    for r in args.rate:
        cur, _, val = r.partition("=")
        manual[cur.strip().upper()] = float(val.replace(",", "."))
    print("📦 Зведення прайсів\n")
    try:
        run(BASE, manual)
    except RuntimeError as e:
        sys.exit(f"❌ {e}")


if __name__ == "__main__":
    main()
    if getattr(sys, "frozen", False):
        input("\nНатисніть Enter, щоб закрити…")
