# Case requirements and evaluation

The case prioritizes the agent's reasoning and correct use of context. The browser
interface helps customers discover products; it is not a replacement for checking
whether generated answers agree with the source material.

## Functional requirements

| Requirement | Implementation | Evidence |
| --- | --- | --- |
| Python as the main language | Catalog rules, PDF extraction, tool execution, Groq integration, and HTTP API are Python. | `store_agent/` |
| Store-aligned persona | Friendly, brief attendant; answers in the customer's language and keeps to instrument-store support. | `prompt.txt` and the recorded answers |
| Answers grounded in supplied context | Product lookups read the CSV snapshot; policy lookup extracts the supplied PDF. | Tool traces in examples 01–04 |
| Distinguish data from policies | Catalog questions use product tools; address, hours, and returns use policy sections. | Examples 01–04 |
| Handle out-of-scope questions | Redirect accessory requests and decline unrelated requests, including attempts to override the role. | Example 05 |
| Usable interaction | Browser chat and CLI share the same agent. A browsable catalog supports discovery without requiring model names. | `static/`, `/api/catalog`, browser checks |

The case explicitly permits selecting which data to use. Order status is not
implemented: the prototype has no customer authentication, and order/customer
CSVs are not published. The agent must explain that limitation rather than expose
another customer's records or invent an order status.

## Recorded conversations

These are actual Groq outputs, not manually composed assistant answers. Each file
includes the question, response, tool calls, request count, token count, and UTC
recording time. Source values were checked against the CSVs and PDF.

| Conversation | What was checked |
| --- | --- |
| [Budget search](../examples/01-budget-search.md) | Three available acoustic guitars below R$1,000; current prices R$429.90, R$459.90, and R$549.00 match the snapshot. |
| [Store information](../examples/02-store-information.md) | Address and normal weekday/Saturday hours match sections 1 and 2. This question does not test holiday exceptions. |
| [Product price](../examples/03-product-price.md) | Takamine GD20 regular price R$2,199.00 and PIX price R$2,089.05 match the lookup. |
| [Online return](../examples/04-online-return.md) | Online purchase, three days since receipt, product condition, seven-day withdrawal period, store-paid return shipping, and referral to staff. |
| [Out of scope](../examples/05-out-of-scope.md) | Redirect accessory requests and decline an unrelated recipe request, despite an instruction to ignore the store role. |

The last response still offers a cooking-site referral. It does not provide the
recipe or invent commercial facts, but that extra offer is outside the intended
store-only assistance and remains a response-quality limitation.

![Chat displaying recorded model responses](images/chat-examples.png)

The image replays the recorded budget and price responses through the browser
renderer. It does not make a new model request. The two questions in this image
come from separate recorded scenarios; it is a presentation check, not an
additional multi-turn quality evaluation.

## Failures found during development

- A named acoustic-guitar search was incorrectly restricted to electric guitars.
  The prompt and tool description now recommend omitting category for named-model
  searches. This is guidance, not a hard guarantee that the model will omit it.
- An initial English budget query received a Portuguese answer using unrequested
  PIX prices and referring to a website. The instructions now distinguish current
  price from optional PIX price, preserve the question's language, and prohibit
  claiming a website or live-system lookup. The corrected response is example 01.
- An initial return response offered a prepaid shipping label and inferred when
  the refund clock starts. A later response referred the customer to staff but
  still speculated about their paperwork. Return instructions now restrict the
  next step to asking the store team to confirm the procedure. The policy tool
  also reports that logistics are unverified and no return actions are available.
  Example 04 records
  the final recheck.
- A political-speech probe was refused but produced only a generic rejection.
  The final out-of-scope example uses an ordinary unrelated recipe request to
  check whether the assistant can also explain the store's scope helpfully.

Failures were corrected in instructions and re-run; generated transcripts were
not silently edited into ideal answers. Examples that already matched the source
were preserved to avoid spending quota on repeated checks.

## Local checks and limits of the evidence

The 31 offline tests cover money and stock rules, inactive promotions, policy
sections across pages, tool argument validation, the request budget, session
isolation, catalog filtering, and pagination. They use mock model responses and
do not demonstrate language-model quality.

Chromium checks cover desktop/mobile layouts, catalog filtering and pagination,
selecting an instrument, suggested questions, message submission, clearing a
conversation, rate-limit recovery, and rendering hostile HTML as text. Chat API
responses are simulated in these checks, so they spend no Groq quota.

Theme checks also cover keyboard selection, operating-system preference changes,
persistence after reload, mobile layout, and a browser that blocks local storage.
The checked primary, muted, button, promotional, and error text pairs meet 4.5:1
contrast in both palettes; focus rings and input borders meet 3:1 against their
surface. These targeted checks are not a full accessibility audit.

Five live examples provide concrete evidence for the selected scenarios, not an
exhaustive evaluation. Multi-turn ambiguity, every policy conflict, and adversarial
prompt variations still need broader testing. The generator can still produce
unsupported language, so the application is a prototype and performs no purchases,
refunds, or customer-record changes.

The five final examples report 10 API requests and 15,204 tokens. Including earlier
development probes and failed responses, the recorded development runs total
26 requests and 38,203 tokens. These are response-reported counts, not an estimate
of the organization's remaining quota; unrelated account usage is not measured.

## Delivery review

- Public GitHub repository with incremental commits.
- README with environment setup, architecture choices, source assumptions,
  limitations, and AI-assistance disclosure.
- Five recorded conversations, including data lookup and policy application.
- English documentation and English example conversations; original product names
  and source excerpts retain their supplied spelling.
- The submission PDF generated from the final documentation remains to be prepared.
- Freeze the repository when the submission is sent; do not modify it afterward.
