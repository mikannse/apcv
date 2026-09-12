# Story 2-3: Conformance Check & Diff Report Generation

**Story Key**: 2-3-conformance-check  
**Epic**: Week 2: Verdict & Reporting  
**Status**: ready-for-dev | **Priority**: 🔴 Critical | **Estimate**: 3 days | **Dependencies**: story-2-2 (isolated execution)

## Story Overview
Implement conformance checker (compares SBOM vs traces), violation detection, and policy validation rules. Generate detailed diff reports and compliance scores.

**Spec Checkpoint**: ✅ Completes CAP-4 (Conformance Check & Diff Report)

## User Story
**As a** security engineer | **I want** detailed reports showing exactly which policies the Agent violates | **So that** I can guide developers to fix their code or update policies appropriately

## Acceptance Criteria
- [ ] AC-1: ConformanceChecker compares Tool SBOM vs Execution Trace
- [ ] AC-2: Violation detection: undeclared tools, parameter violations, hidden capabilities
- [ ] AC-3: Compliance score algorithm (0-100 based on violation severity)
- [ ] AC-4: Policy validator: apply rule engine, determine PASS/FAIL/WARN
- [ ] AC-5: Diff report (JSON + Markdown): violations, remediation hints, audit trail
- [ ] AC-6: Unit & integration tests: various violation scenarios
- [ ] AC-7: Report exports: JSON, Markdown, HTML formats

## Technical Requirements

### Architecture Decisions
- **Conformance Engine** (AD-5): Single unified engine, weighted scoring
- **Violation Detection**: tool, parameter, hidden capability checks
- **Report Generation**: multiple formats (JSON, Markdown, HTML)

### Key Classes
```python
class ConformanceChecker:
    def check(self, sbom, traces, policy) -> ConformanceResult
    def detect_violations(self, sbom, traces, policy) -> List[Violation]
    def compute_compliance_score(self, violations) -> int

class ConformanceResult(BaseModel):
    verdict: str  # PASS, FAIL, WARN
    compliance_score: int  # 0-100
    violations: List[Violation]
    execution_trace: List[TraceEntry]
    recommendations: List[str]

class Violation(BaseModel):
    type: str  # tool, parameter, hidden_capability, rate_limit
    severity: str  # critical, high, medium, low
    description: str
    remediation: str
```

## Tasks (7 tasks, 3 days)

### ✅ Task 1: Violation Detection Logic
- [ ] 1.1: Tool violations (undeclared, denied, injection)
- [ ] 1.2: Parameter violations (type, range, pattern)
- [ ] 1.3: Hidden capability detection

### ✅ Task 2: Compliance Score Algorithm
- [ ] 2.1: Severity weighting (critical=10, high=5, medium=2, low=1)
- [ ] 2.2: Formula: 100 - sum(weights)
- [ ] 2.3: Bounds: 0 ≤ score ≤ 100

### ✅ Task 3: ConformanceChecker Implementation
- [ ] 3.1: Compare SBOM vs traces
- [ ] 3.2: Apply policy rules
- [ ] 3.3: Generate results

### ✅ Task 4: Diff Report Generation
- [ ] 4.1: JSON format with metadata
- [ ] 4.2: Markdown human-readable format
- [ ] 4.3: HTML export

### ✅ Task 5: Remediation Suggestions
- [ ] 5.1: Generate actionable hints
- [ ] 5.2: Link to documentation
- [ ] 5.3: Code fix suggestions

### ✅ Task 6: Policy Validator Integration
- [ ] 6.1: Apply policy rules engine
- [ ] 6.2: Determine PASS/FAIL/WARN verdict
- [ ] 6.3: Audit trail logging

### ✅ Task 7: Testing & Documentation
- [ ] 7.1: Unit tests for each violation type
- [ ] 7.2: Integration tests with real violations
- [ ] 7.3: Documentation and examples

## Status: ready-for-dev
