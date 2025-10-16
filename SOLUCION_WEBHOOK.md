# 🚨 PROBLEMA: Las ventas no aparecen en el panel de admin

## 📊 Situación actual:
- ✅ El pago en Mercado Pago funciona correctamente
- ❌ La orden NO aparece en el admin
- ❌ Dashboard muestra: $0 ingresos, 0 órdenes

## 🔍 Causa del problema:
**El webhook de Mercado Pago NO se está ejecutando**

Esto significa que cuando completas el pago en MP, tu servidor NO recibe la notificación.

---

## 🎯 SOLUCIÓN (Sigue estos pasos EXACTAMENTE)

### PASO 1: Abre ngrok en una terminal separada

```bash
ngrok http 8000
```

Deberías ver algo así:
```
Forwarding    https://abc123-456.ngrok-free.dev -> http://localhost:8000
```

**COPIA ESA URL** (ejemplo: `https://abc123-456.ngrok-free.dev`)

⚠️ **MUY IMPORTANTE:** Cada vez que reinicias ngrok, la URL cambia. Debes actualizar todo.

---

### PASO 2: Actualiza tu archivo `.env`

Abre el archivo `.env` en la raíz del proyecto y cambia:

```env
BACKEND_URL="https://TU-NUEVA-URL-DE-NGROK.ngrok-free.dev"
```

**Ejemplo:**
```env
BACKEND_URL="https://abc123-456.ngrok-free.dev"
```

⚠️ **Sin la barra final `/`**

---

### PASO 3: Configura el webhook en Mercado Pago

1. Ve a: https://www.mercadopago.com.ar/developers/panel

2. Selecciona tu aplicación

3. En el menú lateral, busca **"Webhooks"** o **"Notificaciones"**

4. Haz clic en **"Configurar webhooks"** o **"Nueva notificación"**

5. En el campo **URL**, ingresa:
   ```
   https://TU-URL-DE-NGROK.ngrok-free.dev/api/checkout/webhook
   ```
   
   **Ejemplo:**
   ```
   https://abc123-456.ngrok-free.dev/api/checkout/webhook
   ```

6. Selecciona el evento: **"Pagos"** o **"Payments"**

7. **Guarda** la configuración

---

### PASO 4: Verifica que el webhook sea accesible

Abre tu navegador y ve a:
```
https://TU-URL-DE-NGROK.ngrok-free.dev/api/checkout/webhook-test
```

Deberías ver:
```json
{
  "status": "ok",
  "message": "✅ El webhook está accesible desde internet"
}
```

Si ves un error:
- ❌ ngrok no está corriendo
- ❌ Docker no está corriendo
- ❌ La URL es incorrecta

---

### PASO 5: Reinicia Docker

```bash
docker compose down
docker compose up
```

Espera a que todos los servicios estén corriendo.

---

### PASO 6: Realiza una compra de prueba

1. Ve a http://localhost:5173
2. Agrega un producto al carrito
3. Ve al checkout
4. Completa los datos de envío
5. Haz clic en **"REALIZAR PEDIDO"**
6. Se abrirá una ventana emergente con Mercado Pago

**USA ESTA TARJETA DE PRUEBA:**
- Número: **4509 9535 6623 3704**
- CVV: **123**
- Vencimiento: **11/25**
- Nombre: **APRO** (importante para que sea aprobada)

7. Completa el pago

---

### PASO 7: MIRA LOS LOGS (MUY IMPORTANTE)

**Inmediatamente después de completar el pago**, mira los logs de Docker.

Deberías ver estos mensajes con emojis:

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

### ¿Qué significa cada resultado?

#### ✅ SI VES ESTOS MENSAJES:
- **¡PERFECTO!** El webhook funciona
- La orden se guardó en la base de datos
- Ve al panel de admin y refresca la página
- Deberías ver la venta

#### ❌ SI NO VES ESTOS MENSAJES:
- El webhook NO se ejecutó
- Mercado Pago no pudo comunicarse con tu servidor
- Verifica:
  1. ¿ngrok está corriendo?
  2. ¿La URL en MP coincide con la de ngrok?
  3. ¿El BACKEND_URL en .env es correcto?
  4. ¿Docker está corriendo?

---

### PASO 8: Verifica en el panel de admin

1. Ve a http://localhost:5173/admin
2. Inicia sesión
3. Ve a **"Dashboard"** o **"Ventas"**
4. **Refresca la página** (F5)
5. Deberías ver:
   - Total revenue: $XXXX
   - Total orders: 1 (o más)
   - La venta en la lista

---

## 🐛 PROBLEMAS COMUNES

### "No veo los mensajes con emojis en los logs"

**Causa:** El webhook NO se está ejecutando

**Solución:**
1. Verifica que ngrok esté corriendo
2. Verifica que la URL en MP sea correcta
3. Haz una prueba manual:
   ```bash
   curl -X POST https://TU-URL-NGROK.ngrok-free.dev/api/checkout/webhook \
        -H "Content-Type: application/json" \
        -d '{"type":"test"}'
   ```
   Deberías ver `{"status":"ok"}` y en los logs: `🔔 Webhook recibido`

### "La URL de ngrok sigue cambiando"

**Causa:** Cada vez que reinicias ngrok, la URL cambia (versión gratuita)

**Solución:**
- Usa un plan de ngrok de pago para tener URL fija, O
- Cada vez que reinicies ngrok, actualiza el .env y la configuración en MP

### "El pago se completa pero no aparece"

**Causa 1:** El webhook no se ejecutó (más probable)
- Mira los logs, si no ves los emojis, el webhook no funciona

**Causa 2:** Stock insuficiente
- En los logs verías: `❌ Error CRÍTICO: Stock insuficiente`

**Causa 3:** Error en la base de datos
- En los logs verías: `❌ Error inesperado`

---

## ✅ CHECKLIST FINAL

Antes de hacer una compra, verifica:

- [ ] ngrok está corriendo y tienes la URL
- [ ] El BACKEND_URL en `.env` es la URL de ngrok
- [ ] El webhook en Mercado Pago apunta a: `https://tu-ngrok.ngrok-free.dev/api/checkout/webhook`
- [ ] Docker está corriendo (`docker compose up`)
- [ ] El endpoint de prueba funciona: `https://tu-ngrok.ngrok-free.dev/api/checkout/webhook-test`
- [ ] Los logs de Docker están visibles en la terminal

Si todos estos puntos están ✅, haz la compra de prueba y MIRA LOS LOGS.

---

## 💡 NOTA IMPORTANTE

El código ya está CORREGIDO. El `await db.commit()` está en su lugar.

El problema ahora es **100% de configuración del webhook**. No es un problema de código.

Si ves los mensajes con emojis en los logs = TODO FUNCIONA ✅
Si NO ves los mensajes = El webhook NO se está ejecutando ❌

---

¿Necesitas ayuda con algún paso específico?
