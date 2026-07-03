# Renombrar

Aplicación de escritorio con interfaz Tkinter y backend Python reutilizable, preparado para un futuro frontend Electron.

## Instalación

```powershell
py -m pip install -r requirements.txt
```

## Aplicación actual

```powershell
py renombrar.py
```

## API local

```powershell
py -m backend.api
```

La API escucha solamente en `http://127.0.0.1:8765`. Su documentación interactiva queda disponible en `/docs` y todas las operaciones de la aplicación están bajo `/api/v1`.

## Electron

```powershell
npm install
npm start
```

Electron inicia FastAPI automáticamente. Si Python no está disponible en PATH, configura `RENOMBRAR_PYTHON` con la ruta absoluta del ejecutable o crea `.venv` dentro del proyecto.

## Pruebas

```powershell
py -m pytest -q
```

Las pruebas usan bases SQLite temporales y no modifican `app.db` ni `config.json`.
