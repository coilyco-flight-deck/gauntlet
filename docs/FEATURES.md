# Features

Baseline inventory of what Gauntlet currently does, scoped at the headline level. Use this file to evaluate scope changes over time. If a future change adds a bullet here, that is a scope increase. If it removes one, a scope decrease. For deeper contracts (signatures, breaking-change rules), see [SCOPE.md](../SCOPE.md).

## Headline shape

- **Adversarial inference engine for HTTP services.** Runs a host-driven Attacker / Inspector / HoldoutEvaluator loop against a live SUT to surface behavioral failures that conventional tests miss.
- **MCP server only.** No CLI, no GitHub Action, no library entry point, no remote/CI mode. The deterministic surface lives in `gauntlet/server.py` and speaks stdio to a Claude Code host.
- **Claude Code plugin delivery.** Single install bundles the MCP server, two skills, and three subagents. Marketplace install via `claude plugin marketplace add coilysiren/gauntlet`.
- **No model credentials required.** Gauntlet never calls an LLM. The host provides reasoning and auth.

## Role discipline (train/test split)

- **Three per-role subagents** (`gauntlet-attacker`, `gauntlet-inspector`, `gauntlet-holdout-evaluator`) each declare an MCP-tool allowlist in YAML frontmatter. Permission-layer enforcement, not prompt discipline.
- **Attacker** sees `{id, title, description}` only. Cannot call `get_trial`, `read_holdout_results`, or `record_holdout_result`.
- **Inspector** reads execution results from the buffer. Cannot call `get_trial`, holdout tools, or SUT-execution tools.
- **HoldoutEvaluator** reads full `Trial` including `blockers`. Cannot call `read_iteration_records`, so prior Attacker/Inspector traces never leak in.
- **Schema-level enforcement at the buffer.** `record_iteration` rejects any `Finding` carrying a non-null `violated_blocker`, since the Inspector should never have seen blocker text.

## MCP tool surface (13 tools)

Trial config:
- `list_trials(trials_path)` - attacker-safe view, no blockers.
- `get_trial(trial_id, trials_path)` - full trial including blockers.

Execution:
- `execute_plan(url, plan, user_headers)` - real HTTP requests via `requests`, returns `ExecutionResult` with per-step transport outcome, headers (filtered allowlist), duration, response size.

Run buffer (per-run, filesystem JSONL):
- `start_run(trial_ids)` - opens `.gauntlet/runs/<run_id>/`.
- `record_iteration` / `read_iteration_records` - append-only iteration buffer per trial.
- `record_holdout_result` / `read_holdout_results` - append-only holdout buffer per trial.

Reports:
- `assemble_run_report(run_id, trial_id, clearance_threshold)` - per-trial `RiskReport` + `Clearance`. Side-effect: persists confirmed-failure findings to the cross-run store.
- `assemble_final_clearance(run_id, clearance_threshold, trial_ids?)` - aggregates every per-trial report into one `FinalClearance` with `pass` / `conditional` / `block` recommendation.

Loop helpers:
- `mutate_plans(run_id, trial_id, max_variants)` - deterministic plan variants (drop field, rotate users, negate expected, reverse order). No network, no state change.
- `replay_finding(run_id, trial_id, finding_index, url, user_headers)` - re-executes a stored finding's `ReplayBundle` against the SUT. Drives "did the fix work" loops.
- `recurring_failures(trial_id, lookback, findings_path)` - issues that recurred in >= 2 of the last N runs.

## Skills (host-side prose)

- **`gauntlet`** - the Orchestrator skill. Auto-loads on phrases like "run gauntlet", "adversarial test", "check before merging". Walks the host through the four-stage iteration loop (baseline / boundary / adversarial_misuse / targeted_escalation), holdout evaluation, and final clearance.
- **`gauntlet-author`** - one-shot translator from a product spec to Trial YAMLs in `.gauntlet/trials/`. Auto-loads on "author trials from this spec", "generate gauntlet trials", "propose trials for this API".

## Trial format

- YAML files under `.gauntlet/trials/`. One trial per file.
- Required fields: `title`, `description`, `blockers`. Optional: `id` (snake_case, validated), `inspired_by`.
- `blockers` are the Trial's Vitals - falsifiable statements about expected system behavior. Surfaced only via `get_trial`, never via `list_trials`.

