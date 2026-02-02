from app.core.config import settings

class Messages:
    """
    Centralized store for user-facing messages.
    Uses settings for dynamic content.
    """

    @property
    def GUEST_WELCOME(self) -> str:
        return "🏕 <b>Добро пожаловать домой!</b>\n\nВы в меню гостя. Здесь вся информация о вашем отдыхе."

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
            f"Мы находимся в живописном месте.\n"
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
        return (
            f"📞 <b>Контакты администрации</b>\n\n"
            f"🏕 <b>{settings.project_name} · {settings.project_location}</b>\n\n"
            f"📱 Телефон: {settings.contact_phone}\n"
            f"💬 Telegram: {settings.contact_admin_username}\n"
            f"📧 Email: {settings.contact_email}\n\n"
            f"🕐 Режим работы: {settings.contact_work_hours}\n"
            f"📍 Адрес: {settings.project_address}\n\n"
            "Мы всегда рады помочь! 🤗"
        )

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
