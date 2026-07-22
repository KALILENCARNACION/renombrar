const API = 'http://127.0.0.1:8765/api/v1';
const desktop = window.desktop || {
  appVersion: async () => '',
  backendStatus: async () => {
    try {
      const response = await fetch(`${API}/health`);
      if (!response.ok) throw new Error();
      return { state: 'connected', message: 'Backend conectado' };
    } catch {
      return { state: 'disconnected', message: 'Abre esta pantalla desde Electron.' };
    }
  },
  onBackendChanged: () => () => {},
  choosePdf: async () => [],
  chooseFile: async () => null,
  chooseDirectory: async () => null,
  pathForFile: () => '',
  openPath: async () => null,
  copyText: async text => navigator.clipboard?.writeText(text),
  setPomodoroBadge: async () => false,
  pomodoroSoundData: async () => '',
  playPomodoroFinishedSound: async () => false
};

async function showAppVersion() {
  const versionElement = document.querySelector('#app-version');
  if (!versionElement) return;
  try {
    const version = await desktop.appVersion();
    if (version) versionElement.textContent = `Versión ${version}`;
  } catch {
    // La versión es informativa; no debe bloquear la interfaz si no está disponible.
  }
}

showAppVersion();

const elements = {
  statusPill: document.querySelector('#status-pill'),
  statusText: document.querySelector('#status-text'),
  destinationToggle: document.querySelector('#destination-toggle'),
  destinationPanel: document.querySelector('#destination-panel'),
  destinationSummary: document.querySelector('#destination-summary'),
  destinationSelect: document.querySelector('#destination-select'),
  addDestination: document.querySelector('#add-destination'),
  routeCount: document.querySelector('#route-count'),
  routeList: document.querySelector('#route-list'),
  dropZone: document.querySelector('#drop-zone'),
  processButton: document.querySelector('#process-button'),
  notice: document.querySelector('#notice'),
  filesSection: document.querySelector('#files-section'),
  fileList: document.querySelector('#file-list'),
  clearButton: document.querySelector('#clear-button')
};

const state = { settings: null, files: [], analysis: [], processing: false };
const proposalState = { source: '', preview: '', creating: false, loaded: false };
const clientsState = { items: [], selectedId: null, loaded: false };
const fiscalState = { buyers: [], versions: [], summary: null, selectedId: null, selectedVersionId: null, loaded: false, messageBuyerId: '' };
const clientElements = {
  page: document.querySelector('#clients-page'),
  count: document.querySelector('#client-count'),
  search: document.querySelector('#client-search'),
  list: document.querySelector('#client-list'),
  name: document.querySelector('#client-name'),
  rnc: document.querySelector('#client-rnc'),
  cedula: document.querySelector('#client-cedula'),
  tss: document.querySelector('#client-tss'),
  pcLocation: document.querySelector('#client-pc-location'),
  resource: document.querySelector('#client-resource'),
  resourceLabel: document.querySelector('#client-resource-label'),
  description: document.querySelector('#client-description'),
  folder: document.querySelector('#client-resource-folder'),
  locationSelect: document.querySelector('#client-location-select'),
  locationOpen: document.querySelector('#client-location-open'),
  resourceClear: document.querySelector('#client-resource-clear'),
  copyRnc: document.querySelector('#client-copy-rnc'),
  copyCedula: document.querySelector('#client-copy-cedula'),
  copyTss: document.querySelector('#client-copy-tss'),
  tssToggle: document.querySelector('#client-tss-toggle'),
  delete: document.querySelector('#client-delete'),
  new: document.querySelector('#client-new'),
  save: document.querySelector('#client-save'),
  status: document.querySelector('#client-status')
};
const proposalElements = {
  page: document.querySelector('#proposal-page'),
  savedName: document.querySelector('#proposal-saved-name'),
  sourceLabel: document.querySelector('#proposal-source-label'),
  selectSource: document.querySelector('#proposal-select-source'),
  changeSource: document.querySelector('#proposal-change-source'),
  clearSource: document.querySelector('#proposal-clear-source'),
  variableName: document.querySelector('#proposal-variable-name'),
  type: document.querySelector('#proposal-type'),
  result: document.querySelector('#proposal-result'),
  create: document.querySelector('#proposal-create'),
  status: document.querySelector('#proposal-status'),
  previewFile: document.querySelector('#proposal-preview-file'),
  previewFolder: document.querySelector('#proposal-preview-folder'),
  previewEmpty: document.querySelector('#proposal-preview-empty')
};
const fiscalElements = {
  page: document.querySelector('#fiscal-page'),
  versionsCount: document.querySelector('#fiscal-versions-count'),
  buyersCount: document.querySelector('#fiscal-buyers-count'),
  buyersToday: document.querySelector('#fiscal-buyers-today'),
  netProfit: document.querySelector('#fiscal-net-profit'),
  grossProfit: document.querySelector('#fiscal-gross-profit'),
  name: document.querySelector('#fiscal-buyer-name'),
  purchaseDate: document.querySelector('#fiscal-purchase-date'),
  expirationDate: document.querySelector('#fiscal-expiration-date'),
  email: document.querySelector('#fiscal-email'),
  price: document.querySelector('#fiscal-price'),
  channel: document.querySelector('#fiscal-channel'),
  save: document.querySelector('#fiscal-save-buyer'),
  new: document.querySelector('#fiscal-new-buyer'),
  status: document.querySelector('#fiscal-status'),
  table: document.querySelector('#fiscal-buyers-table'),
  tableCount: document.querySelector('#fiscal-table-count'),
  messageType: document.querySelector('#fiscal-message-type'),
  messageBuyer: document.querySelector('#fiscal-message-buyer'),
  messageName: document.querySelector('#fiscal-message-name'),
  messagePreview: document.querySelector('#fiscal-message-preview'),
  messageCopy: document.querySelector('#fiscal-copy-message'),
  messageStatus: document.querySelector('#fiscal-message-status'),
  activeMessage: document.querySelector('#fiscal-active-message'),
  activeClient: document.querySelector('#fiscal-active-client'),
  versionsList: document.querySelector('#fiscal-versions-list'),
  versionNumber: document.querySelector('#fiscal-version-number'),
  versionDate: document.querySelector('#fiscal-version-date'),
  versionType: document.querySelector('#fiscal-version-type'),
  versionDescription: document.querySelector('#fiscal-version-description'),
  versionAffects: document.querySelector('#fiscal-version-affects'),
  versionManual: document.querySelector('#fiscal-version-manual'),
  versionSave: document.querySelector('#fiscal-save-version'),
  versionClear: document.querySelector('#fiscal-clear-version'),
  versionCopyDescription: document.querySelector('#fiscal-copy-version-description'),
  versionStatus: document.querySelector('#fiscal-version-status')
};
const pomodoroState = {
  data: null, settings: null, tasks: [], flows: [], interval: null, activeTab: 'timer-panel',
  expandedFlows: new Set(), showCompleted: false, showActiveFlowCompleted: true, timerSidebarMode: 'flows',
  flowBuilderOpen: false, editingFlowId: null, draftFlowName: '', draftTaskIds: [], draggedDraftTaskId: null,
  lastBadgeText: null, lastRenderedPhase: null, lastRenderedCompletedCount: null,
  soundDataUrl: null, audioContext: null, audioBuffer: null
};
const pomodoroElements = {
  page: document.querySelector('#pomodoro-page'),
  display: document.querySelector('#timer-display'),
  phase: document.querySelector('#phase-label'),
  minutes: document.querySelector('#metric-minutes'),
  hours: document.querySelector('#metric-hours'),
  count: document.querySelector('#metric-count'),
  toggle: document.querySelector('#timer-toggle'),
  skip: document.querySelector('#timer-skip'),
  reset: document.querySelector('#timer-reset'),
  selection: document.querySelector('#active-selection-label'),
  selectionCount: document.querySelector('#active-selection-count'),
  selectionActions: document.querySelector('#active-selection-actions'),
  activeComplete: document.querySelector('#active-complete'),
  activeClear: document.querySelector('#active-clear'),
  activeFlowZone: document.querySelector('#active-flow-zone'),
  timerCard: document.querySelector('.timer-card'),
  sidebar: document.querySelector('#pomodoro-sidebar-list'),
  sidebarTitle: document.querySelector('#pomodoro-sidebar-title'),
  sidebarSubtitle: document.querySelector('#pomodoro-sidebar-subtitle'),
  autoBreak: document.querySelector('#auto-break'),
  autoWork: document.querySelector('#auto-work'),
  settingsStatus: document.querySelector('#pomodoro-settings-status'),
  taskForm: document.querySelector('#task-form'),
  taskTitle: document.querySelector('#task-title'),
  taskStatus: document.querySelector('#task-status'),
  taskList: document.querySelector('#task-list'),
  flowForm: document.querySelector('#flow-form'),
  flowHome: document.querySelector('#flow-home-view'),
  flowBuilder: document.querySelector('#flow-builder-view'),
  flowCreateOpen: document.querySelector('#flow-create-open'),
  flowBuilderBack: document.querySelector('#flow-builder-back'),
  flowBuilderTitle: document.querySelector('#flow-builder-title'),
  flowName: document.querySelector('#flow-name'),
  flowStatus: document.querySelector('#flow-status'),
  flowList: document.querySelector('#flow-list'),
  flowSelectedCount: document.querySelector('#flow-selected-count'),
  flowSelectedList: document.querySelector('#flow-selected-list'),
  flowTaskModal: document.querySelector('#pomodoro-flow-task-modal'),
  flowTaskModalClose: document.querySelector('#pomodoro-flow-task-modal-close'),
  flowTaskModalForm: document.querySelector('#pomodoro-flow-task-modal-form'),
  flowTaskModalInput: document.querySelector('#pomodoro-flow-task-modal-title-input'),
  flowTaskModalStatus: document.querySelector('#pomodoro-flow-task-modal-status')
};
let navigationBound = false;

async function readBackendStatus() {
  const fallback = async () => {
    try {
      const response = await fetch(`${API}/health`, { cache: 'no-store' });
      if (!response.ok) throw new Error();
      return { state: 'connected', message: 'Backend conectado' };
    } catch {
      return { state: 'disconnected', message: 'Backend desconectado' };
    }
  };
  try {
    return await Promise.race([
      desktop.backendStatus(),
      new Promise((_, reject) => setTimeout(() => reject(new Error('Backend status timeout')), 1200))
    ]);
  } catch {
    return fallback();
  }
}

function bindPageNavigation() {
  if (navigationBound) return;
  navigationBound = true;
  document.querySelectorAll('[data-page]').forEach(button => {
    button.addEventListener('click', async () => {
      const target = button.dataset.page;
      document.querySelectorAll('.app-page').forEach(page => { page.hidden = page.id !== target; });
      document.querySelectorAll('[data-page]').forEach(item => item.classList.toggle('active', item === button));
      if (target === 'pomodoro-page') {
        try { await loadPomodoro(); startPomodoroRefresh(); } catch (error) { showNotice(error.message, 'error'); }
      }
      if (target === 'clients-page') {
        try { await loadClients(); } catch (error) { clientElements.status.textContent = error.message; }
      }
      if (target === 'proposal-page') {
        try { await loadProposal(); } catch (error) { proposalElements.status.textContent = error.message; }
      }
      if (target === 'fiscal-page') {
        try { await loadFiscal(); } catch (error) { fiscalElements.status.textContent = error.message; }
      }
    });
  });
}
bindPageNavigation();

function fileName(filePath) {
  return String(filePath).split(/[\\/]/).pop() || filePath;
}

