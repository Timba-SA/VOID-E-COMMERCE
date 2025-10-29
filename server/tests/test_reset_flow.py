"""
Script de prueba completa del flujo de reset de contraseña
"""
import asyncio
from services.email_service import send_password_reset_email
from utils.security import get_password_hash
import secrets

async def test_reset_flow():
    print("=" * 70)
    print("🧪 PRUEBA DE FLUJO DE RESET DE CONTRASEÑA")
    print("=" * 70)
    
    # Generar un token de prueba
    test_token = secrets.token_urlsafe(32)
    test_email = "voidindumentaria.mza@gmail.com"  # Tu email de la tienda
    
    print(f"\n📧 Email de prueba: {test_email}")
    print(f"🔑 Token generado: {test_token}")
    print(f"\n📨 Enviando email...")
    
    try:
        # Enviar el email
        await send_password_reset_email(test_email, test_token)
        print(f"✅ Email enviado exitosamente!")
        
        # Mostrar la URL que debería aparecer en el email
        from settings import settings
        frontend_url = settings.FRONTEND_URL.rstrip('/')
        expected_url = f"{frontend_url}/reset-password/{test_token}"
        
        print(f"\n🔗 URL en el email:")
        print(f"   {expected_url}")
        
        print(f"\n📋 INSTRUCCIONES:")
        print(f"   1. Revisa tu email en {test_email}")
        print(f"   2. Click en el botón 'CREAR NUEVA CONTRASEÑA'")
        print(f"   3. Deberías ver un formulario para cambiar la contraseña")
        print(f"   4. Si no funciona, copia y pega esta URL en el navegador:")
        print(f"      {expected_url}")
        
    except Exception as e:
        print(f"❌ Error al enviar email: {e}")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    asyncio.run(test_reset_flow())
