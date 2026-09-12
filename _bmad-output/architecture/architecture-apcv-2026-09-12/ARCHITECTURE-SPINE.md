---
name: Agent Policy Conformance Validator (APCV)
type: architecture-spine
purpose: build-substrate
altitude: feature
paradigm: Functional Layering
scope: Complete MVP product supporting LangGraph, with extensible adapter pattern for other frameworks
status: draft
created: 2026-09-12
updated: 2026-09-12
binds: []
sources:
  - Brainstorm Summary (2026-09-12)
  - Project Plan (2026-09-12)
  - Tool/Probe Research (2026-09-12)
  - Open Source Survey (2026-09-12)
companions: []
---

# Architecture Spine — Agent Policy Conformance Validator

## Design Paradigm

**Functional Layering with Framework Abstraction**

System organized into three functional layers processing Agent capability verification:
- **Scan Layer**: Discover Agent abilities across four security boundaries (Tool, Runtime, Network, Identity)
- **Validate Layer**: Generate and execute boundary-crossing probes, capture execution traces
- **Decision Layer**: Aggregate results, compute compliance score, generate verdict and reports

Framework abstraction via Adapter Pattern isolates framework-specific logic from core scanners, enabling multi-framework support (LangGraph first, AgentScope/AutoGen as extensions).

## Invariants & Rules

### AD-1 — Three-Layer Functional Architecture
- **Binds**: Overall system structure and data flow
- **Prevents**: Mixing scanning, validation, and decision logic; unclear boundaries between components
- **Rule**: Scan Layer → Validate Layer → Decision Layer. Each layer has defined input/output contracts. Data flows unidirectionally downward.

### AD-2 — Four Independent Scanners
- **Binds**: Internal organization of Scan Layer
- **Prevents**: Tight coupling between boundary scanners; adding new boundary types requires full refactor
- **Rule**: ToolScanner, RuntimeScanner, NetworkScanner, IdentityScanner each implement common `Scanner` interface. Each produces independent SBOM file. Composition at output layer.

### AD-3 — SBOM Files with Index
- **Binds**: How four scanner outputs are stored and accessed
- **Prevents**: Forcing all dimensions to load together; inefficient memory for large SBOM files
- **Rule**: Each scanner outputs independent JSON file (tool.json, runtime.json, network.json, identity.json) to `.apcv/sbom/`. Index file (index.json) lists all SBOM files. Validate layer loads only needed files on demand.

### AD-4 — Validate Layer: Independent Validators + Shared Infrastructure
- **Binds**: Validate layer internal organization
- **Prevents**: Code duplication; tight coupling between validators; difficulty extending with new boundary types
- **Rule**: Four independent validators (ToolValidator, RuntimeValidator, NetworkValidator, IdentityValidator) each implement common `Validator` interface. Shared infrastructure (ProbeExecutor, ParameterTracer, ProbeLibrary, PolicyEngine) available to all validators via dependency injection.

### AD-5 — Decision Layer: Unified Conformance Engine
- **Binds**: How validation results are aggregated into final verdict
- **Prevents**: Scattered decision logic; inconsistent scoring across dimensions
- **Rule**: Single ConformanceDecisionEngine collects results from all four validators, computes weighted compliance score (0-100), generates unified violations list, outputs final PASS/FAIL verdict and reports in multiple formats.

### AD-6 — Framework Abstraction via Adapter Pattern
- **Binds**: How system interacts with different Agent frameworks
- **Prevents**: Framework lock-in; difficulty supporting multiple frameworks; direct dependency on framework APIs in core scanners
- **Rule**: Define unified `FrameworkAdapter` interface. Each framework gets concrete adapter (LangGraphAdapter, AgentScopeAdapter, etc.). All scanners receive adapter instance, remain framework-agnostic. MVP implements LangGraphAdapter only; additional adapters added in future sprints.

