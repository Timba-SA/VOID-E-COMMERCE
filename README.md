# VOID E-COMMERCE

[![Backend CI - Python Tests](https://github.com/Timba-SA/VOID-E-COMMERCE/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/Timba-SA/VOID-E-COMMERCE/actions/workflows/backend-ci.yml)
![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)
![Framework](https://img.shields.io/badge/framework-FastAPI-green.svg)
![Frontend](https://img.shields.io/badge/frontend-React-blue.svg)

Una plataforma de e-commerce full-stack para la marca de indumentaria "VOID", construida con un backend robusto y asincrónico en FastAPI y un frontend moderno e interactivo en React.



---

## Tabla de Contenidos
1.  [Descripción del Proyecto](#1-descripción-del-proyecto)
2.  [Características Principales](#2-características-principales)
3.  [Tecnologías Utilizadas](#3-tecnologías-utilizadas)
4.  [Prerrequisitos](#4-prerrequisitos)
5.  [Instalación y Puesta en Marcha](#5-instalación-y-puesta-en-marcha)
6.  [Ejecutando la Aplicación](#6-ejecutando-la-aplicación)
7.  [Ejecutando los Tests](#7-ejecutando-los-tests)
8.  [Documentación de la API](#8-documentación-de-la-api)
9.  [Integración Continua (CI/CD)](#9-integración-continua-cicd)

---

## 1. Descripción del Proyecto

**VOID E-COMMERCE** es una solución completa para la venta online de indumentaria. La arquitectura está diseñada para ser escalable, segura y de alto rendimiento, utilizando un stack tecnológico moderno. El backend maneja toda la lógica de negocio, incluyendo gestión de productos, autenticación de usuarios, un carrito de compras persistente, checkout integrado con MercadoPago y un panel de administración. El frontend, construido con React y Vite, ofrece una experiencia de usuario rápida y fluida.

El proyecto ha sido sometido a un riguroso proceso de auditoría y mejora, implementando las mejores prácticas de la industria en cuanto a configuración, seguridad, testing automatizado y performance.

---

## 2. Características Principales

* **Autenticación JWT:** Sistema de registro y login seguro basado en tokens.
* **Catálogo de Productos:** Gestión completa de productos, categorías y variantes (talle, color).
* **Carrito de Compras:** Funcionalidad de carrito tanto para usuarios invitados como registrados, con fusión automática al iniciar sesión.
* **Checkout con MercadoPago:** Integración con la pasarela de pagos de MercadoPago.
* **Panel de Administración:** Endpoints protegidos para la gestión de ventas, usuarios y productos.
* **Chatbot con IA:** Asistente de ventas inteligente (Kara) integrado con Groq para responder consultas de usuarios en tiempo real.
* **Seguridad Mejorada:** Implementación de Rate Limiting para protección contra ataques de fuerza bruta.
* **Arquitectura Optimizada:** Uso de Caché con Redis para acelerar respuestas y una cola de tareas con Celery para procesar trabajos pesados (como el envío de emails) en segundo plano.

---

## 3. Tecnologías Utilizadas

### Backend (`/server`)
* **Framework:** FastAPI
* **Lenguaje:** Python 3.11
* **Bases de Datos:**
    * MySQL (gestionado por SQLAlchemy) para datos transaccionales (órdenes, productos).
    * MongoDB (gestionado por Motor) para datos no estructurados (usuarios, carritos).
* **Asincronía:** Uvicorn como servidor ASGI, Gunicorn para producción.
* **Seguridad:** Passlib con bcrypt para hashing de contraseñas, JWT para autenticación.
* **Optimización:** Redis para caché y como broker de Celery.
* **Tareas en Segundo Plano:** Celery.
* **Testing:** Pytest, httpx, mongomock.
* **Monitoreo:** Sentry para seguimiento de errores.

### Frontend (`/client`)
* **Framework:** React 18
* **Bundler:** Vite
* **Lenguaje:** JavaScript (JSX)
* **Estilos:** Tailwind CSS, PostCSS

---

## 4. Prerrequisitos

Para levantar el entorno de desarrollo, necesitás tener instalado en tu máquina:
* Git
* Python (versión 3.11 o superior)
* Node.js (versión 20 o superior)
* Docker y Docker Compose

---

## 5. Instalación y Puesta en Marcha

1.  **Clonar el repositorio:**
    ```bash
    git clone [https://github.com/Timba-SA/VOID-E-COMMERCE.git](https://github.com/Timba-SA/VOID-E-COMMERCE.git)
    cd VOID-E-COMMERCE
    ```

2.  **Configurar las Variables de Entorno:**
    * En la **raíz del proyecto**, vas a encontrar un archivo llamado `.env.example`.
    * Hacé una copia de este archivo y renombrala a `.env`.
    * Abrí el nuevo archivo `.env` y completá todas las claves (`SECRET_KEY`, URLs de bases de datos, tokens de APIs, etc.) con tus valores de desarrollo.

---

## 6. Ejecutando la Aplicación

La forma recomendada y más simple de levantar todo el entorno de desarrollo es usando Docker Compose.

**Desde la raíz del proyecto**, ejecutá el siguiente comando:
```bash
docker compose up --build
```
Este comando hará lo siguiente:

* Construirá las imágenes de Docker para el backend y el frontend.

* Levantará 4 contenedores: backend, frontend, redis y un worker de Celery.

* La aplicación estará disponible en las siguientes URLs:

    * Frontend: http://localhost:5173
    * Backend API: http://localhost:8000


**Nota:** En caso de no usar Docker se puede acceder al proyecto de la siguiente manera.

1. Abrir una terminal desde la carpeta del backend(`server`), crear el entorno virtual y activarlo.
```bash
# Crear el entorno virtual
python -m venv .venv
# Activar el entorno virtual
.\.venv\Scripts\activate
```

2. Una vez dentro del entorno virtual instalar las dependencias y luego ejecutar el backend.
```bash
# Instalar las dependencias
pip install -r requirements-dev.txt
# Ejecutar el backend
python -m uvicorn main:app --reload
```

3. **Sin cerrar la terminal del backend**. Abrir otra terminal desde el frontend(`client`), instalar las dependencias de node e inicializar el servidor.
```bash
# Instalar las dependencias de node
npm install
# Inicializar el servidor
npm run dev
```

4. Para ingresar a la aplicación utilizar las URLs generadas en las terminales anteriores.

---

## 7. Ejecutando los Tests

Los tests del backend están diseñados para correr de forma aislada. Para ejecutarlos, seguí estos pasos:

1. **Levantar el servicio de Redis:** Los tests de login dependen de Redis para el Rate Limiting. 

    Levantalo en segundo plano:

```bash
docker compose up -d redis
```

2. **Correr Pytest:** Navegá a la carpeta del backend(`server`), crea el entorno virtual, activá el entorno virtual y ejecutá pytest.

```bash
cd server
# Crear el entorno virtual (en caso de no tenerlo creado)
python -m venv .venv
# Activar el entorno virtual (ejemplo para Windows PowerShell)
.\.venv\Scripts\activate
# Correr los tests
python -m pytest
```

---

## 8. Documentación de la API

Gracias a FastAPI, la documentación de la API se genera automáticamente y está siempre actualizada. Una vez que el backend esté corriendo, podés acceder a ella en:

- Swagger UI: http://localhost:8000/docs

- ReDoc: http://localhost:8000/redoc

---

## 9. Integración Continua (CI/CD)
Este proyecto tiene configurado un pipeline de Integración Continua (CI) con GitHub Actions. Cada vez que se sube código a las ramas master o develop, un robot ejecuta automáticamente toda la suite de tests del backend para asegurar la calidad y estabilidad del código.


--- 

