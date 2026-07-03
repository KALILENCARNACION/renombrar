# Renombrar

Aplicación de escritorio Electron con frontend HTML/CSS/JavaScript y backend local Python/FastAPI.

## Ejecutar en desarrollo

```powershell
npm install
npm start
```

Electron inicia FastAPI automáticamente en `http://127.0.0.1:8765`.

## Empaquetar

```powershell
npm run package
```

El ejecutable queda en:

```text
out\renombrar-electron-win32-x64\renombrar-electron.exe
```

## Backend local

Si necesitas iniciar solo la API:

```powershell
.\.venv\Scripts\python.exe -m backend.api
```

La API escucha solamente en `http://127.0.0.1:8765`. Su documentación interactiva queda disponible en `/docs` y todas las operaciones están bajo `/api/v1`.

## Datos

El desarrollo usa `app.db` y `config.json` desde la raíz del proyecto.

El empaquetado incluye una copia inicial en `resources\seed-data` y la copia al perfil de usuario de Electron cuando hace falta.
