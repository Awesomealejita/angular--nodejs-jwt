const templateSelect = document.getElementById('template-select');
const uploadForm = document.getElementById('upload-form');
const uploadStatus = document.getElementById('upload-status');
const sendStatus = document.getElementById('send-status');
const mutuasTable = document.querySelector('#mutuas-table tbody');
const addMutuaBtn = document.getElementById('add-mutua');
const sendBtn = document.getElementById('send-btn');
const fileInput = document.getElementById('template-file');

let mutuas = [];

async function fetchTemplates() {
  const res = await fetch('/api/templates');
  const data = await res.json();
  templateSelect.innerHTML = '';
  if (!data.templates.length) {
    const option = document.createElement('option');
    option.textContent = 'Sube una plantilla primero';
    option.disabled = true;
    option.selected = true;
    templateSelect.appendChild(option);
    return;
  }
  data.templates.forEach((name) => {
    const option = document.createElement('option');
    option.value = name;
    option.textContent = name;
    templateSelect.appendChild(option);
  });
}

function renderMutuas() {
  mutuasTable.innerHTML = '';
  mutuas.forEach((m, index) => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${m.mutua || ''}</td>
      <td>${m.email || ''}</td>
      <td>${m.contacto || ''}</td>
      <td>${m.referencia || ''}</td>
      <td>${m.fecha || ''}</td>
      <td>${m.importe || ''}</td>
      <td>${m.descripcion || ''}</td>
      <td><button data-index="${index}" class="ghost">Eliminar</button></td>
    `;
    mutuasTable.appendChild(row);
  });
}

function clearMutuaForm() {
  ['mutua', 'email', 'contacto', 'referencia', 'fecha', 'importe', 'descripcion'].forEach((id) => {
    const el = document.getElementById(id);
    el.value = '';
  });
}

addMutuaBtn.addEventListener('click', () => {
  const entry = {
    mutua: document.getElementById('mutua').value.trim(),
    email: document.getElementById('email').value.trim(),
    contacto: document.getElementById('contacto').value.trim(),
    referencia: document.getElementById('referencia').value.trim(),
    fecha: document.getElementById('fecha').value.trim(),
    importe: document.getElementById('importe').value.trim(),
    descripcion: document.getElementById('descripcion').value.trim(),
  };
  if (!entry.mutua) {
    alert('Introduce al menos el nombre de la mutua.');
    return;
  }
  mutuas.push(entry);
  renderMutuas();
  clearMutuaForm();
});

mutuasTable.addEventListener('click', (event) => {
  if (event.target.tagName === 'BUTTON') {
    const index = Number(event.target.dataset.index);
    mutuas.splice(index, 1);
    renderMutuas();
  }
});

uploadForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!fileInput.files.length) return;
  const formData = new FormData();
  formData.append('file', fileInput.files[0]);
  uploadStatus.textContent = 'Subiendo...';
  const res = await fetch('/api/templates', { method: 'POST', body: formData });
  const data = await res.json();
  uploadStatus.textContent = data.message || data.error;
  fetchTemplates();
});

sendBtn.addEventListener('click', async () => {
  if (!templateSelect.value || !mutuas.length) {
    alert('Selecciona una plantilla y añade al menos una mutua.');
    return;
  }
  sendStatus.textContent = 'Procesando...';
  const res = await fetch('/api/send', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ template: templateSelect.value, mutuas }),
  });
  const data = await res.json();
  const summary = [`Modo: ${data.mode}`];
  if (data.sent?.length) {
    summary.push(`Generados/enviados: ${data.sent.length}`);
  }
  if (data.failed?.length) {
    summary.push(`Errores: ${data.failed.length}`);
  }
  sendStatus.textContent = summary.join(' | ');
});

fetchTemplates();
