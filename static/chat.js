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
  if (waiting) return;
  if (!text || text.length > 1000) {
    setStatus('Enter a message between 1 and 1,000 characters.', true);
    input.focus();
    return;
  }
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

const catalogDialog = document.querySelector('#catalog');
const catalogFilters = document.querySelector('#catalog-filters');
const catalogProducts = document.querySelector('#catalog-products');
const catalogStatus = document.querySelector('#catalog-status');
const catalogCategory = document.querySelector('#catalog-category');
const catalogMore = document.querySelector('#catalog-more');
const catalogSearch = catalogFilters.querySelector('button');
const currency = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'BRL' });
let catalogOffset = 0;
let catalogLoading = false;
let catalogParams = new URLSearchParams();

function productCard(product) {
  const card = document.createElement('article');
  card.className = 'product';
  const category = document.createElement('span');
  category.className = 'product-category';
  category.textContent = product.category;
  const title = document.createElement('h3');
  title.textContent = product.name;
  const price = document.createElement('p');
  price.className = 'product-price';
  price.textContent = currency.format(Number(product.price_brl));
  card.append(category, title, price);
  if (Number(product.discount_percent) > 0) {
    const offer = document.createElement('p');
    offer.className = 'product-offer';
    offer.textContent = `${product.discount_percent}% off · Was ${currency.format(Number(product.original_price_brl))}`;
    card.append(offer);
  }
  const pix = document.createElement('p');
  pix.className = 'product-pix';
  pix.textContent = `${currency.format(Number(product.pix_price_brl))} with PIX · In stock`;
  const ask = document.createElement('button');
  ask.type = 'button';
  ask.className = 'reset';
  ask.textContent = 'Ask about this instrument';
  ask.addEventListener('click', () => {
    if (waiting) return;
    input.value = `Tell me about the ${product.name}. Is it available, and what are the payment options?`;
    updateInput();
    catalogDialog.close();
    input.focus();
  });
  card.append(pix, ask);
  return card;
}

async function loadCatalog(append = false) {
  if (catalogLoading) return;
  catalogLoading = true;
  catalogSearch.disabled = true;
  catalogMore.disabled = true;
  catalogStatus.textContent = 'Loading instruments…';
  if (!append) {
    catalogParams = new URLSearchParams({
      query: document.querySelector('#catalog-query').value.trim(),
      category: catalogCategory.value,
    });
    const budget = document.querySelector('#catalog-budget').value;
    if (budget) catalogParams.set('max_price', budget);
  }
  catalogParams.set('offset', append ? String(catalogOffset) : '0');
  try {
    const response = await fetch(`/api/catalog?${catalogParams}`);
    const data = await response.json();
    if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Please check your filters.');
    if (catalogCategory.options.length === 1) {
      for (const category of data.categories) {
        const option = document.createElement('option');
        option.value = category.name;
        option.textContent = category.name;
        catalogCategory.append(option);
      }
    }
    if (!append) catalogProducts.replaceChildren();
    data.products.forEach(product => catalogProducts.append(productCard(product)));
    catalogOffset = (append ? catalogOffset : 0) + data.products.length;
    catalogMore.hidden = catalogOffset >= data.total_matches;
    catalogStatus.textContent = data.total_matches
      ? `Showing ${catalogOffset} of ${data.total_matches} available instruments.`
      : 'No instruments match these filters. Try another category or a higher budget.';
  } catch (error) {
    catalogStatus.textContent = error instanceof TypeError ? 'Could not load the catalog. Please try again.' : error.message;
    if (!append) catalogProducts.replaceChildren();
    catalogMore.hidden = true;
  } finally {
    catalogLoading = false;
    catalogSearch.disabled = false;
    catalogMore.disabled = false;
  }
}

document.querySelector('#browse').addEventListener('click', () => {
  catalogDialog.showModal();
  loadCatalog();
});
document.querySelector('#close-catalog').addEventListener('click', () => catalogDialog.close());
catalogFilters.addEventListener('submit', event => {
  event.preventDefault();
  const budget = document.querySelector('#catalog-budget');
  if (!budget.validity.valid) {
    catalogStatus.textContent = 'Enter a valid, non-negative budget with at most two decimal places.';
    budget.focus();
    return;
  }
  loadCatalog();
});
catalogMore.addEventListener('click', () => loadCatalog(true));
