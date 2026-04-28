from __future__ import annotations

from keyboards import admin_menu, back_to_admin, inline_keyboard
from services.admin_service import is_admin
from services.categories_service import create_category, delete_category, get_category, list_categories, set_category_active
from services.subcategories_service import (
    create_subcategory,
    delete_subcategory,
    get_subcategory,
    list_subcategories,
    set_subcategory_active,
)
from services.codes_service import add_codes, stock_summary
from services.state_service import clear_state, get_state, set_state
from telegram_api import edit_message, esc, send_message


async def require_admin(chat_id: int, user_id: int) -> bool:
    if not await is_admin(user_id):
        await send_message(chat_id, "No tienes permisos para usar esta opción.")
        return False
    return True


async def show_admin_menu(chat_id: int, message_id: int | None = None) -> None:
    text = "🛠 <b>Panel admin</b>\n\nGestiona categorías, opciones, códigos y stock."
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
    text = "📁 <b>Categorías principales</b>\n\nEjemplo: Bancos, Compras, Viajes."
    if not categories:
        text += "\n\nNo hay categorías creadas todavía."
    if message_id:
        await edit_message(chat_id, message_id, text, inline_keyboard(rows))
    else:
        await send_message(chat_id, text, inline_keyboard(rows))


async def show_category_detail(chat_id: int, message_id: int | None, category_id: int) -> None:
    cat = await get_category(category_id)
    if not cat:
        text = "Categoría no encontrada."
        if message_id:
            await edit_message(chat_id, message_id, text, back_to_admin())
        else:
            await send_message(chat_id, text, back_to_admin())
        return

    subcategories = await list_subcategories(category_id, active_only=False)
    rows = []
    if cat["is_active"]:
        rows.append([("⏸️ Pausar categoría", f"admin:pause:{category_id}")])
    else:
        rows.append([("▶️ Activar categoría", f"admin:activate:{category_id}")])
    rows.append([("➕ Añadir opción", f"admin:new_subcategory:{category_id}")])
    for sub in subcategories:
        status = "✅" if sub["is_active"] else "⏸️"
        rows.append([(f"{status} {sub['name']}", f"admin:subcategory:{sub['id']}")])
    rows.append([("🗑 Eliminar categoría", f"admin:delete_confirm:{category_id}")])
    rows.append([("⬅️ Categorías", "admin:categories")])

    status = "Activa" if cat["is_active"] else "Pausada"
    text = f"📁 <b>{esc(cat['name'])}</b>\n\nEstado: <b>{status}</b>"
    if subcategories:
        text += "\n\nOpciones dentro de esta categoría:"
    else:
        text += "\n\nTodavía no hay opciones. Añade una, por ejemplo: BBVA, Openbank, Shein..."
    if message_id:
        await edit_message(chat_id, message_id, text, inline_keyboard(rows))
    else:
        await send_message(chat_id, text, inline_keyboard(rows))


async def show_subcategory_detail(chat_id: int, message_id: int | None, subcategory_id: int) -> None:
    sub = await get_subcategory(subcategory_id)
    if not sub:
        text = "Opción no encontrada."
        if message_id:
            await edit_message(chat_id, message_id, text, back_to_admin())
        else:
            await send_message(chat_id, text, back_to_admin())
        return

    rows = []
    if sub["is_active"]:
        rows.append([("⏸️ Pausar opción", f"admin:pause_sub:{subcategory_id}")])
    else:
        rows.append([("▶️ Activar opción", f"admin:activate_sub:{subcategory_id}")])
    rows.append([("🎟 Añadir códigos", f"admin:add_codes:{subcategory_id}")])
    rows.append([("🗑 Eliminar opción", f"admin:delete_sub_confirm:{subcategory_id}")])
    rows.append([("⬅️ Volver a categoría", f"admin:category:{sub['category_id']}")])

    status = "Activa" if sub["is_active"] else "Pausada"
    text = (
        f"🏷 <b>{esc(sub['name'])}</b>\n"
        f"Categoría: <b>{esc(sub['category_name'])}</b>\n\n"
        f"Estado: <b>{status}</b>\n\n"
        "Los códigos se añaden aquí, no en la categoría principal."
    )
    if message_id:
        await edit_message(chat_id, message_id, text, inline_keyboard(rows))
    else:
        await send_message(chat_id, text, inline_keyboard(rows))


async def ask_new_category(chat_id: int, user_id: int) -> None:
    await set_state(user_id, "awaiting_category_name", {})
    await send_message(
        chat_id,
        "➕ <b>Nueva categoría principal</b>\n\nEscribe <b>solo un nombre</b>.\n\nEjemplo: <code>Bancos</code>\n\nUsa /cancelar para salir.",
        inline_keyboard([[("❌ Cancelar", "admin:cancel_input")]]),
    )