function folderName(filePath) {
  const value = String(filePath || '');
  const index = Math.max(value.lastIndexOf('/'), value.lastIndexOf('\\'));
  return index > -1 ? value.slice(0, index) : '';
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"]/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[char]);
}

function formatTimer(totalSeconds) {
  const safe = Math.max(0, Number(totalSeconds) || 0);
  return `${String(Math.floor(safe / 60)).padStart(2, '0')}:${String(safe % 60).padStart(2, '0')}`;
}

function formatMoney(value) {
  return new Intl.NumberFormat('es-DO', { style: 'currency', currency: 'DOP' }).format(Number(value) || 0).replace('DOP', 'RD$');
}

function formatShortDate(value) {
  if (!value) return '-';
  const [year, month, day] = String(value).split('-');
  if (!year || !month || !day) return escapeHtml(value);
  return `${day}/${month}/${year}`;
}

function copyIconSvg() {
  return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 8h11v13H8zM5 16H4a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h11a1 1 0 0 1 1 1v1"/></svg>';
}

function phaseName(data) {
  if (data.phase === 'short_break') return 'Descanso corto';
  if (data.phase === 'long_break') return 'Descanso largo';
  return `Pomodoro #${(data.completed_count || 0) + 1}`;
}

function pomodoroDurationSeconds(data) {
  if (data.phase === 'short_break') return 5 * 60;
  if (data.phase === 'long_break') return 15 * 60;
  return 25 * 60;
}

function pomodoroBadgeText(data) {
  const duration = pomodoroDurationSeconds(data);
  const remaining = Math.max(0, Number(data.remaining_seconds) || 0);
  if (remaining === 0) return '0';
  return String(Math.min(99, Math.ceil(Math.min(remaining, duration) / 60)));
}

function pomodoroBadgeColors(data) {
  if (data.phase === 'short_break' || data.phase === 'long_break') {
    return { border: '#0f6b3d', fill: '#19c76f' };
  }
  return { border: '#8e1f1f', fill: '#f04444' };
}

function makePomodoroBadgeDataUrl(text, colors) {
  const canvas = document.createElement('canvas');
  canvas.width = 32;
  canvas.height = 32;
  const context = canvas.getContext('2d');
  context.clearRect(0, 0, 32, 32);

  context.beginPath();
  context.arc(16, 16, 15, 0, Math.PI * 2);
  context.fillStyle = colors.border;
  context.fill();
  context.beginPath();
  context.arc(16, 16, 13, 0, Math.PI * 2);
  context.fillStyle = colors.fill;
  context.fill();

  context.fillStyle = '#ffffff';
  context.font = `800 ${text.length > 1 ? 16 : 20}px Segoe UI, Arial, sans-serif`;
  context.textAlign = 'center';
  context.textBaseline = 'middle';
  context.fillText(text, 16, 16.5);
  return canvas.toDataURL('image/png');
}

function updatePomodoroTaskbarBadge(data) {
  if (!data?.running) {
    if (pomodoroState.lastBadgeText !== null) {
      desktop.setPomodoroBadge(null).catch(() => {});
      pomodoroState.lastBadgeText = null;
      document.title = 'SAA';
    }
    return;
  }

  const text = pomodoroBadgeText(data);
  const phaseKey = data.phase === 'work' ? 'work' : 'break';
  const badgeKey = `${phaseKey}:${text}`;
  if (badgeKey === pomodoroState.lastBadgeText) return;
  pomodoroState.lastBadgeText = badgeKey;
  const description = `${phaseKey === 'work' ? 'Pomodoro' : 'Descanso'}: faltan ${text} minuto${text === '1' ? '' : 's'}`;
  desktop.setPomodoroBadge(makePomodoroBadgeDataUrl(text, pomodoroBadgeColors(data)), description).catch(() => {});
  document.title = `${description} - SAA`;
}

async function playPomodoroFinishedSound() {
  if (desktop.playPomodoroFinishedSound) {
    try {
      const played = await desktop.playPomodoroFinishedSound();
      if (played) return;
    } catch {}
  }
  try {
    if (!pomodoroState.soundDataUrl) {
      pomodoroState.soundDataUrl = await desktop.pomodoroSoundData('finalizo');
    }
    if (!pomodoroState.soundDataUrl) throw new Error('Sin sonido finalizo.');
    if (!pomodoroState.audioContext) {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      pomodoroState.audioContext = new AudioContextClass();
    }
    if (pomodoroState.audioContext.state === 'suspended') {
      await pomodoroState.audioContext.resume();
    }
    if (!pomodoroState.audioBuffer) {
      const response = await fetch(pomodoroState.soundDataUrl);
      const arrayBuffer = await response.arrayBuffer();
      pomodoroState.audioBuffer = await pomodoroState.audioContext.decodeAudioData(arrayBuffer);
    }
    const source = pomodoroState.audioContext.createBufferSource();
    const gain = pomodoroState.audioContext.createGain();
    source.buffer = pomodoroState.audioBuffer;
    gain.gain.value = 3.2;
    source.connect(gain);
    gain.connect(pomodoroState.audioContext.destination);
    source.start(0);
  } catch {
    const audio = new Audio(pomodoroState.soundDataUrl || '');
    audio.volume = 1;
    audio.play().catch(() => {});
  }
}

function maybePlayPomodoroFinishedSound(data) {
  const previousPhase = pomodoroState.lastRenderedPhase;
  const previousCompleted = pomodoroState.lastRenderedCompletedCount;
  const completedCount = Number(data.completed_count) || 0;
  const finishedWork =
    previousPhase === 'work' &&
    data.phase !== 'work' &&
    previousCompleted !== null &&
    completedCount >= previousCompleted;

  pomodoroState.lastRenderedPhase = data.phase;
  pomodoroState.lastRenderedCompletedCount = completedCount;
  if (finishedWork) playPomodoroFinishedSound();
}

function isTaskCompleted(taskId) {
  return (pomodoroState.data?.completed_task_ids || []).includes(taskId);
}

function flowProgress(flow) {
  const tasks = flow?.tasks || [];
  const total = tasks.length;
  const done = tasks.filter(task => Number(task.completed) === 1).length;
  return { done, total, percent: total ? Math.round((done / total) * 100) : 0 };
}

function renderPomodoro() {
  const data = pomodoroState.data;
  if (!data) return;
  const selectedTask = pomodoroState.tasks.find(task => task.id === data.selected_task_id);
  const selectedFlow = pomodoroState.flows.find(flow => flow.id === data.selected_flow_id);
  const selectedFlowCount = selectedFlow ? Number(data.flow_pomodoros?.[selectedFlow.id] || 0) : 0;
  const selectedTaskCount = selectedTask ? Number(selectedTask.completed_pomodoros || 0) : 0;
  const completed = selectedFlow ? selectedFlowCount : selectedTask ? selectedTaskCount : Number(data.completed_count) || 0;
  const minutes = completed * 25;
  pomodoroElements.display.textContent = formatTimer(data.remaining_seconds);
  pomodoroElements.phase.textContent = phaseName(data);
  pomodoroElements.minutes.textContent = String(minutes);
  pomodoroElements.hours.textContent = `${Math.floor(minutes / 60)}:${String(minutes % 60).padStart(2, '0')}`;
  pomodoroElements.count.textContent = String(completed);
  pomodoroElements.toggle.textContent = data.running ? 'Pausar' : 'Iniciar';
  pomodoroElements.selection.textContent = selectedTask?.title || selectedFlow?.name || 'Sin tarea seleccionada';
  if (selectedFlow) {
    const progress = flowProgress(selectedFlow);
    pomodoroElements.selectionCount.textContent = `Pomodoros en este flujo: ${selectedFlowCount} · ${progress.percent}% terminado`;
  } else {
    pomodoroElements.selectionCount.textContent = selectedTask
      ? `Pomodoros en esta tarea: ${selectedTask.completed_pomodoros || 0}`
      : 'Pomodoros en esta tarea: 0';
  }
  pomodoroElements.selectionActions.hidden = !selectedTask && !selectedFlow;
  pomodoroElements.activeComplete.hidden = !selectedTask;
  pomodoroElements.timerCard.classList.toggle('has-flow', Boolean(selectedFlow));
  updatePomodoroTaskbarBadge(data);
  maybePlayPomodoroFinishedSound(data);
  renderActiveFlow(selectedFlow);
}

function renderActiveFlow(flow) {
  if (!flow) {
    pomodoroElements.activeFlowZone.hidden = true;
    pomodoroElements.activeFlowZone.innerHTML = '';
    return;
  }
  const progress = flowProgress(flow);
  const visibleTasks = flow.tasks || [];
  pomodoroElements.activeFlowZone.hidden = false;
  pomodoroElements.activeFlowZone.innerHTML = `
    <div class="active-flow-progress">
      <span>${progress.done}/${progress.total} tareas · ${progress.percent}%</span>
      <div><i style="width:${progress.percent}%"></i></div>
    </div>
    <div class="active-flow-task-list">
      ${visibleTasks.map(task => `<div class="active-flow-task ${Number(task.completed) === 1 ? 'completed' : ''}" data-active-flow-task-id="${escapeHtml(task.id)}">
        <button class="complete-dot" type="button" data-active-flow-action="complete" title="Marcar completada" aria-label="Marcar completada"></button>
        <span>${escapeHtml(task.title)}</span>
        <button class="clear-active" type="button" data-active-flow-action="remove" title="Quitar del flujo" aria-label="Quitar del flujo">−</button>
      </div>`).join('') || '<p>Todas las tareas visibles están completadas.</p>'}
    </div>`;
}

function oldRenderPomodoroSidebar() {
  if (pomodoroState.activeTab === 'flows-panel') {
    pomodoroElements.sidebarTitle.textContent = 'Tareas';
    pomodoroElements.sidebarSubtitle.textContent = 'Arrastra una tarea hacia un flujo';
    pomodoroElements.sidebar.innerHTML = pomodoroState.tasks.map(task => `<div class="sidebar-item draggable-task" draggable="true" data-sidebar-task-id="${escapeHtml(task.id)}"><small>Tarea</small><strong>${escapeHtml(task.title)}</strong><span>${task.completed_pomodoros || 0} pomodoros</span></div>`).join('') || '<p>No hay tareas todavía.</p>';
    return;
  }
  pomodoroElements.sidebarTitle.textContent = 'Tareas y flujos';
  pomodoroElements.sidebarSubtitle.textContent = 'Solo lectura por ahora';
  const flows = pomodoroState.flows.map(flow => `<div class="sidebar-item"><small>Flujo</small><strong>${escapeHtml(flow.name)}</strong><span>${flow.tasks?.length || 0} tareas</span></div>`);
  const tasks = pomodoroState.tasks.map(task => `<div class="sidebar-item"><small>Tarea</small><strong>${escapeHtml(task.title)}</strong><span>${task.completed_pomodoros || 0} pomodoros</span></div>`);
  pomodoroElements.sidebar.innerHTML = [...flows, ...tasks].join('') || '<p>No hay tareas ni flujos todavía.</p>';
}

function renderTaskList() {
  const selectedId = pomodoroState.data?.selected_task_id;
  pomodoroElements.taskList.innerHTML = pomodoroState.tasks.map(task => {
    const active = task.id === selectedId;
    return `<div class="task-row ${active ? 'active' : ''}" data-task-id="${escapeHtml(task.id)}">
      <span class="task-title">${escapeHtml(task.title)}</span>
      <button class="task-icon tomato" type="button" data-task-action="select" title="Agregar al Pomodoro" aria-label="Agregar al Pomodoro">🍅</button>
      <button class="task-icon trash" type="button" data-task-action="delete" title="Eliminar tarea" aria-label="Eliminar tarea">🗑️</button>
    </div>`;
  }).join('') || '<p class="empty-tasks">Todavía no hay tareas.</p>';
}

