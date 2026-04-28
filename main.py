from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Request

from config import settings
from db import close_db, connect_db, run_migrations
from handlers.admin import (
    ask_codes,
    ask_new_category,
    confirm_delete,
    do_delete,
    handle_admin_text,
    require_admin,
    show_admin_menu,
    show_categories_admin,
    show_category_detail,
    show_stock,
    toggle_category,
)
from handlers.start import show_help, show_start
from handlers.user import handle_get_code, show_categories
from services.state_service import clear_state
from telegram_api import answer_callback, send_message, set_webhook

app = FastAPI(title="Bot Influencer Códigos")
logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup() -> None:
    await connect_db()
    await run_migrations()
    await set_webhook()


@app.on_event("shutdown")
async def shutdown() -> None:
    await close_db()


@app.get("/")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/webhook/{secret}")
async def telegram_webhook(secret: str, request: Request) -> dict[str, bool]:
    if secret != settings.webhook_secret:
        raise HTTPException(status_code=403, detail="Forbidden")
    update = await request.json()
    await handle_update(update)
    return {"ok": True}


async def handle_update(update: dict) -> None:
    try:
        if "message" in update:
            await handle_message(update["message"])
        elif "callback_query" in update:
            await handle_callback(update["callback_query"])
    except Exception:
        logger.exception("Error procesando update")
        message = update.get("message", {})
        callback = update.get("callback_query", {})
        chat_id = message.get("chat", {}).get("id")
        callback_id = callback.get("id")
        callback_chat_id = callback.get("message", {}).get("chat", {}).get("id")
        if callback_id:
            try:
                await answer_callback(callback_id, "Error temporal. Pulsa /start para reintentar.", show_alert=False)
            except Exception:
                logger.exception("No se pudo responder callback de error")
        if chat_id:
            try:
                await send_message(int(chat_id), "Hubo un error temporal. Usa /start para volver al inicio.")
            except Exception:
                logger.exception("No se pudo enviar mensaje de recuperación")
        elif callback_chat_id:
            try:
                await send_message(int(callback_chat_id), "Hubo un error temporal. Usa /start para volver al inicio.")
            except Exception:
                logger.exception("No se pudo enviar mensaje de recuperación desde callback")


def is_command(text: str, command: str) -> bool:
    clean = text.strip().lower()
    if clean == command:
        return True
    return clean.startswith(f"{command}@")


def parse_callback_id(data: str, prefix: str) -> int | None:
    if not data.startswith(prefix):
        return None
    value = data[len(prefix) :].strip()
    if not value.isdigit():
        return None
    return int(value)


async def handle_message(message: dict) -> None:
    chat = message.get("chat", {})
    user = message.get("from", {})
    chat_id = int(chat.get("id"))
    user_id = int(user.get("id"))
    text = message.get("text", "")

    if is_command(text, "/start"):
        await show_start(chat_id, user_id)
        return

    if is_command(text, "/cancelar") or text.strip().lower() == "cancelar":
        handled = await handle_admin_text(chat_id, user_id, "/cancelar")
        if not handled:
            await show_start(chat_id, user_id)
        return

    if await handle_admin_text(chat_id, user_id, text):
        return

    await show_start(chat_id, user_id)


async def handle_callback(callback: dict) -> None:
    callback_id = callback["id"]
    data = callback.get("data", "")
    message = callback.get("message", {})
    chat_id = int(message.get("chat", {}).get("id"))
    message_id = int(message.get("message_id"))
    user_id = int(callback.get("from", {}).get("id"))

    await answer_callback(callback_id)

    if data == "start":
        await show_start(chat_id, user_id)
        return

    if data == "user:help":
        await show_help(chat_id)
        return

    if data == "user:categories":
        await show_categories(chat_id, message_id)
        return

    if data.startswith("user:get:"):
        category_id = parse_callback_id(data, "user:get:")
        if category_id is None:
            await show_start(chat_id, user_id)
            return
        await handle_get_code(chat_id, user_id, category_id)
        return

    if data.startswith("admin:"):
        if not await require_admin(chat_id, user_id):
            return

        if data == "admin:menu":
            await clear_state(user_id)
            await show_admin_menu(chat_id, message_id)
        elif data == "admin:cancel_input":
            await clear_state(user_id)
            await show_admin_menu(chat_id, message_id)
        elif data == "admin:categories":
            await show_categories_admin(chat_id, message_id)
        elif data == "admin:new_category":
            await ask_new_category(chat_id, user_id)
        elif data == "admin:codes":
            await show_categories_admin(chat_id, message_id)
        elif data == "admin:stock":
            await show_stock(chat_id, message_id)
        elif data.startswith("admin:category:"):
            category_id = parse_callback_id(data, "admin:category:")
            if category_id is None:
                await show_admin_menu(chat_id, message_id)
                return
            await show_category_detail(chat_id, message_id, category_id)
        elif data.startswith("admin:pause:"):
            category_id = parse_callback_id(data, "admin:pause:")
            if category_id is None:
                await show_admin_menu(chat_id, message_id)
                return
            await toggle_category(chat_id, message_id, category_id, False)
        elif data.startswith("admin:activate:"):
            category_id = parse_callback_id(data, "admin:activate:")
            if category_id is None:
                await show_admin_menu(chat_id, message_id)
                return
            await toggle_category(chat_id, message_id, category_id, True)
        elif data.startswith("admin:add_codes:"):
            category_id = parse_callback_id(data, "admin:add_codes:")
            if category_id is None:
                await show_admin_menu(chat_id, message_id)
                return
            await ask_codes(chat_id, user_id, category_id)
        elif data.startswith("admin:delete_confirm:"):
            category_id = parse_callback_id(data, "admin:delete_confirm:")
            if category_id is None:
                await show_admin_menu(chat_id, message_id)
                return
            await confirm_delete(chat_id, message_id, category_id)
        elif data.startswith("admin:delete:"):
            category_id = parse_callback_id(data, "admin:delete:")
            if category_id is None:
                await show_admin_menu(chat_id, message_id)
                return
            await do_delete(chat_id, message_id, category_id)
        else:
            await show_admin_menu(chat_id, message_id)
        return
