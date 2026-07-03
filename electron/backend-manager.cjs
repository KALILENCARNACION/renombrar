const { spawn, spawnSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

const DEFAULT_PORT = 8765;

function commandExists(command) {
  const probe = process.platform === 'win32' ? 'where.exe' : 'which';
  return spawnSync(probe, [command], { stdio: 'ignore' }).status === 0;
}

function findPython(projectRoot, env = process.env) {
  const configured = env.RENOMBRAR_PYTHON || env.PYTHON_EXECUTABLE;
  const candidates = [
    configured && { command: configured, args: [] },
    { command: path.join(projectRoot, '.venv', 'Scripts', 'python.exe'), args: [] },
    { command: path.join(projectRoot, 'venv', 'Scripts', 'python.exe'), args: [] },
    { command: 'python', args: [] },
    { command: 'py', args: ['-3'] },
    { command: 'python3', args: [] }
  ].filter(Boolean);

  for (const candidate of candidates) {
    if (path.isAbsolute(candidate.command)) {
      if (fs.existsSync(candidate.command)) return candidate;
    } else if (commandExists(candidate.command)) {
      return candidate;
    }
  }
  return null;
}

async function healthCheck(port = DEFAULT_PORT, timeoutMs = 900) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`http://127.0.0.1:${port}/api/v1/health`, {
      signal: controller.signal,
      cache: 'no-store'
    });
    if (!response.ok) return false;
    const body = await response.json();
    return body.status === 'ok';
  } catch {
    return false;
  } finally {
    clearTimeout(timer);
  }
}

function waitForHealth(port, child, timeoutMs = 15000) {
  return new Promise((resolve, reject) => {
    const startedAt = Date.now();
    const poll = async () => {
      if (child.exitCode !== null) {
        reject(new Error(`El backend terminó antes de iniciar (código ${child.exitCode}).`));
        return;
      }
      if (await healthCheck(port)) {
        resolve();
        return;
      }
      if (Date.now() - startedAt >= timeoutMs) {
        reject(new Error('El backend no respondió dentro de 15 segundos.'));
        return;
      }
      setTimeout(poll, 250);
    };
    poll();
  });
}

class BackendManager {
  constructor({ projectRoot, port = DEFAULT_PORT, env = process.env, logger = console }) {
    this.projectRoot = projectRoot;
    this.port = port;
    this.env = env;
    this.logger = logger;
    this.child = null;
    this.ownsProcess = false;
    this.status = { state: 'starting', message: 'Conectando con Python…', port };
  }

  async start() {
    if (await healthCheck(this.port)) {
      this.status = { state: 'connected', message: 'Backend conectado', port: this.port, external: true };
      return this.status;
    }

    const python = findPython(this.projectRoot, this.env);
    if (!python) {
      this.status = {
        state: 'error',
        message: 'No se encontró Python. Configura RENOMBRAR_PYTHON o crea .venv.',
        port: this.port
      };
      return this.status;
    }

    const args = [...python.args, '-m', 'backend.api'];
    this.child = spawn(python.command, args, {
      cwd: this.projectRoot,
      env: {
        ...this.env,
        APP_HOST: '127.0.0.1',
        APP_PORT: String(this.port),
        PYTHONUNBUFFERED: '1'
      },
      windowsHide: true,
      stdio: ['ignore', 'pipe', 'pipe']
    });
    this.ownsProcess = true;
    this.child.stdout.on('data', data => this.logger.info(`[python] ${String(data).trim()}`));
    this.child.stderr.on('data', data => this.logger.error(`[python] ${String(data).trim()}`));

    try {
      await waitForHealth(this.port, this.child);
      this.status = { state: 'connected', message: 'Backend conectado', port: this.port, external: false };
    } catch (error) {
      this.stop();
      this.status = { state: 'error', message: error.message, port: this.port };
    }
    return this.status;
  }

  async check() {
    if (await healthCheck(this.port)) {
      return { state: 'connected', message: 'Backend conectado', port: this.port };
    }
    return this.status.state === 'error'
      ? this.status
      : { state: 'disconnected', message: 'Backend desconectado', port: this.port };
  }

  stop() {
    if (this.child && this.ownsProcess && this.child.exitCode === null) {
      this.child.kill();
    }
    this.child = null;
    this.ownsProcess = false;
  }
}

module.exports = { BackendManager, findPython, healthCheck, DEFAULT_PORT };