function legacyRenderFlowList() {
  pomodoroElements.flowList.innerHTML = pomodoroState.flows.map(flow => {
    const expanded = pomodoroState.expandedFlows.has(flow.id);
    const tasks = flow.tasks || [];
    const progress = flowProgress(flow);
    const taskItems = expanded
      ? `<div class="flow-task-list">${tasks.map(task => `<div class="flow-task"><span>${escapeHtml(task.title)}</span><button type="button" data-flow-action="remove-task" data-task-id="${escapeHtml(task.id)}" title="Quitar del flujo">×</button></div>`).join('') || '<p>Arrastra tareas aquí.</p>'}</div>`
      : '';
    return `<div class="flow-row ${expanded ? 'expanded' : ''}" data-flow-id="${escapeHtml(flow.id)}">
      <div class="flow-drop-target" data-flow-drop="true">
        <button class="flow-toggle" type="button" data-flow-action="toggle" aria-expanded="${expanded}">${expanded ? '▾' : '▸'}</button>
        <div class="flow-main">
          <strong>${escapeHtml(flow.name)}</strong>
          <small>${progress.done}/${progress.total} tareas · ${progress.percent}%</small>
        </div>
        <button class="flow-delete" type="button" data-flow-action="delete" title="Eliminar flujo" aria-label="Eliminar flujo">&#128465;&#65039;</button>
      </div>
      ${taskItems}
    </div>`;
  }).join('') || '<p class="empty-tasks">Todavía no hay flujos.</p>';
}

function renderTimerPicker() {}

function legacyRenderPomodoroSidebar() {
  if (pomodoroState.activeTab === 'flows-panel') {
    pomodoroElements.sidebarTitle.textContent = 'Tareas';
    pomodoroElements.sidebarSubtitle.textContent = 'Arrastra una tarea hacia un flujo';
    pomodoroElements.sidebar.innerHTML = pomodoroState.tasks.map(task => `<div class="sidebar-item draggable-task" draggable="true" data-sidebar-task-id="${escapeHtml(task.id)}"><small>Tarea</small><strong>${escapeHtml(task.title)}</strong><span>${task.completed_pomodoros || 0} pomodoros</span></div>`).join('') || '<p>No hay tareas todavia.</p>';
    return;
  }
  const mode = pomodoroState.timerSidebarMode === 'tasks' ? 'tasks' : 'flows';
  pomodoroElements.sidebarTitle.textContent = mode === 'tasks' ? 'Tareas' : 'Flujos';
  pomodoroElements.sidebarSubtitle.textContent = 'Usa + o arrastra al temporizador';
  const switcher = `<div class="sidebar-switch" role="tablist" aria-label="Ver tareas o flujos">
    <button class="${mode === 'tasks' ? 'active' : ''}" type="button" data-sidebar-view="tasks" aria-selected="${mode === 'tasks'}">Tareas</button>
    <button class="${mode === 'flows' ? 'active' : ''}" type="button" data-sidebar-view="flows" aria-selected="${mode === 'flows'}">Flujos</button>
  </div>`;
  const completedIds = pomodoroState.data?.completed_task_ids || [];
  const visibleTasks = pomodoroState.showCompleted ? pomodoroState.tasks : pomodoroState.tasks.filter(task => !completedIds.includes(task.id));
  const hiddenCount = pomodoroState.tasks.length - visibleTasks.length;
  const toggle = hiddenCount || pomodoroState.showCompleted ? `<button class="completed-toggle" type="button" data-sidebar-action="toggle-completed">${pomodoroState.showCompleted ? 'Ocultar completadas' : `Mostrar completadas (${hiddenCount})`}</button>` : '';
  const flows = pomodoroState.flows.map(flow => {
    const progress = flowProgress(flow);
    return `<div class="sidebar-item pick-source ${flow.id === pomodoroState.data?.selected_flow_id ? 'active' : ''}" draggable="true" data-pick-type="flow" data-pick-id="${escapeHtml(flow.id)}"><small>Flujo</small><strong>${escapeHtml(flow.name)}</strong><span>${progress.done}/${progress.total} tareas · ${progress.percent}%</span><button type="button" data-pick-action="select">+</button></div>`;
  });
  const tasks = visibleTasks.map(task => {
    const completed = completedIds.includes(task.id);
    return `<div class="sidebar-item pick-source ${task.id === pomodoroState.data?.selected_task_id ? 'active' : ''} ${completed ? 'completed' : ''}" draggable="true" data-pick-type="task" data-pick-id="${escapeHtml(task.id)}"><small>Tarea</small><strong>${escapeHtml(task.title)}</strong><span>${task.completed_pomodoros || 0} pomodoros</span><button type="button" data-pick-action="select">+</button></div>`;
  });
  pomodoroElements.sidebar.innerHTML = [toggle, ...flows, ...tasks].join('') || '<p>No hay tareas ni flujos todavia.</p>';
}

function selectedDraftTasks() {
  return pomodoroState.draftTaskIds
    .map(id => pomodoroState.tasks.find(task => task.id === id))
    .filter(Boolean);
}

function openFlowBuilder(flowId = null) {
  const flow = flowId ? pomodoroState.flows.find(item => item.id === flowId) : null;
  pomodoroState.flowBuilderOpen = true;
  pomodoroState.editingFlowId = flow?.id || null;
  pomodoroState.draftFlowName = flow?.name || '';
  pomodoroState.draftTaskIds = (flow?.tasks || []).map(task => task.id);
  pomodoroElements.flowName.value = pomodoroState.draftFlowName;
  pomodoroElements.flowStatus.textContent = '';
  renderFlowBuilder();
  renderPomodoroSidebar();
}

function closeFlowBuilder() {
  pomodoroState.flowBuilderOpen = false;
  pomodoroState.editingFlowId = null;
  pomodoroState.draftFlowName = '';
  pomodoroState.draftTaskIds = [];
  pomodoroElements.flowStatus.textContent = '';
  renderFlowBuilder();
  renderPomodoroSidebar();
}

function addDraftTask(taskId) {
  if (!taskId || pomodoroState.draftTaskIds.includes(taskId)) return;
  pomodoroState.draftTaskIds = [...pomodoroState.draftTaskIds, taskId];
  renderFlowBuilder();
  renderPomodoroSidebar();
}

function removeDraftTask(taskId) {
  pomodoroState.draftTaskIds = pomodoroState.draftTaskIds.filter(id => id !== taskId);
  renderFlowBuilder();
  renderPomodoroSidebar();
}

function moveDraftTask(taskId, beforeTaskId) {
  if (!taskId || taskId === beforeTaskId) return;
  const withoutTask = pomodoroState.draftTaskIds.filter(id => id !== taskId);
  const targetIndex = beforeTaskId ? withoutTask.indexOf(beforeTaskId) : -1;
  pomodoroState.draftTaskIds = targetIndex < 0
    ? [...withoutTask, taskId]
    : [...withoutTask.slice(0, targetIndex), taskId, ...withoutTask.slice(targetIndex)];
  renderFlowBuilder();
}

function renderFlowBuilder() {
  const isFlowTab = pomodoroState.activeTab === 'flows-panel';
  const builderOpen = isFlowTab && pomodoroState.flowBuilderOpen;
  pomodoroElements.page.classList.toggle('flow-home-mode', isFlowTab && !builderOpen);
  pomodoroElements.page.classList.toggle('flow-builder-mode', builderOpen);
  pomodoroElements.flowHome.hidden = builderOpen;
  pomodoroElements.flowBuilder.hidden = !builderOpen;
  if (!builderOpen) return;
  pomodoroElements.flowBuilderTitle.textContent = pomodoroState.editingFlowId ? 'Editar flujo' : 'Crear flujo';
  pomodoroElements.flowSelectedCount.textContent = `Tareas del flujo: ${pomodoroState.draftTaskIds.length}`;
  const tasks = selectedDraftTasks();
  pomodoroElements.flowSelectedList.innerHTML = tasks.map((task, index) => `
    <div class="flow-selected-task" draggable="true" data-draft-task-id="${escapeHtml(task.id)}">
      <span>${index + 1}</span>
      <strong>${escapeHtml(task.title)}</strong>
      <button type="button" data-draft-action="remove" title="Quitar tarea" aria-label="Quitar tarea">-</button>
    </div>`).join('') || '<p class="empty-tasks">Arrastra o selecciona tareas desde la lista.</p>';
}

function renderFlowList() {
  renderFlowBuilder();
  pomodoroElements.flowList.innerHTML = pomodoroState.flows.map(flow => {
    const progress = flowProgress(flow);
    return `<div class="flow-row" data-flow-id="${escapeHtml(flow.id)}">
      <div class="flow-drop-target">
        <button class="flow-toggle" type="button" data-flow-action="select" title="Usar flujo" aria-label="Usar flujo">+</button>
        <div class="flow-main">
          <strong>${escapeHtml(flow.name)}</strong>
          <small>${progress.done}/${progress.total} tareas - ${progress.percent}%</small>
        </div>
        <button class="flow-edit" type="button" data-flow-action="edit" title="Editar flujo" aria-label="Editar flujo">Editar</button>
        <button class="flow-delete" type="button" data-flow-action="delete" title="Eliminar flujo" aria-label="Eliminar flujo">&#128465;&#65039;</button>
      </div>
    </div>`;
  }).join('') || '<p class="empty-tasks">Todavia no hay flujos.</p>';
}

