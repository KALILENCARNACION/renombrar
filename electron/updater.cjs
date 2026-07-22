function startAutoUpdater({ isPackaged, updateElectronApp, logger = console }) {
  if (!isPackaged) return false;

  try {
    updateElectronApp({ logger });
    return true;
  } catch (error) {
    logger.error('No se pudo iniciar el actualizador automatico:', error);
    return false;
  }
}

module.exports = { startAutoUpdater };
