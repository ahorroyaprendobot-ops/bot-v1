from __future__ import annotations

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
from telegram_api import answer_callback, set_webhook

app = FastAPI(title="Bot Influencer Códigos")


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
    if "message" in update:
        await handle_message(update["message"])
    elif "callback_query" in update:
        await handle_callback(update["callback_query"])


async def handle_message(message: dict) -> None:
    chat = message.get("chat", {})
    user = message.get("from", {})
    chat_id = int(chat.get("id"))
    user_id = int(user.get("id"))
    text = message.get("text", "")

    if text.startswith("/start"):
        await show_start(chat_id, user_id)
        return

    if text.startswith("/cancelar"):
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
        category_id = int(data.split(":")[-1])
        await handle_get_code(chat_id, user_id, category_id)
        return

    if data.startswith("admin:"):
        if not await require_admin(chat_id, user_id):
            return

        if data == "admin:menu":
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
            await show_category_detail(chat_id, message_id, int(data.split(":")[-1]))
        elif data.startswith("admin:pause:"):
            await toggle_category(chat_id, message_id, int(data.split(":")[-1]), False)
        elif data.startswith("admin:activate:"):
            await toggle_category(chat_id, message_id, int(data.split(":")[-1]), True)
        elif data.startswith("admin:add_codes:"):
            await ask_codes(chat_id, user_id, int(data.split(":")[-1]))
        elif data.startswith("admin:delete_confirm:"):
            await confirm_delete(chat_id, message_id, int(data.split(":")[-1]))
        elif data.startswith("admin:delete:"):
            await do_delete(chat_id, message_id, int(data.split(":")[-1]))
        else:
            await show_admin_menu(chat_id, message_id)
        return
