const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const stage = fs.mkdtempSync(path.join(os.tmpdir(), 'renombrar-electron-'));
const directories = ['electron', 'backend', 'sonidos', 'node_modules'];
const files = [
  'package.json', 'package-lock.json', 'forge.config.js',
  'vite.main.config.js', 'vite.preload.config.js', 'vite.renderer.config.js',
  'requirements.txt', 'control_logo.ico', 'control_logo.png'
];

function copyInputs() {
  for (const directory of directories) {
    fs.cpSync(path.join(root, directory), path.join(stage, directory), { recursive: true });
  }
  for (const file of files) fs.copyFileSync(path.join(root, file), path.join(stage, file));
  fs.mkdirSync(path.join(stage, 'seed-data'), { recursive: true });
  for (const file of ['app.db', 'config.json']) {
    fs.copyFileSync(path.join(root, file), path.join(stage, 'seed-data', file));
  }
}

function copyOutput() {
  const destination = path.join(root, 'out');
  fs.rmSync(destination, { recursive: true, force: true });
  fs.cpSync(path.join(stage, 'out'), destination, { recursive: true });
}

try {
  copyInputs();
  const forge = path.join(root, 'node_modules', '@electron-forge', 'cli', 'dist', 'electron-forge.js');
  const result = spawnSync(process.execPath, [forge, 'package'], {
    cwd: stage,
    stdio: 'inherit',
    env: { ...process.env, NODE_PATH: path.join(root, 'node_modules') }
  });
  if (result.error) throw result.error;
  if (result.status !== 0) process.exit(result.status || 1);
  copyOutput();
  console.log(`Paquete generado en ${path.join(root, 'out')}`);
} finally {
  fs.rmSync(stage, { recursive: true, force: true });
}
