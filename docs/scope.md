# Scope

What Gauntlet is, what it isn't, and what counts as a public-API change. The point is to make scope creep deliberate: a change that adds, removes, or alters anything under "Public surface" needs an explicit reason that overrides this doc, not an offhand "while I was in here." Internals move freely.

## Public surface (changes are API-breaking)

The contracts a host orchestrator binds to. They cannot move silently.

**MCP tools** - the 13 tools in `gauntlet/server.py`: `list_trials`, `get_trial`, `execute_plan`, `start_run`, `record_iteration`, `read_iteration_records`, `record_holdout_result`, `read_holdout_results`, `assemble_run_report`, `assemble_final_clearance`, `replay_finding`, `mutate_plans`, `recurring_failures`. Adding, renaming, removing, or changing the parameter set of any is breaking. Signatures live in [architecture.md](architecture.md).

**Subagent allowlists** - each of `agents/gauntlet-attacker.md`, `agents/gauntlet-inspector.md`, `agents/gauntlet-holdout-evaluator.md` declares an MCP-tool allowlist in YAML frontmatter. The allowlists are the train/test split; widening one (e.g. giving the Attacker `get_trial`) collapses it. `tests/test_subagents.py` enforces them; test changes need explicit justification.

**Skill trigger phrases** - `skills/gauntlet/SKILL.md` and `skills/gauntlet-author/SKILL.md` carry trigger phrases in frontmatter. Hosts auto-discover by phrase; renaming or dropping triggers breaks discovery.

**Trial YAML schema** - `Trial` (in `gauntlet/models.py`) is authored into `.gauntlet/trials/*.yaml`. Required fields (`title`, `description`, `blockers`) and the snake_case `id` constraint are contract. Adding optional fields is non-breaking; renaming or removing existing fields is breaking.

## Internals (free to change)

File layout under `gauntlet/`, any tool's implementation (given stable signature and behavior), storage layout under `.gauntlet/runs/`, dependency choices, test layout, prose inside skill/agent files (given triggers and allowlists hold), docstrings, and docs.

## Non-goals (do not implement without revisiting this doc)

- **CLI entry point.** MCP server only. No shell command, `argparse`, or standalone invocation path.
- **Multi-surface execution.** No CLI/WebDriver/browser adapter. HTTP only.
- **Dashboard, web UI, or report renderer.** Gauntlet returns structured data; the host renders it.
- **Multi-provider LLM abstraction.** Gauntlet never calls an LLM.
- **Trial-coverage or test-coverage scorer.** `gauntlet-author` is a one-shot translator.
- **Cross-target generalization.** The host loops; Gauntlet does one trial at a time.
- **CI gate, GitHub Action, or pre-commit hook.** Hosts that want one wrap Gauntlet.
- **Auth beyond a header dict.** No OAuth, env-var indirection, token refresh.
- **Built-in retry/backoff or rate limiting** on `execute_plan`. SUT flakiness is the host's to model.

## When to revisit

Open this file when a user (not a future Kai with an idea) requests a "Non-goals" feature, a second consumer beyond the dark-factory orchestrator appears, or a real cross-run pattern emerges that the run-scoped buffer can't represent. Otherwise it holds.

## See also

- [architecture.md](architecture.md) - module map and tool signatures.
- [../AGENTS.md](../AGENTS.md) - repo operating rules.
- [FEATURES.md](FEATURES.md) - shipped inventory.

Cross-reference convention from [coilysiren/agentic-os#59](https://github.com/coilyco-flight-deck/agentic-os/issues/59).
