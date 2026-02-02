"""
Модель для хранения контактной информации администрации
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ContactInfo(Base):
    """Контактная информация администрации"""

    __tablename__ = "contact_info"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Основные контакты
    phone: Mapped[str] = mapped_column(String, nullable=False)
    telegram_username: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str | None] = mapped_column(String, nullable=True)

    # Дополнительная информация
    whatsapp: Mapped[str | None] = mapped_column(String, nullable=True)
    instagram: Mapped[str | None] = mapped_column(String, nullable=True)
    website: Mapped[str | None] = mapped_column(String, nullable=True)

    # Рабочие часы
    working_hours: Mapped[str | None] = mapped_column(String, default="Круглосуточно")

    # Адрес
    address: Mapped[str | None] = mapped_column(String, nullable=True)
