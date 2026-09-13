# Agent Policy Conformance Validator (APCV)

**Verify AI Agents comply with declared policies before deployment.**

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

- **Tool Surface Discovery (四层)**: 框架层 `@tool`(单文件 + 包级 `scan_package`)、MCP 端点清单、子 Agent 工具面枚举
- **Policy DSL**: Declare capabilities and boundaries in YAML (deny-by-default)
- **Probe Execution**: 策略相对型 agent 探针 + baseline 审计探针,在隔离 Docker 沙箱中执行
- **Parameter Tracing**: wrapt 记录每次工具调用的参数,产出审计证据 (JSONL)
- **Conformance Checking**: Compare Agent behavior against declared policy
- **CLI Tool**: `apcv validate --output json|sarif|html`
- **Web UI**: FastAPI dashboard (stub — 尚未接真实报告数据)

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

- [架构主干](_bmad-output/architecture/architecture-apcv-2026-09-12/ARCHITECTURE-SPINE.md)
- [产品规格 (SPEC)](_bmad-output/specs/spec-apcv-2026-09-12/SPEC.md)
- [Policy DSL Schema](_bmad-output/specs/spec-apcv-2026-09-12/policy-dsl-schema.md)
- [探针规则](_bmad-output/specs/spec-apcv-2026-09-12/probe-rules.md)
- [Sprint 状态](_implementation/sprint-status.yaml)

## License

Apache 2.0
