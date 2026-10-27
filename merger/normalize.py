"""Нормалізація даних з прайсів: артикули, ціни, наявність."""
from __future__ import annotations

import re

_ARTICLE_JUNK = re.compile(r"[\s\-_./\\]+")
_PRICE_JUNK = re.compile(r"[^\d,.\-]")


def normalize_article(value) -> str:
    """'ab-123 / 45' → 'AB12345'. Однакові деталі з різним написанням зводяться до одного ключа."""
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return _ARTICLE_JUNK.sub("", str(value)).upper()


def parse_price(value) -> float | None:
    """Розуміє 1234.5, '1 234,50', '$12.5', '12,5 грн', '1.234,50'. Повертає None, якщо ціни немає."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value) if value > 0 else None
    s = _PRICE_JUNK.sub("", str(value).replace(" ", ""))
    if not s or not re.search(r"\d", s):
        return None
    if "," in s and "." in s:
        # 1.234,50 (європейський) або 1,234.50 (американський) — роздільник дробу той, що останній
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        price = float(s)
    except ValueError:
        return None
    return price if price > 0 else None


_YES = {"є", "+", "так", "yes", "в наявності", "наявність", "есть", "в наличии", "да", "true", "склад", "y"}
_NO = {"немає", "-", "ні", "no", "нет", "відсутній", "нема", "0", "false", "під замовлення", "под заказ", "n", ""}


def parse_stock(value) -> int | None:
    """Наявність → кількість. Невідома кількість, але «є» → -1. Немає → 0. Не вказано → None."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return max(int(value), 0)
    s = str(value).strip().lower()
    if s in _YES:
        return -1
    if s in _NO:
        return 0
    m = re.search(r"\d+", s)
    if m:
        n = int(m.group())
        if s.startswith((">", "більше", "больше", "понад")):
            return n + 1
        return n
    return None


def stock_label(qty: int | None, raw=None) -> str:
    """Підпис наявності для звіту. Діапазони на кшталт «>10» залишаємо як у прайсі."""
    if isinstance(raw, str) and raw.strip() and raw.strip()[0] in "><" and qty:
        return raw.strip()
    if qty is None:
        return "?"
    if qty == -1:
        return "є"
    if qty == 0:
        return "немає"
    return str(qty)
