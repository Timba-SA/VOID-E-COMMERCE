"""
Script de prueba para verificar la URL de reset de contraseña
"""
from settings import settings

# Simular lo que hace el email_service
token_ejemplo = "abc123xyz456token789"

# Método actual
frontend_url = settings.FRONTEND_URL.rstrip('/')
reset_link = f"{frontend_url}/reset-password/{token_ejemplo}"

print("=" * 70)
print("🔍 VERIFICACIÓN DE URL DE RESET DE CONTRASEÑA")
print("=" * 70)
print(f"\n1. FRONTEND_URL desde .env:")
print(f"   {settings.FRONTEND_URL}")
print(f"\n2. FRONTEND_URL normalizada (sin barra final):")
print(f"   {frontend_url}")
print(f"\n3. URL completa de reset generada:")
print(f"   {reset_link}")
print(f"\n4. ¿Tiene doble barra? {'❌ SÍ - PROBLEMA!' if '//' in reset_link.replace('http://', '').replace('https://', '') else '✅ NO - CORRECTO'}")
print("\n" + "=" * 70)

# Verificar que la URL sea válida
import re
if re.match(r'^https?://[^/]+/reset-password/[a-zA-Z0-9]+$', reset_link):
    print("✅ FORMATO DE URL VÁLIDO")
else:
    print("❌ FORMATO DE URL INVÁLIDO")

print("\n💡 Copia esta URL y pruébala en tu navegador:")
print(f"   {reset_link}")
print("\n   (Reemplaza el token con el real que recibiste en el email)")
print("=" * 70)
