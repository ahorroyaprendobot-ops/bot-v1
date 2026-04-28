from __future__ import annotations

from keyboards import inline_keyboard, main_menu
from services.admin_service import is_admin
from services.categories_service import get_category, list_categories
from services.subcategories_service import get_subcategory, list_subcategories
from services.codes_service import deliver_code
from telegram_api import edit_message, esc, send_message


async def show_categories(chat_id: int, message_id: int | None = None) -> None:
    categories = await list_categories(active_only=True)
    if not categories:
        text = "Ahora mismo no hay promociones disponibles."
        if message_id:
            await edit_message(chat_id, message_id, text)
        else:
            await send_message(chat_id, text)
        return

    rows = [[(f"📁 {cat['name']}", f"user:cat:{cat['id']}")] for cat in categories]
    rows.append([("⬅️ Volver", "start")])
    text = "Elige una categoría:"
    if message_id:
        await edit_message(chat_id, message_id, text, inline_keyboard(rows))
    else:
        await send_message(chat_id, text, inline_keyboard(rows))


async def show_subcategories(chat_id: int, message_id: int | None, category_id: int) -> None:
    category = await get_category(category_id)
    if not category or not category["is_active"]:
        await send_message(chat_id, "Esta categoría ya no está disponible. Vuelve al inicio con /start.")
        return

    subcategories = await list_subcategories(category_id, active_only=True)
    if not subcategories:
        text = f"Ahora mismo no hay opciones disponibles dentro de <b>{esc(category['name'])}</b>."
        rows = [[("⬅️ Categorías", "user:categories")], [("🏠 Inicio", "start")]]
    else:
        text = f"Elige una opción dentro de <b>{esc(category['name'])}</b>:"
        rows = [[(f"🎁 {sub['name']}", f"user:get:{sub['id']}")] for sub in subcategories]
        rows.append([("⬅️ Categorías", "user:categories")])

    if message_id:
        await edit_message(chat_id, message_id, text, inline_keyboard(rows))
    else:
        await send_message(chat_id, text, inline_keyboard(rows))


async def handle_get_code(chat_id: int, user_id: int, subcategory_id: int) -> None:
    subcategory = await get_subcategory(subcategory_id)
    if not subcategory or not subcategory["is_active"] or not subcategory["category_active"]:
        await send_message(chat_id, "Esta promoción ya no está disponible. Vuelve al inicio con /start.")
        return

    code = await deliver_code(user_id, subcategory_id)
    if not code:
        msg = subcategory.get("empty_message") or "Ahora mismo no hay códigos disponibles para esta promoción."
        await send_message(chat_id, msg)
        return

    admin = await is_admin(user_id)
    text = (
        f"Aquí tienes tu código para <b>{esc(subcategory['category_name'])}</b> "
        f"→ <b>{esc(subcategory['name'])}</b>:\n\n"
        f"<code>{esc(code)}</code>"
    )
    await send_message(chat_id, text, main_menu(admin))
