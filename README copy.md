# Bot Influencer Códigos

Versión mínima de bot de Telegram para que los seguidores pidan códigos por privado y el admin gestione categorías/promociones desde el propio bot.

## Qué hace

### Usuario

- `/start`
- Ver promociones activas
- Pedir un código
- Recibir un código disponible o mensaje de agotado

### Admin

- Crear categorías/promociones
- Activar o pausar categorías
- Añadir códigos en lote, uno por línea
- Ver stock disponible y entregado
- Eliminar categorías con confirmación

## Variables necesarias

Copia `.env.example` a `.env` en local o configura estas variables en Render/GitHub:

```env
BOT_TOKEN=token_del_bot
DATABASE_URL=postgresql://user:password@host:5432/database
INITIAL_ADMIN_ID=tu_id_de_telegram
PUBLIC_BASE_URL=https://tu-app.onrender.com
WEBHOOK_SECRET=un_secreto_largo
```

`INITIAL_ADMIN_ID` solo crea el primer admin al arrancar. Después puedes ampliar el sistema si quieres añadir admins desde el bot.

## Instalación local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

## Despliegue en Render

1. Sube este proyecto a GitHub.
2. Crea un Web Service en Render.
3. Configura las variables de entorno.
4. Conecta PostgreSQL.
5. Despliega.

El bot ejecuta la migración inicial automáticamente al arrancar.

## Webhook

Si `PUBLIC_BASE_URL` está definido, el webhook se configura automáticamente en:

```text
https://TU-DOMINIO/webhook/WEBHOOK_SECRET
```

## Base de datos

Tablas incluidas:

- `admins`
- `categories`
- `promo_codes`
- `user_states`

La entrega de códigos es atómica usando `FOR UPDATE SKIP LOCKED`, para evitar que dos usuarios reciban el mismo código a la vez.

## Flujo recomendado

1. Arranca el bot.
2. Abre Telegram con el usuario cuyo ID pusiste en `INITIAL_ADMIN_ID`.
3. Envía `/start`.
4. Entra en `🛠 Panel admin`.
5. Crea una categoría.
6. Añade códigos.
7. Prueba pedir un código como usuario.

## Notas de diseño

Esta versión no tiene canal, posts automáticos, rotación ni usuarios subiendo códigos. Está pensada para ser sencilla, estable y fácil de administrar por un influencer.
