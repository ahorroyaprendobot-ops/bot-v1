from __future__ import annotations

from keyboards import admin_menu, back_to_admin, inline_keyboard
from services.admin_service import is_admin
from services.categories_service import create_category, delete_category, get_category, list_categories, set_category_active
from services.codes_service import add_codes, stock_summary
from services.state_service import clear_state, get_state, set_state
from telegram_api import edit_message, esc, send_message


async def require_admin(chat_id: int, user_id: int) -> bool:
    if not await is_admin(user_id):
        await send_message(chat_id, "No tienes permisos para usar esta opción.")
        return False
    return True


async def show_admin_menu(chat_id: int, message_id: int | None = None) -> None:
    text = "🛠 <b>Panel admin</b>\n\nGestiona categorías, códigos y stock."
    if message_id:
        await edit_message(chat_id, message_id, text, admin_menu())
    else:
        await send_message(chat_id, text, admin_menu())


async def show_categories_admin(chat_id: int, message_id: int | None = None) -> None:
    categories = await list_categories(active_only=False)
    rows = [[("➕ Nueva categoría", "admin:new_category")]]
    for cat in categories:
        status = "✅" if cat["is_active"] else "⏸️"
        rows.append([(f"{status} {cat['name']}", f"admin:category:{cat['id']}")])
    rows.append([("⬅️ Panel admin", "admin:menu")])
    text = "📁 <b>Categorías</b>"
    if not categories:
        text += "\n\nNo hay categorías creadas todavía."
    if message_id:
        await edit_message(chat_id, message_id, text, inline_keyboard(rows))
    else:
        await send_message(chat_id, text, inline_keyboard(rows))


async def show_category_detail(chat_id: int, message_id: int, category_id: int) -> None:
    cat = await get_category(category_id)
    if not cat:
        await edit_message(chat_id, message_id, "Categoría no encontrada.", back_to_admin())
        return
    rows = []
    if cat["is_active"]:
        rows.append([("⏸️ Pausar", f"admin:pause:{category_id}")])
    else:
        rows.append([("▶️ Activar", f"admin:activate:{category_id}")])
    rows.append([("🎟 Añadir códigos", f"admin:add_codes:{category_id}")])
    rows.append([("🗑 Eliminar", f"admin:delete_confirm:{category_id}")])
    rows.append([("⬅️ Categorías", "admin:categories")])
    status = "Activa" if cat["is_active"] else "Pausada"
    text = f"📁 <b>{esc(cat['name'])}</b>\n\nEstado: <b>{status}</b>"
    await edit_message(chat_id, message_id, text, inline_keyboard(rows))


async def ask_new_category(chat_id: int, user_id: int) -> None:
    await set_state(user_id, "awaiting_category_name")
    await send_message(
        chat_id,
        "Escribe el nombre de la nueva categoría.\n\nUsa /cancelar para salir.",
        inline_keyboard([[("⬅️ Cancelar", "admin:cancel_input")]]),
    )


async def ask_codes(chat_id: int, user_id: int, category_id: int) -> None:
    cat = await get_category(category_id)
    if not cat:
        await send_message(chat_id, "Categoría no encontrada.", back_to_admin())
        return
    await set_state(user_id, "awaiting_codes", {"category_id": category_id})
    await send_message(
        chat_id,
        f"Pega los códigos para <b>{esc(cat['name'])}</b>, uno por línea.\n\nMáximo recomendado: 500 por mensaje.\nUsa /cancelar para salir.",
        inline_keyboard([[("⬅️ Cancelar", "admin:cancel_input")]]),
    )


async def show_stock(chat_id: int, message_id: int | None = None) -> None:
    rows = await stock_summary()
    if not rows:
        text = "📊 <b>Stock actual</b>\n\nNo hay categorías creadas."
    else:
        lines = ["📊 <b>Stock actual</b>", ""]
        for row in rows:
            status = "activa" if row["is_active"] else "pausada"
            lines.append(
                f"• <b>{esc(row['name'])}</b>: {row['available']} disponibles / {row['used']} entregados ({status})"
            )
        text = "\n".join(lines)
    if message_id:
        await edit_message(chat_id, message_id, text, back_to_admin())
    else:
        await send_message(chat_id, text, back_to_admin())


async def handle_admin_text(chat_id: int, user_id: int, text: str) -> bool:
    state = await get_state(user_id)
    if not state:
        return False

    if text.strip().lower() == "/cancelar":
        await clear_state(user_id)
        await send_message(chat_id, "Operación cancelada.", back_to_admin())
        return True

    if state["state"] == "awaiting_category_name":
        ok, message = await create_category(text)
        await clear_state(user_id)
        await send_message(chat_id, message, back_to_admin())
        return True

    if state["state"] == "awaiting_codes":
        raw_category_id = state.get("data", {}).get("category_id")
        if raw_category_id is None or not str(raw_category_id).isdigit():
            await clear_state(user_id)
            await send_message(
                chat_id,
                "El flujo de carga de códigos expiró o era inválido. Vuelve a intentarlo desde el panel admin.",
                back_to_admin(),
            )
            return True
        category_id = int(raw_category_id)
        result = await add_codes(category_id, text)
        await clear_state(user_id)
        limited = "\n⚠️ Se procesaron solo los primeros 500 códigos." if result["limited"] else ""
        await send_message(
            chat_id,
            "🎟 <b>Resultado</b>\n\n"
            f"Añadidos: <b>{result['added']}</b>\n"
            f"Duplicados ignorados: <b>{result['duplicated']}</b>\n"
            f"Líneas vacías ignoradas: <b>{result['empty']}</b>\n"
            f"Stock disponible actual: <b>{result['available']}</b>"
            f"{limited}",
            back_to_admin(),
        )
        return True

    await clear_state(user_id)
    return False


async def toggle_category(chat_id: int, message_id: int, category_id: int, active: bool) -> None:
    await set_category_active(category_id, active)
    await show_category_detail(chat_id, message_id, category_id)


async def confirm_delete(chat_id: int, message_id: int, category_id: int) -> None:
    cat = await get_category(category_id)
    if not cat:
        await edit_message(chat_id, message_id, "Categoría no encontrada.", back_to_admin())
        return
    await edit_message(
        chat_id,
        message_id,
        f"¿Seguro que quieres eliminar <b>{esc(cat['name'])}</b>?\n\nEsto borrará también todos sus códigos.",
        inline_keyboard(
            [
                [("Sí, eliminar", f"admin:delete:{category_id}")],
                [("Cancelar", f"admin:category:{category_id}")],
            ]
        ),
    )


async def do_delete(chat_id: int, message_id: int, category_id: int) -> None:
    ok = await delete_category(category_id)
    text = "Categoría eliminada." if ok else "No se ha podido eliminar la categoría."
    await edit_message(chat_id, message_id, text, back_to_admin())
