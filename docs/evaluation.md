# Validation report

**Matheus Souza Garcez — October 31, 2026**

This report records what was checked and what remains uncertain. The selected
conversations are evidence for specific scenarios, not a claim of exhaustive
model reliability. Detailed observations are retained in
[development-notes.md](development-notes.md).

## Requirements and scope

| Case requirement | Implementation and evidence |
| --- | --- |
| Python as the main language | Catalog rules, PDF extraction, Groq/tool loop, CLI, and FastAPI backend are Python. |
| Store-aligned persona | English instructions define a friendly, brief attendant; the recorded responses show the resulting behavior. |
| Answers from supplied context | Product tools read the CSV snapshot; policy tools retrieve the manual. |
| Choose between data and policies | Discovery/price queries use catalog functions; address, hours, and return questions retrieve policy context. |
| Handle out-of-scope requests | Example 05 declines accessory sales and the unrelated recipe, with a remaining scope-drift limitation noted below. |
| Working interface | Browser chat and CLI share the agent; the catalog supports discovery without model calls. |
| Documentation and examples | README covers setup, choices, assumptions, limitations, and AI use; five conversations include recorded execution details. |

The case permits choosing which supplied data to use. Customer/order files are
excluded because order status would require authentication and access control.
The prototype explains that limitation instead of exposing private records or
inventing a status.

## Reproducibility and offline checks

The latest offline suite passed all **37 tests on Python 3.14.3**:

```bash
python -m unittest discover -v
```

Coverage includes monetary rounding, inactive promotions, availability conflicts,
stock changes between lookups, category aliases, PDF sections spanning pages,
tool validation, missing/null return facts, history limits, session isolation,
provider errors, and log privacy. Model responses are mocked in these tests.

A clean installation from tracked files at commit `0ff9778` used a new virtual
environment without system packages and downloaded `requirements.txt` without
pip's cache. `pip check` found no broken requirements and the then-current 31 tests
passed. Later application revisions passed the expanded 37-test suite; dependency
pins have not changed since that installation check.

The clean copy started on a separate loopback port. HTML, static assets, API docs,
and filtered catalog loaded. Without credentials, the CLI reported a missing key
and chat returned HTTP 503 while browsing remained available. These checks made
no Groq calls. Other operating systems and Python versions were not exercised.

## Live application checks

Live checks used the actual browser, FastAPI backend, Groq, and local tools.
No response interception was used for these runs.

| Scenario | Source comparison and observed outcome |
| --- | --- |
| Discovery | Six categories and 61 available models matched the snapshot. |
| Budget follow-up | Three available acoustic guitars were R$429.90, R$459.90, and R$549.00. The first attempt returned HTTP 502; a manual resend succeeded. The original upstream cause was not established. |
| Takamine GD20 | Regular price R$2,199.00 and PIX price R$2,089.05 matched the CSV calculation. The isolated frontend check returned HTTP 200 with two model requests and 2,944 reported tokens. |
| Crafter HT-100 promotion | Original R$2,399.00, 18% discount, final R$1,967.18. PIX did not add another discount. This calculation came from the catalog tool's Python pricing rules. |
| Incomplete return | The corrected `check_return` flow requested purchase channel and elapsed receipt time directly in Python; no eligibility deadline was generated. |
| Return follow-up | With online purchase, receipt three days earlier, and the stated product condition, the model cited section 4.1, store-paid return shipping, and the refund deadline without inventing its starting event. Staff confirms the procedure. |

The frontend price check took approximately 2.1 seconds in that run. It is a
single observation, not a latency benchmark. Provider-reported token counts are
not a full account ledger: rejected requests did not return usage and unrelated
account activity was not measured.

![Live promotion response with non-stacking PIX pricing](images/promotion-pix-live.png)

![Return workflow asking for missing facts](images/return-clarification.png)

The [return follow-up capture](images/return-follow-up.png) and
[original frontend price capture](images/frontend-price-live.png) provide
additional evidence. The manual resend was reviewed from the text supplied by
the candidate and checked against the source prices and server completion metrics.

## Five selected conversations

