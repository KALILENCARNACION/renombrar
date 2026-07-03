const { defineConfig } = require('vite');
const fs = require('node:fs');
const path = require('node:path');

module.exports = defineConfig({
  build: { sourcemap: true },
  plugins: [
    {
      name: 'copy-backend-manager',
      generateBundle() {
        this.emitFile({
          type: 'asset',
          fileName: 'backend-manager.cjs',
          source: fs.readFileSync(path.resolve(__dirname, 'electron/backend-manager.cjs'), 'utf8')
        });
      }
    }
  ]
});
