# Architecture Diagrams

## System Architecture (High-Level)

```
┌─────────────────────────────────────────────────────────────────┐
│                        Application Layer                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  CLI Tool              Web UI (React/FastAPI)                    │
│  ┌──────────────────┐  ┌──────────────────────────────────────┐ │
│  │ apcv validate    │  │ Dashboard                            │ │
│  │ --agent X        │  │ ├─ Agent List (compliance scores)   │ │
│  │ --policy Y       │  │ ├─ Policy Editor (YAML)             │ │
│  │ --output json    │  │ ├─ Execution Timeline               │ │
│  └──────────────────┘  │ └─ Report Generator (PDF/JSON)      │ │
│  Output: JSON, SARIF   └──────────────────────────────────────┘ │
│                                                                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Core Engine Layer                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Tool Discovery       Probe Generation    Execution Engine      │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐  │
│  │ AST Parser     │  │ Rule Library   │  │ Docker Runner    │  │
│  │ Runtime        │  │ (20-30 rules)  │  │ Parameter Tracer │  │
│  │ Interceptor    │  │ Policy-Relative│  │ (wrapt wrapper)  │  │
│  │                │  │ Generation     │  │                  │  │
│  └────────────────┘  └────────────────┘  └──────────────────┘  │
│                                                                   │
│  Conformance Checker    Policy Validator                         │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Compare SBOM vs Execution Trace                           │ │
│  │ Generate Diff (violations + severity)                     │ │
│  │ Apply Policy Rules → PASS/FAIL Decision                   │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Adapter & Framework Layer                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Framework-Agnostic Interface                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ ToolRegistry    ToolInterceptor    ParameterTracer      │  │
│  │ IsolatedExecutor    FrameworkAdapter                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  LangGraph Adapter (MVP)    AgentScope Adapter (Sprint 2)       │
│  AutoGen Adapter (Sprint 3) ...                                  │
│                                                                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Framework Layer                               │
├─────────────────────────────────────────────────────────────────┤
│ LangGraph │ AgentScope │ AutoGen │ Custom Agents                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow: Complete Validation Cycle

```
┌──────────────────┐
│  Agent Code      │
│  + Policy YAML   │
└────────┬─────────┘
         │
         ▼
    ┌────────────────────────────────────┐
    │  PHASE 1: Static Discovery         │
    │  ┌──────────────────────────────┐  │
    │  │ 1. Parse Agent code (AST)    │  │
    │  │ 2. Extract @tool decorators  │  │
    │  │ 3. Find runtime capabilities │  │
    │  │ 4. Detect sub-agents         │  │
    │  └──────────────────────────────┘  │
    │           ↓                         │
    │  Tool SBOM (JSON)                   │
    │  ├─ tool_name, signature            │
    │  ├─ source (code/runtime/mcp)       │
    │  └─ parameters (name, type)         │
    └────────┬─────────────────────────────┘
             │
             ▼
    ┌────────────────────────────────────┐
    │  PHASE 2: Probe Generation         │
    │  ┌──────────────────────────────┐  │
    │  │ 1. Load Declared Policy      │  │
    │  │ 2. Select relevant rules     │  │
    │  │ 3. Generate policy-relative  │  │
    │  │    boundary-crossing tests   │  │
    │  └──────────────────────────────┘  │
    │           ↓                         │
    │  Probe Suite (20-30 tests)          │
    │  ├─ probe_fs_1, probe_fs_2, ...     │
    │  ├─ probe_tool_1, probe_tool_2, ... │
    │  └─ probe_priv_1, ...               │
    └────────┬─────────────────────────────┘
             │
             ▼
    ┌────────────────────────────────────┐
    │  PHASE 3: Dynamic Execution        │
    │  (Docker Container Isolation)      │
    │  ┌──────────────────────────────┐  │
    │  │ For each probe:              │  │
    │  │  1. Spawn Docker container   │  │
    │  │  2. Inject wrapt tracer      │  │
    │  │  3. Run probe (tool call)    │  │
    │  │  4. Capture execution trace  │  │
    │  │  5. Clean up container       │  │
    │  └──────────────────────────────┘  │
    │           ↓                         │
    │  Execution Trace (JSONL)            │
    │  ├─ timestamp                       │
    │  ├─ probe_id                        │
    │  ├─ tool_called                     │
    │  ├─ args (parameters)               │
    │  ├─ result (success/error)          │
    │  └─ policy_violation (Y/N)          │
    └────────┬─────────────────────────────┘
             │
             ▼
    ┌────────────────────────────────────┐
    │  PHASE 4: Conformance Check        │
    │  ┌──────────────────────────────┐  │
    │  │ 1. Compare SBOM vs Trace     │  │
    │  │ 2. Find undeclared tools     │  │
    │  │ 3. Check parameter ranges    │  │
    │  │ 4. Apply policy rules        │  │
    │  └──────────────────────────────┘  │
    │           ↓                         │
    │  Violations & Diff Report           │
    │  ├─ tool, severity, reason          │
    │  ├─ parameter violations            │
    │  ├─ hidden capabilities             │
    │  └─ compliance_score (0-100)        │
    └────────┬─────────────────────────────┘
             │
             ▼
    ┌────────────────────────────────────┐
    │  PHASE 5: Policy Validation        │
    │  ┌──────────────────────────────┐  │
    │  │ Apply severity rules:        │  │
    │  │ - critical violation → FAIL  │  │
    │  │ - warning → WARN             │  │
    │  │ - info → PASS (if no critical)│ │
    │  └──────────────────────────────┘  │
    │           ↓                         │
    │  VERDICT: PASS | FAIL | WARN        │
    │  + Detailed Report (JSON/PDF/HTML) │
    └────────┬─────────────────────────────┘
             │
             ▼
    ┌──────────────────────────┐
    │  Output & Deployment Gate│
    │  ├─ CI/CD: exit 0 or 1   │
    │  ├─ Report: PDF/JSON/HTML│
    │  ├─ Audit Log: traceable │
    │  └─ Dashboard: updated   │
    └──────────────────────────┘
