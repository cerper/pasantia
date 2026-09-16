# Movilnet Intelligence

Aplicación web para la gestión, edición y presentación de reportes de competencia del mercado telecomunicativo.

## Descripción

Movilnet Intelligence es una plataforma desarrollada con Flask para centralizar la creación de reportes competitivos relacionados con la operación de Movilnet. La herramienta permite documentar la situación actual de los competidores, definir escenarios estratégicos, registrar seguimiento de campañas y exportar la información en una presentación profesional en formato PPTX.

El sistema está pensado para equipos de inteligencia competitiva, analistas y administradores que necesitan mantener reportes estructurados, revisables y listos para presentar.

## Características principales

- Registro e inicio de sesión de usuarios.
- Control de acceso por roles: Admin y Usuario.
- Gestión de reportes de competencia.
- Registro de situación actual para Movistar y Digitel.
- Creación de múltiples escenarios con categoría, análisis y curso de acción.
- Seguimiento de campañas por operadora.
- Carga de imágenes y métricas visuales.
- Generación automática de presentación PowerPoint.
- Dashboard para consultar y administrar reportes.

## Stack tecnológico

- Python
- Flask
- SQLAlchemy
- Flask-Login
- Flask-Migrate
- MariaDB
- Jinja2
- python-pptx
- Pillow
- Tailwind CSS

## Estructura del proyecto

```text
pasantia/
├── app.py
├── requirements.txt
├── package.json
├── tailwind.config.js
├── migrations/
├── static/
│   ├── js/
│   ├── src/
│   └── uploads/
├── templates/
│   ├── index.html
│   ├── registro.html
│   ├── reportes.html
│   ├── dashboard.html
│   ├── editar_reporte.html
│   ├── presentacion.html
│   └── layout.html
└── README.md
```

## Instalación

### Requisitos

- Python 3.10+
- MariaDB o MySQL
- pip

### Pasos

1. Clona el repositorio.
2. Accede a la carpeta del proyecto.
3. crea un entorno virtual e inicialo
```bash
python3 -m venv venv
source venv/bin/activate
```
4. Instala las dependencias:

```bash
pip install -r requirements.txt
```

5. Configura la conexión a la base de datos en la aplicación.
```bash
 sudo systemctl start mariadb 
```

6. Ejecuta la aplicación:

```bash
flask run
```

## Uso

1. Registra un usuario o inicia sesión.
2. Crea un reporte de competencia.
3. Completa la información de situación actual, escenarios y seguimiento de campañas.
4. Guarda el reporte y revisa su estado.
5. Desde la gestion de reportes puedes editar o generar la presentación final.
6. Descarga el archivo PPTX generado desde la vista de presentación.

## Modelo de negocio

El sistema está orientado a la gestión de información competitiva en telecomunicaciones, permitiendo transformar análisis cualitativos y visuales en presentaciones ejecutivas útiles para toma de decisiones.

## Estado del proyecto

Proyecto en desarrollo activo, orientado a la gestión interna de reportes y entregables ejecutivos.