## Run-scoped buffer

- Per-run filesystem layout under `.gauntlet/runs/<run_id>/<trial_id>/` with `iterations.jsonl` and `holdouts.jsonl`.
- Append-only, JSONL, `fcntl.flock` serialized writers. Multiple subagent processes can append concurrently.
- Manifest carries `schema_version`. Readers tolerate older buffers.
- Corrupt JSONL lines are skipped with a logged warning and counted via `RunStore.corrupt_record_counts()`.
- Lifecycle: one run, one host session. No expectation of cross-run survival.

## Cross-run findings store

- `.gauntlet/findings/<trial_id>.jsonl` accumulates confirmed-failure `Finding`s across runs.
- One consumer: `recurring_failures`. Writes happen as a side effect of `assemble_run_report`, wrapped so a store-write failure never aborts the report.

## Risk and clearance model

- **`RiskReport`** - confidence score, risk level (`low`/`medium`/`high`), confirmed failures, suspicious patterns, unexplored surfaces, anomalies, coverage, failure clusters (grouped by endpoint+method+severity), response collisions (identical fingerprints across distinct plans), timing anomalies (>= 10x endpoint-median latency).
- **`Clearance`** - passed flag, holdout satisfaction score, threshold, recommendation (`pass`/`conditional`/`block`), rationale.
- **`FinalClearance`** - aggregate across trials. `overall_confidence` is the weakest-link minimum across per-trial confidence and holdout scores. `final_recommendation` gates on threshold + per-trial risk levels.

## Plan execution semantics

- `Plan` = ordered `PlanStep`s with `name`, `category`, `goal`, optional assertions.
- `PlanStep` = `{user, request, extract}` where `extract` captures values from a step's response into the path-template context for later steps (simple dotted keys, no jmespath).
- Supported HTTP methods: `GET`, `POST`, `PATCH`.
- Per-user auth via `user_headers: dict[str, dict[str, str]]`. Users without an entry fall back to `X-User: <name>`.
- Transport-level outcomes distinguished: `ok`, `timeout`, `connection_reset`, `dns_failure`, `other_error`. Non-`ok` outcomes produce a synthetic `HttpResponse` so downstream consumers see uniform shape.
- Currently-supported assertion kind: `status_code`.

## Observability

- JSON stderr logging (`gauntlet/_log.py`) including a `log_tool_call` decorator on every MCP tool.
- Heuristic plausibility checks (`gauntlet/_plausibility.py`) run on every recorded `HoldoutResult` and surface as warnings on the `record_holdout_result` response.

## Determinism boundary

- Deterministic: Drone (path templates, assertion eval), risk-report assembly, plan mutator, findings store I/O.
- Non-deterministic: `HttpApi` (real network), and the host (LLM agent) - but Gauntlet does not run the host.

## Engineering posture

- Python 3.13, `uv`-managed.
- Pydantic models with `extra="forbid"` for all interchange types.
- mypy strict, ruff lint+format, pre-commit, hypothesis property tests.
- Docker compose test runner (`docker compose run --rm test`).

## Explicit non-features

These are guarded by [SCOPE.md](../SCOPE.md) under "Non-goals" and should not appear here without an explicit scope-revisit:

- No CLI, no shell entry point, no `argparse`.
- No browser/WebDriver/CLI execution adapters. HTTP only.
- No web UI, dashboard, or report renderer.
- No multi-provider LLM abstraction. Gauntlet does not call an LLM.
- No trial-coverage or test-coverage scorer.
- No cross-target generalization (one trial against many SUTs in one call).
- No CI gate, GitHub Action, or pre-commit hook shipped from this repo.
- No auth beyond a header dict (no OAuth, env-var indirection, token refresh).
- No retry/backoff or rate limiting in `execute_plan`.

## See also

- [README.md](../README.md) - human-facing intro.
- [AGENTS.md](../AGENTS.md) - agent-facing operating rules.
- [.coily/coily.yaml](../.coily/coily.yaml) - allowlisted commands.

Cross-reference convention from [coilysiren/coilyco-ai#313](https://github.com/coilysiren/coilyco-ai/issues/313).
