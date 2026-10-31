# Empório da Música

A customer-support agent for a fictional instrument store, built for the Artefact
AI Engineer case. It looks up catalog facts in CSV files and reads store policies
from the supplied PDF before answering.

## Run locally

Use Python 3.11 or newer. Development checks have run on Python 3.14.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Set `GROQ_API_KEY` in `.env` to your own Groq key. Keep that file local.
The default model is `openai/gpt-oss-120b`; change `GROQ_MODEL` to use another
compatible model. The API key never belongs in the browser or repository.

Start the web application:

```bash
python -m store_agent.web
```

Open http://127.0.0.1:8000. The page and API run on the same server. Suggested
questions fill the input without sending a request; press Enter or click Send
to submit. Shift+Enter inserts a newline. New conversation clears the server
session. Reloading the page also starts a fresh conversation.

The terminal chat is available too:

```bash
python -m store_agent
```

Use `/reset` to clear the conversation or `/exit` to leave. For one question:

```bash
python -m store_agent --trace --message "How much is the Takamine GD20 with PIX?"
```

`--trace` prints tool names, arguments, request count, and reported token usage
to stderr. It does not print credentials or internal model reasoning.

## How it works

The model chooses between three Python functions: `search_products`,
`get_product`, and `read_policy`. Python executes the chosen function and sends
its result back to Groq. The model then writes the customer-facing answer.

- `store_agent/catalog.py` handles product lookup, stock, and pricing.
- `store_agent/policies.py` extracts the manual into its ten numbered sections.
- `store_agent/tools.py` describes those functions to the model.
- `store_agent/prompt.txt` defines the attendant's tone, scope, and response rules.
- `store_agent/agent.py` runs the conversation and tool loop.
- `store_agent/__main__.py` handles terminal input and API errors.
- `store_agent/web.py` exposes the FastAPI endpoints and serves the frontend.
- `static/` contains the HTML, CSS, and browser JavaScript.

The frontend uses plain JavaScript because this interface has one screen and
does not need a separate build system. It sends messages to `POST /api/chat`;
the server returns the answer and a random session ID. Each session has its own
agent history. `DELETE /api/sessions/{id}` clears it. `GET /api/health` checks
whether credentials are configured, without making a model request. Endpoint
schemas are available at `/docs` while the server is running.

The server keeps at most 20 sessions and accepts one chat request at a time to
avoid accidental concurrent usage. Sessions are in memory and disappear on
restart. Oldest sessions are discarded when the cap is reached. This is a local
demo bound to loopback, with no authentication; it needs access controls and
per-user quotas before public deployment. Customer input and model output are
rendered with text nodes, not interpreted as HTML.

I chose direct function calling rather than an agent framework because this case
needs only three tools and a short loop. Keeping that loop visible makes failures
easier to inspect. Policy retrieval is section-based: the model selects a topic,
and Python returns that section with its source. For an eight-page manual with
clear headings, embeddings and a vector database would add setup without a clear
benefit. PDF text is extracted in layout mode to retain table relationships.

Groq hosts the model. GPT-OSS 120B supports tool calling and is the starting point
for questions that combine catalog facts and policies. This is a practical initial
choice, not the result of a comparison benchmark. The 20B model has the same
reported account quotas, so switching to it would not increase those quotas.

The prompt asks the agent to answer in the customer's language, consult current
facts even on follow-up questions, cite policy sections, and ask for missing
information instead of guessing. Accessories and unrelated requests are outside
the store's scope.

## Free-tier budget

The account reports 30 requests/minute, 1,000 requests/day, 8,000 tokens/minute,
and 200,000 tokens/day. These limits can change and are shared by the organization.

Each turn allows at most three model requests. The third request disables tools
so it can only produce a final answer from retrieved facts. SDK retries are off;
rate-limit errors stop the request rather than silently consuming more quota.
Outputs are capped at 800 tokens, search results at five products, and input at
1,000 characters. Only the last two completed turns are kept in memory. Tool
results are used for the current turn and are not retained in session history.
These bounds reduce usage; they do not guarantee a fixed token cost or prevent
429 responses during rapid conversations.

References: [Groq model](https://console.groq.com/docs/model/openai/gpt-oss-120b),
[function calling](https://console.groq.com/docs/tool-use/local-tool-calling),
and [rate limits](https://console.groq.com/docs/rate-limits).

## Data and assumptions

The supplied products, categories, promotions, and policy PDF are in `data/` with
shorter filenames and unchanged contents. Customer and order files are excluded:
this prototype does not authenticate customers or expose private order records.

CSV files are read on each lookup. They are a local snapshot, not a live commerce
integration. Editing a file changes the next lookup's result.

- Availability requires both `status=active` and positive stock. A discontinued
  product with stock, or a coming-soon item, is not offered as available.
- Only `is_active=1` promotions apply. No date fields exist, so descriptions are
  not used to guess validity. If active offers overlap, the largest discount
  applies once; this is an assumption consistent with the no-stacking rule.
- PIX gets 5% off the list price only when no promotion applies. Promotional
  answers must show the original price, percentage, and final price.
- Money uses `Decimal` and rounds to cents with `ROUND_HALF_UP`. Budget filters
  use the current price before the payment-specific PIX discount.
- Specific model searches omit category. An early live test incorrectly put a
  Takamine acoustic guitar in the electric-guitar category and found nothing;
  the tool description and prompt were corrected after observing that failure.
- The detailed installment bands in section 3.1 take precedence over the summary
  table in section 3. Unclear cases are referred to staff.
- Shipping at exactly R$500 is undefined. Contact numbers conflict. The agent
  should explain uncertainty and refer these questions to staff.
- For returns, the agent must ask for purchase channel and receipt date when
  needed. Defect exchange and warranty are distinct policies. Conflicting return
  exclusions are referred to staff rather than used to deny a customer's rights.

## Checks

```bash
python -m unittest discover -v
```

The 27 tests run offline. They cover catalog rules, changes to source stock, policy
sections spanning pages, tool execution, invalid arguments, bounded history,
request limits, session isolation, and API errors. Mock responses test
orchestration, not model quality. A Chromium check also exercised desktop and
mobile layouts, suggested prompts, send/reset actions, rate-limit recovery,
and safe rendering with simulated API responses.

A live Portuguese conversation queried the Takamine GD20 and the online return
policy. It made three requests and reported 4,052 tokens, returning R$2,089.05 for
PIX and citing section 4.1. The earlier failed category test used three requests
and 3,951 tokens. No other API requests were needed for these checks.

## Limitations and next steps

Three to five recorded example conversations still need to be added before
submission. The final README and documentation will also be exported to PDF.

The agent cannot place orders, check private order status, issue refunds, register
complaints, or contact staff. It must not claim those actions were completed.
History is in memory and short. The PDF parser depends on this manual's headings;
a different layout needs revalidation. Prompt instructions reduce unsupported
answers but do not guarantee that every generated statement is grounded.

With more time, I would add a broader evaluation set for policy conflicts and
Portuguese product searches, measure answer quality and latency, and implement
authenticated order lookup before expanding the scope.

## AI assistance

I used OpenAI Codex to review the case, discuss architecture, implement code, and
run checks. I review the implementation and decisions as the project progresses.
The first live test exposed a category-selection failure; we used that result to
correct the search instructions and reserve the last request for a final answer.
