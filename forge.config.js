module.exports = {
  packagerConfig: {
    asar: true,
    electronVersion: '38.8.6',
    icon: 'control_logo',
    extraResource: ['backend', 'sonidos', 'requirements.txt', 'seed-data'],
    ignore: [
      /(^|[\\/])\.git([\\/]|$)/,
      /(^|[\\/])\.pytest_cache([\\/]|$)/,
      /(^|[\\/])__pycache__([\\/]|$)/,
      /(^|[\\/])backups([\\/]|$)/,
      /(^|[\\/])tests([\\/]|$)/,
      /(^|[\\/])electron-tests([\\/]|$)/,
      /(^|[\\/])app\.db$/,
      /(^|[\\/])config\.json$/,
      /(^|[\\/])renombrar\.py$/
    ]
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
