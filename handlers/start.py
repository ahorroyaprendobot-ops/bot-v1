from __future__ import annotations

from keyboards import main_menu
from services.admin_service import is_admin
from services.state_service import clear_state
from telegram_api import send_message


async def show_start(chat_id: int, user_id: int) -> None:
    await clear_state(user_id)
    admin = await is_admin(user_id)
    text = (
        "🤖 ¡Bienvenido al bot de referidos de AhorroYAprendo!\n\n"
        "🎁 Códigos y promos activas\n"
        "💸 Bancos y apps recomendadas\n"
        "⚡ Actualizado constantemente\n\n"
        "📣 Canal: https://t.co/J24uZNpdKT\n"
        "💬 Grupo: https://t.co/bJvMM5GykB\n\n"
        "🐦 X: https://t.co/e6dtvB3qb1\n\n"
        "💙 Bot creado por mi buen amigo Ahorrathor:\n"
        "https://t.co/PFUImjOgHz\n\n"
        "Selecciona una opción 👇"
    )
    await send_message(chat_id, text, main_menu(admin))


async def show_help(chat_id: int) -> None:
    text = (
        "ℹ️ <b>Ayuda</b>\n\n"
        "1. Pulsa <b>🎁 Pedir código</b>.\n"
        "2. Elige una promoción activa.\n"
        "3. Recibirás un código si hay stock disponible.\n\n"
        "Si una promoción no aparece, puede estar pausada o sin configurar."
    )
    await send_message(chat_id, text)
