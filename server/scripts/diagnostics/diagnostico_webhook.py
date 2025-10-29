"""
Script para diagnosticar por qué el webhook NO se está ejecutando
"""
import sys
import os

# Leer el .env para obtener la configuración actual
env_file = os.path.join(os.path.dirname(__file__), '..', '.env')

backend_url = None
if os.path.exists(env_file):
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('BACKEND_URL='):
                backend_url = line.split('=', 1)[1].strip().strip('"')
                break

print("\n" + "="*80)
print("🚨 PROBLEMA: Las ventas no aparecen en el admin")
print("="*80 + "\n")

print("📊 SÍNTOMAS:")
print("   ✅ El pago en Mercado Pago se procesa correctamente")
print("   ❌ La orden NO aparece en el panel de admin")
print("   ❌ El dashboard muestra $0 en ingresos y 0 órdenes")
print()

print("🔍 DIAGNÓSTICO:")
print("   El problema es que el WEBHOOK de Mercado Pago NO se está ejecutando")
print("   Esto significa que MP no puede comunicarse con tu servidor")
print()

print("="*80)
print("💡 SOLUCIÓN - Sigue estos pasos EXACTAMENTE:")
print("="*80 + "\n")

print("PASO 1: Verifica que ngrok esté corriendo")
print("-" * 80)
print("   1. Abre una nueva terminal")
print("   2. Ejecuta: ngrok http 8000")
print("   3. Copia la URL que te da (ej: https://xxxx-xxx.ngrok-free.dev)")
print()

if backend_url:
    print(f"   📍 Tu BACKEND_URL actual es: {backend_url}")
    print(f"   🌐 URL del webhook: {backend_url}/api/checkout/webhook")
else:
    print("   ⚠️  No se pudo leer el BACKEND_URL del archivo .env")

print()
print("PASO 2: Prueba que el webhook sea accesible")
print("-" * 80)
if backend_url:
    print(f"   Abre tu navegador y ve a:")
    print(f"   {backend_url}/api/checkout/webhook-test")
    print()
    print("   Deberías ver un mensaje que dice:")
    print("   ✅ El webhook está accesible desde internet")
    print()
    print("   Si ves un error o no carga:")
    print("   ❌ Verifica que ngrok esté corriendo")
    print("   ❌ Verifica que el BACKEND_URL en .env sea correcto")
    print("   ❌ Verifica que Docker esté corriendo")
else:
    print("   ⚠️  Configura el BACKEND_URL en tu archivo .env primero")

print()
print("PASO 3: Configura el webhook en Mercado Pago")
print("-" * 80)
print("   1. Ve a: https://www.mercadopago.com.ar/developers/panel")
print("   2. Selecciona tu aplicación")
print("   3. Ve a la sección 'Webhooks' en el menú lateral")
print("   4. Haz clic en 'Configurar Webhooks'")
print()
if backend_url:
    print(f"   5. En 'URL de producción' o 'URL de pruebas', ingresa:")
    print(f"      {backend_url}/api/checkout/webhook")
else:
    print("   5. En 'URL de producción' o 'URL de pruebas', ingresa:")
    print("      https://TU-URL-DE-NGROK.ngrok-free.dev/api/checkout/webhook")
print()
print("   6. Selecciona el evento: 'Pagos' (payments)")
print("   7. Guarda la configuración")
print()

print("PASO 4: Reinicia Docker para que tome los cambios")
print("-" * 80)
print("   Ejecuta en tu terminal:")
print("   docker compose down")
print("   docker compose up")
print()

print("PASO 5: Realiza una compra de prueba")
print("-" * 80)
print("   1. Ve a http://localhost:5173")
print("   2. Agrega un producto al carrito")
print("   3. Ve al checkout y completa los datos")
print("   4. Usa esta tarjeta de prueba:")
print("      • Número: 4509 9535 6623 3704")
print("      • CVV: 123")
print("      • Vencimiento: 11/25")
print("      • Nombre: APRO")
print("   5. Completa el pago")
print()

print("PASO 6: MIRA LOS LOGS de Docker (ESTO ES CRÍTICO)")
print("-" * 80)
print("   Inmediatamente después de completar el pago, deberías ver:")
print()
print("   🔔 Webhook recibido de Mercado Pago: {...}")
print("   💳 Procesando pago con ID: XXXX")
print("   📋 Información del pago obtenida de MP. Estado: approved")
print("   ✅ Pago aprobado, creando orden...")
print("   💾 Guardando orden en la base de datos...")
print("   🔄 Haciendo commit de la transacción...")
print("   ✅ Orden guardada exitosamente para el pago XXXX")
print()
print("   Si NO ves estos mensajes:")
print("   ❌ El webhook NO se está ejecutando")
print("   ❌ Mercado Pago no puede alcanzar tu servidor")
print("   ❌ Revisa los pasos anteriores")
print()

print("="*80)
print("🔧 PRUEBAS ADICIONALES:")
print("="*80 + "\n")

print("Prueba manual del webhook (desde tu computadora):")
if backend_url:
    print(f"   curl -X POST {backend_url}/api/checkout/webhook \\")
else:
    print("   curl -X POST https://TU-URL-NGROK.ngrok-free.dev/api/checkout/webhook \\")
print('        -H "Content-Type: application/json" \\')
print('        -d \'{"type":"test"}\'')
print()
print("   Deberías ver: {'status': 'ok'}")
print("   Y en los logs de Docker: 🔔 Webhook recibido de Mercado Pago")
print()

print("="*80)
print("📝 CHECKLIST FINAL:")
print("="*80 + "\n")
print("   ☐ ngrok está corriendo")
print("   ☐ La URL de ngrok está en el .env como BACKEND_URL")
print("   ☐ La URL del webhook está configurada en Mercado Pago")
print("   ☐ Docker está corriendo (docker compose up)")
print("   ☐ El endpoint /webhook-test es accesible desde el navegador")
print()

print("="*80)
print()
