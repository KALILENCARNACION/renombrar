const { app, BrowserWindow, clipboard, dialog, ipcMain, shell } = require('electron');
const fs = require('node:fs');
const path = require('node:path');
const { BackendManager } = require('./backend-manager.cjs');

let mainWindow;
let backend;

function projectRoot() {
  return app.isPackaged ? process.resourcesPath : process.cwd();
}

function seedPackagedData(dataRoot) {
  if (!app.isPackaged) return;
  const seedRoot = path.join(process.resourcesPath, 'seed-data');
  if (!fs.existsSync(seedRoot)) return;
  fs.mkdirSync(dataRoot, { recursive: true });
  for (const file of ['app.db', 'config.json']) {
    const source = path.join(seedRoot, file);
    const destination = path.join(dataRoot, file);
    if (!fs.existsSync(source)) continue;
    if (!fs.existsSync(destination)) {
      fs.copyFileSync(source, destination);
      continue;
    }
    const sourceSize = fs.statSync(source).size;
    const destinationSize = fs.statSync(destination).size;
    if (sourceSize > destinationSize) {
      const backup = `${destination}.backup-${Date.now()}`;
      fs.copyFileSync(destination, backup);
      fs.copyFileSync(source, destination);
    }
  }
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
      sandbox: true
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
}

app.whenReady().then(async () => {
  const root = projectRoot();
  const dataRoot = app.isPackaged ? app.getPath('userData') : root;
  seedPackagedData(dataRoot);
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
