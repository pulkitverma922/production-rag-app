let stagedFiles = [];
let isLoading = false;

// ── On page load: restore docs from Pinecone ──
window.addEventListener('load', async () => {
  try {
    const res = await fetch('/api/v1/query/sources');
    if (!res.ok) throw new Error('no sources');
    const data = await res.json();
    if (data.sources && data.sources.length) {
      renderDocsFromSources(data.sources);
    } else {
      document.getElementById('docsList').innerHTML = '<div class="empty-docs">No documents yet</div>';
    }
  } catch {
    document.getElementById('docsList').innerHTML = '<div class="empty-docs">No documents yet</div>';
  }
});

function renderDocsFromSources(sources) {
  const list = document.getElementById('docsList');
  const badge = document.getElementById('docCountBadge');
  badge.textContent = `${sources.length} doc${sources.length !== 1 ? 's' : ''} indexed`;
  list.innerHTML = '';
  sources.forEach(doc => {
    const name = doc.filename || doc;
    const ext = name.split('.').pop().toUpperCase();
    const el = document.createElement('div');
    el.className = 'doc-item';
    el.innerHTML = `
      <span class="doc-type-badge ${ext === 'PDF' ? 'badge-pdf' : 'badge-docx'}">${ext}</span>
      <div class="doc-info">
        <div class="doc-name" title="${name}">${name}</div>
        <div class="doc-meta">${doc.chunks ? doc.chunks + ' chunks' : 'indexed'}</div>
      </div>
      <span class="doc-status status-ok">indexed</span>`;
    list.appendChild(el);
  });
}

// ── Drag & drop ──
const dropZone = document.getElementById('dropZone');
dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', e => { e.preventDefault(); dropZone.classList.remove('dragover'); stageFiles(e.dataTransfer.files); });

function stageFiles(fileList) {
  for (const f of fileList) {
    if (!f.name.match(/\.(pdf|docx)$/i)) { showToast('Only PDF and DOCX supported', 'error'); continue; }
    if (stagedFiles.find(s => s.name === f.name)) continue;
    stagedFiles.push(f);
  }
  renderStaged();
}

function renderStaged() {
  const list = document.getElementById('stagedList');
  list.innerHTML = '';
  stagedFiles.forEach((f, i) => {
    const el = document.createElement('div');
    el.className = 'staged-file';
    el.innerHTML = `<span>${f.name.endsWith('.pdf') ? '📄' : '📝'}</span><span class="file-name" title="${f.name}">${f.name}</span><button class="remove-btn" onclick="removeStaged(${i})">✕</button>`;
    list.appendChild(el);
  });
  document.getElementById('uploadBtn').disabled = stagedFiles.length === 0;
}

function removeStaged(i) { stagedFiles.splice(i, 1); renderStaged(); }

// ── Upload ──
async function uploadFiles() {
  if (!stagedFiles.length) return;
  const btn = document.getElementById('uploadBtn');
  btn.classList.add('loading'); btn.disabled = true;
  const fd = new FormData();
  stagedFiles.forEach(f => fd.append('files', f));
  try {
    const res = await fetch('/api/v1/ingest/upload', { method: 'POST', body: fd });
    const data = await res.json();
    let anySuccess = false;
    data.results.forEach(r => {
      if (r.status === 'success') { showToast(`Indexed: ${r.filename} (${r.chunks_created} chunks)`, 'success'); anySuccess = true; }
      else showToast(`Failed: ${r.filename} — ${r.reason}`, 'error');
    });
    if (anySuccess) {
      stagedFiles = [];
      renderStaged();
      const src = await fetch('/api/v1/query/sources');
      const srcData = await src.json();
      renderDocsFromSources(srcData.sources || []);
    }
  } catch (e) {
    showToast('Upload failed — check terminal for error', 'error');
  } finally {
    btn.classList.remove('loading');
    btn.disabled = stagedFiles.length === 0;
  }
}

// ── Chat ──
function fillSuggestion(el) {
  document.getElementById('chat-input').value = el.textContent;
  document.getElementById('chat-input').focus();
}

function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
}

function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

async function sendMessage() {
  const input = document.getElementById('chat-input');
  const q = input.value.trim();
  if (!q || isLoading) return;
  isLoading = true;
  document.getElementById('sendBtn').disabled = true;
  input.value = ''; input.style.height = 'auto';
  const welcome = document.getElementById('welcome');
  if (welcome) welcome.remove();
  appendMessage('user', q);
  const typingId = appendTyping();
  try {
    const res = await fetch('/api/v1/query/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q, top_k: 5 })
    });
    const data = await res.json();
    removeTyping(typingId);
    appendMessage('bot', data.answer, data.sources);
  } catch (e) {
    removeTyping(typingId);
    appendMessage('bot', 'Request failed. Check that uvicorn is running and check the terminal for errors.');
  } finally {
    isLoading = false;
    document.getElementById('sendBtn').disabled = false;
    input.focus();
  }
}

function appendMessage(role, text, sources) {
  const msgs = document.getElementById('messages');
  const row = document.createElement('div');
  row.className = `msg-row ${role}`;
  const avatar = document.createElement('div');
  avatar.className = `avatar avatar-${role}`;
  avatar.textContent = role === 'bot' ? 'AI' : 'You';
  const bubble = document.createElement('div');
  bubble.className = `bubble bubble-${role}`;
  bubble.textContent = text;
  if (sources && sources.length) {
    const srcDiv = document.createElement('div');
    srcDiv.className = 'bubble-sources';
    srcDiv.innerHTML = '<span class="source-label">Sources:</span>';
    sources.forEach(s => {
      const tag = document.createElement('span');
      tag.className = 'source-tag'; tag.textContent = s;
      srcDiv.appendChild(tag);
    });
    bubble.appendChild(srcDiv);
  }
  row.appendChild(avatar); row.appendChild(bubble);
  msgs.appendChild(row);
  msgs.scrollTop = msgs.scrollHeight;
}

function appendTyping() {
  const msgs = document.getElementById('messages');
  const id = 'typing-' + Date.now();
  const row = document.createElement('div');
  row.className = 'msg-row'; row.id = id;
  const avatar = document.createElement('div');
  avatar.className = 'avatar avatar-bot'; avatar.textContent = 'AI';
  const bubble = document.createElement('div');
  bubble.className = 'bubble bubble-bot';
  bubble.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';
  row.appendChild(avatar); row.appendChild(bubble);
  msgs.appendChild(row);
  msgs.scrollTop = msgs.scrollHeight;
  return id;
}

function removeTyping(id) { const el = document.getElementById(id); if (el) el.remove(); }

function showToast(msg, type = 'success') {
  const t = document.getElementById('toast');
  t.textContent = msg; t.className = `toast ${type} show`;
  setTimeout(() => t.classList.remove('show'), 3500);
}
