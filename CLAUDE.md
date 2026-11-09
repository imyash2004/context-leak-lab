# Instructions for the coding agent

You are building **Context Leak Lab**. Read `README.md`, then `docs/02-design.md` → `docs/05-build-plan.md` in order. Build exactly what `docs/03-architecture.md` describes.

## Prime directive: keep it minimal

- Target **under ~700 lines of Python total** (excluding tests and page content).
- Standard library first. Allowed dependencies: `anthropic`, `pyyaml`, `pandas`, `matplotlib`, `pytest`. Nothing else without a reason written in `NOTES.md`.
- No frameworks, no classes where a function will do, no plugin systems, no async unless a step is clearly too slow (then a simple thread pool).
- One file per responsibility as listed in `docs/03-architecture.md`. Do not add layers.
- Prefer readable over clever. A reviewer should understand any file in 2 minutes.

## Safety rules (non-negotiable)

1. **Never** let the agent under test reach the real internet. All tool execution happens inside the `cll-sandbox` container started with `--network none`.
2. Only fake identities, emails, phone numbers and API keys. Emails use the `.test` TLD.
3. Never put a real API key, email or personal detail into any page, prompt, config or log.
4. The Anthropic API key lives only in `.env` (git-ignored). The sandbox container never receives it.
5. Do not test, scrape or contact any real website or the real Claude Code product as part of this build.

## Conventions

- Python 3.11+, package name `cll`, source in `src/cll/`.
- Every run writes to `runs/<YYYY-MM-DD>_<name>/`: frozen `config.yaml`, `episodes.jsonl`, `transcripts/`, `requests/`.
- Every model call logs: model id returned by the API, input/output tokens, stop reason.
- Grading is deterministic code. No LLM judge anywhere in the primary metrics.
- Seeds: `seed = hash(task_id, rep)` so all conditions in a repetition share the same canary token pattern and task.
- Commit after each build step in `docs/05-build-plan.md` with a message naming the step.

## Definition of done for any step

- Its acceptance check in `docs/05-build-plan.md` passes.
- `pytest` passes.
- No new dependency or file beyond the plan, unless written up in `NOTES.md`.

## When unsure

Pick the simplest option that keeps the measurement valid, write the choice in `NOTES.md`, and continue. Do not stop to ask about cosmetic choices.
