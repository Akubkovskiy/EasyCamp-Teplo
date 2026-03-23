from types import SimpleNamespace

from app.services.avito_sync_service import extract_avito_contact_field
from app.services.booking_service import extract_avito_contact_value


class PayloadWithDictContact:
    def __init__(self, contact=None, guest_name=None, guest_phone=None):
        self.contact = contact
        self.guest_name = guest_name
        self.guest_phone = guest_phone


def test_booking_service_extracts_name_from_dict_contact():
    payload = PayloadWithDictContact(contact={"name": "Иван Иванов", "phone": "+79990000001"})

    assert extract_avito_contact_value(payload, "name") == "Иван Иванов"
    assert extract_avito_contact_value(payload, "phone") == "+79990000001"


def test_booking_service_falls_back_to_legacy_top_level_fields():
    payload = PayloadWithDictContact(contact={}, guest_name="Мария", guest_phone="+79990000002")

    assert extract_avito_contact_value(payload, "name") == "Мария"
    assert extract_avito_contact_value(payload, "phone") == "+79990000002"


def test_booking_service_supports_object_contact():
    payload = PayloadWithDictContact(contact=SimpleNamespace(name="Пётр", phone="+79990000003"))

    assert extract_avito_contact_value(payload, "name") == "Пётр"
    assert extract_avito_contact_value(payload, "phone") == "+79990000003"


def test_sync_service_extracts_name_from_dict_contact():
    booking_data = {
        "contact": {"name": "Ольга", "phone": "+79990000004"},
    }

    assert extract_avito_contact_field(booking_data, "name") == "Ольга"
    assert extract_avito_contact_field(booking_data, "phone") == "+79990000004"


def test_sync_service_falls_back_to_legacy_top_level_fields():
    booking_data = {
        "guest_name": "Сергей",
        "guest_phone": "+79990000005",
    }

    assert extract_avito_contact_field(booking_data, "name") == "Сергей"
    assert extract_avito_contact_field(booking_data, "phone") == "+79990000005"

