# 🛍️ VOID E-Commerce

Proyecto Full Stack de una tienda de ropa online. Incluye un backend robusto con FastAPI para manejar la lógica de negocio, productos, usuarios y pagos, y un frontend interactivo construido con React.

---
## ✨ Tecnologías Utilizadas

* **Backend:**
  * Python 3.11+
  * FastAPI
  * SQLAlchemy (para SQL) y Motor (para NoSQL)
  * Pydantic
  * MySQL (con driver `aiomysql`)
  * MongoDB
  * JWT para autenticación (`python-jose`)
  * Google Generative AI para el Chatbot
  * MercadoPago para la pasarela de pagos

* **Frontend:**
  * React 18+
  * Vite como herramienta de desarrollo
  * JavaScript (ES6+)
  * CSS

---
## 📋 Prerrequisitos

Antes de empezar, asegurate de tener instalado:

* **Python** (versión 3.11 o superior)
* **Node.js** (versión 18.x o superior) y npm
* Un servidor de **MySQL** corriendo en tu máquina.
* Un servidor de **MongoDB** (opcional, si se implementan todas las funcionalidades de usuario NoSQL).
* **Git** para control de versiones.

---
## 🚀 Instalación y Puesta en Marcha

Seguí estos pasos para levantar el proyecto en tu entorno local.

### 1. Preparación del Proyecto

Primero, clonamos el repositorio y preparamos los archivos de configuración inicial.

```bash
# Clonar el repositorio
git clone https://URL_DE_TU_REPOSITORIO.git

# Entrar a la carpeta del proyecto
cd NOMBRE_DE_LA_CARPETA_DEL_PROYECTO
```

**Importante:** Este proyecto usa un archivo `.gitignore` para evitar subir archivos sensibles o innecesarios. Asegurate de que el archivo `.gitignore` exista en la raíz del proyecto y contenga al menos `.env`, `venv/`, y `frontend/node_modules/`.

### 2. Configuración de la Base de Datos

El backend necesita una base de datos MySQL para funcionar.

1.  Abrí tu cliente de MySQL (MySQL Workbench, DBeaver, etc.).
2.  Creá una nueva base de datos y sus tablas correspondientes (si no se crean automáticamente).
    ```sql
    CREATE DATABASE void_db_sql;
    ```
    *Nota: Las tablas se deberían crear automáticamente al iniciar el backend por primera vez gracias al `lifespan` de FastAPI.*

### 3. Configuración del Backend

1.  **Crear el Entorno Virtual:** Desde la carpeta raíz del proyecto, creá el entorno.
    ```bash
    python -m venv venv
    ```

2.  **Activar el Entorno:**
    ```bash
    # En Windows
    .\venv\Scripts\activate
    ```

3.  **Configurar Variables de Entorno:**
    * Este proyecto usa un archivo `.env` para manejar las claves secretas. **Este archivo NO debe subirse a GitHub.**
    * Creá un archivo llamado `.env` dentro de la carpeta `BACKEND`.
    * Copiá y pegá el siguiente contenido, reemplazando los valores con tus propias credenciales.

    ```ini
    # backend/.env
    DATABASE_URL="mysql+aiomysql://TU_USUARIO_MYSQL:TU_CONTRASEÑA@localhost/void_db"
    SECRET_KEY="UNA_CLAVE_SUPER_SECRETA_Y_LARGA_PARA_JWT"
    ALGORITHM="HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES=30
    MERCADOPAGO_ACCESS_TOKEN="TU_ACCESS_TOKEN_DE_MERCADOPAGO"
    GOOGLE_API_KEY="TU_API_KEY_DE_GOOGLE_AI"
    ```

4.  **Instalar Dependencias:** Con el entorno activado, instalá todas las librerías de Python.
    ```bash
    pip install -r backend/requirements.txt
    ```

### 4. Configuración del Frontend

1.  **Navegar a la Carpeta:** Abrí una **nueva terminal** y andá a la carpeta del frontend.
    ```bash
    cd frontend
    ```
2.  **Instalar Dependencias:** Instalamos todas las librerías de Node.js.
    ```bash
    npm install
    ```

---
## ▶️ Ejecutando la Aplicación

Para correr el proyecto, necesitás tener **dos terminales abiertas**.

### Terminal 1: Iniciar el Backend
```bash
# 1. (Si no lo hiciste) Activar el entorno virtual desde la raíz del proyecto
.\venv\Scripts\activate

# 2. Arrancar el servidor de FastAPI
python -m uvicorn main:app --reload
```
El backend estará corriendo en `http://localhost:8000`.

### Terminal 2: Iniciar el Frontend
```bash
# 1. (Si no lo hiciste) Ir a la carpeta del frontend
cd frontend

# 2. Arrancar el servidor de Vite
npm run dev
```
La aplicación web estará disponible en `http://localhost:5173`.

---
## 📚 Documentación de la API

Una vez que el backend esté corriendo, podés acceder a la documentación interactiva de la API (generada por Swagger UI) en la siguiente URL:

[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)