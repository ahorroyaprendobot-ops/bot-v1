from __future__ import annotations

import html
from typing import Any

import httpx
from config import settings

API_BASE = f"https://api.telegram.org/bot{settings.bot_token}"


def esc(text: object) -> str:
    return html.escape(str(text), quote=False)


async def tg_call(method: str, payload: dict[str, Any]) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(f"{API_BASE}/{method}", json=payload)
        response.raise_for_status()
        data = response.json()
        if not data.get("ok"):
            raise RuntimeError(f"Telegram error en {method}: {data}")
        return data


async def send_message(chat_id: int, text: str, reply_markup: dict[str, Any] | None = None) -> None:
    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    await tg_call("sendMessage", payload)


async def edit_message(chat_id: int, message_id: int, text: str, reply_markup: dict[str, Any] | None = None) -> None:
    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        await tg_call("editMessageText", payload)
    except Exception:
        await send_message(chat_id, text, reply_markup)


async def answer_callback(callback_query_id: str, text: str | None = None, show_alert: bool = False) -> None:
    payload: dict[str, Any] = {"callback_query_id": callback_query_id, "show_alert": show_alert}
    if text:
        payload["text"] = text
    await tg_call("answerCallbackQuery", payload)


async def set_webhook() -> None:
    if not settings.public_base_url:
        return
    await tg_call(
        "setWebhook",
        {
            "url": f"{settings.public_base_url.rstrip('/')}/webhook/{settings.webhook_secret}",
            "drop_pending_updates": True,
        },
    )
