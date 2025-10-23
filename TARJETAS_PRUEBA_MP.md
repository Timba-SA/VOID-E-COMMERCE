# 💳 Tarjetas de Prueba - Mercado Pago Argentina

## ✅ Aprobación Inmediata (RECOMENDADA PARA TESTING)

### 🏆 Mastercard - Aprobación Automática
- **Número:** `5031 7557 3453 0604`
- **Titular:** `APRO`
- **Vencimiento:** Cualquier fecha futura (ej: `11/25`, `12/26`)
- **CVV:** `123`
- **DNI/Documento:** Cualquier número válido

### 🏆 Visa - Aprobación Automática
- **Número:** `4509 9535 6623 3704`
- **Titular:** `APRO`
- **Vencimiento:** Cualquier fecha futura
- **CVV:** `123`
- **DNI/Documento:** Cualquier número válido

---

## ❌ Rechazos (Para Testing de Errores)

### 💰 Fondos Insuficientes
- **Número:** `5031 7557 3453 0604`
- **Titular:** `OTHE`
- **Vencimiento:** Cualquier fecha futura
- **CVV:** `123`

### 📞 Llamar para Autorizar
- **Número:** `5031 7557 3453 0604`
- **Titular:** `CALL`
- **Vencimiento:** Cualquier fecha futura
- **CVV:** `123`

### 🚫 Rechazado por Datos Inválidos
- **Número:** `5031 7557 3453 0604`
- **Titular:** `EXPI`
- **Vencimiento:** Cualquier fecha futura
- **CVV:** `123`

---

## 🎯 Cómo Usar

### 1. El nombre del titular determina el resultado:
- `APRO` → ✅ Aprobado
- `OTHE` → ❌ Rechazado (otros motivos)
- `CALL` → ❌ Rechazado (llamar para autorizar)
- `EXPI` → ❌ Rechazado (tarjeta vencida)

### 2. Cualquier fecha futura funciona para vencimiento
- `11/25` ✅
- `12/26` ✅
- `01/30` ✅

### 3. CVV siempre puede ser `123`

### 4. DNI/Documento puede ser cualquier número
- `12345678` ✅
- `20304050` ✅

---

## 🔧 Troubleshooting

### ⚠️ Si Mercado Pago rechaza tu tarjeta:

1. **Verifica que el titular sea EXACTAMENTE `APRO`**
   - ✅ `APRO`
   - ❌ `apro`
   - ❌ `Apro`
   - ❌ `APPROVED`

2. **Usa la tarjeta Mastercard completa:**
   - `5031 7557 3453 0604`

3. **Verifica que estés en modo Sandbox:**
   - Las credenciales del backend deben ser TEST (no PROD)
   - `MP_ACCESS_TOKEN` debe empezar con `TEST-`

4. **Intenta con Visa si Mastercard falla:**
   - `4509 9535 6623 3704`
   - Titular: `APRO`

5. **Borra cookies y cache del navegador:**
   - A veces MP cachea información de pagos anteriores

---

## 📚 Documentación Oficial

Para más información sobre tarjetas de prueba:
https://www.mercadopago.com.ar/developers/es/docs/checkout-api/testing

---

## ✨ Testing Exitoso

Si todo funciona correctamente verás:
1. ✅ Pago procesado exitosamente en MP
2. ✅ Botón "Volver al sitio" aparece
3. ✅ Redirección a `/payment/success?order_id=X`
4. ✅ Página muestra "COMPRA EXITOSA"
5. ✅ Orden con estado "Pendiente" (luego webhook la actualizará)
