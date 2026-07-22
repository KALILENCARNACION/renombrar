const { contextBridge, ipcRenderer, webUtils } = require('electron');

contextBridge.exposeInMainWorld('desktop', {
  platform: process.platform,
  appVersion: () => ipcRenderer.invoke('app:version'),
  backendStatus: () => ipcRenderer.invoke('backend:status'),
  onBackendChanged: callback => {
    const listener = (_event, status) => callback(status);
    ipcRenderer.on('backend:changed', listener);
    return () => ipcRenderer.removeListener('backend:changed', listener);
  },
  choosePdf: multiple => ipcRenderer.invoke('dialog:pdf', Boolean(multiple)),
  chooseFile: () => ipcRenderer.invoke('dialog:file'),
  chooseDirectory: () => ipcRenderer.invoke('dialog:directory'),
  pathForFile: file => webUtils.getPathForFile(file),
  openPath: targetPath => ipcRenderer.invoke('shell:open-path', targetPath),
  copyText: text => ipcRenderer.invoke('clipboard:write', text),
  setPomodoroBadge: (imageDataUrl, description) => ipcRenderer.invoke('pomodoro:badge', imageDataUrl, description),
  pomodoroSoundData: soundName => ipcRenderer.invoke('pomodoro:sound-data', soundName),
  playPomodoroFinishedSound: () => ipcRenderer.invoke('pomodoro:play-finished-sound')
});
