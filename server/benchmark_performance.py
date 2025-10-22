"""
Script de prueba de rendimiento - Compara velocidad con y sin cache
Ejecutar cuando el backend esté corriendo
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_endpoint(name, url, iterations=3):
    """Prueba un endpoint múltiples veces y mide el rendimiento."""
    print(f"\n{'='*70}")
    print(f"🧪 Probando: {name}")
    print(f"{'='*70}")
    
    times = []
    cache_statuses = []
    
    for i in range(iterations):
        start = time.time()
        
        try:
            response = requests.get(url, timeout=10)
            elapsed = (time.time() - start) * 1000  # ms
            
            if response.status_code == 200:
                cache_status = response.headers.get('X-Cache-Status', 'UNKNOWN')
                cache_statuses.append(cache_status)
                times.append(elapsed)
                
                icon = "⚡" if cache_status == "HIT" else "🔄"
                print(f"  {icon} Iteración {i+1}: {elapsed:.2f}ms [{cache_status}]")
            else:
                print(f"  ❌ Error: Status {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return None
    
    if times:
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        # Calcular mejora si hay HITs
        miss_times = [t for t, s in zip(times, cache_statuses) if s == "MISS"]
        hit_times = [t for t, s in zip(times, cache_statuses) if s == "HIT"]
        
        print(f"\n  📊 Estadísticas:")
        print(f"     • Promedio: {avg_time:.2f}ms")
        print(f"     • Mínimo: {min_time:.2f}ms")
        print(f"     • Máximo: {max_time:.2f}ms")
        
        if miss_times and hit_times:
            avg_miss = sum(miss_times) / len(miss_times)
            avg_hit = sum(hit_times) / len(hit_times)
            improvement = ((avg_miss - avg_hit) / avg_miss) * 100
            
            print(f"\n  🚀 Mejora con Cache:")
            print(f"     • Sin cache (MISS): {avg_miss:.2f}ms")
            print(f"     • Con cache (HIT): {avg_hit:.2f}ms")
            print(f"     • Mejora: {improvement:.1f}% más rápido ⚡")
        
        return {
            "avg": avg_time,
            "min": min_time,
            "max": max_time,
            "cache_statuses": cache_statuses
        }
    
    return None

def clear_cache():
    """Limpia el cache de Redis."""
    try:
        import redis
        from settings import settings
        
        r = redis.from_url(settings.REDIS_URL)
        r.flushdb()
        print("\n🗑️ Cache limpiado!")
        return True
    except Exception as e:
        print(f"\n⚠️ No se pudo limpiar el cache: {e}")
        return False

def main():
    print("=" * 70)
    print("⚡ PRUEBA DE RENDIMIENTO - VOID E-COMMERCE")
    print("=" * 70)
    print("\n💡 Asegúrate de que el backend esté corriendo en http://localhost:8000")
    input("\nPresiona ENTER para comenzar...")
    
    # Limpiar cache antes de empezar
    clear_cache()
    time.sleep(1)
    
    # Test 1: Categorías
    test_endpoint(
        "GET /api/categories",
        f"{BASE_URL}/api/categories",
        iterations=5
    )
    
    time.sleep(0.5)
    
    # Test 2: Productos (sin filtros)
    test_endpoint(
        "GET /api/products (todos)",
        f"{BASE_URL}/api/products?limit=12",
        iterations=5
    )
    
    time.sleep(0.5)
    
    # Test 3: Productos por categoría
    test_endpoint(
        "GET /api/products (categoría 1)",
        f"{BASE_URL}/api/products?categoria_id=1&limit=12",
        iterations=5
    )
    
    time.sleep(0.5)
    
    # Test 4: Productos con filtros
    test_endpoint(
        "GET /api/products (con filtros)",
        f"{BASE_URL}/api/products?categoria_id=1&precio_max=50000&sort_by=precio_asc&limit=12",
        iterations=5
    )
    
    print("\n" + "=" * 70)
    print("✅ PRUEBA COMPLETADA")
    print("=" * 70)
    
    print("\n📈 Observaciones:")
    print("  • Primera llamada: MISS (va a PostgreSQL)")
    print("  • Llamadas siguientes: HIT (desde Redis)")
    print("  • Mejora esperada: 90-95% más rápido con cache")
    print("\n💡 Tip: Ejecuta este script varias veces para ver la diferencia!")

if __name__ == "__main__":
    main()
