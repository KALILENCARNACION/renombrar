const { app, BrowserWindow, clipboard, dialog, ipcMain, nativeImage, shell } = require('electron');
const fs = require('node:fs');
const path = require('node:path');
const { BackendManager } = require('./backend-manager.cjs');
const { updateElectronApp } = require('update-electron-app');
const { startAutoUpdater } = require('./updater.cjs');

// Squirrel ejecuta la aplicaciÃ³n durante las operaciones de instalar, actualizar y desinstalar.
if (require('electron-squirrel-startup')) app.quit();

let mainWindow;
let backend;
const soundWindows = new Set();

app.commandLine.appendSwitch('autoplay-policy', 'no-user-gesture-required');

function projectRoot() {
  return app.isPackaged ? process.resourcesPath : process.cwd();
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1180,
    height: 760,
    minWidth: 920,
    minHeight: 620,
    backgroundColor: '#f8f9ff',
    title: 'Renombrar PDF',
    icon: path.join(projectRoot(), 'control_logo.png'),
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      backgroundThrottling: false
    }
  });

  mainWindow.removeMenu();
  mainWindow.once('ready-to-show', () => mainWindow.show());
  mainWindow.webContents.on('console-message', (event, level, message, line, sourceId) => {
    const detail = typeof event?.message === 'string'
      ? event
      : { level, message, lineNumber: line, sourceId };
    console.log(`[renderer:${detail.level}] ${detail.message} (${detail.sourceId}:${detail.lineNumber})`);
  });
  mainWindow.webContents.on('did-fail-load', (_event, code, description, url) => {
    console.error(`No se pudo cargar la interfaz (${code}): ${description} · ${url}`);
  });
  if (process.env.RENOMBRAR_CAPTURE_PATH) {
    mainWindow.webContents.once('did-finish-load', () => {
      setTimeout(async () => {
        const image = await mainWindow.webContents.capturePage();
        fs.writeFileSync(process.env.RENOMBRAR_CAPTURE_PATH, image.toPNG());
      }, 800);
    });
  }
  if (!app.isPackaged && MAIN_WINDOW_VITE_DEV_SERVER_URL) {
    mainWindow.loadURL(MAIN_WINDOW_VITE_DEV_SERVER_URL);
  } else {
    const rendererPath = path.join(__dirname, `../renderer/${MAIN_WINDOW_VITE_NAME}/index.html`);
    mainWindow.loadFile(rendererPath).catch(error => console.error('No se pudo abrir el renderer empaquetado:', error));
  }
}

function findSoundPath(soundName = 'finalizo') {
  const safeName = String(soundName).replace(/[^a-zA-Z0-9 _-]/g, '').trim() || 'finalizo';
  for (const extension of ['.mp3', '.wav', '.m4a', '.wma']) {
    const soundPath = path.join(projectRoot(), 'sonidos', `${safeName}${extension}`);
    if (fs.existsSync(soundPath)) return { soundPath, extension };
  }
  return null;
}

function soundMimeType(extension) {
  if (extension === '.wav') return 'audio/wav';
  if (extension === '.m4a') return 'audio/mp4';
  return 'audio/mpeg';
}

function soundDataUrl(soundName = 'finalizo') {
  const found = findSoundPath(soundName);
  if (!found) return '';
  return `data:${soundMimeType(found.extension)};base64,${fs.readFileSync(found.soundPath).toString('base64')}`;
}

async function playSoundInBackground(soundName = 'finalizo') {
  const source = soundDataUrl(soundName);
  if (!source) return false;
  const soundWindow = new BrowserWindow({
    width: 1,
    height: 1,
    show: false,
    skipTaskbar: true,
    webPreferences: {
      backgroundThrottling: false,
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    }
  });
  soundWindows.add(soundWindow);
  soundWindow.on('closed', () => soundWindows.delete(soundWindow));
  const html = `<!doctype html><meta charset="utf-8"><audio id="sound" src="${source}" autoplay></audio><script>
    const sound = document.getElementById('sound');
    sound.volume = 1;
    sound.play().catch(() => {});
    sound.addEventListener('ended', () => window.close());
    setTimeout(() => window.close(), 15000);
  </script>`;
  await soundWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(html)}`);
  return true;
}

function registerIpc() {
  ipcMain.handle('backend:status', () => backend.check());
  ipcMain.handle('dialog:pdf', async (_event, multiple = true) => {
    const result = await dialog.showOpenDialog(mainWindow, {
      properties: multiple ? ['openFile', 'multiSelections'] : ['openFile'],
      filters: [{ name: 'Documentos PDF', extensions: ['pdf'] }]
    });
    return result.canceled ? [] : result.filePaths;
  });
  ipcMain.handle('dialog:file', async () => {
    const result = await dialog.showOpenDialog(mainWindow, { properties: ['openFile'] });
    return result.canceled ? null : result.filePaths[0];
  });
  ipcMain.handle('dialog:directory', async () => {
    const result = await dialog.showOpenDialog(mainWindow, { properties: ['openDirectory'] });
    return result.canceled ? null : result.filePaths[0];
  });
  ipcMain.handle('shell:open-path', (_event, targetPath) => {
    if (typeof targetPath !== 'string' || !path.isAbsolute(targetPath)) {
      throw new Error('La ruta debe ser absoluta.');
    }
    return shell.openPath(targetPath);
  });
  ipcMain.handle('clipboard:write', (_event, text) => {
    if (typeof text !== 'string') throw new Error('El contenido debe ser texto.');
    clipboard.writeText(text);
    return true;
  });
  ipcMain.handle('pomodoro:badge', (_event, imageDataUrl, description = '') => {
    if (!mainWindow || mainWindow.isDestroyed()) return false;
    if (!imageDataUrl) {
      mainWindow.setOverlayIcon(null, '');
      return true;
    }
    if (typeof imageDataUrl !== 'string' || !imageDataUrl.startsWith('data:image/png;base64,')) {
      throw new Error('Badge invalido.');
    }
    const image = nativeImage.createFromDataURL(imageDataUrl);
    mainWindow.setOverlayIcon(image, String(description || 'Pomodoro'));
    return true;
  });
  ipcMain.handle('pomodoro:sound-data', (_event, soundName = 'finalizo') => {
    return soundDataUrl(soundName);
  });
  ipcMain.handle('pomodoro:play-finished-sound', () => {
    return playSoundInBackground('finalizo');
  });
}

app.whenReady().then(async () => {
  if (process.platform === 'win32') app.setAppUserModelId('com.renombrar.pdf');
  startAutoUpdater({ isPackaged: app.isPackaged, updateElectronApp, logger: console });
  const root = projectRoot();
  const dataRoot = app.isPackaged ? app.getPath('userData') : root;
  backend = new BackendManager({
    projectRoot: root,
    env: {
      ...process.env,
      APP_DB_PATH: path.join(dataRoot, 'app.db'),
      APP_CONFIG_PATH: path.join(dataRoot, 'config.json')
    }
  });
  registerIpc();
  const startup = backend.start();
  createWindow();
  await startup;
  if (mainWindow && !mainWindow.isDestroyed()) mainWindow.webContents.send('backend:changed', backend.status);
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});

app.on('before-quit', () => backend?.stop());
