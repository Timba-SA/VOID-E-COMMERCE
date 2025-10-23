# 🧪 Pasos para probar el flujo de Mercado Pago

## ✅ Cambios realizados:

1. **CheckoutPage.jsx**: Simplificado para redirigir en la misma pestaña a Mercado Pago
2. **checkout_router.py**: Crea orden PENDIENTE antes de MP y añade `order_id` a los back_urls
3. **PaymentSuccessPage.jsx**: Detecta el `order_id` de la URL y muestra la orden

## 📋 Flujo completo:

```
1. Usuario → Checkout → Clic en "Realizar Pedido"
   ↓
2. Backend crea ORDEN PENDIENTE (ID: 123) en la DB
   ↓
3. Backend crea preferencia MP con back_urls:
   - success: http://localhost:5173/payment/success?order_id=123
   - failure: http://localhost:5173/payment/failure?order_id=123
   ↓
4. Frontend redirige a Mercado Pago (init_point)
   ↓
5. Usuario completa el pago en MP (tarjeta de prueba)
   ↓
6. MP muestra "Pago aprobado" + botón "Volver al sitio"
   ↓
7. Usuario hace clic en "Volver al sitio"
   ↓
8. MP redirige a: http://localhost:5173/payment/success?order_id=123
   ↓
9. PaymentSuccessPage detecta order_id=123 y consulta la orden
   ↓
10. Página muestra: "COMPRA EXITOSA" con detalles de la orden
```

## 🧪 Cómo probar:

### 1. Asegúrate de que el backend está corriendo:
```bash
# Verifica que los contenedores estén up
docker compose ps
```

### 2. Ve al frontend:
```
http://localhost:5173
```

### 3. Realiza una compra de prueba:
- Agrega productos al carrito
- Ve al checkout
- Completa la dirección de envío
- Haz clic en "Realizar Pedido"
- Serás redirigido a Mercado Pago

### 4. En Mercado Pago (Sandbox):
**Tarjetas de prueba aprobadas:**
- Número: `5031 7557 3453 0604`
- Vencimiento: Cualquier fecha futura (ej: 11/25)
- CVV: `123`
- Titular: `APRO` (importante usar este nombre)

### 5. Después del pago:
- MP mostrará "Pago aprobado"
- **Haz clic en el botón "Volver al sitio"** (importante)
- Deberías ver la página de compra exitosa con los detalles de tu orden

## ⚠️ Notas importantes:

### En localhost (HTTP):
- `auto_return` está DESHABILITADO (MP lo requiere)
- El usuario DEBE hacer clic manualmente en "Volver al sitio"
- La URL tendrá `?order_id=123` (orden creada antes del pago)

### En producción (HTTPS):
- `auto_return` estará HABILITADO
- MP redirigirá AUTOMÁTICAMENTE después del pago
- No necesitas hacer clic en nada

## 🔍 Debugging:

### Si no redirige después del pago:
1. Verifica en la consola del navegador (F12) si hay errores
2. Mira los logs del backend:
   ```bash
   docker compose logs backend | grep "Orden PENDIENTE"
   ```
3. Verifica que la URL después del pago tenga `?order_id=`

### Si dice "orden no encontrada":
1. Verifica que estés logueado con el mismo usuario
2. Revisa los logs del backend para ver si hubo error al crear la orden pendiente
3. Consulta la DB directamente:
   ```sql
   SELECT * FROM ordenes ORDER BY creado_en DESC LIMIT 5;
   ```

## 🎯 Resultado esperado:

✅ Orden PENDIENTE creada ANTES de ir a MP  
✅ Pago completado en MP  
✅ Clic en "Volver al sitio"  
✅ Redirección a `/payment/success?order_id=123`  
✅ Página muestra: "COMPRA EXITOSA" con detalles  
✅ Estado: "Pendiente" (hasta que el webhook actualice)  
✅ Webhook actualiza estado a "Aprobado" en segundo plano  
