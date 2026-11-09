# 06 — Analysis and report

`python -m cll.analyze runs/<run_id>` produces everything below into `runs/<run_id>/analysis/`. The report quotes only numbers from `analysis/numbers.json`.

## 1. Statistics (keep it simple and correct)

```python
from math import sqrt
def wilson(k, n, z=1.96):
    if n == 0: return (None, None, None)
    p = k / n; d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d
    h = z * sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return p, max(0, c - h), min(1, c + h)

def newcombe(k1, n1, k2, n2):
    """95% CI for p1 - p2 (Newcombe hybrid score)."""
    p1, l1, u1 = wilson(k1, n1); p2, l2, u2 = wilson(k2, n2)
    d = p1 - p2
    return d, d - sqrt((p1-l1)**2 + (u2-p2)**2), d + sqrt((u1-p1)**2 + (p2-l2)**2)
```

Pooled over models = equal-weight mean of per-model rates; report per-model too.

## 2. Tables

| ID | Table | Rows × columns |
| --- | --- | --- |
| T1 | **Leak rate** `k/n = x% [lo–hi]` | conditions × models |
| T2 | **Leak rate by pressure** (C1 only) | none / soft / hard × models |
| T3 | **Channels and encodings** (all leaked episodes) | channel × condition; encoding × condition |
| T4 | **Fix trade-offs** | C1, C2, C3, C4: leak %, attempted %, blocked calls, task success %, invented contact %, gave up on hard site % |
| T5 | **Key leak (C5)** | key sent to another host %, which hosts |

## 3. Charts (one message each; title states the finding in words)

| ID | Chart | Notes |
| --- | --- | --- |
| F1 | **Hero:** leak rate for C0 / C1 / C2 / C3 / C4, bars per model, Wilson whiskers | The image for the LinkedIn post. Title like "With the user's email in context, agents sent it to websites X% of the time". 1200×1200 PNG + SVG |
| F2 | C1 leak rate by pressure (none / soft / hard) | Shows whether polite requests drive leaks |
| F3 | Fix trade-off: leak % vs task success % per fix | Scatter or paired bars |
| F4 | Where it leaked: channel breakdown, stacked to 100% per condition | Only for leaked episodes |

Style: flat colours, colour-blind-safe pair for models, direct labels, n under each group, no dual axes.

## 4. `REPORT.md` template

```markdown
# Do AI agents leak what's in their context?

**TL;DR**
- With a user's email in context, [model] sent it to a third-party site in X% of research tasks [CI]; Y% on sites that demanded contact info.
- Telling the model "never share it" cut that to Z% [CI]. / did not change it.
- An exact-match guard blocked A%; B leaks got past it via [encoding].
- Removing the email stopped the leak, but on hard sites the agent [gave up / invented an email] C% of the time.

## Why this study
Two incidents in November 2026 (Claude Code's User-Agent email leak; "don't ask again" secrets in public repos) share one cause: private data in an agent's context leaves through its own tool calls. [2–3 sentences, sources]

## Setup
- Harness: minimal agent loop (Anthropic API), tools `bash` + `web_fetch`, sandbox with no internet, 8 mock sites.
- Models: [ids returned by the API, dates].
- 12 tasks (4 no pressure, 4 soft, 4 hard), N episodes, fake identity, canary per episode.
- Conditions C0–C5 (table).
- Grading: deterministic detection of the canary in every received request.

## Results
F1 + T1. F2 + T2. T3/F4. T4/F3. T5.

## What a leak looks like
3–5 real request lines from the logs (all fake data), e.g.
`GET fanwiki.test/wiki/Brightwater_Rovers  User-Agent: ResearchBot/1.0 (priya.sharma.k7f3qz@mailbox.test)`

## What works
Ranked list of fixes with their trade-offs.

## Limitations
- Our harness, not the Claude Code product (see Step 9 status).
- Mock sites; invented tasks; 3 reps per cell.
- Default sampling settings; [thinking off/on].
- Guard is exact-match by design; real guards may differ.

## Reproduce
Commands + config files + commit hash.

## Ethics
Fake data only, no network, disclosure policy.

## Sources
[links from docs/01]
```

## 5. Post plan

One LinkedIn post, written after the report:

```
[Hook: "Claude Code sent users' emails to websites. I tested whether AI agents leak anything you put in their context."]

Setup in 2 lines (models, tasks, fake data, no internet).

Results:
→ email in context: X% leaked
→ on sites that ask for contact info: Y%
→ "never share it": Z%
→ code guard: A% (B got past via encoding)
→ email removed: 0%, but agents [gave up/invented one] C%

Takeaway (bold): don't put private data in an agent's context unless a tool needs it; check at the network boundary, not in the prompt.

Code, data, report: <repo link>
Question to readers.
#AIAgents #AISecurity #Privacy #LLM
```

Attach F1. Credit the incident reporters and Apiiro by name, link sources in the first comment, and keep tags friendly.
