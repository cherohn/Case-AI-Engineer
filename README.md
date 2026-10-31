# Empório da Música

**Matheus Souza Garcez — Artefact AI Engineer technical case**

A Python support agent for a fictional instrument store. It helps customers
discover instruments, check prices and stock, and understand store policies.
A browser chat and a CLI use the same agent.

[Validation report](docs/evaluation.md) · [Recorded conversations](examples/) ·
[Development notes](docs/development-notes.md)

## Run locally

You need Python 3.11 or newer and a Groq API key with access to
`openai/gpt-oss-120b`. Installation and runtime checks used Linux and Python 3.14.3.
The browser interface requires no Node.js installation or frontend build.

```bash
git clone https://github.com/cherohn/Case-AI-Engineer.git
cd Case-AI-Engineer
```

On Linux or macOS (bash/zsh):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

On Windows PowerShell, the equivalent setup is below. These commands have not
been exercised on Windows; use `.\.venv\Scripts\python.exe` in place of `python`
in subsequent commands.

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` locally:

| Variable | Configuration |
| --- | --- |
| `GROQ_API_KEY` | Your own key; required for model responses. |
| `GROQ_MODEL` | Defaults to `openai/gpt-oss-120b`, the model validated for this case. Other models must support the request options in `agent.py` and have not been validated here. |

Existing environment variables take precedence over `.env`. Restart the application
after changing credentials or model configuration. The key stays on the server;
`.env.example` contains no credentials.

Start the application:

```bash
python -m store_agent.web
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). If that port is occupied:

```bash
python -m uvicorn store_agent.web:app --host 127.0.0.1 --port 8001
```

Without a key, the page and catalog still work. Chat reports that the assistant
is not configured. A successful configuration check does not verify API access
or remaining quota.

The CLI is also available:

```bash
python -m store_agent
python -m store_agent --trace --message "How much is the Takamine GD20 with PIX?"
```

Use `/reset` to clear CLI history and `/exit` to leave. `--trace` prints tool
arguments and reported usage to stderr. Web completion logs record counts and
tool names. Unexpected provider errors also log class/status and available usage
counters. These application logs exclude messages, answers, tool arguments, and
credentials.

## Try the interface

Tell the assistant what you want to play or how much you want to spend. Suggested
questions fill the input without sending it. Enter sends; Shift+Enter adds a line.
**New conversation** clears the web session.

**Browse instruments** opens the available catalog with category, name, and budget
filters. The catalog uses Python lookups without calling the model. **Ask about this
instrument** prepares a question in the chat. Prices and stock must be checked
again when the agent answers.

The Theme selector offers System, Light, and Dark, and saves the choice locally.
Application messages and model instructions use English. Store/product names,
street addresses, source excerpts, and historical tool arguments retain their
original spelling.

## Architecture and decisions

FastAPI provides request validation and interactive API documentation, and serves
the HTML/CSS/JavaScript interface. Plain JavaScript suits the single-screen flow
without adding a frontend build. The browser
sends a message and optional session ID to `POST /api/chat`. Python sends the
conversation and tool definitions to Groq, executes requested functions, and
usually returns their results to the model for an answer.

| Tool | Responsibility |
| --- | --- |
| `list_categories` | Introduce categories that actually have available stock. |
| `search_products` | Filter by name, category, and current price; return up to five matches to the model. |
| `get_product` | Check a known product ID, including unavailable items. |
| `read_policy` | Retrieve a numbered section of the policy PDF. |
| `check_return` | Request missing purchase channel/receipt time, or return the policy with supplied customer facts. |

When `check_return` receives incomplete facts, Python supplies the clarification
question directly. It makes no eligibility decision and requires no second model
request. Once those minimum facts are supplied, the model explains the retrieved
policy; condition, exceptions, and the actual return procedure still require
appropriate confirmation. No tool initiates a purchase, refund, complaint, or
change to customer records.

I chose direct function calling to keep the five-tool loop visible and easy to
debug. A framework would add structure that this prototype does not yet need.
CSV scans are sufficient for 65 products and avoid database setup. Monetary
calculations stay in Python rather than relying on generated arithmetic.

Policy retrieval uses the manual's ten numbered sections. For an eight-page
document with clear headings, selecting a section is simpler to inspect than
embedding search. `pypdf` extracts text in layout mode to retain table relationships.
Original headings locate the text; English labels describe the retrieved section.

Groq hosts the default GPT-OSS 120B model. It supports tool calling and was
available within the account's free-tier limits during the case. It was selected
as a practical starting point for questions combining catalog facts and policies,
not as the winner of a model comparison. The 20B alternative had the same reported
quotas, so switching would not increase those limits.

The prompt defines a brief, friendly music-store attendant, English replies,
source consultation, scope boundaries, and staff referral for unclear policies.
Tool selection and most final answers remain model-driven; these instructions
do not guarantee that every generated statement is grounded.

### Code and HTTP API

- `store_agent/agent.py`: bounded model/tool loop and short conversation history.
- `store_agent/catalog.py`: CSV lookups, availability, English category labels, and prices.
- `store_agent/policies.py`: PDF sections and return-fact clarification.
- `store_agent/tools.py` and `prompt.txt`: tool schemas and attendant instructions.
- `store_agent/web.py`: API, session handling, and static files.
- `store_agent/__main__.py`: CLI and provider errors.
- `static/`: interface without a separate build system.

`GET /api/catalog` accepts `query`, `category`, `max_price`, and `offset` and returns
12 available products per page. `GET /api/health` checks configuration without
contacting Groq. `DELETE /api/sessions/{id}` clears a session. Interactive endpoint
schemas are available at `/docs` while the server is running.

