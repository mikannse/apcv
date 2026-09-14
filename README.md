# Agent Policy Conformance Validator (APCV)

**Verify AI Agents comply with declared policies before deployment.**

[English](README.md) | [中文](README.zh-CN.md)

APCV is an MVP that validates LangGraph Agents against security and capability policies. It discovers what tools an Agent can call, generates targeted test probes, runs them in isolated environments, and reports policy violations with remediation suggestions.

## Quick Start

```bash
# Install dependencies (uv-managed virtualenv)
uv sync

# Validate an Agent against a policy
uv run apcv validate --agent tests/fixtures/sample_agents/simple_agent.py \
                     --policy tests/fixtures/policies/read_only.yaml

# View results in Web UI (FastAPI dashboard at http://127.0.0.1:8000)
uv run apcv web
```

## Features

- **Tool Surface Discovery (four-layer)**: framework-level `@tool` (single-file + package-level `scan_package`), MCP endpoint inventory, sub-agent tool surface enumeration
- **Policy DSL**: Declare capabilities and boundaries in YAML (deny-by-default)
- **Probe Execution**: policy-relative agent probes + baseline audit probes, executed in isolated Docker sandboxes
- **Parameter Tracing**: wrapt records the arguments of every tool call, producing audit evidence (JSONL)
- **Conformance Checking**: Compare Agent behavior against declared policy
- **CLI Tool**: `apcv validate --output json|sarif|html`
- **Web UI**: FastAPI dashboard (stub — not yet wired to real report data)

## Project Structure

```
apcv/
├── core/
│   ├── scanners/          # Tool discovery (single-file + package-level)
│   ├── frameworks/        # Framework adapters (LangGraph)
│   ├── policy/            # Policy DSL & validation
│   ├── probes/            # Test probes (agent + baseline)
│   ├── execution/         # Sandbox executor + tracer + ProbeHost
│   └── utils/             # SBOM data models
│
├── cli/                    # CLI interface (validate / web)
├── web/                    # FastAPI backend (stub)
├── tests/                  # Test suite
└── docker/                 # apcv-probe sandbox image
```

## Documentation

- [Architecture spine](_bmad-output/architecture/architecture-apcv-2026-09-12/ARCHITECTURE-SPINE.md)
- [Product spec (SPEC)](_bmad-output/specs/spec-apcv-2026-09-12/SPEC.md)
- [Policy DSL Schema](_bmad-output/specs/spec-apcv-2026-09-12/policy-dsl-schema.md)
- [Probe rules](_bmad-output/specs/spec-apcv-2026-09-12/probe-rules.md)
- [Sprint status](_implementation/sprint-status.yaml)

## License

Apache 2.0
