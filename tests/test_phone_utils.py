from app.utils.phone import normalize_phone, phones_match


def test_normalize_phone():
    assert normalize_phone('+7 (999) 123-45-67') == '79991234567'
    assert normalize_phone('8 999 123 45 67') == '79991234567'
    assert normalize_phone('9991234567') == '79991234567'


def test_phones_match_by_exact_or_last10():
    assert phones_match('+7 (999) 123-45-67', '89991234567')
    assert phones_match('9991234567', '+7 999 123 45 67')
    assert not phones_match('79991234567', '79991234568')
