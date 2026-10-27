"""Курс валют з НБУ з запасним варіантом (ручний курс у налаштуваннях)."""
from __future__ import annotations

import json
import logging
import urllib.request

log = logging.getLogger(__name__)
NBU_URL = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?valcode={code}&json"


def fetch_rate(code: str, timeout: float = 10) -> float:
    with urllib.request.urlopen(NBU_URL.format(code=code.upper()), timeout=timeout) as r:
        data = json.loads(r.read().decode("utf-8"))
    if not data or "rate" not in data[0]:
        raise ValueError(f"НБУ не повернув курс для {code}")
    return float(data[0]["rate"])


def get_rates(currencies: set[str], manual: dict[str, float] | None = None, fetch=fetch_rate) -> tuple[dict, dict]:
    """Повертає (курси, джерела). UAH = 1. Ручний курс має пріоритет, якщо заданий."""
    manual = {k.upper(): float(v) for k, v in (manual or {}).items() if v}
    rates, sources = {"UAH": 1.0}, {"UAH": "—"}
    for cur in {c.upper() for c in currencies} - {"UAH"}:
        if cur in manual:
            rates[cur], sources[cur] = manual[cur], "вручну"
            continue
        try:
            rates[cur], sources[cur] = fetch(cur), "НБУ"
        except Exception as e:  # немає інтернету, НБУ недоступний
            raise RuntimeError(
                f"Не вдалося отримати курс {cur} з НБУ ({e}). "
                f"Вкажіть курс вручну в config.json → manual_rates → {cur}") from e
    return rates, sources
