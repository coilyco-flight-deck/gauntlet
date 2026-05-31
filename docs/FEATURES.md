# Features

Baseline of what Gauntlet does. Bullet added = scope increase. For signatures and breaking-change rules see [scope.md](scope.md).

## Headline shape

- Adversarial inference engine for HTTP services. Host-driven Attacker / Inspector / HoldoutEvaluator loop against a SUT.
- MCP server only - no CLI, Action, library entry, or CI mode. Deterministic surface in `gauntlet/server.py`, stdio to a Claude Code host.
- Claude Code plugin: MCP server + two skills + three subagents in one install.
- No model credentials. Gauntlet never calls an LLM; the host provides reasoning and auth.

## Role discipline (train/test split)

- Three per-role subagents declare MCP-tool allowlists in YAML frontmatter. Permission-layer, not prompt discipline.
- Attacker sees `{id, title, description}` only. Inspector reads the iteration buffer only. Neither can call `get_trial` or holdout tools.
- HoldoutEvaluator reads full `Trial` including `blockers` but cannot `read_iteration_records`, so prior traces never leak in.
- `record_iteration` rejects any `Finding` carrying a non-null `violated_blocker`. Schema-enforced.

## MCP tool surface

- Trial config: `list_trials` (attacker-safe), `get_trial` (full).
- Execution: `execute_plan` - real HTTP via `requests`; `ExecutionResult` with per-step outcome, filtered headers, duration, size.
- Run buffer: `start_run`, `record_iteration` / `read_iteration_records`, `record_holdout_result` / `read_holdout_results`.
- Reports: `assemble_run_report` (per-trial `RiskReport` + `Clearance`), `assemble_final_clearance` (aggregate `pass` / `conditional` / `block`).
- Loop helpers: `mutate_plans`, `replay_finding`, `recurring_failures` (issues in 2+ of last N runs).

## Skills and trials

- `gauntlet` - the Orchestrator. Drives the four-stage loop (baseline / boundary / adversarial_misuse / targeted_escalation), holdout, final clearance.
- `gauntlet-author` - one-shot translator from spec to Trial YAMLs under `.gauntlet/trials/`.
- Trial YAML: one per file. Required `title`, `description`, `blockers`; optional `id`, `inspired_by`. `blockers` surface via `get_trial` only.

## Storage and clearance model

- Run buffer: `.gauntlet/runs/<run_id>/<trial_id>/{iterations,holdouts}.jsonl`. Append-only, `fcntl.flock` serialized; manifest carries `schema_version`. One run per host session.
- Findings store: `.gauntlet/findings/<trial_id>.jsonl` accumulates confirmed failures across runs. Sole consumer is `recurring_failures`; writes are a wrapped side effect of `assemble_run_report`.
- `RiskReport` - confidence, risk level, confirmed failures, suspicious patterns, coverage, clusters, timing anomalies (>=10x endpoint-median).
- `Clearance` / `FinalClearance` - passed flag, holdout score, threshold, recommendation. `overall_confidence` is weakest-link min across per-trial confidence + holdout scores.

## Plan execution and posture

- `Plan` = ordered `PlanStep`s `{user, request, extract}`; `extract` captures response values into the path-template context (dotted keys).
- HTTP GET/POST/PATCH. Per-user auth via `user_headers`; fallback `X-User: <name>`. Transport outcomes include `timeout`, `connection_reset`, `dns_failure`. Assertion kind: `status_code`.
- JSON stderr logging + `log_tool_call` on every tool. Plausibility checks on each `HoldoutResult` surface as warnings.
- Python 3.13, `uv`, Pydantic `extra="forbid"`, mypy strict, ruff, pre-commit, hypothesis, docker compose test runner.

## Non-features

Guarded by [scope.md](scope.md) "Non-goals": no CLI / shell entry; HTTP only; no web UI or report renderer; no LLM abstraction; no coverage scorer or cross-target generalization; no CI gate or Action shipped from here; no auth beyond a header dict; no retry/backoff in `execute_plan`.

## See also

- [README.md](../README.md), [AGENTS.md](../AGENTS.md), [.coily/coily.yaml](../.coily/coily.yaml).

Cross-reference convention from [coilysiren/agentic-os#59](https://github.com/coilyco-flight-deck/agentic-os/issues/59).
