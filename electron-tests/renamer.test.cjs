const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(require('node:path').join(__dirname, '../electron/renderer/app.js'), 'utf8').replace(/\r\n/g, '\n');
function setup(overrides = {}) {
  const nodes = new Map();
  const node = () => ({ hidden: false, disabled: false, textContent: '', innerHTML: '', classList: { toggle() {} }, setAttribute() {}, querySelector() { return this; }, querySelectorAll() { return []; } });
  const elements = Object.fromEntries(['dropZone', 'processButton', 'clearButton', 'destinationSelect', 'addDestination', 'fileList', 'filesSection'].map(key => [key, node()]));
  const context = vm.createContext({
    state: { files: [], analysis: [], processing: false, settings: {} }, analysisRevision: 0, elements,
    document: { querySelector(selector) { if (!nodes.has(selector)) nodes.set(selector, node()); return nodes.get(selector); } },
    fileCard: path => path, folderName: path => String(path || '').replace(/[\\/][^\\/]*$/, ''),
    fileName: path => String(path).split(/[\\/]/).pop(), escapeHtml: value => String(value), showNotice() {}, ...overrides
  });
  for (const name of ['renderFiles', 'analyzeFiles', 'processFiles']) {
    const start = source.indexOf(`function ${name}(`);
    const end = source.indexOf('\n}\n', start) + 2;
    vm.runInContext(source.slice(source.slice(start - 6, start) === 'async ' ? start - 6 : start, end), context);
  }
  return { context, nodes };
}
test('la carga inicial oculta procesar; la selección oculta arrastrar y muestra subir más', () => {
  const { context: c, nodes } = setup();
  c.renderFiles();
  assert.equal(c.elements.dropZone.hidden, false);
  assert.equal(c.elements.processButton.hidden, true);
  c.state.files = ['a.pdf']; c.state.analysis = [{ source: 'a.pdf', status: 'ready' }];
  c.renderFiles();
  assert.equal(c.elements.dropZone.hidden, true);
  assert.equal(nodes.get('#add-more-files').hidden, false);
  assert.equal(c.elements.processButton.disabled, false);
});
test('el resultado ofrece una acción por carpeta y bloquea cambios mientras procesa', () => {
  const { context: c, nodes } = setup();
  c.state.files = ['a.pdf', 'b.pdf']; c.state.processing = true;
  c.state.analysis = ['a', 'b'].map(name => ({ source: `${name}.pdf`, status: 'completed', target: `C:/facturas/${name}.pdf` }));
  c.renderFiles();
  assert.equal((nodes.get('#processed-folders').innerHTML.match(/data-open-folder=/g) || []).length, 1);
  assert.equal(c.elements.clearButton.disabled, true);
  assert.equal(nodes.get('#add-more-files').disabled, true);
});
test('subir más conserva las facturas procesadas sin volver a analizar sus rutas antiguas', async () => {
  let submitted;
  const { context: c } = setup({ api: async (_path, request) => { submitted = JSON.parse(request.body); return [{ source: 'b.pdf', status: 'ready' }]; } });
  c.state.files = ['a.pdf', 'b.pdf']; c.state.analysis = [{ source: 'a.pdf', status: 'completed', target: 'C:/facturas/a.pdf' }];
  await c.analyzeFiles();
  assert.deepEqual(submitted.paths, ['b.pdf']);
  assert.equal(c.state.analysis[0].status, 'completed');
  assert.equal(c.state.analysis[1].status, 'ready');
});
test('ignora un análisis antiguo cuando llega otro más reciente', async () => {
  const pending = [];
  const { context: c } = setup({ api: () => new Promise(resolve => pending.push(resolve)) });
  c.state.files = ['a.pdf'];
  const first = c.analyzeFiles(); const second = c.analyzeFiles();
  pending[1]([{ source: 'a.pdf', status: 'ready', destination: 'nuevo' }]); await second;
  pending[0]([{ source: 'a.pdf', status: 'ready', destination: 'anterior' }]); await first;
  assert.equal(c.state.analysis[0].destination, 'nuevo');
});