### AD-7 — CLI Interface Design
- **Binds**: Command structure, parameter options, output behavior
- **Prevents**: Unclear interface; non-standard parameters; poor CI/CD integration
- **Rule**: Single `apcv validate` command. Required params: `--agent`, `--policy`. Optional: `--output`, `--format` (json/sarif/html), `--fail-on` (score threshold), `--workers` (concurrency), `--timeout`. Always outputs table to stdout and JSON to `.apcv/reports/`. Exit code: 0=PASS, 1=FAIL, 2=error.

### AD-8 — Output Format and Reporting
- **Binds**: What CLI outputs and what gets saved for audit
- **Prevents**: Lost information; unclear compliance status; difficult historical analysis
- **Rule**: Terminal output = human-readable table (tool SBOM, violations, compliance score). Automatically saved to `.apcv/reports/{timestamp}_{agent_name}.json` = full execution trace + metadata. Additional formats (SARIF, PDF, HTML) generated on demand via `--format` flag.

### AD-9 — Policy DSL Design
- **Binds**: Policy declaration syntax and structure
- **Prevents**: Ambiguous policy definitions; difficult to compose reusable policies
- **Rule**: YAML-based declarative format with five sections: `metadata`, and four `boundaries` (tool, runtime, network, identity). Each boundary specifies `allowed` and `denied` lists plus constraints (path patterns, domain whitelists, etc.).

### AD-10 — Web UI Architecture
- **Binds**: Web interface structure and data model
- **Prevents**: Tight coupling between backend and frontend; difficult to extend with new visualizations
- **Rule**: Backend: FastAPI + file-based storage (.apcv/reports/). Frontend: React/Vue dashboard consuming backend APIs. Dashboard shows: Agent list with compliance cards, historical trends, policy editor, execution timeline, report export. MVP single-process deployment; backend and frontend can separate in future.

### AD-11 — Error Handling and Logging
- **Binds**: How errors are handled and logged across all layers
- **Prevents**: Silent failures; difficult debugging; lost error context
- **Rule**: Three-tier error handling: silent failures (scanner error → log + continue), non-fatal (probe timeout → WARNING flag + continue), fatal (invalid policy → stop immediately + exit 2). All logs written to `.apcv/logs/{timestamp}.log` with structured JSON format.

## Consistency Conventions

| Concern | Convention |
|---------|-----------|
| **Naming** | Classes: PascalCase (ToolScanner, ConformanceDecisionEngine). Functions/vars: snake_case. Files: lowercase_with_underscores.py. |
| **Data Formats** | SBOM: JSON Schema 2020-12. Reports: UTF-8 JSON. Logs: JSON Lines (one JSON object per line). |
| **Configuration** | Policy files: YAML (human readable, version-controllable). Runtime config: env vars + CLI flags (CLI flags override env vars). |
| **State Management** | Immutable data structures where possible. State mutations logged explicitly. No shared mutable state between scanners. |
| **Error Handling** | Exceptions propagated with context (filename, line number, operation name). Custom exceptions inherit from base `APCVException`. All exceptions logged before re-raising. |
| **Asynchronous** | Probe execution: concurrent (use ThreadPoolExecutor or asyncio). Tool call interception: must support both sync and async tools via wrapt + asyncio hooks. |

## Stack

| Name | Version | Purpose |
|------|---------|---------|
| Python | 3.9+ | Language |
| LangGraph | 0.1.0+ | Agent framework (MVP) |
| wrapt | 1.14+ | Parameter interception |
| Docker Python SDK | 6.0+ | Probe sandbox isolation |
| OPA/Rego | 0.45+ | Policy evaluation (primary) or AgenticContract for MVP |
| FastAPI | 0.100+ | Web UI backend |
| React | 18+ | Web UI frontend |
| Pydantic | 2.0+ | Data validation |
| pytest | 7.0+ | Testing |

## Structural Seed

