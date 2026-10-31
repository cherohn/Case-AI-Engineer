# Empório da Música — Customer Support Agent

Python prototype for the Artefact AI Engineer technical case. The agent will help
customers find instruments and understand the store's policies using the supplied
CSV files and policy manual.

## Project status

Catalog lookups and pricing rules are implemented. The conversational agent and
policy retrieval are not implemented yet. Model configuration and interaction
examples will be added in the next steps.

## Run the current checks

The catalog uses only the Python standard library. From the repository root:

```bash
python3 -m unittest discover -v
```

To inspect a real product lookup without a language model:

```bash
python3 -c 'from store_agent.catalog import Catalog; import json; print(json.dumps(Catalog().search_products(query="Takamine GD20"), ensure_ascii=False, indent=2))'
```

## Scope

- Answer questions about instruments, prices, availability, and promotions.
- Answer store policy questions using the supplied manual.
- Keep a friendly, informal, professional tone.
- Redirect requests outside the store's scope without inventing information.

The first interface will be a command-line chat. Operational information must
come from data lookups rather than the model's memory. Ambiguous source material
and implementation assumptions will be documented here.

## Data and catalog decisions

The supplied products, categories, promotions, and policy PDF are included in
`data/` with shorter filenames and unchanged contents. Customer and order files
are not included at this stage because catalog support does not need them.

`store_agent/catalog.py` reads the CSV files on each lookup. These files are a
local snapshot, not a connection to a live store system. Re-reading allows changes
to the snapshot to appear on the next query.

- A product is available only when its status is `active` and stock is positive.
  Discontinued and coming-soon products are excluded from available offers even
  when they have stock. Direct product lookup still reports their status.
- Only promotions with `is_active=1` apply. There are no validity dates in the
  promotion data, so the application does not infer expiration from descriptions.
- If multiple active promotions target one product, the largest discount applies
  once. This is an explicit assumption; the manual prohibits stacking promotions.
- Promotional prices do not receive an additional PIX discount. Otherwise, PIX
  receives 5% off the list price.
- Money uses `Decimal`, rounded to cents with `ROUND_HALF_UP`. Price filters use
  the current price before the payment-specific PIX discount.
- Name searches support multiple terms, case differences, and missing accents.
  Category is a separate filter. These functions expect structured search terms;
  interpreting a full customer sentence is the conversational agent's job.

The policy PDF will be used as the source for policy answers. Ambiguities such as
the exact R$500 shipping boundary and conflicting contact numbers still need an
explicit policy-handling strategy before the agent is complete.

## Planned delivery

- Runnable Python application and environment configuration instructions.
- Explanation of the model, tools, prompts, and policy retrieval approach.
- Three to five recorded conversations, including a non-trivial scenario.
- Known limitations and possible improvements.
- A PDF generated from the final README and documentation for submission.

## AI assistance

OpenAI Codex is being used to review the requirements, propose implementation
options, and help write and check the project. The candidate reviews the changes
and technical decisions. This section will be updated to reflect the final
workflow and validation performed.
