# ⚔️🛡️🎯 Gauntlet

[![CI](https://github.com/coilysiren/gauntlet/actions/workflows/ci.yml/badge.svg)](https://github.com/coilysiren/gauntlet/actions/workflows/ci.yml)
[![Python 3.13](https://img.shields.io/badge/python-3.13-3776AB?logo=python&logoColor=white)](https://www.python.org/downloads/release/python-3130/)
[![mypy strict](https://img.shields.io/badge/mypy-strict-1f5082?logo=python&logoColor=white)](http://mypy-lang.org/)
[![MCP server](https://img.shields.io/badge/MCP-server-8A63D2)](https://modelcontextprotocol.io/)
[![Claude Code plugin](https://img.shields.io/badge/Claude%20Code-plugin-D4A27F?logo=anthropic&logoColor=white)](https://docs.claude.com/en/docs/claude-code)

Two-role adversarial MCP server that infers software correctness by observing how code behaves under sustained, targeted attack. Quality control for dark-factory environments where code is written by bots and verified by attack.

**Run your service through the gauntlet.** Point a host Claude Code agent at a running service, hand it the trial set, and the gauntlet is what the service survives. The host plays Attacker and Inspector; Gauntlet provides the deterministic tools (config loading, plan execution, risk-report assembly).

AI-written code can look correct while hiding behavioral failures. Traditional tests miss this because the same agent wrote code and tests. Gauntlet's Attacker context assumes the code is broken, and each Trial's `blockers` never load into that context, preserving a train/test split.

> An **Attacker** uses a **Trial** aimed at a **Target** to generate **Plans**. Gauntlet's Drone executes those Plans as a **User**. An **Inspector** watches and surfaces **Findings**. Hidden **Vitals** are checked independently to produce a **Clearance**.

See [`docs/architecture.md`](docs/architecture.md) for the model, [`docs/usage.md`](docs/usage.md) for the runbook, [`docs/development.md`](docs/development.md) for dev setup.

## Install

Gauntlet ships as a Claude Code plugin bundling the MCP server and the host [skill](skills/gauntlet/SKILL.md):

```bash
claude plugin marketplace add coilysiren/gauntlet
claude plugin install gauntlet@coilysiren-gauntlet
```

Restart Claude Code so the skill, MCP server, and subagents register. Confirm with `/mcp` and "run gauntlet". No Anthropic creds needed; the host has auth. Local dev: `git clone ... && claude --plugin-dir path/to/gauntlet`.

The plugin delivers the MCP server, the `gauntlet` skill (orchestrator loop), `gauntlet-author` skill (spec to trial YAMLs), and `gauntlet-attacker` / `-inspector` / `-holdout-evaluator` subagents whose MCP allowlists enforce the train/test split. The Attacker subagent literally cannot call `get_trial`. The full MCP tool surface is listed in [`docs/FEATURES.md`](docs/FEATURES.md).

## Project config

```
your-project/
└── .gauntlet/
    └── trials/
        ├── task_ownership.yaml
        └── ...
```

Trials define reusable attack strategies. `blockers` are externally observable truths about expected behavior, never loaded into the Attacker context:

```yaml
title: Users cannot modify each other's tasks
description: >
  The task API must enforce resource ownership.
blockers:
  - A PATCH request by a non-owner is rejected with 403
  - The task body is unchanged after an unauthorized PATCH attempt
  - A GET by the owner after an unauthorized PATCH returns the original data
```

If the SUT requires auth, the orchestrator passes `user_headers` to `execute_plan` (a `dict[str, dict[str, str]]` mapping user names to headers). Users without an entry fall back to `X-User: <name>`.

## See also

- [AGENTS.md](AGENTS.md), [docs/FEATURES.md](docs/FEATURES.md), [.coily/coily.yaml](.coily/coily.yaml).
- Prior art (RESTler, Schemathesis, ToolFuzz) and the full model live in [`docs/architecture.md`](docs/architecture.md).

Cross-reference convention from [coilysiren/agentic-os#59](https://github.com/coilysiren/agentic-os/issues/59).
