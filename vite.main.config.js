const { defineConfig } = require('vite');
const fs = require('node:fs');
const path = require('node:path');

module.exports = defineConfig({
  build: { sourcemap: true },
  plugins: [
    {
      name: 'copy-runtime-modules',
      generateBundle() {
        for (const fileName of ['backend-manager.cjs', 'updater.cjs']) {
          this.emitFile({
            type: 'asset',
            fileName,
            source: fs.readFileSync(path.resolve(__dirname, 'electron', fileName), 'utf8')
          });
        }
      }
    }
  ]
});
