# Features

Baseline of what Gauntlet does. Bullet added = scope increase. For signatures + breaking-change rules see [SCOPE.md](../SCOPE.md).

## Headline shape

- Adversarial inference engine for HTTP services. Host-driven Attacker / Inspector / HoldoutEvaluator loop against a live SUT.
- MCP server only. No CLI, GitHub Action, library entry, or CI mode. Deterministic surface in `gauntlet/server.py`, stdio to a Claude Code host.
- Claude Code plugin delivery. One install: MCP server + two skills + three subagents.
- No model credentials. Gauntlet never calls an LLM; the host provides reasoning and auth.

## Role discipline (train/test split)

- Three per-role subagents declare MCP-tool allowlists in YAML frontmatter. Permission-layer, not prompt discipline.
- Attacker sees `{id, title, description}` only. No `get_trial`, no holdout tools.
- Inspector reads the iteration buffer only. No `get_trial`, no holdout tools, no SUT execution.
- HoldoutEvaluator reads full `Trial` including `blockers`. No `read_iteration_records`, so prior traces never leak in.
- `record_iteration` rejects any `Finding` carrying a non-null `violated_blocker`. Schema-level enforcement.

## MCP tool surface

- Trial config: `list_trials` (attacker-safe), `get_trial` (full).
- Execution: `execute_plan` (real HTTP via `requests`; returns `ExecutionResult` with per-step outcome, filtered headers, duration, size).
- Run buffer: `start_run`, `record_iteration` / `read_iteration_records`, `record_holdout_result` / `read_holdout_results`. Filesystem JSONL, append-only.
- Reports: `assemble_run_report` (per-trial `RiskReport` + `Clearance`; persists confirmed failures to cross-run store), `assemble_final_clearance` (aggregate `pass` / `conditional` / `block`).
- Loop helpers: `mutate_plans` (deterministic variants, no network), `replay_finding` (re-execute `ReplayBundle`), `recurring_failures` (issues in 2+ of last N runs).

## Skills

- `gauntlet` - the Orchestrator. Walks the host through the four-stage loop (baseline / boundary / adversarial_misuse / targeted_escalation), holdout, final clearance.
- `gauntlet-author` - one-shot translator from spec to Trial YAMLs under `.gauntlet/trials/`.

## Trial format

- YAML under `.gauntlet/trials/`, one trial per file.
- Required: `title`, `description`, `blockers`. Optional: `id` (snake_case), `inspired_by`.
- `blockers` = Vitals, falsifiable statements about expected behavior. Surfaced via `get_trial` only, never via `list_trials`.

## Run-scoped buffer

- `.gauntlet/runs/<run_id>/<trial_id>/{iterations,holdouts}.jsonl`. Append-only, `fcntl.flock` serialized.
- Manifest carries `schema_version`. Readers tolerate older buffers. Corrupt lines skipped + counted.
- One run per host session. No cross-run survival expectation.

## Cross-run findings store

- `.gauntlet/findings/<trial_id>.jsonl` accumulates confirmed-failure `Finding`s across runs.
- Sole consumer: `recurring_failures`. Writes are a side effect of `assemble_run_report`, wrapped so a store-write failure never aborts the report.

## Risk and clearance model

- `RiskReport` - confidence score, risk level, confirmed failures, suspicious patterns, unexplored surfaces, anomalies, coverage, failure clusters, response collisions, timing anomalies (>=10x endpoint-median).
- `Clearance` - passed flag, holdout score, threshold, recommendation, rationale.
- `FinalClearance` - aggregate across trials. `overall_confidence` is weakest-link min across per-trial confidence + holdout scores.

## Plan execution

- `Plan` = ordered `PlanStep`s with name, category, goal, optional assertions.
- `PlanStep` = `{user, request, extract}`. `extract` captures response values into the path-template context (dotted keys, no jmespath).
- HTTP methods: GET, POST, PATCH. Per-user auth via `user_headers`; fallback `X-User: <name>`.
- Transport outcomes: `ok`, `timeout`, `connection_reset`, `dns_failure`, `other_error`. Non-ok yields synthetic `HttpResponse`.
- Assertion kind today: `status_code`.

## Observability + posture

- JSON stderr logging + `log_tool_call` decorator on every MCP tool.
- Heuristic plausibility checks run on every `HoldoutResult`, surface as warnings.
- Python 3.13, `uv`, Pydantic `extra="forbid"`, mypy strict, ruff, pre-commit, hypothesis, docker compose test runner.

## Non-features

Guarded by SCOPE.md "Non-goals":

- No CLI / shell entry / `argparse`.
- HTTP only (no browser/WebDriver adapters).
- No web UI, dashboard, report renderer.
- No LLM abstraction (Gauntlet does not call an LLM).
- No coverage scorer, no cross-target generalization.
- No CI gate / GitHub Action / pre-commit hook shipped from here.
- No auth beyond a header dict. No retry/backoff/rate limiting in `execute_plan`.

## See also

- [README.md](../README.md), [AGENTS.md](../AGENTS.md), [.coily/coily.yaml](../.coily/coily.yaml).

Cross-reference convention from [coilysiren/agentic-os#59](https://github.com/coilysiren/agentic-os/issues/59).
