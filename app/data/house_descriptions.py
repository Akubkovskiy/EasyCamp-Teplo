"""
Описания домиков — единый источник для бота и API.
Чтобы изменить описание — правим здесь, подхватится везде.

Поиск: по точному имени, по подстроке ("1" в "Тепло 1"), по алиасам.
Приоритет: curated catalog > DB description (если DB не авто-генерация).
"""

from typing import Optional


# Маркеры авто-сгенерированных / внутренних описаний — не показываем гостям.
_INTERNAL_MARKERS = [
    "автоматически создан",
    "auto-generated",
    "avito sync",
    "test",
]

# Данные домиков: ключ = каноническое имя, алиасы для гибкого поиска
_HOUSES = {
    "Тепло 1": {
        "aliases": ["тепло 1", "тепло1", "teplo 1", "teplo1", "домик 1", "forest", "лесной", "дом 1"],
        "short": (
            "34 м² · до 4 гостей · терраса с видом на горы\n"
            "Лесной домик в стороне от суеты. Тишина, сосны, чистый горный воздух."
        ),
        "full": (
            "🌲 <b>Лесной домик · 34 м²</b>\n\n"
            "Уютный деревянный домик в хвойном лесу — с верандой и видом на горы Архызской долины. "
            "Расположен в стороне от посёлка: здесь не слышно машин, зато слышно птиц.\n\n"
            "<b>Удобства:</b>\n"
            "• Двуспальная кровать + диван\n"
            "• Горячий душ и туалет внутри\n"
            "• Мини-кухня с чайником и посудой\n"
            "• Wi‑Fi · постельное бельё · полотенца\n"
            "• Терраса с видом · мангальная зона · парковка\n\n"
            "До центра Архыза — 5 минут на машине. До горнолыжных трасс — 12 км."
        ),
        "capacity": 4,
        "area": 34,
    },
    "Тепло 2": {
        "aliases": ["тепло 2", "тепло2", "teplo 2", "teplo2", "домик 2", "family", "семейный", "дом 2"],
        "short": (
            "40 м² · до 6 гостей · две спальни\n"
            "Просторный семейный домик с отдельными комнатами и большой террасой."
        ),
        "full": (
            "🏡 <b>Семейный домик · 40 м²</b>\n\n"
            "Два отдельных спальных пространства, большая терраса и зона отдыха — "
            "идеально для семьи или небольшой компании. Больше места, больше свободы.\n\n"
            "<b>Удобства:</b>\n"
            "• Две спальные зоны (спальня + гостиная-спальня)\n"
            "• Горячий душ и туалет внутри\n"
            "• Кухня с плитой, посудой и холодильником\n"
            "• Wi‑Fi · постельное бельё · полотенца\n"
            "• Просторная терраса · мангальная зона · парковка\n\n"
            "До центра Архыза — 5 минут на машине. До горнолыжных трасс — 12 км."
        ),
        "capacity": 6,
        "area": 40,
    },
    "Тепло 3": {
        "aliases": ["тепло 3", "тепло3", "teplo 3", "teplo3", "домик 3", "compact", "компактный", "дом 3"],
        "short": (
            "32 м² · до 4 гостей · для двоих или пары\n"
            "Компактный и уютный — всё необходимое в одном пространстве."
        ),
        "full": (
            "🪵 <b>Компактный домик · 32 м²</b>\n\n"
            "Практичный формат для пары или небольшой компании: всё необходимое "
            "без лишнего — максимум уюта на минимум площади.\n\n"
            "<b>Удобства:</b>\n"
            "• Двуспальная кровать\n"
            "• Горячий душ и туалет внутри\n"
            "• Мини-кухня с чайником и посудой\n"
            "• Wi‑Fi · постельное бельё · полотенца\n"
            "• Терраса · мангальная зона · парковка\n\n"
            "До центра Архыза — 5 минут на машине. До горнолыжных трасс — 12 км."
        ),
        "capacity": 4,
        "area": 32,
    },
}

# Общие удобства базы
COMMON_AMENITIES = [
    "Wi‑Fi и горячая вода",
    "Постельное бельё и полотенца",
    "Кухонная зона и посуда",
    "Мангальная зона и парковка",
    "Горный воздух и тишина леса",
]


def _find_house(house_name: str) -> Optional[dict]:
    """Ищем домик по имени: точное совпадение → алиасы → подстрока → цифра."""
    if not house_name:
        return None
    name_lower = house_name.strip().lower()

    for key, data in _HOUSES.items():
        if key.lower() == name_lower:
            return data

    for key, data in _HOUSES.items():
        if name_lower in data["aliases"]:
            return data

    for key, data in _HOUSES.items():
        if key.lower() in name_lower or name_lower in key.lower():
            return data

    for ch in name_lower:
        if ch.isdigit():
            idx = int(ch)
            keys = list(_HOUSES.keys())
            if 1 <= idx <= len(keys):
                return _HOUSES[keys[idx - 1]]
            break

    return None


def _is_internal_description(text: str) -> bool:
    """True если описание авто-сгенерированное или внутреннее (не для гостей)."""
    lower = text.strip().lower()
    return any(marker in lower for marker in _INTERNAL_MARKERS)


def get_display_description(house_name: str, db_description: Optional[str] = None) -> str:
    """
    Лучшее описание для показа гостям.
    Приоритет: curated catalog short > db description (если не авто) > ""
    """
    catalog = get_short_description(house_name)
    if catalog:
        return catalog
    if db_description and not _is_internal_description(db_description):
        return db_description
    return ""


def get_short_description(house_name: str) -> str:
    """Краткое описание (для карточек, каталога)."""
    data = _find_house(house_name)
    return data["short"] if data else ""


def get_full_description(house_name: str) -> str:
    """Полное описание (для детальной карточки)."""
    data = _find_house(house_name)
    return data["full"] if data else ""


def get_house_data(house_name: str) -> Optional[dict]:
    """Все данные по домику (short, full, capacity, area, aliases)."""
    return _find_house(house_name)
