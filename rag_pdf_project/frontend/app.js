const API_BASE = 'http://localhost:8000';

async function uploadFiles() {
  const apiKey = document.getElementById('api_key').value;
  const session = document.getElementById('session_id').value;
  const files = document.getElementById('pdfs').files;
  const status = document.getElementById('uploadStatus');

  if (!apiKey) { alert('Enter Groq API key'); return; }
  if (files.length === 0) { alert('Select at least one PDF'); return; }

  const form = new FormData();
  form.append('api_key', apiKey);
  form.append('session_id', session);
  for (let f of files) form.append('files', f);

  status.innerText = 'Uploading...';

  try {
    const res = await fetch(`${API_BASE}/upload`, { method: 'POST', body: form });
    const j = await res.json();
    status.innerText = j.detail || JSON.stringify(j);
  } catch (e) {
    status.innerText = 'Upload failed: ' + e.message;
  }
}

async function ask() {
  const apiKey = document.getElementById('api_key').value;
  const session = document.getElementById('session_id').value;
  const q = document.getElementById('question').value;

  if (!apiKey) { alert('Enter Groq API key'); return; }
  if (!q) return;

  const chat = document.getElementById('chat');

  // Show user message
  const userDiv = document.createElement('div');
  userDiv.className = 'msg user';
  userDiv.innerText = 'User: ' + q;
  chat.appendChild(userDiv);
  chat.scrollTop = chat.scrollHeight;

  try {
    const res = await fetch(`${API_BASE}/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: apiKey, session_id: session, question: q })
    });

    const j = await res.json();

    // Show assistant reply
    const botDiv = document.createElement('div');
    botDiv.className = 'msg bot';
    botDiv.innerText = 'Assistant: ' + (j.answer || JSON.stringify(j));
    chat.appendChild(botDiv);
    chat.scrollTop = chat.scrollHeight;

  } catch (e) {
    const errDiv = document.createElement('div');
    errDiv.className = 'msg bot error';
    errDiv.innerText = 'Error: ' + e.message;
    chat.appendChild(errDiv);
  }
}
