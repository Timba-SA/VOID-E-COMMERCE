# Instrucciones de Migración y Optimización

Este documento describe los pasos para aplicar las migraciones y optimizaciones al proyecto VOID E-COMMERCE.

## 📋 Tareas Completadas

### ✅ Tarea 6: Wishlist
- **Backend**: Ya implementado correctamente con React Query
- **Frontend**: Funcionando con invalidación de queries
- **Estado**: ✅ Completado

### ✅ Tarea 8: Restablecer Contraseña
- **ForgotPasswordPage**: Envío de email funcionando
- **ResetPasswordPage**: Cambio de contraseña funcionando
- **Backend**: Endpoints `/forgot-password` y `/reset-password/{token}` listos
- **Estado**: ✅ Completado

### ✅ Tarea 9: Traducción de Categorías
- **Modelo**: Agregado campo `nombre_i18n` (JSON) a `Categoria`
- **Schemas**: Actualizados para soportar traducciones
- **Backend**: Endpoints CRUD completos con soporte i18n
- **Frontend**: Helper `getCategoryName()` para obtener nombre traducido
- **Estado**: ✅ Completado - **REQUIERE MIGRACIÓN**

### ✅ Tarea 7: IA Recuerda Compras
- **Función**: `get_user_purchase_history()` en `chatbot_router.py`
- **Autenticación opcional**: Nuevo endpoint con `get_current_user_optional()`
- **Contexto**: Historial de compras se inyecta en el prompt de la IA
- **Estado**: ✅ Completado

## 🚀 Pasos de Migración

### 1. Migrar Modelo de Categorías

El modelo `Categoria` ahora incluye el campo `nombre_i18n` para soportar traducciones:

```python
nombre_i18n = Column(JSON, nullable=True)  # {"es": "Remeras", "en": "T-shirts"}
```

**Para aplicar cambios a la base de datos:**

```bash
# Desde el directorio server/
cd server

# Ejecutar script de migración de categorías
python migrate_categories_i18n.py
```

Este script:
- Busca todas las categorías existentes
- Agrega traducciones predefinidas para categorías comunes
- Mantiene compatibilidad con el campo `nombre` original

### 2. Optimizar Base de Datos

Después de la migración, ejecutar el script de optimización:

```bash
# Desde el directorio server/
python optimize_database.py
```

Este script:
- Crea índices en tablas principales (productos, ordenes, wishlist, etc.)
- Optimiza búsquedas por categoría, precio, usuario
- Mejora rendimiento del chatbot y órdenes
- Actualiza estadísticas de PostgreSQL

## 📝 Cambios Importantes en el Frontend

### Uso de Categorías Traducidas

Importar el helper en componentes que usen categorías:

```javascript
import { getCategoryName } from '../utils/categoryHelper';
import { useTranslation } from 'react-i18next';

const { i18n } = useTranslation();
const categoryName = getCategoryName(category, i18n.language);
```

### Gestión de Categorías en Admin

El componente `CategoryManagement.jsx` ahora incluye:
- Campos para nombre en Español e Inglés
- Botón de edición para actualizar categorías
- Visualización de traducciones en la tabla

## 🔧 Nuevas Funcionalidades

### 1. Chatbot con Memoria de Compras

El chatbot ahora:
- Detecta si el usuario está autenticado
- Incluye historial de últimas 5 compras
- Personaliza recomendaciones basadas en compras anteriores
- Ejemplo: "Veo que compraste una remera negra antes, ¿te interesa ver más en ese estilo?"

### 2. Sistema de Traducción

Las categorías ahora soportan múltiples idiomas:
- El campo `nombre` se mantiene como identificador único
- El campo `nombre_i18n` contiene traducciones en formato JSON
- Fallback automático si una traducción no existe

## ⚠️ Notas Importantes

### Compatibilidad

Todos los cambios son **retrocompatibles**:
- El campo `nombre` en categorías se mantiene
- Si `nombre_i18n` es `null`, se usa `nombre` como fallback
- APIs existentes siguen funcionando sin cambios

### Cache

El sistema de cache se invalida automáticamente en:
- Creación de categorías
- Actualización de categorías
- Eliminación de categorías

### Seguridad

- La autenticación del chatbot es **opcional**
- Usuarios no autenticados siguen usando el chatbot sin historial de compras
- El historial solo se muestra al usuario autenticado correspondiente

## 📊 Índices Creados

Los siguientes índices mejoran el rendimiento:

- **productos**: categoria_id, precio, nombre (búsqueda full-text)
- **ordenes**: usuario_id, estado_pago, creado_en, payment_id_mercadopago
- **variantes_productos**: producto_id, cantidad_en_stock
- **wishlist_items**: usuario_id, producto_id, (usuario_id + producto_id)
- **conversaciones_ia**: sesion_id, creado_en
- **gastos**: fecha, categoria
- **email_tasks**: status, sender_email

## 🧪 Testing

Después de aplicar las migraciones, verificar:

1. **Categorías**:
   - Crear una categoría con traducciones
   - Editar una categoría existente
   - Cambiar idioma en el frontend y verificar nombres

2. **Chatbot**:
   - Probar como usuario anónimo (sin historial)
   - Probar como usuario autenticado con compras previas
   - Verificar que el chatbot mencione compras anteriores

3. **Wishlist**:
   - Agregar productos a favoritos
   - Verificar que el corazón se marque
   - Ver la página de wishlist

4. **Reset Password**:
   - Solicitar restablecimiento de contraseña
   - Verificar email recibido
   - Cambiar contraseña con el token

## 🎯 Próximos Pasos Sugeridos

1. **Agregar más traducciones**: Extender soporte a portugués, francés, etc.
2. **Panel de traducción en Admin**: UI para gestionar traducciones fácilmente
3. **Caché más agresivo**: Implementar cache en más endpoints
4. **Analytics**: Agregar tracking de preferencias de usuarios
5. **Tests automatizados**: Crear tests para las nuevas funcionalidades

## 📞 Soporte

Si encuentras algún problema durante la migración:
1. Revisa los logs del backend
2. Verifica que las variables de entorno estén configuradas
3. Asegúrate de tener permisos de escritura en la base de datos
4. Contacta al equipo de desarrollo

---

**Fecha de creación**: Octubre 2025  
**Versión**: 1.0.0
