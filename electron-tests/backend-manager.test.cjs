const assert = require('node:assert/strict');
const path = require('node:path');
const test = require('node:test');
const fs = require('node:fs');
const { findPython } = require('../electron/backend-manager.cjs');

test('respeta RENOMBRAR_PYTHON cuando apunta a un ejecutable existente', () => {
  const executable = process.execPath;
  const result = findPython(path.resolve(__dirname, '..'), { RENOMBRAR_PYTHON: executable });
  assert.equal(result.command, executable);
  assert.deepEqual(result.args, []);
});

test('la ventana mantiene aislamiento y desactiva Node en el renderer', () => {
  const mainSource = fs.readFileSync(path.resolve(__dirname, '../electron/main.js'), 'utf8');
  assert.match(mainSource, /contextIsolation:\s*true/);
  assert.match(mainSource, /nodeIntegration:\s*false/);
  assert.match(mainSource, /sandbox:\s*true/);
  assert.match(mainSource, /!app\.isPackaged\s*&&\s*MAIN_WINDOW_VITE_DEV_SERVER_URL/);
  assert.match(mainSource, /\.\.\/renderer\/\$\{MAIN_WINDOW_VITE_NAME\}\/index\.html/);
});

test('el backend solo usa la interfaz local', () => {
  const managerSource = fs.readFileSync(path.resolve(__dirname, '../electron/backend-manager.cjs'), 'utf8');
  assert.match(managerSource, /http:\/\/127\.0\.0\.1:/);
  assert.doesNotMatch(managerSource, /0\.0\.0\.0/);
});

test('la pantalla Renombrar PDF contiene el flujo y la paleta acordados', () => {
  const html = fs.readFileSync(path.resolve(__dirname, '../electron/renderer/index.html'), 'utf8');
  const css = fs.readFileSync(path.resolve(__dirname, '../electron/renderer/styles.css'), 'utf8');
  for (const id of ['destination-toggle', 'drop-zone', 'process-button', 'file-list']) {
    assert.match(html, new RegExp(`id="${id}"`));
  }
  for (const color of ['#007aff', '#f8f9ff', '#ffffff', '#cbdbf5', '#1a1c1e', '#44474e']) {
    assert.match(css.toLowerCase(), new RegExp(color));
  }
});

test('el cascarón Pomodoro incluye temporizador, pestañas y panel lateral', () => {
  const html = fs.readFileSync(path.resolve(__dirname, '../electron/renderer/index.html'), 'utf8');
  for (const id of ['pomodoro-page', 'timer-display', 'timer-toggle', 'tasks-panel', 'flows-panel', 'settings-panel', 'pomodoro-sidebar-list']) {
    assert.match(html, new RegExp(`id="${id}"`));
  }
});