```
apcv/
├── core/                          # Core engine
│   ├── scanners/
│   │   ├── base.py               # Scanner abstract interface
│   │   ├── tool_scanner.py
│   │   ├── runtime_scanner.py
│   │   ├── network_scanner.py
│   │   └── identity_scanner.py
│   │
│   ├── validators/
│   │   ├── base.py               # Validator abstract interface
│   │   ├── tool_validator.py
│   │   ├── runtime_validator.py
│   │   ├── network_validator.py
│   │   └── identity_validator.py
│   │
│   ├── decision/
│   │   ├── conformance_engine.py  # ConformanceDecisionEngine
│   │   └── scoring.py            # Scoring logic
│   │
│   ├── infrastructure/
│   │   ├── probe_executor.py     # Docker-based probe execution
│   │   ├── parameter_tracer.py   # wrapt-based interception
│   │   ├── probe_library.py      # Probe templates
│   │   └── policy_engine.py      # Policy evaluation (OPA/Rego wrapper)
│   │
│   └── frameworks/
│       ├── adapter.py            # FrameworkAdapter abstract interface
│       ├── langgraph_adapter.py  # LangGraphAdapter (MVP)
│       └── agentscope_adapter.py # AgentScopeAdapter (future)
│
├── cli/
│   ├── main.py                   # apcv validate command entry point
│   ├── output.py                 # Table formatting, report generation
│   └── config.py                 # CLI argument parsing
│
├── web/
│   ├── backend/
│   │   ├── app.py               # FastAPI application
│   │   ├── api/
│   │   │   ├── reports.py
│   │   │   ├── policies.py
│   │   │   └── agents.py
│   │   └── models.py            # Pydantic models
│   │
│   └── frontend/
│       ├── src/
│       │   ├── components/
│       │   ├── pages/
│       │   └── App.tsx
│       └── package.json
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── docs/
│   ├── architecture/
│   ├── api/
│   ├── user_guide/
│   └── examples/
│
├── config/
│   └── probe_library.yaml        # Probe templates
│
└── requirements.txt
```

## Capability → Architecture Map

| Capability/Area | Lives in | Governed by |
|---|---|---|
| Discover Agent tools across frameworks | Scanner layer + FrameworkAdapter | AD-2, AD-6 |
| Intercept tool calls and capture parameters | ParameterTracer | AD-11 (async support), core design |
| Generate policy-relative probes for four boundaries | ProbeLibrary + Validators | AD-4 |
| Execute probes in isolated sandbox | ProbeExecutor | Docker SDK, security via AD-11 |
| Evaluate execution trace against policy | PolicyEngine | OPA/Rego or AgenticContract, AD-9 |
| Compute compliance score across dimensions | ConformanceDecisionEngine | AD-5, scoring algorithm |
| CLI interface for CI/CD integration | cli/main.py | AD-7, AD-8 |
| Web UI dashboard and policy editor | web/backend + frontend | AD-10 |
| Persist verification results for audit | .apcv/reports/ | AD-3, AD-8 |
| Log all operations for debugging | .apcv/logs/ | AD-11 |

## Deferred

- **Multi-framework support beyond LangGraph**: AgentScope, AutoGen adapters deferred to Sprint 2. Architecture supports via Adapter Pattern (AD-6).
- **LLM-assisted Probe generation**: Currently static probe library (30-50 probes). Dynamic/adversarial probe generation deferred to Sprint 2. Reference: Garak framework integration.
- **Advanced policy features**: Conditional rules (e.g., "if A then B"), temporal constraints, delegation chains deferred to Sprint 2.
- **Runtime Monitoring Mode**: MVP is pre-deployment validation only. Continuous runtime monitoring deferred to Sprint 2+.
- **Compliance Reporting Automation**: Manual SBOM/audit proof generation in MVP. Automated compliance mapping (NIST, EU AI Act, ISO) deferred to Sprint 2.
- **High-security sandboxing**: MVP uses Docker (OS-level isolation). gVisor (syscall filtering), Firecracker (micro-VM) deferred to Sprint 2 for high-risk agents.
- **Horizontal scaling**: MVP is single-process. Distributed execution and cloud deployment deferred to production phase.
