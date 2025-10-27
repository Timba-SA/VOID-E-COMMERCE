"""
Script para diagnosticar el sistema de emails de confirmacion de compra.
Ejecutar con: python test_email_system.py
"""

import asyncio
import sys
import os

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(__file__))

from database import database
from database.models import Orden
from sqlalchemy import select, desc
from workers.transactional_tasks import enviar_email_confirmacion_compra_task
from services import email_service
from settings import settings

# Inicializar el engine de la base de datos
database.setup_database_engine()


async def check_email_config():
    """Verificar configuracion de email"""
    print("\n" + "="*80)
    print("🔍 VERIFICANDO CONFIGURACION DE EMAIL")
    print("="*80)
    
    print(f"\n📧 EMAIL_SENDER: {settings.EMAIL_SENDER if settings.EMAIL_SENDER else '❌ NO CONFIGURADO'}")
    print(f"🔑 EMAIL_APP_PASSWORD: {'✅ Configurado' if settings.EMAIL_APP_PASSWORD else '❌ NO CONFIGURADO'}")
    print(f"📥 IMAP_SERVER: {settings.IMAP_SERVER}")
    
    if not settings.EMAIL_SENDER or not settings.EMAIL_APP_PASSWORD:
        print("\n❌ ERROR: Las credenciales de email NO están configuradas!")
        print("   Necesitas configurar EMAIL_SENDER y EMAIL_APP_PASSWORD en tus variables de entorno.")
        return False
    
    print("\n✅ Configuracion de email OK")
    return True


async def check_redis_connection():
    """Verificar conexion a Redis"""
    print("\n" + "="*80)
    print("🔍 VERIFICANDO CONEXION A REDIS")
    print("="*80)
    
    try:
        from celery_worker import celery_app
        
        # Intentar hacer ping a Redis
        result = celery_app.control.ping(timeout=5)
        
        if result:
            print(f"\n✅ Redis conectado correctamente")
            print(f"   Workers activos: {list(result[0].keys())}")
            return True
        else:
            print("\n❌ No se pudo conectar a Redis")
            return False
            
    except Exception as e:
        print(f"\n❌ Error al conectar a Redis: {e}")
        return False


async def get_latest_order():
    """Obtener la ultima orden de la base de datos"""
    print("\n" + "="*80)
    print("🔍 BUSCANDO ULTIMA ORDEN EN LA BASE DE DATOS")
    print("="*80)
    
    try:
        async with database.AsyncSessionLocal() as session:
            stmt = select(Orden).order_by(desc(Orden.id)).limit(1)
            result = await session.execute(stmt)
            orden = result.scalar_one_or_none()
            
            if orden:
                print(f"\n✅ Orden encontrada:")
                print(f"   ID: {orden.id}")
                print(f"   Usuario ID (Email): {orden.usuario_id}")
                print(f"   Monto Total: ${orden.monto_total}")
                print(f"   Estado: {orden.estado}")
                print(f"   Estado Pago: {orden.estado_pago}")
                print(f"   Creada: {orden.creado_en}")
                return orden
            else:
                print("\n❌ No se encontraron ordenes en la base de datos")
                return None
                
    except Exception as e:
        print(f"\n❌ Error al consultar la base de datos: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_email_task(order_id: int):
    """Probar enviar email para una orden especifica"""
    print("\n" + "="*80)
    print(f"🚀 PROBANDO ENVIO DE EMAIL PARA ORDEN {order_id}")
    print("="*80)
    
    try:
        # Importar la funcion interna directamente para probarla
        from workers.transactional_tasks import _send_purchase_confirmation_email
        
        print(f"\n📧 Ejecutando funcion de envio de email...")
        await _send_purchase_confirmation_email(order_id)
        print(f"\n✅ Email enviado exitosamente!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error al enviar email: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_celery_task(order_id: int):
    """Probar encolar tarea de Celery"""
    print("\n" + "="*80)
    print(f"🚀 PROBANDO ENCOLAR TAREA DE CELERY PARA ORDEN {order_id}")
    print("="*80)
    
    try:
        task_result = enviar_email_confirmacion_compra_task.delay(order_id)
        print(f"\n✅ Tarea encolada exitosamente!")
        print(f"   Task ID: {task_result.id}")
        print(f"   Estado: {task_result.state}")
        
        print(f"\n⏳ Esperando resultado (timeout: 30s)...")
        result = task_result.get(timeout=30)
        print(f"✅ Tarea completada exitosamente!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error al encolar/ejecutar tarea: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Funcion principal de diagnostico"""
    print("\n" + "="*80)
    print("🔧 DIAGNOSTICO DEL SISTEMA DE EMAILS DE CONFIRMACION")
    print("="*80)
    
    # 1. Verificar configuracion de email
    email_ok = await check_email_config()
    
    if not email_ok:
        print("\n⚠️  No se puede continuar sin configuracion de email")
        return
    
    # 2. Verificar conexion a Redis
    redis_ok = await check_redis_connection()
    
    # 3. Obtener ultima orden
    orden = await get_latest_order()
    
    if not orden:
        print("\n⚠️  No hay ordenes para probar")
        return
    
    # 4. Probar envio directo de email
    print("\n" + "="*80)
    print("OPCION 1: Enviar email directamente (sin Celery)")
    print("="*80)
    email_sent = await test_email_task(orden.id)
    
    # 5. Si Redis esta OK, probar con Celery
    if redis_ok:
        print("\n" + "="*80)
        print("OPCION 2: Enviar email via Celery (cola de tareas)")
        print("="*80)
        await test_celery_task(orden.id)
    else:
        print("\n⚠️  No se puede probar Celery porque Redis no esta conectado")
    
    print("\n" + "="*80)
    print("✅ DIAGNOSTICO COMPLETO")
    print("="*80)
    
    if not email_sent:
        print("\n❌ PROBLEMA ENCONTRADO:")
        print("   El email NO se esta enviando correctamente.")
        print("\n💡 POSIBLES CAUSAS:")
        print("   1. Credenciales de email incorrectas")
        print("   2. Configuracion de SMTP de Gmail")
        print("   3. Error en el template HTML")
        print("   4. Problema con la base de datos")


if __name__ == "__main__":
    asyncio.run(main())