## Source data and assumptions

The supplied products, categories, promotions, and policy PDF are included in
`data/` under shorter filenames, with unchanged contents. Customer and order
files are excluded because this prototype has no authenticated order lookup.

Catalog files are re-read on every lookup. This is a local operational snapshot,
not a live retail integration. The current snapshot contains 61 available products
across six categories. English category labels are normalized in Python; original
Portuguese names remain accepted as filter aliases.

The policy PDF is parsed when an agent is created. Start a new web conversation
or restart the CLI to load an updated manual. Its heading-based parser needs
revalidation if the document structure changes.

| Rule or ambiguity | Treatment |
| --- | --- |
| Active status and stock disagree | Python offers an item only if `status=active` and stock is positive. Discontinued/coming-soon items are excluded even with stock. |
| Promotions | Python uses only `is_active=1`. If active offers overlap, the largest applies once. No validity dates are inferred from descriptions. |
| PIX | Python applies 5% to the list price only when no promotion applies. Promotional replies should show original price, percentage, and final price. |
| Money and budget | `Decimal`, cents rounded with `ROUND_HALF_UP`. Budget filters use the current price before payment-specific PIX discounts. |
| Installment summary conflicts with detailed bands | The prompt prefers section 3.1 and refers unclear cases to staff. Installment eligibility is not a separate deterministic rules engine. |
| Shipping at exactly R$500; conflicting phone numbers | The manual leaves these unclear. The prompt instructs the agent to request staff confirmation. |
| Exchanges, withdrawal, and warranty overlap | Retrieve the relevant rules and avoid inventing procedures or denying rights from an uncertain interpretation. Staff confirms exceptions. |

## Validation and examples

Run the 37 offline Python tests:

```bash
python -m unittest discover -v
```

They cover prices and stock, PDF extraction, tool arguments, nullable facts,
history, sessions, API errors, and clarification behavior. Mock model responses
test orchestration, not language-model quality.

The [validation report](docs/evaluation.md) distinguishes offline tests, recorded
live Groq checks, and browser checks with simulated responses. It also records
failures and the limits of the evidence.

Five selected conversations are included:

1. [Product discovery](examples/01-product-discovery.md)
2. [Store information](examples/02-store-information.md)
3. [Product price and PIX](examples/03-product-price.md)
4. [Return clarification and policy](examples/04-online-return.md)
5. [Out-of-scope request](examples/05-out-of-scope.md)

Optional: record fresh outputs with the commands below. This calls Groq and
overwrites the selected example files. New outputs can differ from the historical
recordings, including the selected two-turn browser conversation.

```bash
python -m scripts.record_examples
python -m scripts.record_examples --case 1
```

The recorder waits 60 seconds between cases and stops on API errors without retrying.

## Runtime budget

The account limits observed on October 31, 2026 were 30 requests/minute,
1,000 requests/day, 8,000 tokens/minute, and 200,000 tokens/day. They are shared
by the organization and can change; the application does not measure remaining quota.

Each turn allows at most three model requests. The third disables tools to reserve
a final answer. SDK retries are off and each request has a 30-second timeout.
Generation uses low reasoning effort, temperature 0.2, and an 800-token output cap.

Input is limited to 1,000 characters. History keeps the last two completed turns,
with stored assistant messages capped at 2,000 characters; tool results are not
retained between turns. These bounds reduce usage but do not prevent rate limits.

The web demo serializes chat requests and keeps at most 20 in-memory sessions,
discarding the oldest when full. Restarting the server clears them. It runs on
loopback without authentication; public deployment needs a separate access and
quota design. Browser responses use text nodes with limited bold formatting.

References: [Groq model](https://console.groq.com/docs/model/openai/gpt-oss-120b),
[tool calling](https://console.groq.com/docs/tool-use/local-tool-calling),
[rate limits](https://console.groq.com/docs/rate-limits).

## Limitations and next work

The assistant cannot authenticate customers, check private orders, place purchases,
issue refunds, register complaints, or contact staff. A referral is guidance,
not an action performed by the prototype.

Generated replies can still drift outside scope or add unsupported wording.
Example 05 offers a cooking-site referral after declining the unrelated request;
that extra offer remains a quality limitation. Short history, static PDF headings,
and the local snapshot also limit the experience.

Next priorities would be authenticated order/inventory integration, a broader
repeatable evaluation set for follow-ups and policy conflicts, and stronger
grounding checks before expanding the workflow.

## AI assistance

I used OpenAI Codex for requirement analysis, architecture discussion, implementation,
test execution, and documentation. I reviewed design choices and visible browser
outputs alongside it, including manually retrying a failed message and checking
the returned prices. Observed failures led to explicit return clarification,
nullable tool arguments, and English category normalization.

Selected responses are captured application outputs, not ideal answers written
afterward. Example 04 identifies the Python-generated clarification separately
from the model-generated policy explanation.

## Written submission

[Download the submission PDF](submission/Matheus%20Souza%20Garcez%20-%20AI%20Engineer%20%E2%80%93%20Full-Stack%20para%20Aplica%C3%A7%C3%B5es%20com%20IA%20Generativa.pdf).

The PDF source order and cover metadata are recorded in
[docs/submission.json](docs/submission.json): this README, the validation report,
and the five selected conversations. Detailed development notes remain available
in the repository as supporting evidence.

To rebuild the PDF, install the optional export dependencies in the virtual environment:

```bash
python -m pip install -r requirements-docs.txt
python -m scripts.build_pdf
```

The exporter uses WeasyPrint with system text-rendering libraries and fonts; this
export was validated on Linux. These optional dependencies are separate from the
application requirements. The build imports only documentation tools and makes
no Groq requests.
