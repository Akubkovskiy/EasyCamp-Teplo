import re


def normalize_phone(raw: str | None) -> str:
    if not raw:
        return ""
    p = re.sub(r"[^0-9]", "", raw)
    if p.startswith("8") and len(p) == 11:
        p = "7" + p[1:]
    if len(p) == 10:
        p = "7" + p
    return p


def phone_last10(raw: str | None) -> str:
    p = normalize_phone(raw)
    return p[-10:] if len(p) >= 10 else p


def phones_match(a: str | None, b: str | None) -> bool:
    na = normalize_phone(a)
    nb = normalize_phone(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    return phone_last10(na) == phone_last10(nb)