function renderPomodoroSidebar() {
  if (pomodoroState.activeTab === 'flows-panel') {
    if (!pomodoroState.flowBuilderOpen) {
      pomodoroElements.sidebarTitle.textContent = '';
      pomodoroElements.sidebarSubtitle.textContent = '';
      pomodoroElements.sidebar.innerHTML = '';
      return;
    }
    const availableTasks = pomodoroState.tasks.filter(task => !pomodoroState.draftTaskIds.includes(task.id));
    pomodoroElements.sidebarTitle.textContent = 'Tareas';
    pomodoroElements.sidebarSubtitle.textContent = 'Arrastra o selecciona una tarea';
    const createButton = '<button class="sidebar-create-task" type="button" data-flow-task-action="open-modal">Nueva tarea</button>';
    const tasks = availableTasks.map(task => `<div class="sidebar-item draggable-task" draggable="true" data-sidebar-task-id="${escapeHtml(task.id)}"><small>Tarea</small><strong>${escapeHtml(task.title)}</strong><span>${task.completed_pomodoros || 0} pomodoros</span><button type="button" data-flow-task-action="add" data-task-id="${escapeHtml(task.id)}">+</button></div>`).join('');
    pomodoroElements.sidebar.innerHTML = createButton + (tasks || '<p>No hay tareas disponibles.</p>');
    return;
  }
  const mode = pomodoroState.timerSidebarMode === 'tasks' ? 'tasks' : 'flows';
  pomodoroElements.sidebarTitle.textContent = mode === 'tasks' ? 'Tareas' : 'Flujos';
  pomodoroElements.sidebarSubtitle.textContent = 'Usa + o arrastra al temporizador';
  const switcher = `<div class="sidebar-switch" role="tablist" aria-label="Ver tareas o flujos">
    <button class="${mode === 'tasks' ? 'active' : ''}" type="button" data-sidebar-view="tasks" aria-selected="${mode === 'tasks'}">Tareas</button>
    <button class="${mode === 'flows' ? 'active' : ''}" type="button" data-sidebar-view="flows" aria-selected="${mode === 'flows'}">Flujos</button>
  </div>`;
  const completedIds = pomodoroState.data?.completed_task_ids || [];
  const visibleTasks = pomodoroState.showCompleted ? pomodoroState.tasks : pomodoroState.tasks.filter(task => !completedIds.includes(task.id));
  const hiddenCount = pomodoroState.tasks.length - visibleTasks.length;
  const toggle = hiddenCount || pomodoroState.showCompleted ? `<button class="completed-toggle" type="button" data-sidebar-action="toggle-completed">${pomodoroState.showCompleted ? 'Ocultar completadas' : `Mostrar completadas (${hiddenCount})`}</button>` : '';
  const flows = pomodoroState.flows.map(flow => {
    const progress = flowProgress(flow);
    const active = flow.id === pomodoroState.data?.selected_flow_id;
    const taskList = active && flow.tasks?.length
      ? `<div class="sidebar-flow-tasks">${flow.tasks.map(task => `<span class="${Number(task.completed) === 1 ? 'completed' : ''}">${escapeHtml(task.title)}</span>`).join('')}</div>`
      : '';
    return `<div class="sidebar-item pick-source ${active ? 'active' : ''}" draggable="true" data-pick-type="flow" data-pick-id="${escapeHtml(flow.id)}"><small>Flujo</small><strong>${escapeHtml(flow.name)}</strong><span>${progress.done}/${progress.total} tareas - ${progress.percent}%</span>${taskList}<button type="button" data-pick-action="select">+</button></div>`;
  });
  const tasks = visibleTasks.map(task => {
    const completed = completedIds.includes(task.id);
    return `<div class="sidebar-item pick-source ${task.id === pomodoroState.data?.selected_task_id ? 'active' : ''} ${completed ? 'completed' : ''}" draggable="true" data-pick-type="task" data-pick-id="${escapeHtml(task.id)}"><small>Tarea</small><strong>${escapeHtml(task.title)}</strong><span>${task.completed_pomodoros || 0} pomodoros</span><button type="button" data-pick-action="select">+</button></div>`;
  });
  const items = mode === 'tasks' ? [toggle, ...tasks] : flows;
  const empty = mode === 'tasks' ? '<p>No hay tareas todavia.</p>' : '<p>No hay flujos todavia.</p>';
  pomodoroElements.sidebar.innerHTML = switcher + (items.join('') || empty);
}

async function loadPomodoro() {
  const [data, settings, tasks, flows] = await Promise.all([
    api('/pomodoro/state'), api('/pomodoro/settings'), api('/pomodoro/tasks'), api('/pomodoro/flows')
  ]);
  pomodoroState.data = data;
  pomodoroState.settings = settings;
  pomodoroState.tasks = tasks;
  pomodoroState.flows = flows;
  pomodoroElements.autoBreak.checked = Boolean(settings.auto_start_break);
  pomodoroElements.autoWork.checked = Boolean(settings.auto_start_work);
  renderPomodoro();
  renderPomodoroSidebar();
  renderTaskList();
  renderFlowList();
  renderTimerPicker();
}

async function initializePomodoroRefresh() {
  await loadPomodoro();
  startPomodoroRefresh();
}

async function sendPomodoroCommand(action) {
  pomodoroState.data = await api('/pomodoro/commands', { method: 'POST', body: JSON.stringify({ action }) });
  renderPomodoro();
  renderTaskList();
  renderFlowList();
  renderTimerPicker();
}

async function createPomodoroTask(title) {
  const task = await api('/pomodoro/tasks', { method: 'POST', body: JSON.stringify({ title }) });
  pomodoroState.tasks = [...pomodoroState.tasks, task];
  if (pomodoroElements.taskStatus) pomodoroElements.taskStatus.textContent = 'Tarea agregada.';
  if (pomodoroElements.taskTitle) pomodoroElements.taskTitle.value = '';
  renderTaskList();
  renderPomodoroSidebar();
  renderFlowList();
  renderTimerPicker();
  return task;
}

async function deletePomodoroTask(taskId) {
  await api(`/pomodoro/tasks/${encodeURIComponent(taskId)}`, { method: 'DELETE' });
  pomodoroState.tasks = pomodoroState.tasks.filter(task => task.id !== taskId);
  pomodoroState.flows = await api('/pomodoro/flows');
  if (pomodoroState.data?.selected_task_id === taskId) {
    pomodoroState.data = await api('/pomodoro/selection', { method: 'PUT', body: JSON.stringify({ task_id: null }) });
  }
  pomodoroElements.taskStatus.textContent = 'Tarea eliminada.';
  renderPomodoro();
  renderTaskList();
  renderFlowList();
  renderTimerPicker();
  renderPomodoroSidebar();
}

async function selectPomodoroTask(taskId) {
  pomodoroState.data = await api('/pomodoro/selection', { method: 'PUT', body: JSON.stringify({ task_id: taskId }) });
  pomodoroElements.taskStatus.textContent = 'Tarea agregada al Pomodoro.';
  renderPomodoro();
  renderTaskList();
  renderTimerPicker();
  renderPomodoroSidebar();
}

async function selectPomodoroFlow(flowId) {
  pomodoroState.data = await api('/pomodoro/selection', { method: 'PUT', body: JSON.stringify({ flow_id: flowId }) });
  pomodoroState.showActiveFlowCompleted = false;
  pomodoroElements.flowStatus.textContent = 'Flujo agregado al Pomodoro.';
  renderPomodoro();
  renderTaskList();
  renderTimerPicker();
  renderPomodoroSidebar();
}

async function selectPomodoroItem(type, id) {
  if (type === 'flow') await selectPomodoroFlow(id);
  else await selectPomodoroTask(id);
}

async function clearPomodoroSelection() {
  pomodoroState.data = await api('/pomodoro/selection', { method: 'PUT', body: JSON.stringify({ task_id: null, flow_id: null }) });
  renderPomodoro();
  renderTaskList();
  renderPomodoroSidebar();
}

async function completeActiveTask() {
  const taskId = pomodoroState.data?.selected_task_id;
  if (!taskId) return;
  pomodoroState.data = await api(`/pomodoro/tasks/${encodeURIComponent(taskId)}/completed`, {
    method: 'PUT',
    body: JSON.stringify({ completed: true })
  });
  renderPomodoro();
  renderTaskList();
  renderPomodoroSidebar();
}

async function completeActiveFlowTask(taskId) {
  const flowId = pomodoroState.data?.selected_flow_id;
  if (!flowId || !taskId) return;
  await api(`/pomodoro/flows/${encodeURIComponent(flowId)}/completion`, {
    method: 'PUT',
    body: JSON.stringify({ task_id: taskId, completed: true })
  });
  pomodoroState.flows = await api('/pomodoro/flows');
  renderPomodoro();
  renderFlowList();
  renderPomodoroSidebar();
}

async function removeActiveFlowTask(taskId) {
  const flowId = pomodoroState.data?.selected_flow_id;
  if (!flowId || !taskId) return;
  await assignTaskToFlow(flowId, taskId, false);
  renderPomodoro();
}

async function createPomodoroFlow(name) {
  const flow = await api('/pomodoro/flows', { method: 'POST', body: JSON.stringify({ name }) });
  pomodoroState.flows = [...pomodoroState.flows, flow];
  pomodoroState.expandedFlows.add(flow.id);
  pomodoroElements.flowStatus.textContent = 'Flujo agregado.';
  pomodoroElements.flowName.value = '';
  renderFlowList();
  renderPomodoroSidebar();
  renderTimerPicker();
}

async function saveFlowDraft() {
  const name = pomodoroElements.flowName.value.trim();
  if (!name) {
    pomodoroElements.flowStatus.textContent = 'Escribe un nombre para el flujo.';
    return;
  }
  const flowId = pomodoroState.editingFlowId;
  const flow = await api(flowId ? `/pomodoro/flows/${encodeURIComponent(flowId)}` : '/pomodoro/flows', {
    method: flowId ? 'PUT' : 'POST',
    body: JSON.stringify({ name })
  });
  const existingIds = new Set((flow.tasks || []).map(task => task.id));
  const draftIds = new Set(pomodoroState.draftTaskIds);
  for (const taskId of draftIds) {
    if (!existingIds.has(taskId)) {
      await api(`/pomodoro/flows/${encodeURIComponent(flow.id)}/assignment`, {
        method: 'PUT',
        body: JSON.stringify({ task_id: taskId, assigned: true })
      });
    }
  }
  for (const taskId of existingIds) {
    if (!draftIds.has(taskId)) {
      await api(`/pomodoro/flows/${encodeURIComponent(flow.id)}/assignment`, {
        method: 'PUT',
        body: JSON.stringify({ task_id: taskId, assigned: false })
      });
    }
  }
  await api(`/pomodoro/flows/${encodeURIComponent(flow.id)}/order`, {
    method: 'PUT',
    body: JSON.stringify({ task_ids: pomodoroState.draftTaskIds })
  });
  pomodoroState.flows = await api('/pomodoro/flows');
  closeFlowBuilder();
  pomodoroElements.flowStatus.textContent = 'Flujo guardado.';
  renderPomodoro();
  renderFlowList();
  renderPomodoroSidebar();
  renderTimerPicker();
}

async function deletePomodoroFlow(flowId) {
  await api(`/pomodoro/flows/${encodeURIComponent(flowId)}`, { method: 'DELETE' });
  pomodoroState.flows = pomodoroState.flows.filter(flow => flow.id !== flowId);
  pomodoroState.expandedFlows.delete(flowId);
  if (pomodoroState.data?.selected_flow_id === flowId) {
    pomodoroState.data = await api('/pomodoro/selection', { method: 'PUT', body: JSON.stringify({ task_id: null, flow_id: null }) });
  }
  pomodoroElements.flowStatus.textContent = 'Flujo eliminado.';
  renderFlowList();
  renderPomodoro();
  renderPomodoroSidebar();
  renderTimerPicker();
}

async function assignTaskToFlow(flowId, taskId, assigned = true) {
  await api(`/pomodoro/flows/${encodeURIComponent(flowId)}/assignment`, {
    method: 'PUT',
    body: JSON.stringify({ task_id: taskId, assigned })
  });
  pomodoroState.flows = await api('/pomodoro/flows');
  pomodoroState.expandedFlows.add(flowId);
  pomodoroElements.flowStatus.textContent = assigned ? 'Tarea agregada al flujo.' : 'Tarea quitada del flujo.';
  renderFlowList();
  renderPomodoroSidebar();
}

async function savePomodoroSettings() {
  pomodoroState.settings = await api('/pomodoro/settings', {
    method: 'PUT',
    body: JSON.stringify({ auto_start_break: pomodoroElements.autoBreak.checked, auto_start_work: pomodoroElements.autoWork.checked })
  });
  pomodoroElements.settingsStatus.textContent = 'Configuración guardada.';
  setTimeout(() => { pomodoroElements.settingsStatus.textContent = ''; }, 1800);
}

function startPomodoroRefresh() {
  if (pomodoroState.interval) return;
  pomodoroState.interval = setInterval(async () => {
    try {
      const previousPhase = pomodoroState.data?.phase;
      const previousCompletedCount = Number(pomodoroState.data?.completed_count) || 0;
      pomodoroState.data = await api('/pomodoro/state');
      const completedWork =
        previousPhase === 'work' &&
        pomodoroState.data.phase !== 'work' &&
        Number(pomodoroState.data.completed_count || 0) > previousCompletedCount;
      if (completedWork) {
        pomodoroState.tasks = await api('/pomodoro/tasks');
        pomodoroState.flows = await api('/pomodoro/flows');
      }
      renderPomodoro();
      if (!pomodoroElements.page.hidden) {
        renderTaskList();
        renderFlowList();
        renderTimerPicker();
        renderPomodoroSidebar();
      }
    } catch {}
  }, 1000);
}

