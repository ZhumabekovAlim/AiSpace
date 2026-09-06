"""Фиксированный каталог допов к брони (вода, кофе и т.п.).

Хранится в коде намеренно: набор небольшой и меняется редко. В брони пишутся
только id допов; отдаём каталог фронту эндпоинтом GET /amenities.
"""
from typing import Final

# id -> (человекочитаемое название, эмодзи-иконка)
AMENITIES: Final[dict[str, tuple[str, str]]] = {
    "water": ("Вода", "💧"),
    "coffee": ("Кофе", "☕"),
    "tea": ("Чай", "🍵"),
    "snacks": ("Снеки", "🍪"),
    "projector": ("Проектор", "📽️"),
    "whiteboard": ("Маркерная доска", "📋"),
}

AMENITY_IDS: Final[frozenset[str]] = frozenset(AMENITIES)


def catalog() -> list[dict[str, str]]:
    return [
        {"id": key, "label": label, "icon": icon}
        for key, (label, icon) in AMENITIES.items()
    ]
