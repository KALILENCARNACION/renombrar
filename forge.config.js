const path = require('node:path');

module.exports = {
  packagerConfig: {
    asar: true,
    prune: true,
    electronVersion: '38.8.6',
    icon: 'control_logo',
    extraResource: ['backend', 'sonidos', 'requirements.txt'],
    // La app empaquetada solo necesita los bundles de Vite; backend y sonidos
    // se incorporan explícitamente como recursos adicionales.
    ignore: filePath => {
      const value = String(filePath);
      const absolutePath = /^[\\/]+/.test(value)
        ? path.resolve(__dirname, value.replace(/^[\\/]+/, ''))
        : path.resolve(value);
      const relativePath = path.relative(__dirname, absolutePath);
      if (!relativePath) return false;
      const topLevel = relativePath.split(path.sep)[0];
      return !['.vite', 'node_modules'].includes(topLevel) && relativePath !== 'package.json';
    }
  },
  makers: [
    {
      name: '@electron-forge/maker-squirrel',
      config: {
        name: 'Renombrar',
        authors: 'Kalil Encarnacion',
        description: 'Renombrar PDF'
      }
    },
    { name: '@electron-forge/maker-zip', platforms: ['win32'] }
  ],
  publishers: [
    {
      name: '@electron-forge/publisher-github',
      config: {
        repository: { owner: 'KALILENCARNACION', name: 'renombrar' },
        draft: false,
        prerelease: false,
        generateReleaseNotes: true
      }
    }
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
