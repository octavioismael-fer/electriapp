# ⚡ ElectriApp

App móvil para registro de trabajos eléctricos. Desarrollada en Python con Flet.

## Correr localmente

```bash
pip install -r requirements.txt
python -m electriapp.main
```

Luego abrí el navegador en `http://localhost:8080`

## Deploy en Render (gratis)

### Paso 1 — Subir a GitHub
1. Creá un repositorio nuevo en github.com (puede ser privado)
2. Desde la carpeta del proyecto:
```bash
git init
git add .
git commit -m "ElectriApp inicial"
git remote add origin https://github.com/TU_USUARIO/electriapp.git
git push -u origin main
```

### Paso 2 — Crear servicio en Render
1. Entrá a https://render.com y creá una cuenta gratuita
2. Clic en **New → Web Service**
3. Conectá tu cuenta de GitHub y seleccioná el repositorio
4. Render detecta el `render.yaml` automáticamente
5. Clic en **Deploy**

### Paso 3 — Usar en el iPhone
1. Abrí Safari en el iPhone
2. Entrá a la URL que te da Render (ej: `https://electriapp.onrender.com`)
3. Tocá el botón de compartir → **Agregar a pantalla de inicio**
4. ¡Listo! La app aparece como si fuera nativa

## Estructura

```
electriapp/
├── main.py                          ← Punto de entrada
├── requirements.txt
├── render.yaml                      ← Config de deploy
├── database/connection.py           ← SQLite
├── models/
│   ├── cliente.py
│   └── trabajo.py
├── controllers/
│   ├── cliente_controller.py
│   └── trabajo_controller.py
└── views/
    ├── vista_inicio.py              ← Lista mensual
    ├── vista_nuevo_trabajo.py       ← Formulario
    └── vista_cliente.py             ← Detalle por cliente
```
