# Cambio: categorías principales + opciones/subcategorías

Este paquete cambia el flujo a:

Categoría principal → Opción/subcategoría → Códigos

Ejemplo:

Bancos → BBVA → códigos
Bancos → Openbank → códigos
Compras → Shein → códigos

## Antes de desplegar

No tienes que eliminar nada de la base de datos.

El ZIP incluye la migración:

migrations/002_subcategories.sql

La app ejecutará automáticamente las migraciones al arrancar porque `db.py` ahora ejecuta todos los `.sql` dentro de `migrations/` en orden.

## Recomendado después de desplegar

Ejecuta una vez en Supabase para limpiar estados antiguos:

```sql
DELETE FROM user_states;
```

## Qué cambia en el bot

Admin:
1. Crea categoría principal: Bancos
2. Entra en Bancos
3. Añade opción: BBVA, Openbank, etc.
4. Entra en BBVA
5. Añade códigos

Usuario:
1. Pedir código
2. Elige categoría principal
3. Elige opción
4. Recibe código

## Importante

Los códigos nuevos se añaden a subcategorías. Los códigos antiguos que estuvieran asociados directamente a categorías no se borran, pero ya no se entregan en el nuevo flujo.