async def ask_new_subcategory(chat_id: int, user_id: int, category_id: int) -> None:
    cat = await get_category(category_id)
    if not cat:
        await send_message(chat_id, "Categoría no encontrada.", back_to_admin())
        return
    await set_state(user_id, "awaiting_subcategory_name", {"category_id": category_id})
    await send_message(
        chat_id,
        f"➕ <b>Nueva opción dentro de {esc(cat['name'])}</b>\n\nEscribe <b>solo un nombre</b>.\n\nEjemplos: <code>BBVA</code>, <code>Openbank</code>, <code>Shein</code>\n\nUsa /cancelar para salir.",
        inline_keyboard([[("❌ Cancelar", "admin:cancel_input")]]),
    )


async def ask_codes(chat_id: int, user_id: int, subcategory_id: int) -> None:
    sub = await get_subcategory(subcategory_id)
    if not sub:
        await send_message(chat_id, "Opción no encontrada.", back_to_admin())
        return
    await set_state(user_id, "awaiting_codes", {"subcategory_id": subcategory_id})
    await send_message(
        chat_id,
        f"🎟 <b>Añadir códigos a {esc(sub['category_name'])} → {esc(sub['name'])}</b>\n\nPega los códigos, uno por línea.\n\nEjemplo:\n<code>CODIGO1\nCODIGO2\nCODIGO3</code>\n\nMáximo: 500 por mensaje.\nUsa /cancelar para salir.",
        inline_keyboard([[("❌ Cancelar", "admin:cancel_input")]]),
    )


async def show_stock(chat_id: int, message_id: int | None = None) -> None:
    rows = await stock_summary()
    if not rows:
        text = "📊 <b>Stock actual</b>\n\nNo hay categorías creadas."
    else:
        lines = ["📊 <b>Stock actual</b>", ""]
        current_category: str | None = None
        for row in rows:
            category_name = row["category_name"]
            if category_name != current_category:
                current_category = category_name
                cat_status = "activa" if row["category_active"] else "pausada"
                lines.append(f"📁 <b>{esc(category_name)}</b> ({cat_status})")

            if row["subcategory_id"] is None:
                lines.append("  • Sin opciones creadas")
            else:
                sub_status = "activa" if row["subcategory_active"] else "pausada"
                lines.append(
                    f"  • <b>{esc(row['subcategory_name'])}</b>: {row['available']} disponibles / {row['used']} entregados ({sub_status})"
                )
        text = "\n".join(lines)
    if message_id:
        await edit_message(chat_id, message_id, text, back_to_admin())
    else:
        await send_message(chat_id, text, back_to_admin())


async def cancel_admin_flow(chat_id: int, user_id: int) -> None:
    await clear_state(user_id)
    await send_message(chat_id, "Operación cancelada. Has vuelto al panel admin.", admin_menu())


