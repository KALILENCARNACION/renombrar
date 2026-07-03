const { defineConfig } = require('vite');
const path = require('node:path');

module.exports = defineConfig({
  root: path.resolve(__dirname, 'electron/renderer'),
  build: {
    sourcemap: true,
    outDir: path.resolve(__dirname, '.vite/renderer/main_window'),
    emptyOutDir: true
  }
});
