const path = require('node:path');

module.exports = {
  packagerConfig: {
    asar: true,
    electronVersion: '38.8.6',
    icon: 'control_logo',
    extraResource: ['backend', 'sonidos', 'requirements.txt', 'seed-data'],
    // La app empaquetada solo necesita los bundles de Vite; backend y sonidos
    // se incorporan explícitamente como recursos adicionales.
    ignore: filePath => {
      const relativePath = path.relative(__dirname, filePath);
      if (!relativePath) return false;
      const topLevel = relativePath.split(path.sep)[0];
      return topLevel !== '.vite' && relativePath !== 'package.json';
    }
  },
  makers: [
    { name: '@electron-forge/maker-squirrel', config: { name: 'Renombrar' } },
    { name: '@electron-forge/maker-zip', platforms: ['win32'] }
  ],
  plugins: [
    {
      name: '@electron-forge/plugin-vite',
      config: {
        build: [
          { entry: 'electron/main.js', config: 'vite.main.config.js' },
          { entry: 'electron/preload.js', config: 'vite.preload.config.js' }
        ],
        renderer: [
          { name: 'main_window', config: 'vite.renderer.config.js' }
        ]
      }
    }
  ]
};
