# 🔍 Guía de Diagnóstico: Ventas no aparecen en el panel de Admin

## ✅ Cambios realizados

### 1. **Backend - Corrección de transacciones**
- ✅ Eliminamos `begin_nested()` que creaba un savepoint en lugar de una transacción completa
- ✅ Agregamos `await db.commit()` después de `save_order_and_update_stock()`
- ✅ Agregamos `await db.rollback()` en caso de error
- ✅ Agregamos logging detallado con emojis para rastrear cada paso

### 2. **Frontend - Ventana emergente de Mercado Pago**
- ✅ Cambiamos `window.location.href` por `window.open()` para abrir MP en ventana emergente
- ✅ Agregamos detección de bloqueo de pop-ups
- ✅ Agregamos traducciones en español e inglés

---

## 🔍 Pasos para diagnosticar por qué no aparecen las ventas

### Paso 1: Verificar que el webhook esté configurado correctamente

El webhook de Mercado Pago debe apuntar a tu servidor backend:
```
https://tu-dominio.com/api/checkout/webhook
```

**Para desarrollo local con ngrok:**
```bash
ngrok http 8000
# Copiar la URL de ngrok y configurarla en Mercado Pago
https://XXXX-XXX-XX.ngrok.io/api/checkout/webhook
```

### Paso 2: Verificar los logs del backend

Después de realizar una compra, busca en los logs del backend los siguientes mensajes:

```
🔔 Webhook recibido de Mercado Pago: {...}
💳 Procesando pago con ID: XXXX
📋 Información del pago obtenida de MP. Estado: approved
✅ Pago aprobado, creando orden...
💾 Guardando orden en la base de datos...
🔄 Haciendo commit de la transacción...
✅ Orden guardada exitosamente para el pago XXXX
📧 Enviando email de confirmación...
```

**Si NO ves estos mensajes:**
- El webhook no se está ejecutando
- Verifica la configuración en Mercado Pago
- Verifica que `BACKEND_URL` en tu `.env` sea correcto

**Si ves errores como:**
```
❌ Error inesperado al procesar el webhook para el pago XXXX
```
- Revisa el detalle del error en los logs
- Puede ser un problema de conexión a la base de datos
- Puede ser un problema con el stock insuficiente

### Paso 3: Ejecutar el script de verificación

Ejecuta el script que creamos para verificar las órdenes en la base de datos:

```bash
cd server
python check_orders.py
```

Esto te mostrará:
- Cuántas órdenes hay en la base de datos
- Los detalles de cada orden
- Si hay órdenes pero no aparecen en el admin, hay un problema en el endpoint GET

### Paso 4: Verificar que el endpoint de admin funcione

Prueba el endpoint manualmente:

```bash
# Con token de admin
curl -H "Authorization: Bearer TU_TOKEN_DE_ADMIN" \
     http://localhost:8000/api/admin/sales
```

Deberías recibir un JSON con todas las ventas.

### Paso 5: Verificar la configuración de la base de datos

**En tu `.env` verifica que:**
```env
DB_SQL_URI=mysql+aiomysql://usuario:contraseña@host:puerto/nombre_db
BACKEND_URL=http://tu-dominio.com  # o ngrok URL para desarrollo
FRONTEND_URL=http://localhost:5173  # o tu URL de frontend
```

---

## 🐛 Problemas comunes y soluciones

### Problema 1: "El webhook nunca se ejecuta"
**Causa:** Mercado Pago no puede llegar a tu servidor
**Solución:**
- Usa ngrok para desarrollo local
- Verifica que tu firewall no bloquee el puerto
- Verifica la URL del webhook en la configuración de MP

### Problema 2: "El webhook se ejecuta pero da error"
**Causa:** Puede ser stock insuficiente, error de DB, etc.
**Solución:**
- Revisa los logs detallados con emojis
- Verifica que el producto tenga stock suficiente
- Verifica que la conexión a la DB funcione

### Problema 3: "Las órdenes están en la DB pero no aparecen en el admin"
**Causa:** Problema en el endpoint GET /api/admin/sales
**Solución:**
- Verifica que el token de admin sea válido
- Verifica que el usuario tenga rol 'admin'
- Prueba el endpoint manualmente con curl

### Problema 4: "La ventana de MP se abre pero no pasa nada"
**Causa:** El usuario no completó el pago o lo canceló
**Solución:**
- Completa el pago en el sandbox de MP
- Usa las tarjetas de prueba de Mercado Pago
- Verifica que el webhook se llame después del pago

---

## 📊 Tarjetas de prueba de Mercado Pago

Para probar pagos en el sandbox:

| Tarjeta | Número | CVV | Vencimiento | Resultado |
|---------|--------|-----|-------------|-----------|
| Visa | 4509 9535 6623 3704 | 123 | 11/25 | ✅ Aprobado |
| Mastercard | 5031 7557 3453 0604 | 123 | 11/25 | ✅ Aprobado |

---

## 🚀 Próximos pasos

1. **Reinicia el servidor backend** para que tome los nuevos cambios
2. **Reinicia el frontend** (si lo tienes corriendo)
3. **Realiza una compra de prueba** con las tarjetas de sandbox
4. **Revisa los logs del backend** durante todo el proceso
5. **Ejecuta `check_orders.py`** para ver si la orden se guardó
6. **Accede al panel de admin** y verifica si aparece la venta

---

## 📝 Notas importantes

- El commit que agregamos es **CRÍTICO** - sin él, las órdenes no se persisten
- Los logs con emojis te ayudarán a rastrear exactamente dónde falla el proceso
- El webhook solo se ejecuta cuando el pago es **approved**
- Para desarrollo local, **DEBES usar ngrok** o similar para que MP pueda llamar tu webhook
