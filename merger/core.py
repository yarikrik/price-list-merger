"""Зведення позицій усіх постачальників: одна деталь — один рядок, найкраща ціна."""
from __future__ import annotations

from dataclasses import dataclass, field

from .readers import Item


@dataclass
class Offer:
    supplier: str
    price_uah: float
    price_orig: float
    currency: str
    stock: int | None
    stock_text: str = ""

    @property
    def available(self) -> bool:
        return self.stock is None or self.stock != 0


@dataclass
class Position:
    article: str
    article_raw: str
    name: str
    brand: str
    offers: dict[str, Offer] = field(default_factory=dict)

    @property
    def best(self) -> Offer:
        """Найдешевша пропозиція серед тих, що є в наявності; якщо ніде немає — просто найдешевша."""
        pool = [o for o in self.offers.values() if o.available] or list(self.offers.values())
        return min(pool, key=lambda o: o.price_uah)

    @property
    def in_stock_anywhere(self) -> bool:
        return any(o.available for o in self.offers.values())

    @property
    def saving(self) -> float:
        """Скільки економимо порівняно з найдорожчою пропозицією."""
        prices = [o.price_uah for o in self.offers.values()]
        return round(max(prices) - self.best.price_uah, 2) if len(prices) > 1 else 0.0


def merge(items: list[Item], rates: dict[str, float], markup_percent: float = 0) -> list[Position]:
    positions: dict[str, Position] = {}
    for it in items:
        rate = rates[it.currency]
        price_uah = round(it.price * rate * (1 + markup_percent / 100), 2)
        pos = positions.get(it.article)
        if pos is None:
            pos = positions[it.article] = Position(it.article, it.article_raw, it.name, it.brand)
        else:  # доповнюємо назву/бренд, якщо в першого постачальника їх не було
            pos.name = pos.name or it.name
            pos.brand = pos.brand or it.brand
        offer = Offer(it.supplier, price_uah, it.price, it.currency, it.stock, it.stock_text)
        prev = pos.offers.get(it.supplier)
        # той самий артикул двічі в одного постачальника — лишаємо дешевший
        if prev is None or offer.price_uah < prev.price_uah:
            pos.offers[it.supplier] = offer
    return sorted(positions.values(), key=lambda p: (p.brand.lower(), p.name.lower(), p.article))
