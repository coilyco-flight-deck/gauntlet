# Agent instructions

Workspace conventions load globally via `~/.claude/CLAUDE.md` -> `agentic-os-kai/AGENTS.md`. This file covers only what is specific to this repo.

## Scope

Gauntlet is a two-role adversarial MCP server: a host Claude Code agent plays Attacker and Inspector, Gauntlet provides deterministic tools (config loading, plan execution, risk-report assembly) against a running HTTP service. Public-surface changes (MCP tools, subagent allowlists, skill triggers, Trial schema) are governed by [docs/scope.md](docs/scope.md) - read it before touching that surface.

## Project shape

Runs **exclusively as an MCP server inside Claude Code**. No CLI, no standalone invocation. Server entry is `gauntlet/server.py`; models in `gauntlet/models.py`; subagent definitions in `agents/`; host skills in `skills/`. No Anthropic/OpenAI credentials - the host provides auth. See [docs/architecture.md](docs/architecture.md) for the module map and [docs/usage.md](docs/usage.md) for the driven loop.

## Repo boundaries

Gauntlet does one trial against one SUT per call; the host loops. It never calls an LLM and ships no CI gate - consumers that want one wrap Gauntlet themselves. Storage under `.gauntlet/` is an implementation detail; nothing outside Gauntlet reads it.

## Commands

Route every dev command through coily, which reads [`.coily/coily.yaml`](.coily/coily.yaml). The lockdown denies bare `uv` / `docker`. Add new verbs to that file before invoking them. Any command listed in [docs/development.md](docs/development.md) may be run without requesting approval.

## Validation

After any code change:

1. `coily exec test` - docker compose pytest suite, all green.
2. `coily exec lint` and `coily exec fmt-check` - no ruff lint or format errors.
3. `coily exec typecheck` - `mypy --strict` clean across `gauntlet/` and `tests/`.

Pre-commit enforces lint, format, types, and the agentic-os shared hook block. Never `--no-verify`.

## Safety

Inherited from `../AGENTS.md`. Readonly git and shell commands run without confirmation. Never bypass pre-commit; fix the violation instead.

## Cross-repo contracts

The MCP tool surface in `gauntlet/server.py`, the per-role subagent allowlists in `agents/`, the skill triggers in `skills/`, and the Trial YAML schema are the contracts a host binds to. They cannot move silently; [docs/scope.md](docs/scope.md) is the source of truth for what counts as breaking.

## Release

Shipped as a Claude Code plugin (`.claude-plugin/`). `coily exec release <patch|minor|major> --issue N` bumps `plugin.json` / `marketplace.json` / `pyproject.toml` in lockstep, tags, and pushes. Commit to canonical Forgejo `main`; the GitHub mirror stays PR-gated.

## Agent rules

- Before every commit, sync [docs/architecture.md](docs/architecture.md) with the current module structure in `gauntlet/` (new/removed files, changed abstractions).
- Before changing the public surface, check [docs/scope.md](docs/scope.md); if the change lands under "Non-goals", surface it instead of doing it.
- After pushing to `main`, schedule a wake-up ~240s later to verify CI (`coily gh run list --repo coilysiren/gauntlet --limit 1` shows `completed/success`). Skip for docs-only pushes.

## See also

- [README.md](README.md) - human-facing intro.
- [docs/FEATURES.md](docs/FEATURES.md) - inventory of what ships today.
- [.coily/coily.yaml](.coily/coily.yaml) - allowlisted commands.
- [docs/scope.md](docs/scope.md) - public surface and non-goals.

Cross-reference convention from [coilysiren/agentic-os#59](https://github.com/coilyco-flight-deck/agentic-os/issues/59).
