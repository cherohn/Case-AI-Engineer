const form = document.querySelector('#chat-form');
const input = document.querySelector('#message');
const messages = document.querySelector('#messages');
const conversation = document.querySelector('#conversation');
const welcome = document.querySelector('#welcome');
const status = document.querySelector('#status');
const send = document.querySelector('#send');
const reset = document.querySelector('#reset');
const count = document.querySelector('#count');

let sessionId = null;
let waiting = false;

function setStatus(text, error = false) {
  status.textContent = text;
  status.classList.toggle('error', error);
}

function setWaiting(value) {
  waiting = value;
  send.disabled = value;
  reset.disabled = value;
  input.disabled = value;
  form.setAttribute('aria-busy', String(value));
}

function updateInput() {
  count.textContent = `${input.value.length} / 1000`;
  input.style.height = 'auto';
  input.style.height = `${Math.min(input.scrollHeight, 140)}px`;
}

function addMessage(role, text) {
  welcome.hidden = true;
  const message = document.createElement('div');
  message.className = `message ${role}`;
  const label = document.createElement('div');
  label.className = 'message-label';
  label.textContent = role === 'user' ? 'YOU' : 'EMPÓRIO DA MÚSICA';
  const content = document.createElement('div');
  content.className = 'message-text';
  // Use text nodes so model output and customer input cannot inject HTML.
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  for (const part of parts) {
    if (part.startsWith('**') && part.endsWith('**')) {
      const strong = document.createElement('strong');
      strong.textContent = part.slice(2, -2);
      content.append(strong);
    } else {
      content.append(document.createTextNode(part));
    }
  }
  message.append(label, content);
  messages.append(message);
  conversation.scrollTop = conversation.scrollHeight;
  return message;
}

document.querySelectorAll('[data-question]').forEach(button => {
  button.addEventListener('click', () => {
    if (waiting) return;
    input.value = button.dataset.question;
    updateInput();
    input.focus();
  });
});

input.addEventListener('input', updateInput);
input.addEventListener('keydown', event => {
  if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    if (!waiting) form.requestSubmit();
  }
});

form.addEventListener('submit', async event => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text || waiting) return;
  const userMessage = addMessage('user', text);
  input.value = '';
  updateInput();
  setWaiting(true);
  setStatus('Checking that for you…');
  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, session_id: sessionId }),
    });
    const data = await response.json();
    if (!response.ok) {
      if (response.status === 404) sessionId = null;
      throw new Error(typeof data.detail === 'string' ? data.detail : 'Please check your message and try again.');
    }
    sessionId = data.session_id;
    addMessage('assistant', data.answer);
    setStatus('');
  } catch (error) {
    userMessage.remove();
    input.value = text;
    updateInput();
    welcome.hidden = messages.children.length > 0;
    setStatus(error instanceof TypeError ? 'Could not reach the assistant. Check your connection and try again.' : error.message, true);
  } finally {
    setWaiting(false);
    input.focus();
  }
});

reset.addEventListener('click', async () => {
  if (waiting) return;
  setWaiting(true);
  try {
    if (sessionId) {
      const response = await fetch(`/api/sessions/${sessionId}`, { method: 'DELETE' });
      if (!response.ok) throw new Error('Could not clear the conversation. Please try again.');
    }
    sessionId = null;
    messages.replaceChildren();
    welcome.hidden = false;
    input.value = '';
    updateInput();
    setStatus('');
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    setWaiting(false);
    input.focus();
  }
});

fetch('/api/health')
  .then(response => response.json())
  .then(data => {
    if (!data.configured) setStatus('The assistant is not configured yet. Please contact the demo owner.', true);
  })
  .catch(() => setStatus('Could not connect to the assistant. Try refreshing the page.', true));