| Recording | What it demonstrates | Model requests / reported tokens |
| --- | --- | --- |
| [Product discovery](../examples/01-product-discovery.md) | Available categories, counts, and a question about customer needs. | 2 / 2,870 |
| [Store information](../examples/02-store-information.md) | Address and normal weekday/Saturday hours from sections 1 and 2. Holiday exceptions were not exercised. | 3 / 4,772 |
| [Product price](../examples/03-product-price.md) | Takamine GD20 regular and PIX prices from a product lookup. | 2 / 2,668 |
| [Online return](../examples/04-online-return.md) | Two turns: Python requests missing facts, then the model explains the policy using supplied customer details. | 3 / 5,320 |
| [Out of scope](../examples/05-out-of-scope.md) | Accessory redirection and refusal of an unrelated recipe request. | 1 / 1,418 |

Together they report 11 model requests and 17,048 tokens. The texts are captured
application outputs, not editorially corrected answers. The first return
clarification is explicitly identified as Python-generated. Store/product names,
addresses, source excerpts, and historical diagnostic values preserve their
original spelling.

![Presentation replay of selected discovery and price responses](images/chat-examples.png)

This last image replays saved responses for presentation. It makes no model
request and combines separate recorded scenarios; it is not another live or
multi-turn model evaluation.

## Browser and language checks

Browser checks covered desktop/mobile layouts, catalog filtering and pagination,
suggested questions, instrument selection, send/reset actions, rate-limit recovery,
and safe rendering of hostile HTML as text. Simulated chat responses were used
where live model behavior was not the subject of the check.

Native-window checks confirmed that the message field stayed visible before,
during, and after a response, and accepted an unsent follow-up. An earlier
oversized test window was corrected; no application layout change was required.

Theme checks covered keyboard selection, system-preference changes, persistence,
and blocked local storage. The checked primary, muted, button, promotional, and
error text pairs met 4.5:1 contrast; focus rings and input borders met 3:1 against
their surfaces. This was a targeted check, not a full accessibility audit.

English labels and application validation messages were also checked with a
`pt-BR` browser locale. Empty messages and invalid budgets produced English
feedback without model calls. English policy labels are separate from the PDF
headings used to extract unchanged source text.

## Failures, corrections, and remaining limits

| Finding | Resolution or remaining limit |
| --- | --- |
| Incorrect category guessed for a named model | Tool instructions recommend omitting category. Category values are normalized to English for both model and UI. Routing remains model-driven. |
| Generic return answer skipped necessary questions and invented procedure/timing details | `check_return` now asks for missing channel/receipt time directly in Python before returning the policy. It does not verify physical condition or initiate a return. |
| Unknown return facts were sent as null and rejected with HTTP 400 | A diagnostic identified `tool_use_failed`. The schema and local validator now accept null for unknown facts; regression and live checks passed. |
| A follow-up first failed with HTTP 502 | Manual resend recovered. That first upstream cause was not captured. Later error logs record class/status and usage counters without conversation content. Automatic retries remain disabled. |
| Out-of-scope answer offered a cooking-site referral | The recipe was not provided, but the extra offer remains outside the intended store-only assistance. |

Policy interpretation beyond the deterministic pricing and missing-fact checks
still depends on the model. Multi-turn ambiguity, all policy conflicts, adversarial
variations, and every possible wording have not been exhaustively evaluated.
The prototype has short in-memory history, no authenticated order access, and no
purchase/refund/customer-record operations. The supplied operational files are a
snapshot, and the PDF parser depends on this manual's structure.

## Submission contents

The [submission PDF](../submission/Matheus%20Souza%20Garcez%20-%20AI%20Engineer%20%E2%80%93%20Full-Stack%20para%20Aplica%C3%A7%C3%B5es%20com%20IA%20Generativa.pdf) uses the ordered sources in [submission.json](submission.json):
README, this report, and the five selected conversations. The public repository
also retains source data, tests, captures, incremental commits, and detailed
development notes. The PDF export uses selectable text, document links, and embedded
captures. Freeze the repository when the submission is sent.
