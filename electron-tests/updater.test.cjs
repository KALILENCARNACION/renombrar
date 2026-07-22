const test = require('node:test');
const assert = require('node:assert/strict');
const { startAutoUpdater } = require('../electron/updater.cjs');

test('no inicia el actualizador durante el desarrollo', () => {
  let calls = 0;
  const started = startAutoUpdater({
    isPackaged: false,
    updateElectronApp: () => { calls += 1; }
  });

  assert.equal(started, false);
  assert.equal(calls, 0);
});

test('inicia el actualizador en la aplicacion empaquetada', () => {
  let receivedLogger;
  const logger = { error() {} };
  const started = startAutoUpdater({
    isPackaged: true,
    logger,
    updateElectronApp: ({ logger: updaterLogger }) => { receivedLogger = updaterLogger; }
  });

  assert.equal(started, true);
  assert.equal(receivedLogger, logger);
});

test('no bloquea el inicio cuando el actualizador falla', () => {
  const errors = [];
  const started = startAutoUpdater({
    isPackaged: true,
    logger: { error: (...args) => errors.push(args) },
    updateElectronApp: () => { throw new Error('sin conexion'); }
  });

  assert.equal(started, false);
  assert.equal(errors.length, 1);
});
