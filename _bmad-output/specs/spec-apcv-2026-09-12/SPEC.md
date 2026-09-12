---
title: Agent Policy Conformance Validator (APCV)
date: 2026-09-12
project: apcv
companions:
  - probe-rules.md
  - policy-dsl-schema.md
  - architecture-diagrams.md
sources:
  - ../../../brainstorming/brainstorm-ai-agent-containment-2026-09-12/brainstorm-summary.md
  - ../../../research-outputs/PROJECT-PLAN-FINAL-2026-09-12.md
assumptions:
  - LangGraph tool surface is statically parseable via AST decorators with >95% accuracy
  - Parameter-level tracing suffices for MVP conformance verification
  - Declared policy (YAML) is developer responsibility; no auto-inference from IAM/IaC in MVP
  - Docker is available in deployment environments
  - Compliance scope focuses on audit trail + deterministic verification, not behavioral guarantees
open_questions:
  - What's the acceptable false-positive rate for Probe tests?
  - Should Policy DSL use Rego/OPA (industry standard, steep learning curve) or custom YAML (simpler)?
  - How to prevent execution cross-pollution in multi-tenant SaaS deployment?
---

# Agent Policy Conformance Validator (APCV)

## Why

Enterprises deploying AI Agents apply permission restrictions and isolation policies, then assume "the Agent is restricted." But they cannot answer: **Are these restrictions actually enforced? Is there a gap between declared policy and actual capability?**

This confidence gap blocks production deployment. HuggingFace incident and industry data (65% of enterprises experienced Agent security incidents in 2026) confirm the problem is real: declared resource access ranges often diverge from actual access ability.

**Market position**: No specialized "Agent conformance validator" exists. Competitors (Microsoft Agent Governance Toolkit, Snyk, SIEM) are too broad or don't handle Agent-specific dynamic capabilities. EU AI Act (effective 2026) creates legal compliance pressure. DevOps teams need a pre-deployment CI/CD gate, not runtime enforcement.

## Capabilities

### CAP-1: Tool Surface Discovery (4-Layer)
**Intent**: Discover the complete tool surface available to an Agent across all layers.  
**Success**: Identify ≥99% of tools (MCP-defined, framework-defined, runtime built-in, sub-agent inherited) with accuracy >95% on LangGraph; processing time <10s.

### CAP-2: Policy-Relative Probe Generation
**Intent**: Automatically generate boundary-crossing test cases tailored to the Agent's declared policy, not a fixed resource list.  
**Success**: For any policy, generate ≥15 probes that test the policy's explicit edges (e.g., if policy says "only access /data", probe tests access to /etc, /home, /var); each probe has clear PASS/FAIL semantics.

### CAP-3: Isolated Probe Execution & Parameter Tracing
**Intent**: Execute probes in a sandboxed environment and record every tool invocation with parameters.  
**Success**: Run 20–30 probes in <2 min total; record 100% of tool calls; parameter tracing overhead <1%; Docker-isolated (read-only FS, no network, <30s timeout per probe).

### CAP-4: Conformance Check & Diff Report
**Intent**: Compare execution trace against declared policy; produce auditable PASS/FAIL verdict and violation details.  
**Success**: Output machine-readable diff (JSON), human-readable report (Markdown), and compliance_score (0–100); every violation includes tool name, parameters, severity, remediation hint.

### CAP-5: CLI & Web UI Dual Interface
**Intent**: Serve DevOps (CLI for CI/CD automation) and security teams (Web UI for policy mgmt + visualization).  
**Success**: `apcv validate --agent <path> --policy <yaml>` works in CI/CD pipelines; Web dashboard shows Agent list, compliance scores, execution timeline, policy editor; both accept/output JSON for integration.

### CAP-6: Regulatory-Grade Compliance Reports
**Intent**: Generate evidence-ready reports suitable for GDPR/SOX/ISO27001 audits.  
**Success**: PDF + JSON exports include execution trace, all probe results, policy declarations, timestamps, signatures (for chain-of-custody); can prove "Agent was tested against declared policy on date X with result Y."

