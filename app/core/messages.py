from typing import Optional
from app.core.config import settings

class Messages:
    """
    Centralized store for user-facing messages.
    Uses settings for dynamic content.
    """

    @property
    def GUEST_WELCOME(self) -> str:
        return (
            f"🏕 <b>Добро пожаловать в «{settings.project_name}»</b>\n\n"
            "Глэмпинг в хвойном лесу рядом с Архызом — тишина, горный воздух "
            "и уют в деревянных домиках. Здесь нет шума посёлка, но до трасс "
            "и водопадов — рукой подать.\n\n"
            "Выберите домик, проверьте даты и забронируйте прямо здесь."
        )

    @property
    def GUEST_LOGIN_PROMPT(self) -> str:
        return (
            f"👋 <b>Добрый день!</b>\n\n"
            f"Чтобы увидеть детали своего бронирования в <b>{settings.project_name}</b>, "
            f"пожалуйста, подтвердите номер телефона."
        )
    
    @property
    def BOOKING_FOUND_TITLE(self) -> str:
        return "✅ <b>Бронь найдена!</b>"

    @property
    def BOOKING_NOT_FOUND(self) -> str:
        return (
            "❌ <b>Бронь не найдена.</b>\n\n"
            "Мы не нашли активных бронирований на этот номер.\n"
            "Если вы бронировали через сторонний сервис, возможно, там указан другой номер.\n\n"
            "Пожалуйста, свяжитесь с администратором."
        )

    @property
    def CONTACT_ADMIN(self) -> str:
        return (
            f"📞 <b>Связь с администратором</b>\n\n"
            f"Если у вас возникли вопросы, напишите нам {settings.contact_admin_username}."
        )

    def payment_instructions(self, amount: int) -> str:
        return (
            f"💳 <b>Оплата бронирования</b>\n\n"
            f"Для оплаты остатка, пожалуйста, переведите сумму {amount}₽ по номеру телефона:\n"
            f"<code>{settings.contact_phone}</code> ({settings.payment_methods})\n"
            f"Получатель: {settings.payment_receiver}\n\n"
            f"После перевода отправьте чек администратору."
        )

    def directions(self, coords: str) -> str:
        return (
            f"🗺 <b>Как добраться</b>\n\n"
            f"📍 <b>Адрес:</b> {settings.project_address}\n\n"
            f"Спокойная локация рядом с Архызом.\n"
            f"Координаты для навигатора:\n<code>{coords}</code>\n"
        )
    
    def wifi_info(self, house_name: str, info: str) -> str:
        return f"📶 <b>Wi-Fi: {house_name}</b>\n\n{info}\n"

    def rules_content(self, rules_text: str) -> str:
        return f"ℹ️ <b>Правила проживания</b>\n\n{rules_text}\n"

    def booking_card(self, house_name: str, check_in: str, check_out: str, guests: int, total: int, paid: int, remainder: int, status_emoji: str) -> str:
        return (
            f"🏠 <b>Ваша бронь: {house_name}</b>\n\n"
            f"📅 <b>Даты:</b> {check_in} — {check_out}\n"
            f"👤 <b>Гости:</b> {guests}\n\n"
            f"💰 <b>Финансы:</b>\n"
            f"Всего: {total}₽\n"
            f"Оплачено: {paid}₽\n"
            f"<b>К оплате: {remainder}₽</b> {status_emoji}\n\n"
            f"📍 <b>Адрес:</b> {settings.project_address}\n"
        )

    def welcome_success(self, user_name: str) -> str:
        return (
            f"✅ <b>Бронь найдена!</b>\n"
            f"Мы рады видеть вас, {user_name}!"
        )

    @property
    def CONTACTS_INFO(self) -> str:
        lines = [
            f"📞 <b>Контакты</b>\n",
            f"🏕 <b>{settings.project_name} · {settings.project_location}</b>",
            f"📍 {settings.project_address}",
            f"",
            f"📱 {settings.contact_phone}",
            f"💬 Telegram: {settings.contact_admin_username}",
        ]
        if settings.contact_website:
            lines.append(f"🌐 {settings.contact_website}")
        lines.append(f"")
        lines.append(f"🕐 {settings.contact_work_hours}")
        return "\n".join(lines)

    @property
    def YANDEX_REVIEWS_URL(self) -> Optional[str]:
        return settings.yandex_reviews_url or None

    @property
    def SITE_URL(self) -> Optional[str]:
        return settings.contact_website or None

    @property
    def ADMIN_PANEL_TITLE(self) -> str:
        return f"🏕 <b>{settings.project_name} · {settings.project_location}</b>\n\nАдминистративная панель"

    @property
    def CONTACT_ADMIN_URL(self) -> str:
        username = settings.contact_admin_username.replace("@", "").strip()
        return f"https://t.me/{username}"

    @property
    def GUEST_MENU_TITLE(self) -> str:
        return f"🏕 <b>{settings.project_name} · {settings.project_location}</b>\n\nГлавное меню"

messages = Messages()