async function api(path, options = {}) {
  const response = await fetch(`${API}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) }
  });
  if (!response.ok) {
    let message = `Error ${response.status}`;
    try { message = (await response.json()).detail || message; } catch {}
    throw new Error(message);
  }
  return response.status === 204 ? null : response.json();
}

function emptyClient() {
  return { id: null, name: '', rnc: '', pc_location: '', cedula: '', tss_class: '', resource_path: '', work_description: '' };
}

function clientInitials(name) {
  return String(name || '?').split(/\s+/).filter(Boolean).slice(0, 2).map(part => part[0]?.toUpperCase()).join('') || '?';
}

function clientFormData() {
  return {
    id: clientsState.selectedId,
    name: clientElements.name.value.trim(),
    rnc: clientElements.rnc.value.trim(),
    pc_location: clientElements.pcLocation.value.trim(),
    cedula: clientElements.cedula.value.trim(),
    tss_class: clientElements.tss.value.trim(),
    resource_path: clientElements.resource.value.trim(),
    work_description: clientElements.description.value.trim()
  };
}

function renderClientResourceState() {
  const resource = clientElements.resource.value.trim();
  if (clientElements.resourceLabel) {
    clientElements.resourceLabel.textContent = resource ? fileName(resource) : 'Sin recurso guardado';
  }
  if (clientElements.folder) {
    clientElements.folder.title = resource ? resource : 'Seleccionar recurso';
  }
  if (clientElements.resourceClear) {
    clientElements.resourceClear.disabled = !resource;
  }
}

function fillClientForm(client = emptyClient()) {
  clientsState.selectedId = client.id || null;
  clientElements.name.value = client.name || '';
  clientElements.rnc.value = client.rnc || '';
  clientElements.cedula.value = client.cedula || '';
  clientElements.tss.value = client.tss_class || '';
  clientElements.pcLocation.value = client.pc_location || '';
  clientElements.resource.value = client.resource_path || '';
  clientElements.description.value = client.work_description || '';
  clientElements.delete.disabled = !clientsState.selectedId;
  renderClientResourceState();
  renderClientList();
}

async function copyClientValue(value, button) {
  const text = String(value || '').trim();
  if (!text) return;
  await desktop.copyText(text);
  document.querySelectorAll('.copy-toast').forEach(item => item.remove());
  const toast = document.createElement('span');
  toast.className = 'copy-toast';
  toast.textContent = 'copiado en el portapapeles';
  button.parentElement.appendChild(toast);
  setTimeout(() => toast.remove(), 5000);
}

function renderClientList() {
  const selected = clientsState.selectedId;
  clientElements.count.textContent = `${clientsState.items.length} cliente${clientsState.items.length === 1 ? '' : 's'}`;
  clientElements.list.innerHTML = clientsState.items.map(client => `<button class="client-list-item ${client.id === selected ? 'active' : ''}" type="button" data-client-id="${escapeHtml(client.id)}">
    <span class="client-avatar">${escapeHtml(clientInitials(client.name))}</span>
    <span><strong>${escapeHtml(client.name)}</strong><span>${escapeHtml(client.rnc || client.cedula || 'Sin identificación')}</span></span>
  </button>`).join('') || '<p>No hay clientes todavía.</p>';
}

async function loadClients(search = clientElements.search.value.trim()) {
  clientsState.items = await api(`/clients${search ? `?search=${encodeURIComponent(search)}` : ''}`);
  clientsState.loaded = true;
  renderClientList();
  if (clientsState.selectedId && !clientsState.items.some(item => item.id === clientsState.selectedId)) fillClientForm();
}

async function selectClient(clientId) {
  const client = await api(`/clients/${encodeURIComponent(clientId)}`);
  fillClientForm(client);
}

async function saveClient() {
  const payload = clientFormData();
  if (!payload.name) {
    clientElements.status.textContent = 'El nombre es obligatorio.';
    return;
  }
  const saved = await api(payload.id ? `/clients/${encodeURIComponent(payload.id)}` : '/clients', {
    method: payload.id ? 'PUT' : 'POST',
    body: JSON.stringify(payload)
  });
  clientElements.status.textContent = 'Cliente guardado.';
  await loadClients('');
  clientElements.search.value = '';
  fillClientForm(saved);
}

async function deleteClient() {
  if (!clientsState.selectedId) return;
  await api(`/clients/${encodeURIComponent(clientsState.selectedId)}`, { method: 'DELETE' });
  clientElements.status.textContent = 'Cliente eliminado.';
  fillClientForm();
  await loadClients();
}

function renderProposal() {
  const source = proposalState.source || '';
  const preview = proposalState.preview || '';
  const folder = folderName(source);
  proposalElements.savedName.textContent = source ? fileName(source) : 'Sin PDF guardado';
  proposalElements.sourceLabel.textContent = source || 'Sin PDF base seleccionado.';
  proposalElements.result.textContent = preview ? `Resultado: "${preview}"` : 'Resultado: escribe un nombre para generar la vista previa.';
  proposalElements.previewFile.textContent = preview ? `Archivo nuevo: ${preview}` : 'Archivo nuevo: pendiente';
  proposalElements.previewFolder.textContent = folder ? `Carpeta: ${folder}` : 'Carpeta: pendiente';
  proposalElements.previewEmpty.textContent = preview && source ? preview : 'Selecciona un PDF base y escribe un nombre.';
  proposalElements.create.disabled = proposalState.creating || !source || !preview;
  proposalElements.create.textContent = proposalState.creating ? 'Creando copia...' : 'Crear copia renombrada';
}

async function loadProposal() {
  const settings = await api('/proposals/settings');
  proposalState.source = settings.copy_source_pdf || '';
  proposalState.loaded = true;
  await updateProposalPreview();
  renderProposal();
}

async function saveProposalSource(source) {
  await api('/proposals/settings', { method: 'PUT', body: JSON.stringify({ copy_source_pdf: source || '' }) });
  proposalState.source = source || '';
  await updateProposalPreview();
  renderProposal();
}

async function chooseProposalSource() {
  const file = await desktop.chooseFile();
  if (!file) return;
  await saveProposalSource(file);
  proposalElements.status.textContent = 'PDF base guardado.';
}

async function updateProposalPreview() {
  const variableName = proposalElements.variableName.value.trim();
  if (!variableName) {
    proposalState.preview = '';
    renderProposal();
    return;
  }
  try {
    const result = await api('/proposals/preview', {
      method: 'POST',
      body: JSON.stringify({ variable_name: variableName, proposal_type: proposalElements.type.value })
    });
    proposalState.preview = result.filename || '';
    proposalElements.status.textContent = '';
  } catch (error) {
    proposalState.preview = '';
    proposalElements.status.textContent = error.message;
  }
  renderProposal();
}

async function createProposalCopy() {
  if (!proposalState.source || !proposalState.preview) return;
  proposalState.creating = true;
  renderProposal();
  try {
    const result = await api('/proposals/create', {
      method: 'POST',
      body: JSON.stringify({
        source: proposalState.source,
        variable_name: proposalElements.variableName.value.trim(),
        proposal_type: proposalElements.type.value
      })
    });
    proposalElements.status.textContent = `Copia creada: ${result.filename}`;
    if (result.target) await desktop.openPath(folderName(result.target));
  } finally {
    proposalState.creating = false;
    renderProposal();
  }
}

function emptyFiscalBuyer() {
  return { id: null, name: '', purchase_date: '', expiration_date: '', email: '', price: '', channel: 'desconocido' };
}

function normalizeFiscalChannel(channel) {
  const allowed = ['instagram', 'pagina web', 'youtube', 'desconocido'];
  return allowed.includes(channel) ? channel : 'desconocido';
}

function todayIsoDate() {
  return new Date().toISOString().slice(0, 10);
}

function emptyFiscalVersion() {
  return { id: null, version: '', change_date: todayIsoDate(), change_type: 'Lanzamiento', description: '', affects_macros: 'Si', requires_manual_update: 'No' };
}

function fiscalVersionData() {
  return {
    id: fiscalState.selectedVersionId,
    version: fiscalElements.versionNumber.value.trim(),
    change_date: fiscalElements.versionDate.value,
    change_type: fiscalElements.versionType.value,
    description: fiscalElements.versionDescription.value.trim(),
    affects_macros: fiscalElements.versionAffects.value,
    requires_manual_update: fiscalElements.versionManual.value
  };
}

function fillFiscalVersionForm(version = emptyFiscalVersion()) {
  fiscalState.selectedVersionId = version.id || null;
  fiscalElements.versionNumber.value = version.version || '';
  fiscalElements.versionDate.value = version.change_date || todayIsoDate();
  fiscalElements.versionType.value = version.change_type || 'Lanzamiento';
  fiscalElements.versionDescription.value = version.description || '';
  fiscalElements.versionAffects.value = version.affects_macros || 'Si';
  fiscalElements.versionManual.value = version.requires_manual_update || 'No';
}

function fiscalMessageText(name, messageType = 'Plantilla fiscal') {
  const buyerName = String(name || '').trim();
  const greeting = buyerName ? `Hola, ${buyerName},` : 'Hola,';
  if (messageType === 'Actualizacion') {
    return `${greeting}

Te comparto la actualizacion de la plantilla fiscal.

Antes de abrir el archivo, recuerda activar las macros para que la plantilla funcione correctamente.

Si tienes alguna duda o necesitas ayuda, puedes escribirme con confianza.

Quedo atento.`;
  }
  return `${greeting} Gracias por tu compra.

Te informamos que la plantilla tiene una duracion de 365 dias a partir de hoy.

Importante antes de usarla:
Antes de abrir el archivo, debes activar las macros, ya que esto es necesario para que la plantilla funcione correctamente.

A continuacion te comparto los enlaces de apoyo:

Primer uso (como activar las macros):
https://youtu.be/i-_2RdeaRko?si=eELy0jSVx9VWXEzV

Tutoriales de uso:
https://www.rddebito.com/servicios/plantillas/plantilla-fiscal/tutoriales

Si tienes alguna duda o necesitas ayuda, puedes escribirme con confianza. Estoy para ayudarte.

Exitos con la plantilla.`;
}

function fiscalBuyerData() {
  return {
    id: fiscalState.selectedId,
    name: fiscalElements.name.value.trim(),
    purchase_date: fiscalElements.purchaseDate.value,
    expiration_date: fiscalElements.expirationDate.value,
    email: fiscalElements.email.value.trim(),
    price: fiscalElements.price.value.trim(),
    channel: fiscalElements.channel.value
  };
}

function fillFiscalBuyerForm(buyer = emptyFiscalBuyer()) {
  fiscalState.selectedId = buyer.id || null;
  fiscalElements.name.value = buyer.name || '';
  fiscalElements.purchaseDate.value = buyer.purchase_date || '';
  fiscalElements.expirationDate.value = buyer.expiration_date || '';
  fiscalElements.email.value = buyer.email || '';
  fiscalElements.price.value = buyer.price || '';
  fiscalElements.channel.value = normalizeFiscalChannel(buyer.channel || 'desconocido');
}

function renderFiscal() {
  const summary = fiscalState.summary || {};
  const buyers = fiscalState.buyers || [];
  const versions = fiscalState.versions || [];
  if (!fiscalElements.versionDate.value) fillFiscalVersionForm();
  const today = todayIsoDate();
  const todayCount = buyers.filter(buyer => buyer.purchase_date === today).length;
  fiscalElements.versionsCount.textContent = String(summary.versions ?? fiscalState.versions.length);
  fiscalElements.buyersCount.textContent = String(summary.buyers ?? buyers.length);
  fiscalElements.buyersToday.textContent = `+${todayCount} hoy`;
  fiscalElements.netProfit.textContent = formatMoney(summary.net_profit);
  fiscalElements.grossProfit.textContent = formatMoney(summary.gross_profit);
  fiscalElements.tableCount.textContent = `Mostrando ${buyers.length} comprador${buyers.length === 1 ? '' : 'es'}`;
  fiscalElements.messageBuyer.innerHTML = '<option value="">Selecciona un comprador</option>' + buyers.map(buyer => {
    const label = `${buyer.name}${buyer.email ? ` - ${buyer.email}` : ''}`;
    return `<option value="${escapeHtml(buyer.id)}">${escapeHtml(label)}</option>`;
  }).join('');
  fiscalElements.messageBuyer.value = buyers.some(buyer => buyer.id === fiscalState.messageBuyerId) ? fiscalState.messageBuyerId : '';
  fiscalElements.table.innerHTML = buyers.map(buyer => `
    <tr data-fiscal-buyer-id="${escapeHtml(buyer.id)}">
      <td>
        <div class="fiscal-copy-cell">
          <strong>${escapeHtml(buyer.name)}</strong>
          <button class="fiscal-copy-icon" type="button" data-fiscal-copy="${escapeHtml(buyer.name)}" title="Copiar nombre" aria-label="Copiar nombre">${copyIconSvg()}</button>
        </div>
      </td>
      <td>${formatShortDate(buyer.purchase_date)}</td>
      <td>${formatShortDate(buyer.expiration_date)}</td>
      <td>
        <div class="fiscal-copy-cell">
          <span>${escapeHtml(buyer.email || '-')}</span>
          <button class="fiscal-copy-icon" type="button" data-fiscal-copy="${escapeHtml(buyer.email || '')}" title="Copiar correo electronico" aria-label="Copiar correo electronico">${copyIconSvg()}</button>
        </div>
      </td>
      <td><b>${formatMoney(buyer.price)}</b></td>
      <td><span class="fiscal-channel">${escapeHtml(normalizeFiscalChannel(buyer.channel || 'desconocido'))}</span></td>
    </tr>
  `).join('') || '<tr><td colspan="6">No hay compradores registrados.</td></tr>';
  fiscalElements.versionsList.innerHTML = versions.map(version => `
    <tr class="${version.id === fiscalState.selectedVersionId ? 'active' : ''}" data-fiscal-version-id="${escapeHtml(version.id)}">
      <td>${escapeHtml(version.version)}</td>
      <td>${formatShortDate(version.change_date)}</td>
      <td>${escapeHtml(version.change_type)}</td>
      <td><span title="${escapeHtml(version.description || '')}">${escapeHtml(version.description || '-')}</span></td>
      <td>${escapeHtml(version.affects_macros || 'No')}</td>
      <td>${escapeHtml(version.requires_manual_update || 'No')}</td>
    </tr>
  `).join('') || '<tr><td colspan="6">No hay versiones registradas.</td></tr>';
  renderFiscalMessage();
}

async function loadFiscal() {
  const [versions, buyers, summary] = await Promise.all([
    api('/fiscal/versions'),
    api('/fiscal/buyers'),
    api('/fiscal/summary')
  ]);
  fiscalState.versions = versions;
  fiscalState.buyers = buyers;
  fiscalState.summary = summary;
  fiscalState.loaded = true;
  renderFiscal();
}

async function saveFiscalBuyer() {
  const payload = fiscalBuyerData();
  if (!payload.name || !payload.purchase_date) {
    fiscalElements.status.textContent = 'Nombre y fecha de compra son obligatorios.';
    return;
  }
  const saved = await api(payload.id ? `/fiscal/buyers/${encodeURIComponent(payload.id)}` : '/fiscal/buyers', {
    method: payload.id ? 'PUT' : 'POST',
    body: JSON.stringify(payload)
  });
  fiscalElements.status.textContent = 'Comprador guardado.';
  fillFiscalBuyerForm(saved);
  await loadFiscal();
}

async function saveFiscalVersion() {
  const payload = fiscalVersionData();
  if (!payload.version || !payload.change_date || !payload.change_type) {
    fiscalElements.versionStatus.textContent = 'Version, fecha y tipo de cambio son obligatorios.';
    return;
  }
  const saved = await api('/fiscal/versions', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
  fiscalElements.versionStatus.textContent = 'Version guardada.';
  fillFiscalVersionForm(saved);
  await loadFiscal();
}

function selectFiscalVersion(versionId) {
  const version = fiscalState.versions.find(item => item.id === versionId);
  if (!version) return;
  fillFiscalVersionForm(version);
  renderFiscal();
}

function selectFiscalBuyer(buyerId) {
  const buyer = fiscalState.buyers.find(item => item.id === buyerId);
  if (!buyer) return;
  fillFiscalBuyerForm(buyer);
  fiscalState.messageBuyerId = buyer.id;
  fiscalElements.messageBuyer.value = buyer.id;
  fiscalElements.messageName.value = buyer.name || '';
  renderFiscalMessage();
}

function renderFiscalMessage() {
  const selectedBuyer = fiscalState.buyers.find(item => item.id === fiscalState.messageBuyerId);
  const name = fiscalElements.messageName.value.trim() || selectedBuyer?.name || '';
  const messageType = fiscalElements.messageType.value || 'Plantilla fiscal';
  fiscalElements.activeMessage.textContent = messageType;
  fiscalElements.activeClient.textContent = name || 'Sin cliente';
  fiscalElements.messagePreview.value = fiscalMessageText(name, messageType);
}

function showFiscalTab(panelId) {
  document.querySelectorAll('[data-fiscal-tab]').forEach(tab => {
    const active = tab.dataset.fiscalTab === panelId;
    tab.classList.toggle('active', active);
    tab.setAttribute('aria-selected', String(active));
  });
  document.querySelectorAll('.fiscal-panel').forEach(panel => {
    const active = panel.id === panelId;
    panel.hidden = !active;
    panel.classList.toggle('active', active);
  });
}

function showNotice(message, type = '') {
  elements.notice.hidden = !message;
  elements.notice.className = `notice ${type}`.trim();
  elements.notice.textContent = message;
}

function renderBackendStatus(status) {
  const current = status?.state || 'error';
  elements.statusPill.className = `status-pill ${current}`;
  elements.statusText.textContent = status?.message || 'Backend no disponible';
}

function renderSettings() {
  const settings = state.settings || { saved_folders: [], selected_output_folder: '', company_route_mappings: [] };
  const folders = [...new Set((settings.saved_folders || []).filter(Boolean))];
  if (settings.selected_output_folder && !folders.includes(settings.selected_output_folder)) folders.unshift(settings.selected_output_folder);
  elements.destinationSelect.innerHTML = folders.length
    ? folders.map(folder => `<option value="${escapeHtml(folder)}">${escapeHtml(folder)}</option>`).join('')
    : '<option value="">Sin carpeta configurada</option>';
  elements.destinationSelect.value = settings.selected_output_folder || folders[0] || '';

  const routes = (settings.company_route_mappings || []).filter(route => route.active !== false);
  elements.routeCount.textContent = `${routes.length} activa${routes.length === 1 ? '' : 's'}`;
  elements.routeList.innerHTML = routes.length
    ? routes.map(route => `<div class="route-item" title="${escapeHtml(route.folder || '')}"><b>${escapeHtml(route.company)}</b><span>Automática</span></div>`).join('')
    : '<div class="empty-routes">No hay rutas automáticas configuradas.</div>';
  const selected = elements.destinationSelect.value;
  elements.destinationSummary.textContent = selected
    ? `${routes.length} ruta${routes.length === 1 ? '' : 's'} automática${routes.length === 1 ? '' : 's'} · ${fileName(selected)}`
    : `${routes.length} rutas automáticas · Elige una carpeta general`;
}

function analysisFor(path) {
  return state.analysis.find(item => item.source === path);
}

function fileCard(path) {
  const item = analysisFor(path);
  const status = item?.status || 'analyzing';
  const cardClass = status === 'error' ? 'error' : status === 'completed' ? 'completed' : '';
  const label = status === 'analyzing' ? 'Analizando factura' : status === 'completed' ? 'Factura procesada' : status === 'error' ? 'Revisión necesaria' : 'Factura lista';
  let recommendation = '<div class="file-detail">Leyendo NCF y razón social…</div>';
  if (item?.status === 'error') {
    recommendation = `<div class="file-detail error-text">${escapeHtml(item.error)}</div>`;
  } else if (item) {
    recommendation = `<div class="recommendation">
      <div class="name-block"><small>Original</small><span>${escapeHtml(fileName(path))}</span></div>
      <span class="arrow">→</span>
      <div class="name-block recommended"><small>${item.status === 'completed' ? 'Renombrado' : 'Recomendado'}</small><span>${escapeHtml(item.proposed_name)}</span></div>
    </div>
    <div class="file-detail">${escapeHtml(item.route_company)} · ${escapeHtml(item.destination)}</div>`;
  }
  return `<article class="file-card ${cardClass}">
    <div class="file-main">
      <span class="file-icon"><svg viewBox="0 0 24 24"><path d="M7 3h7l4 4v14H7zM14 3v5h5M9.5 13h5M9.5 17h3"/></svg></span>
      <div class="file-meta"><small>${label}</small><strong title="${escapeHtml(path)}">${escapeHtml(fileName(path))}</strong></div>
      <button class="remove-file" type="button" data-remove-path="${escapeHtml(path)}" aria-label="Quitar ${escapeHtml(fileName(path))}">×</button>
    </div>${recommendation}
  </article>`;
}

function renderFiles() {
  elements.filesSection.hidden = state.files.length === 0;
  elements.fileList.innerHTML = state.files.map(fileCard).join('');
  const ready = state.analysis.filter(item => item.status === 'ready').length;
  elements.processButton.disabled = state.processing || ready === 0;
  elements.processButton.classList.toggle('loading', state.processing);
  elements.processButton.querySelector('span').textContent = state.processing ? 'Procesando…' : ready ? `Procesar ${ready} PDF${ready === 1 ? '' : 's'}` : 'Procesar';
}

async function loadSettings() {
  state.settings = await api('/renamer/settings');
  renderSettings();
}

async function saveSettings(changes) {
  state.settings = await api('/renamer/settings', { method: 'PUT', body: JSON.stringify(changes) });
  renderSettings();
  if (state.files.length) await analyzeFiles();
}

async function addFiles(paths) {
  const uniquePdfPaths = [...new Set(paths.filter(path => path && path.toLowerCase().endsWith('.pdf')))];
  state.files = [...new Set([...state.files, ...uniquePdfPaths])];
  showNotice(uniquePdfPaths.length ? '' : 'Solo puedes agregar archivos PDF.', uniquePdfPaths.length ? '' : 'error');
  renderFiles();
  if (uniquePdfPaths.length) await analyzeFiles();
}

async function analyzeFiles() {
  if (!state.files.length || !state.settings) return;
  state.analysis = [];
  renderFiles();
  try {
    state.analysis = await api('/renamer/analyze', {
      method: 'POST',
      body: JSON.stringify({
        paths: state.files,
        routes: state.settings.company_route_mappings || [],
        default_folder: state.settings.selected_output_folder || ''
      })
    });
    const errors = state.analysis.filter(item => item.status === 'error').length;
    showNotice(errors ? `${errors} archivo${errors === 1 ? '' : 's'} necesita${errors === 1 ? '' : 'n'} revisión antes de procesar.` : '', errors ? 'error' : '');
  } catch (error) {
    showNotice(error.message, 'error');
  }
  renderFiles();
}

async function processFiles() {
  const readyItems = state.analysis.filter(item => item.status === 'ready');
  if (!readyItems.length) return;
  state.processing = true;
  renderFiles();
  showNotice('Renombrando y moviendo los archivos…');
  try {
    const results = await api('/renamer/execute', { method: 'POST', body: JSON.stringify({ items: readyItems }) });
    const resultMap = new Map(results.map(item => [item.source, item]));
    state.analysis = state.analysis.map(item => resultMap.get(item.source) || item);
    const completed = results.filter(item => item.status === 'completed').length;
    const failed = results.length - completed;
    showNotice(
      failed ? `${completed} procesado${completed === 1 ? '' : 's'} y ${failed} con error.` : `${completed} PDF${completed === 1 ? '' : 's'} procesado${completed === 1 ? '' : 's'} correctamente.`,
      failed ? 'error' : 'success'
    );
  } catch (error) {
    showNotice(error.message, 'error');
  } finally {
    state.processing = false;
    renderFiles();
  }
}

elements.destinationToggle.addEventListener('click', () => {
  const expanded = elements.destinationToggle.getAttribute('aria-expanded') === 'true';
  elements.destinationToggle.setAttribute('aria-expanded', String(!expanded));
  elements.destinationPanel.hidden = expanded;
});
elements.destinationSelect.addEventListener('change', () => saveSettings({ selected_output_folder: elements.destinationSelect.value }));
elements.addDestination.addEventListener('click', async () => {
  const folder = await desktop.chooseDirectory();
  if (!folder) return;
  const folders = [...new Set([...(state.settings.saved_folders || []), folder])];
  await saveSettings({ saved_folders: folders, selected_output_folder: folder });
});
elements.dropZone.addEventListener('click', async () => addFiles(await desktop.choosePdf(true)));
for (const eventName of ['dragenter', 'dragover']) {
  elements.dropZone.addEventListener(eventName, event => { event.preventDefault(); elements.dropZone.classList.add('dragging'); });
}
for (const eventName of ['dragleave', 'drop']) {
  elements.dropZone.addEventListener(eventName, event => { event.preventDefault(); elements.dropZone.classList.remove('dragging'); });
}
elements.dropZone.addEventListener('drop', event => {
  const paths = [...event.dataTransfer.files].map(file => desktop.pathForFile(file)).filter(Boolean);
  addFiles(paths);
});
elements.processButton.addEventListener('click', processFiles);
elements.clearButton.addEventListener('click', () => { state.files = []; state.analysis = []; showNotice(''); renderFiles(); });
elements.fileList.addEventListener('click', event => {
  const button = event.target.closest('[data-remove-path]');
  if (!button) return;
  const path = button.dataset.removePath;
  state.files = state.files.filter(item => item !== path);
  state.analysis = state.analysis.filter(item => item.source !== path);
  renderFiles();
});

bindPageNavigation();

document.querySelectorAll('[data-pomodoro-tab]').forEach(button => {
  button.addEventListener('click', () => {
    const target = button.dataset.pomodoroTab;
    pomodoroState.activeTab = target;
    document.querySelectorAll('.pomodoro-panel').forEach(panel => { panel.hidden = panel.id !== target; panel.classList.toggle('active', panel.id === target); });
    document.querySelectorAll('[data-pomodoro-tab]').forEach(item => {
      const active = item === button;
      item.classList.toggle('active', active);
      item.setAttribute('aria-selected', String(active));
    });
    renderPomodoroSidebar();
    renderFlowList();
    renderTimerPicker();
  });
});

clientElements.search.addEventListener('input', () => {
  loadClients(clientElements.search.value.trim()).catch(error => { clientElements.status.textContent = error.message; });
});
clientElements.list.addEventListener('click', event => {
  const button = event.target.closest('[data-client-id]');
  if (!button) return;
  selectClient(button.dataset.clientId).catch(error => { clientElements.status.textContent = error.message; });
});
clientElements.new.addEventListener('click', () => {
  clientElements.status.textContent = '';
  fillClientForm();
});
clientElements.save.addEventListener('click', () => saveClient().catch(error => { clientElements.status.textContent = error.message; }));
clientElements.delete.addEventListener('click', () => deleteClient().catch(error => { clientElements.status.textContent = error.message; }));
clientElements.locationSelect.addEventListener('click', async () => {
  const folder = await desktop.chooseDirectory();
  if (!folder) return;
  clientElements.pcLocation.value = folder;
  clientElements.status.textContent = '';
});
clientElements.locationOpen.addEventListener('click', async () => {
  const folder = clientElements.pcLocation.value.trim();
  if (folder) {
    await desktop.openPath(folder);
    return;
  }
  const selected = await desktop.chooseDirectory();
  if (selected) clientElements.pcLocation.value = selected;
});
clientElements.folder.addEventListener('click', async () => {
  const resource = clientElements.resource.value.trim();
  if (resource) {
    await desktop.openPath(resource);
    return;
  }
  const file = await desktop.chooseFile();
  if (file) {
    clientElements.resource.value = file;
    renderClientResourceState();
  }
});
clientElements.resourceClear.addEventListener('click', () => {
  clientElements.resource.value = '';
  renderClientResourceState();
  clientElements.status.textContent = 'Recurso borrado. Guarda el cliente para confirmar.';
});
clientElements.copyRnc.addEventListener('click', () => copyClientValue(clientElements.rnc.value, clientElements.copyRnc).catch(error => { clientElements.status.textContent = error.message; }));
clientElements.copyCedula.addEventListener('click', () => copyClientValue(clientElements.cedula.value, clientElements.copyCedula).catch(error => { clientElements.status.textContent = error.message; }));
clientElements.copyTss.addEventListener('click', () => copyClientValue(clientElements.tss.value, clientElements.copyTss).catch(error => { clientElements.status.textContent = error.message; }));
clientElements.tssToggle.addEventListener('click', () => {
  const fields = document.querySelector('.client-tss-fields');
  const expanded = clientElements.tssToggle.getAttribute('aria-expanded') !== 'false';
  clientElements.tssToggle.setAttribute('aria-expanded', String(!expanded));
  fields.hidden = expanded;
});

proposalElements.selectSource.addEventListener('click', () => chooseProposalSource().catch(error => { proposalElements.status.textContent = error.message; }));
proposalElements.changeSource.addEventListener('click', () => chooseProposalSource().catch(error => { proposalElements.status.textContent = error.message; }));
proposalElements.clearSource.addEventListener('click', () => saveProposalSource('').then(() => { proposalElements.status.textContent = 'Ruta borrada.'; }).catch(error => { proposalElements.status.textContent = error.message; }));
proposalElements.variableName.addEventListener('input', () => updateProposalPreview());
proposalElements.type.addEventListener('change', () => updateProposalPreview());
proposalElements.create.addEventListener('click', () => createProposalCopy().catch(error => { proposalElements.status.textContent = error.message; proposalState.creating = false; renderProposal(); }));

fiscalElements.new.addEventListener('click', () => {
  fiscalElements.status.textContent = '';
  fillFiscalBuyerForm();
});
fiscalElements.save.addEventListener('click', () => saveFiscalBuyer().catch(error => { fiscalElements.status.textContent = error.message; }));
fiscalElements.versionClear.addEventListener('click', () => {
  fiscalElements.versionStatus.textContent = '';
  fillFiscalVersionForm();
  renderFiscal();
});
fiscalElements.versionSave.addEventListener('click', () => saveFiscalVersion().catch(error => { fiscalElements.versionStatus.textContent = error.message; }));
fiscalElements.versionsList.addEventListener('click', event => {
  const target = event.target instanceof Element ? event.target : event.target.parentElement;
  const row = target?.closest('[data-fiscal-version-id]');
  if (row) selectFiscalVersion(row.dataset.fiscalVersionId);
});
fiscalElements.versionCopyDescription.addEventListener('click', () => {
  const version = fiscalState.versions.find(item => item.id === fiscalState.selectedVersionId);
  const description = version?.description || fiscalElements.versionDescription.value;
  copyClientValue(description, fiscalElements.versionCopyDescription)
    .then(() => { fiscalElements.versionStatus.textContent = 'Descripcion copiada.'; })
    .catch(error => { fiscalElements.versionStatus.textContent = error.message; });
});
document.querySelectorAll('[data-fiscal-tab]').forEach(tab => {
  tab.addEventListener('click', () => showFiscalTab(tab.dataset.fiscalTab));
});
fiscalElements.messageType.addEventListener('change', renderFiscalMessage);
fiscalElements.messageName.addEventListener('input', () => {
  fiscalState.messageBuyerId = '';
  fiscalElements.messageBuyer.value = '';
  renderFiscalMessage();
});
fiscalElements.messageBuyer.addEventListener('change', () => {
  fiscalState.messageBuyerId = fiscalElements.messageBuyer.value;
  const buyer = fiscalState.buyers.find(item => item.id === fiscalState.messageBuyerId);
  fiscalElements.messageName.value = buyer?.name || '';
  renderFiscalMessage();
});
fiscalElements.messageCopy.addEventListener('click', () => {
  copyClientValue(fiscalElements.messagePreview.value, fiscalElements.messageCopy)
    .then(() => { fiscalElements.messageStatus.textContent = 'Mensaje copiado.'; })
    .catch(error => { fiscalElements.messageStatus.textContent = error.message; });
});
fiscalElements.table.addEventListener('click', event => {
  const target = event.target instanceof Element ? event.target : event.target.parentElement;
  const copyButton = target?.closest('[data-fiscal-copy]');
  if (copyButton) {
    copyClientValue(copyButton.dataset.fiscalCopy, copyButton).catch(error => { fiscalElements.status.textContent = error.message; });
    return;
  }
  const row = target?.closest('[data-fiscal-buyer-id]');
  if (row) selectFiscalBuyer(row.dataset.fiscalBuyerId);
});

pomodoroElements.toggle.addEventListener('click', () => sendPomodoroCommand(pomodoroState.data?.running ? 'pause' : 'start'));
pomodoroElements.skip.addEventListener('click', () => sendPomodoroCommand('skip'));
pomodoroElements.reset.addEventListener('click', () => sendPomodoroCommand('reset'));
pomodoroElements.autoBreak.addEventListener('change', savePomodoroSettings);
pomodoroElements.autoWork.addEventListener('change', savePomodoroSettings);
pomodoroElements.taskForm.addEventListener('submit', async event => {
  event.preventDefault();
  const title = pomodoroElements.taskTitle.value.trim();
  if (!title) {
    pomodoroElements.taskStatus.textContent = 'Escribe una tarea primero.';
    return;
  }
  try { await createPomodoroTask(title); } catch (error) { pomodoroElements.taskStatus.textContent = error.message; }
});
pomodoroElements.taskList.addEventListener('click', async event => {
  const clickTarget = event.target instanceof Element ? event.target : event.target.parentElement;
  const button = clickTarget?.closest('[data-task-action]');
  if (!button) return;
  const row = button.closest('[data-task-id]');
  const taskId = row?.dataset.taskId;
  if (!taskId) return;
  try {
    if (button.dataset.taskAction === 'delete') await deletePomodoroTask(taskId);
    if (button.dataset.taskAction === 'select') await selectPomodoroTask(taskId);
  } catch (error) {
    pomodoroElements.taskStatus.textContent = error.message;
  }
});
pomodoroElements.activeClear.addEventListener('click', () => clearPomodoroSelection().catch(error => showNotice(error.message, 'error')));
pomodoroElements.activeComplete.addEventListener('click', () => completeActiveTask().catch(error => showNotice(error.message, 'error')));
pomodoroElements.activeFlowZone.addEventListener('click', async event => {
  const clickTarget = event.target instanceof Element ? event.target : event.target.parentElement;
  const button = clickTarget?.closest('[data-active-flow-action]');
  if (!button) return;
  const taskId = button.closest('[data-active-flow-task-id]')?.dataset.activeFlowTaskId;
  try {
    if (button.dataset.activeFlowAction === 'toggle-completed') {
      pomodoroState.showActiveFlowCompleted = !pomodoroState.showActiveFlowCompleted;
      renderPomodoro();
    }
    if (button.dataset.activeFlowAction === 'complete') await completeActiveFlowTask(taskId);
    if (button.dataset.activeFlowAction === 'remove') await removeActiveFlowTask(taskId);
  } catch (error) {
    showNotice(error.message, 'error');
  }
});
pomodoroElements.sidebar.addEventListener('click', async event => {
  const clickTarget = event.target instanceof Element ? event.target : event.target.parentElement;
  const viewButton = clickTarget?.closest('[data-sidebar-view]');
  if (viewButton) {
    pomodoroState.timerSidebarMode = viewButton.dataset.sidebarView;
    renderPomodoroSidebar();
    return;
  }
  const flowTaskAction = clickTarget?.closest('[data-flow-task-action]');
  if (flowTaskAction) {
    if (flowTaskAction.dataset.flowTaskAction === 'open-modal') {
      pomodoroElements.flowTaskModal.hidden = false;
      pomodoroElements.flowTaskModalStatus.textContent = '';
      pomodoroElements.flowTaskModalInput.value = '';
      pomodoroElements.flowTaskModalInput.focus();
    }
    if (flowTaskAction.dataset.flowTaskAction === 'add') addDraftTask(flowTaskAction.dataset.taskId);
    return;
  }
  const toggle = clickTarget?.closest('[data-sidebar-action="toggle-completed"]');
  if (toggle) {
    pomodoroState.showCompleted = !pomodoroState.showCompleted;
    renderPomodoroSidebar();
    return;
  }
  const button = clickTarget?.closest('[data-pick-action]');
  if (!button) return;
  const item = button.closest('[data-pick-id]');
  if (!item) return;
  try { await selectPomodoroItem(item.dataset.pickType, item.dataset.pickId); } catch (error) { showNotice(error.message, 'error'); }
});
document.querySelector('#timer-panel').addEventListener('click', async event => {
  const clickTarget = event.target instanceof Element ? event.target : event.target.parentElement;
  const button = clickTarget?.closest('[data-pick-action]');
  if (!button) return;
  const item = button.closest('[data-pick-id]');
  if (!item) return;
  try { await selectPomodoroItem(item.dataset.pickType, item.dataset.pickId); } catch (error) { showNotice(error.message, 'error'); }
});
document.querySelector('#timer-panel').addEventListener('dragstart', event => {
  const dragTarget = event.target instanceof Element ? event.target : event.target.parentElement;
  const item = dragTarget?.closest('[data-pick-id]');
  if (!item) return;
  event.dataTransfer.setData('application/x-pomodoro-type', item.dataset.pickType);
  event.dataTransfer.setData('text/plain', item.dataset.pickId);
  event.dataTransfer.effectAllowed = 'copy';
});
pomodoroElements.timerCard.addEventListener('dragover', event => {
  if (!Array.from(event.dataTransfer.types).includes('text/plain')) return;
  event.preventDefault();
  pomodoroElements.timerCard.classList.add('drag-over');
});
pomodoroElements.timerCard.addEventListener('dragleave', () => {
  pomodoroElements.timerCard.classList.remove('drag-over');
});
pomodoroElements.timerCard.addEventListener('drop', async event => {
  event.preventDefault();
  pomodoroElements.timerCard.classList.remove('drag-over');
  const id = event.dataTransfer.getData('text/plain');
  const type = event.dataTransfer.getData('application/x-pomodoro-type') || 'task';
  if (!id) return;
  try { await selectPomodoroItem(type, id); } catch (error) { showNotice(error.message, 'error'); }
});
pomodoroElements.flowForm.addEventListener('submit', async event => {
  event.preventDefault();
  try { await saveFlowDraft(); } catch (error) { pomodoroElements.flowStatus.textContent = error.message; }
});
pomodoroElements.flowCreateOpen.addEventListener('click', () => openFlowBuilder());
pomodoroElements.flowBuilderBack.addEventListener('click', () => closeFlowBuilder());
pomodoroElements.flowList.addEventListener('click', async event => {
  const clickTarget = event.target instanceof Element ? event.target : event.target.parentElement;
  const button = clickTarget?.closest('[data-flow-action]');
  if (!button) return;
  const row = button.closest('[data-flow-id]');
  const flowId = row?.dataset.flowId;
  if (!flowId) return;
  try {
    if (button.dataset.flowAction === 'select') await selectPomodoroFlow(flowId);
    if (button.dataset.flowAction === 'edit') openFlowBuilder(flowId);
    if (button.dataset.flowAction === 'delete') await deletePomodoroFlow(flowId);
    if (button.dataset.flowAction === 'remove-task') await assignTaskToFlow(flowId, button.dataset.taskId, false);
  } catch (error) {
    pomodoroElements.flowStatus.textContent = error.message;
  }
});
pomodoroElements.sidebar.addEventListener('dragstart', event => {
  const dragTarget = event.target instanceof Element ? event.target : event.target.parentElement;
  const item = dragTarget?.closest('[data-pick-id]');
  if (item) {
    event.dataTransfer.setData('application/x-pomodoro-type', item.dataset.pickType);
    event.dataTransfer.setData('text/plain', item.dataset.pickId);
    event.dataTransfer.effectAllowed = 'copy';
    return;
  }
  const task = dragTarget?.closest('[data-sidebar-task-id]');
  if (!task) return;
  event.dataTransfer.setData('application/x-pomodoro-type', 'task');
  event.dataTransfer.setData('text/plain', task.dataset.sidebarTaskId);
  event.dataTransfer.effectAllowed = 'copy';
});
pomodoroElements.flowList.addEventListener('dragover', event => {
  const dragTarget = event.target instanceof Element ? event.target : event.target.parentElement;
  const target = dragTarget?.closest('[data-flow-drop]');
  if (!target) return;
  event.preventDefault();
  target.classList.add('drag-over');
});
pomodoroElements.flowList.addEventListener('dragleave', event => {
  const dragTarget = event.target instanceof Element ? event.target : event.target.parentElement;
  dragTarget?.closest('[data-flow-drop]')?.classList.remove('drag-over');
});
pomodoroElements.flowList.addEventListener('drop', async event => {
  const dropTarget = event.target instanceof Element ? event.target : event.target.parentElement;
  const target = dropTarget?.closest('[data-flow-drop]');
  if (!target) return;
  event.preventDefault();
  target.classList.remove('drag-over');
  const flowId = target.closest('[data-flow-id]')?.dataset.flowId;
  const taskId = event.dataTransfer.getData('text/plain');
  if (!flowId || !taskId) return;
  try { await assignTaskToFlow(flowId, taskId, true); } catch (error) { pomodoroElements.flowStatus.textContent = error.message; }
});
pomodoroElements.flowSelectedList.addEventListener('click', event => {
  const clickTarget = event.target instanceof Element ? event.target : event.target.parentElement;
  const button = clickTarget?.closest('[data-draft-action="remove"]');
  const taskId = button?.closest('[data-draft-task-id]')?.dataset.draftTaskId;
  if (taskId) removeDraftTask(taskId);
});
pomodoroElements.flowSelectedList.addEventListener('dragstart', event => {
  const dragTarget = event.target instanceof Element ? event.target : event.target.parentElement;
  const item = dragTarget?.closest('[data-draft-task-id]');
  if (!item) return;
  pomodoroState.draggedDraftTaskId = item.dataset.draftTaskId;
  event.dataTransfer.setData('application/x-flow-draft-task', item.dataset.draftTaskId);
  event.dataTransfer.effectAllowed = 'move';
});
pomodoroElements.flowSelectedList.addEventListener('dragover', event => {
  const hasDraftTask = Array.from(event.dataTransfer.types).includes('application/x-flow-draft-task');
  const hasSidebarTask = Array.from(event.dataTransfer.types).includes('text/plain');
  if (!hasDraftTask && !hasSidebarTask) return;
  event.preventDefault();
  const dragTarget = event.target instanceof Element ? event.target : event.target.parentElement;
  document.querySelectorAll('.flow-selected-task.drag-over').forEach(item => item.classList.remove('drag-over'));
  dragTarget?.closest('[data-draft-task-id]')?.classList.add('drag-over');
});
pomodoroElements.flowSelectedList.addEventListener('dragleave', event => {
  const dragTarget = event.target instanceof Element ? event.target : event.target.parentElement;
  dragTarget?.closest('[data-draft-task-id]')?.classList.remove('drag-over');
});
pomodoroElements.flowSelectedList.addEventListener('drop', event => {
  event.preventDefault();
  document.querySelectorAll('.flow-selected-task.drag-over').forEach(item => item.classList.remove('drag-over'));
  const dropTarget = event.target instanceof Element ? event.target : event.target.parentElement;
  const beforeTaskId = dropTarget?.closest('[data-draft-task-id]')?.dataset.draftTaskId || null;
  const draftTaskId = event.dataTransfer.getData('application/x-flow-draft-task');
  const sidebarTaskId = event.dataTransfer.getData('text/plain');
  if (draftTaskId) moveDraftTask(draftTaskId, beforeTaskId);
  else if (sidebarTaskId) addDraftTask(sidebarTaskId);
  pomodoroState.draggedDraftTaskId = null;
});
pomodoroElements.flowTaskModalClose.addEventListener('click', () => {
  pomodoroElements.flowTaskModal.hidden = true;
});
pomodoroElements.flowTaskModal.addEventListener('click', event => {
  if (event.target === pomodoroElements.flowTaskModal) pomodoroElements.flowTaskModal.hidden = true;
});
pomodoroElements.flowTaskModalForm.addEventListener('submit', async event => {
  event.preventDefault();
  const title = pomodoroElements.flowTaskModalInput.value.trim();
  if (!title) {
    pomodoroElements.flowTaskModalStatus.textContent = 'Escribe una tarea primero.';
    return;
  }
  try {
    const task = await createPomodoroTask(title);
    addDraftTask(task.id);
    pomodoroElements.flowTaskModal.hidden = true;
  } catch (error) {
    pomodoroElements.flowTaskModalStatus.textContent = error.message;
  }
});

desktop.onBackendChanged(status => {
  renderBackendStatus(status);
  if (status.state === 'connected') {
    loadSettings().catch(error => showNotice(error.message, 'error'));
    initializePomodoroRefresh().catch(() => {});
    if (!clientElements.page.hidden) loadClients().catch(error => { clientElements.status.textContent = error.message; });
    if (!proposalElements.page.hidden) loadProposal().catch(error => { proposalElements.status.textContent = error.message; });
    if (!fiscalElements.page.hidden) loadFiscal().catch(error => { fiscalElements.status.textContent = error.message; });
    if (!pomodoroElements.page.hidden) loadPomodoro().catch(() => {});
  }
});
readBackendStatus().then(async status => {
  renderBackendStatus(status);
  if (status.state === 'connected') {
    await loadSettings();
    initializePomodoroRefresh().catch(() => {});
  }
}).catch(error => { renderBackendStatus({ state: 'error', message: error.message }); showNotice(error.message, 'error'); });