### CAP-7: LangGraph End-to-End Support
**Intent**: Full lifecycle support for LangGraph Agents (discovery, probe gen, execution, reporting).  
**Success**: Discover all @tool decorators and runtime capabilities; generate policy-relative probes; execute and trace; produce verdict in <2 min E2E; no manual code patching required.

## Constraints

### Design Constraints

**Four-Layer Tool Fragmentation**: Agent capabilities scatter across MCP manifests (most visible), framework code (@tool decorators), runtime implicit tooling, and sub-agent delegation. Unified Tool SBOM is the single source of truth; any layer omission = false confidence in policy verification.

**Policy-Relative Generation, Not Fixed Heuristics**: Probe content must vary by declared policy (agent declaring "only read_file" gets different probes than one declaring "full filesystem"). Determinism over adaptability: use parameter-level tracing (wrapt instrumentation), not LLM-driven probes.

**Deterministic Verification for Audit**: Compliance evidence must be reproducible and non-subjective. Parameter traces (what was called + what arguments) are facts; behavioral interpretation is not. Traces recorded by standard library, not custom side-effect monitors.

**Isolated Execution, Zero Cross-Pollution**: Each Probe runs in a clean Docker container; no state leakage between tests; consistent environment ensures traces are comparable.

### Implementation Constraints

**MVP: LangGraph Only**: Framework support limited to LangGraph in 3-week sprint. Architecture must be framework-agnostic (adapter pattern) to permit AgentScope, AutoGen, etc. in later sprints without redesign.

**Probe Library: Hardcoded Rules (MVP)**: 20–30 hardcoded probes covering filesystem access, tool invocation, privilege escalation, network categories. LLM-assisted probe generation deferred to "Could Have" (post-MVP).

**Developer-Declared Policy**: Developers write Declared Policy as YAML; no auto-inference from IAM/IaC in MVP. This matches DevSecOps convention (container security policies are human-authored) and avoids false IAM-to-Agent mappings.

**Performance Target**: Complete validation <2 min (tool discovery + probe generation + execution + reporting). Latency budget: static scan 10s, probe gen 5s, execution 60s, reporting 5s.

## Non-Goals

- **Runtime enforcement**: APCV validates; deployment platform enforces. Out of scope.
- **Prompt injection detection**: Separate security layer; not a Probe concern.
- **Adversarial Agent deep audit**: LLM-based multi-turn probing is non-deterministic. Marked "Could Have" for later. MVP uses deterministic parameter-level tests only.
- **Multi-framework MVP**: LangGraph only; others in Sprint 2+.
- **IAM/IaC auto-inference**: Policy declaration is human responsibility (MVP). Reverse IAM-to-policy mapping is a "Could Have" future direction.
- **Sandbox side-effect tracking**: Filesystem writes, network connections beyond parameter tracing are not captured. Parameter calls are sufficient for policy conformance.

## Success Signal

**Technical**: Tool discovery accuracy >95%; Probe execution <2 min; tracing overhead <1%; Docker isolation with zero cross-test contamination; compliance_score aligns with manual audit verdicts.

**Product**: DevOps runs `apcv validate` in CI/CD pre-merge; receives PASS/FAIL + auditable diff in <2 min; can confidently promote Agent to production OR identify capability gaps for remediation without manual security review.

**Market**: Zero existing competitive products in this niche; enterprise DevOps teams adopt within 4 weeks (low onboarding friction); positive signals from 3+ pilot customers (internal + external); EU AI Act compliance pathway clear.

**Regulatory**: Generated reports pass compliance review (auditors accept parameter traces as evidence); chain-of-custody (who ran what test when) is preserved and machine-verifiable.

---

## Next Steps

1. **Validate Companions**: Create `probe-rules.md` (20–30 rule catalog), `policy-dsl-schema.md` (YAML spec), `architecture-diagrams.md` (system diagrams).
2. **Story Breakdown**: Decompose MVP into 6–8 independently shippable stories (Week 1: discovery + policy DSL; Week 2: probe gen + execution; Week 3: CLI + UI).
3. **Begin Sprint 1**: Framework scaffolding, AST parser PoC for LangGraph @tool extraction.
