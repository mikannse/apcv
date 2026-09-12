# Agent Policy Conformance Validator (APCV)

**Verify AI Agents comply with declared policies before deployment.**

APCV is a 3-week MVP that validates LangGraph Agents against security and capability policies. It discovers what tools an Agent can call, generates targeted test probes, runs them in isolated environments, and reports policy violations with remediation suggestions.

## Quick Start

```bash
# Install
pip install -e .

# Validate an Agent
apcv validate --agent my_agent.py --policy policy.yaml

# View results in Web UI
apcv web
```

## Features (MVP - Week 1-3)

- **Tool Discovery**: Automatically find all `@tool` decorators in LangGraph Agents
- **Policy DSL**: Declare capabilities and boundaries in YAML
- **Probe Generation**: Create 20-30 security test cases based on policy
- **Isolated Execution**: Run probes in Docker containers safely
- **Conformance Checking**: Compare Agent behavior against declared policy
- **CLI Tool**: Single `apcv validate` command
- **Web UI**: Dashboard with compliance scores and detailed reports

## Project Structure

```
apcv/
├── core/
│   ├── scanners/          # Tool discovery
│   ├── frameworks/        # Framework adapters
│   ├── policy/            # Policy DSL & validation
│   ├── probes/            # Test probes
│   ├── execution/         # Execution engine
│   └── utils/             # Shared utilities
│
├── cli/                    # CLI interface
├── web/                    # Web UI (FastAPI + React)
├── tests/                  # Test suite
├── docs/                   # Documentation
└── docker/                 # Docker images
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Policy DSL](docs/POLICY_DSL.md)
- [Probe Rules](docs/PROBE_RULES.md)
- [API Reference](docs/API.md)
- [Deployment Guide](docs/DEPLOYMENT.md)

## License

Apache 2.0