async def handle_admin_text(chat_id: int, user_id: int, text: str) -> bool:
    clean_text = (text or "").strip()
    lower_text = clean_text.lower()

    if lower_text in {"/cancelar", "cancelar"} or lower_text.startswith("/cancelar@"):
        await cancel_admin_flow(chat_id, user_id)
        return True

    state = await get_state(user_id)
    if not state:
        return False

    state_name = state.get("state")

    if state_name == "awaiting_category_name":
        ok, message, category_id = await create_category(clean_text)
        if not ok:
            rows = [[("❌ Cancelar", "admin:cancel_input")]]
            if category_id:
                rows.insert(0, [("Ver categoría existente", f"admin:category:{category_id}")])
            await send_message(chat_id, f"⚠️ {esc(message)}\n\nEscribe otro nombre o usa /cancelar.", inline_keyboard(rows))
            return True

        await clear_state(user_id)
        await send_message(
            chat_id,
            f"✅ {esc(message)}\n\nAhora añade opciones dentro de esta categoría.",
            inline_keyboard(
                [
                    [("➕ Añadir opción", f"admin:new_subcategory:{category_id}")],
                    [("📁 Ver categoría", f"admin:category:{category_id}")],
                    [("🛠 Panel admin", "admin:menu")],
                ]
            ),
        )
        return True

    if state_name == "awaiting_subcategory_name":
        raw_category_id = state.get("data", {}).get("category_id")
        if raw_category_id is None or not str(raw_category_id).isdigit():
            await clear_state(user_id)
            await send_message(chat_id, "El flujo expiró. Vuelve a intentarlo desde el panel admin.", back_to_admin())
            return True

        category_id = int(raw_category_id)
        ok, message, subcategory_id = await create_subcategory(category_id, clean_text)
        if not ok:
            rows = [[("❌ Cancelar", "admin:cancel_input")]]
            if subcategory_id:
                rows.insert(0, [("Ver opción existente", f"admin:subcategory:{subcategory_id}")])
            await send_message(chat_id, f"⚠️ {esc(message)}\n\nEscribe otro nombre o usa /cancelar.", inline_keyboard(rows))
            return True

        await clear_state(user_id)
        await send_message(
            chat_id,
            f"✅ {esc(message)}\n\nAhora puedes añadir códigos a esta opción.",
            inline_keyboard(
                [
                    [("🎟 Añadir códigos", f"admin:add_codes:{subcategory_id}")],
                    [("➕ Crear otra opción", f"admin:new_subcategory:{category_id}")],
                    [("📁 Ver categoría", f"admin:category:{category_id}")],
                    [("🛠 Panel admin", "admin:menu")],
                ]
            ),
        )
        return True

    if state_name == "awaiting_codes":
        raw_subcategory_id = state.get("data", {}).get("subcategory_id")
        # Compatibilidad por si queda algún estado antiguo con category_id: lo limpiamos sin romper.
        if raw_subcategory_id is None or not str(raw_subcategory_id).isdigit():
            await clear_state(user_id)
            await send_message(
                chat_id,
                "El flujo de carga de códigos expiró o era antiguo. Vuelve a entrar en la opción concreta y pulsa “Añadir códigos”.",
                back_to_admin(),
            )
            return True

        subcategory_id = int(raw_subcategory_id)
        sub = await get_subcategory(subcategory_id)
        result = await add_codes(subcategory_id, clean_text)
        await clear_state(user_id)
        limited = "\n⚠️ Se procesaron solo los primeros 500 códigos." if result["limited"] else ""
        rows = [
            [("🎟 Añadir más códigos", f"admin:add_codes:{subcategory_id}")],
            [("📊 Ver stock", "admin:stock")],
            [("🛠 Panel admin", "admin:menu")],
        ]
        if sub:
            rows.insert(1, [("🏷 Ver opción", f"admin:subcategory:{subcategory_id}")])
        await send_message(
            chat_id,
            "🎟 <b>Resultado</b>\n\n"
            f"Añadidos: <b>{result['added']}</b>\n"
            f"Duplicados ignorados: <b>{result['duplicated']}</b>\n"
            f"Líneas vacías ignoradas: <b>{result['empty']}</b>\n"
            f"Stock disponible actual: <b>{result['available']}</b>"
            f"{limited}",
            inline_keyboard(rows),
        )
        return True

    await clear_state(user_id)
    await send_message(chat_id, "Había un flujo antiguo bloqueado. Lo he limpiado. Vuelve a intentarlo desde el panel admin.", admin_menu())
    return True


async def toggle_category(chat_id: int, message_id: int, category_id: int, active: bool) -> None:
    await set_category_active(category_id, active)
    await show_category_detail(chat_id, message_id, category_id)


async def toggle_subcategory(chat_id: int, message_id: int, subcategory_id: int, active: bool) -> None:
    await set_subcategory_active(subcategory_id, active)
    await show_subcategory_detail(chat_id, message_id, subcategory_id)


async def confirm_delete(chat_id: int, message_id: int, category_id: int) -> None:
    cat = await get_category(category_id)
    if not cat:
        await edit_message(chat_id, message_id, "Categoría no encontrada.", back_to_admin())
        return
    await edit_message(
        chat_id,
        message_id,
        f"¿Seguro que quieres eliminar <b>{esc(cat['name'])}</b>?\n\nEsto borrará también sus opciones y todos sus códigos.",
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


async def confirm_delete_subcategory(chat_id: int, message_id: int, subcategory_id: int) -> None:
    sub = await get_subcategory(subcategory_id)
    if not sub:
        await edit_message(chat_id, message_id, "Opción no encontrada.", back_to_admin())
        return
    await edit_message(
        chat_id,
        message_id,
        f"¿Seguro que quieres eliminar <b>{esc(sub['name'])}</b>?\n\nEsto borrará también todos sus códigos.",
        inline_keyboard(
            [
                [("Sí, eliminar", f"admin:delete_sub:{subcategory_id}")],
                [("Cancelar", f"admin:subcategory:{subcategory_id}")],
            ]
        ),
    )


async def do_delete_subcategory(chat_id: int, message_id: int, subcategory_id: int) -> None:
    sub = await get_subcategory(subcategory_id)
    category_id = int(sub["category_id"]) if sub else None
    ok = await delete_subcategory(subcategory_id)
    text = "Opción eliminada." if ok else "No se ha podido eliminar la opción."
    if category_id:
        await edit_message(chat_id, message_id, text, inline_keyboard([[("⬅️ Volver a categoría", f"admin:category:{category_id}")], [("🛠 Panel admin", "admin:menu")]]))
    else:
        await edit_message(chat_id, message_id, text, back_to_admin())