```

---

## Four-Layer Tool Discovery Model

```
Agent Codebase
  │
  ├─ Layer 1: MCP Tools
  │  ├─ Load MCP Server manifest.json
  │  ├─ Parse declared tools
  │  └─ Extract tool signatures
  │
  ├─ Layer 2: Framework-Defined Tools
  │  ├─ AST parse: find @tool decorators
  │  ├─ Extract function signature (args, return type)
  │  ├─ Find parameter constraints (type hints, docstrings)
  │  └─ Build ToolRegistry
  │
  ├─ Layer 3: Runtime Built-in Capabilities
  │  ├─ Detect framework implicit tools (e.g., code_execute, file_access)
  │  ├─ Scan for common patterns (os.system, subprocess, etc.)
  │  ├─ Identify framework-provided utilities
  │  └─ Add to Tool SBOM (marked as "runtime-implicit")
  │
  └─ Layer 4: Sub-Agent Delegation
     ├─ Find sub-agent instantiation
     ├─ Recursively apply discovery to sub-agent code
     ├─ Mark inherited capabilities
     └─ Track agent hierarchy
             │
             ▼
        ┌──────────────────┐
        │  Unified Tool    │
        │  SBOM (JSON)     │
        │  100% complete   │
        │  capability list │
        └──────────────────┘
```

---

## Parameter Tracing & Wrapt Integration

```
Agent Code
  │
  ├─ Tool Definition
  │  │
  │  def read_file(path: str) → str:
  │      """Read file contents"""
  │      return open(path).read()
  │
  │
  ├─ Instrumentation Layer (wrapt)
  │  │
  │  @trace_parameters  ◄─── Decorator injected at runtime
  │  def read_file(path: str) → str:
  │      trace_record = {
  │          "timestamp": now,
  │          "function": "read_file",
  │          "params": {"args": [path]},
  │      }
  │      try:
  │          result = original_read_file(path)
  │          trace_record["result"] = result
  │          return result
  │      finally:
  │          TRACE_LOG.append(trace_record)
  │
  │
  └─ Execution in Docker Container
     │
     Trace Output (JSONL)
     {
       "timestamp": "2026-09-12T10:00:01.234Z",
       "tool": "read_file",
       "args": ["/etc/passwd"],
       "result": "success",
       "policy_violation": true,
       "violation_reason": "path not in allowed_paths"
     }
     
     Traces are collected & matched against Policy
