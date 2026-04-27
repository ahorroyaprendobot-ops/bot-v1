from __future__ import annotations


def inline_keyboard(rows: list[list[tuple[str, str]]]) -> dict:
    return {
        "inline_keyboard": [
            [{"text": text, "callback_data": callback_data} for text, callback_data in row]
            for row in rows
        ]
    }


def main_menu(is_admin: bool = False) -> dict:
    rows = [[("🎁 Pedir código", "user:categories")], [("ℹ️ Ayuda", "user:help")]]
    if is_admin:
        rows.append([("🛠 Panel admin", "admin:menu")])
    return inline_keyboard(rows)


def admin_menu() -> dict:
    return inline_keyboard(
        [
            [("📁 Categorías", "admin:categories")],
            [("🎟 Códigos", "admin:codes")],
            [("📊 Stock", "admin:stock")],
            [("⬅️ Volver", "start")],
        ]
    )


def back_to_admin() -> dict:
    return inline_keyboard([[("⬅️ Panel admin", "admin:menu")]])