```

---

## Multi-Container Parallel Execution

```
Probe Suite (20-30 probes)
  │
  ├─ Probe 1 ────┐
  ├─ Probe 2 ────┤
  ├─ Probe 3 ────┼──► ThreadPoolExecutor(max_workers=4)
  ├─ Probe 4 ────│
  └─ ...         │
     └─ Probe N ─┘
        │
        ▼
   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
   │  Docker 1        │  │  Docker 2        │  │  Docker 3        │  │  Docker 4        │
   │ (probe_fs_1)     │  │ (probe_fs_2)     │  │ (probe_tool_1)   │  │ (probe_priv_1)   │
   │                  │  │                  │  │                  │  │                  │
   │ Isolated FS      │  │ Isolated FS      │  │ Isolated FS      │  │ Isolated FS      │
   │ No network       │  │ No network       │  │ No network       │  │ No network       │
   │ 30s timeout      │  │ 30s timeout      │  │ 30s timeout      │  │ 30s timeout      │
   │ Trace recorded   │  │ Trace recorded   │  │ Trace recorded   │  │ Trace recorded   │
   └──────────────────┘  └──────────────────┘  └──────────────────┘  └──────────────────┘
        │                     │                     │                     │
        ▼                     ▼                     ▼                     ▼
   Trace 1                Trace 2                Trace 3                Trace 4
   
   Aggregated Results
   ├─ All traces collected
   ├─ Violations summarized
   ├─ Compliance score calculated
   └─ Report generated
```

---

## CLI to CICD Integration

```
Developer's Git Workflow
  │
  git commit → git push
  │
  ▼
GitHub Actions (or GitLab CI)
  │
  stages:
    - test
    - security  ◄─── APCV runs here
    - deploy
  
  ┌─────────────────────────────────────┐
  │ Conformance Check Stage             │
  ├─────────────────────────────────────┤
  │                                     │
  │ apcv validate \                     │
  │   --agent langgraph:./agent.py \   │
  │   --policy ./policy.yaml \          │
  │   --output sarif > results.sarif    │
  │                                     │
  │ Exit code: 0 (PASS) or 1 (FAIL)     │
  │                                     │
  │ Post-action: Comment on PR          │
  │ "✅ Agent conforms to policy"       │
  │ or                                  │
  │ "❌ Agent violates policy:          │
  │  - Undeclared bash tool"            │
  └─────────────────────────────────────┘
         │
         ▼
    PASS → Proceed to deploy
    FAIL → Block merge, notify developer
```

---

## Compliance Report Output

```
APCV Validation Report
├─ Metadata
│  ├─ Agent: github-assistant
│  ├─ Policy: github-readonly (v2)
│  ├─ Timestamp: 2026-09-12T14:30:00Z
│  └─ Validator: apcv/0.1.0
│
├─ Executive Summary
│  ├─ Verdict: ❌ FAIL
│  ├─ Compliance Score: 72/100
│  └─ Critical Violations: 2
│
├─ Tool SBOM
│  ├─ Total tools discovered: 15
│  ├─ Declared in policy: 8
│  ├─ Undeclared found: 2
│  └─ Table: [tool_name, source, status]
│
├─ Policy Violations
│  ├─ Violation 1: Undeclared tool 'bash_execute'
│  │  ├─ Severity: Critical
│  │  ├─ Count: 3 calls detected
│  │  └─ Remediation: Remove bash_execute or add to declared_tools
│  │
│  └─ Violation 2: Parameter out of range
│     ├─ Tool: read_file
│     ├─ Argument: '/etc/passwd'
│     ├─ Policy: '^/data/.*'
│     ├─ Severity: High
│     └─ Remediation: Update policy or fix agent code
│
├─ Execution Trace (sample)
│  ├─ Call 1: read_file('/data/repo/README.md') ✅ PASS
│  ├─ Call 2: http_get('https://api.github.com/repos') ✅ PASS
│  ├─ Call 3: bash_execute('ls -la /etc') ❌ FAIL (undeclared)
│  └─ ...
│
├─ Audit Trail
│  ├─ Tester: ci-system@github.com
│  ├─ Run ID: apcv-20260912-143000
│  └─ Signature: [SHA256 hash for chain-of-custody]
│
└─ Recommended Actions
   ├─ Option A: Modify agent code (remove bash calls)
   ├─ Option B: Extend policy (justify why bash is needed)
   └─ Contact: security-team@company.com for approval
```
