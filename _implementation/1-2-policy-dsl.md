# Story 1-2: Policy DSL & Validation Engine

**Story Key**: 1-2-policy-dsl  
**Epic**: Week 1: Policy Foundation  
**Status**: ready-for-dev  
**Priority**: 🔴 Critical  
**Estimate**: 2.5 days  
**Created**: 2026-09-12  
**Dependencies**: story-1-1 (tool discovery) must be complete first

---

## Story Overview

Design and implement Policy DSL (YAML schema), validator, and error reporting. This story delivers the policy declaration layer that enables all downstream validation work (CAP-2, CAP-4).

**Spec Checkpoint**: ✅ Completes policy declaration layer (input to CAP-2 and CAP-4)

---

## User Story

**As a** security engineer  
**I want** to declare Agent policy constraints in a standard YAML format  
**So that** I can version control policies and integrate them into CI/CD

---

## Acceptance Criteria

### AC-1: Valid Policy YAML Parsing
- [ ] Valid policy YAML parses without error
- [ ] All required fields recognized (metadata, boundaries)
- [ ] Optional fields have sensible defaults
- [ ] YAML structure matches schema spec (policy-dsl-schema.md)

### AC-2: Clear Error Messages
- [ ] Invalid policy produces clear, actionable error message
- [ ] Error includes: field name, expected type, actual value, suggestion
- [ ] Error message points to line number in YAML file
- [ ] User can fix error without needing to read source code

### AC-3: Multi-Agent Policy Application
- [ ] Policy can be applied to multiple Agents
- [ ] Policy is reusable (not tied to single agent)
- [ ] Policy version tracking supported (optional version field)
- [ ] Policy composition possible (inherit from base policy)

### AC-4: Complete Constraint Support
- [ ] Schema supports all constraint types:
  - [ ] Tools: allowed_tools, denied_tools
  - [ ] Filesystem: allowed_paths, denied_paths, read_only
  - [ ] Network: network_enabled, allowed_domains, denied_domains
  - [ ] Parameters: parameter_constraints (type checks, value ranges)
  - [ ] Rate limits: calls_per_minute, calls_per_hour, concurrent_limit
  - [ ] Privilege: privilege_level (user, admin, root), no_sudo
  - [ ] Compliance: gdpr_compliant, sox_compliant, iso27001_compliant
  - [ ] Environment: allowed_env_vars, denied_env_vars

### AC-5: Testing & Coverage
- [ ] Unit tests for PolicyValidator (coverage >80%)
- [ ] Tests for valid policies (passes as expected)
- [ ] Tests for invalid policies (rejects with clear error)
- [ ] Tests for edge cases (empty policy, all constraints, none set)
- [ ] Integration tests: 3-5 reference policies (read-only, github-api, internal-admin)

### AC-6: IDE Integration Support
- [ ] JSON schema export (`.schema.json`) for VS Code autocomplete
- [ ] JSON schema endpoint mockup (for future SaaS version)
- [ ] Schema documentation with examples
- [ ] Policy template generator (scaffold new policies)

---

## Technical Requirements

### Architecture Decisions (Must Follow)

**Policy Engine** (AD-9):
- YAML-based declarative format with five sections: `metadata` and four `boundaries` (tool, runtime, network, identity)
- Each boundary specifies `allowed` and `denied` lists plus constraints
- DO NOT use JSON or TOML — YAML is human-readable and version-controllable

**Policy Evaluation** (AD-3, AD-5):
- Policy is input to validators (story 2: probe generation)
- Policy is input to decision engine (story 2.3: conformance checking)
- DO NOT embed validation logic in policy parser — separation of concerns

**CLI Integration** (AD-7):
- Policy file passed to `apcv validate --policy <yaml>`
- Store policy SBOM alongside tool SBOM in `.apcv/sbom/`
- File: `.apcv/sbom/policy.json` (normalized policy for processing)

### Technology Stack

| Component | Technology | Version | Notes |
|-----------|-----------|---------|-------|
| Language | Python | 3.9+ | Type hints required |
| YAML Parsing | PyYAML | 6.0+ | Standard YAML library |
| Schema Validation | jsonschema | 4.0+ | JSON Schema validation |
| Data Models | Pydantic | 2.0+ | Type-safe models |
| Testing | pytest | 7.0+ | Unit and integration tests |

### Project Structure (Build on story-1-1)

```
apcv/
├── core/
│   ├── policy/                  # NEW: Policy DSL module
│   │   ├── __init__.py
│   │   ├── schema.py            # Pydantic models for policy schema
│   │   ├── validator.py         # PolicyValidator class
│   │   └── loader.py            # YAML→Policy loader
│   │
│   └── (previous from story-1-1)
│
├── tests/
│   ├── unit/
│   │   ├── test_policy_validator.py  # NEW
│   │   ├── test_policy_schema.py     # NEW
│   │   ├── test_policy_loader.py     # NEW
│   │   └── (previous from story-1-1)
│   │
│   ├── fixtures/
│   │   ├── policies/            # NEW: Test policies
│   │   │   ├── read_only.yaml
│   │   │   ├── github_api.yaml
│   │   │   ├── internal_admin.yaml
│   │   │   ├── invalid_policies/ # Invalid YAML for error testing
│   │   │   └── ...
│   │   │
│   │   └── (previous)
│   │
│   └── integration/
│       ├── test_policy_pipeline.py   # NEW
│       └── (previous)
│
├── docs/
│   ├── POLICY_DSL.md            # NEW: Policy DSL documentation
│   └── (previous)
│
└── (previous structure)
```

### Data Structures

**Policy Schema** (Pydantic models in `core/policy/schema.py`):

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class Metadata(BaseModel):
    name: str = Field(..., description="Policy name")
    version: str = Field(default="1.0", description="Policy version")
    description: str = Field(default="", description="Policy description")
    author: str = Field(default="", description="Policy author")
    tags: List[str] = Field(default_factory=list, description="Policy tags")

class ToolBoundary(BaseModel):
    allowed_tools: List[str] = Field(default_factory=list)
    denied_tools: List[str] = Field(default_factory=list)

class FilesystemBoundary(BaseModel):
    allowed_paths: List[str] = Field(default_factory=list)
    denied_paths: List[str] = Field(default_factory=list)
    read_only: bool = Field(default=False)

class NetworkBoundary(BaseModel):
    network_enabled: bool = Field(default=False)
    allowed_domains: List[str] = Field(default_factory=list)
    denied_domains: List[str] = Field(default_factory=list)

class ParameterConstraint(BaseModel):
    tool: str
    parameter: str
    allowed_values: Optional[List[str]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None  # Regex pattern

class ParameterBoundary(BaseModel):
    constraints: List[ParameterConstraint] = Field(default_factory=list)

class RateLimitBoundary(BaseModel):
    calls_per_minute: Optional[int] = None
    calls_per_hour: Optional[int] = None
    concurrent_limit: Optional[int] = None

class PrivilegeBoundary(BaseModel):
    privilege_level: str = Field(default="user", regex="^(user|admin|root)$")
    no_sudo: bool = Field(default=True)

class ComplianceBoundary(BaseModel):
    gdpr_compliant: bool = Field(default=False)
    sox_compliant: bool = Field(default=False)
    iso27001_compliant: bool = Field(default=False)

class EnvironmentBoundary(BaseModel):
    allowed_env_vars: List[str] = Field(default_factory=list)
    denied_env_vars: List[str] = Field(default_factory=list)

class Policy(BaseModel):
    metadata: Metadata
    boundaries: Dict[str, any] = Field(
        default_factory=lambda: {
            "tool": ToolBoundary(),
            "filesystem": FilesystemBoundary(),
            "network": NetworkBoundary(),
            "parameter": ParameterBoundary(),
            "rate_limit": RateLimitBoundary(),
            "privilege": PrivilegeBoundary(),
            "compliance": ComplianceBoundary(),
            "environment": EnvironmentBoundary(),
        }
    )
    
    class Config:
        validate_assignment = True
```

**YAML Policy Format** (example):

```yaml
metadata:
  name: "GitHub API Access Policy"
  version: "1.0"
  description: "Allow GitHub API access only, read-only filesystem"
  author: "security-team"
  tags: ["github", "read-only"]

boundaries:
  tool:
    allowed_tools:
      - github_search
      - github_get_issue
      - github_get_pr
    denied_tools: []
  
  filesystem:
    allowed_paths:
      - /tmp
      - /var/tmp
    denied_paths:
      - /etc
      - /root
    read_only: true
  
  network:
    network_enabled: true
    allowed_domains:
      - api.github.com
      - github.com
    denied_domains: []
  
  rate_limit:
    calls_per_minute: 60
    calls_per_hour: 3600
    concurrent_limit: 5
  
  privilege:
    privilege_level: "user"
    no_sudo: true
  
  compliance:
    gdpr_compliant: true
    sox_compliant: false
    iso27001_compliant: true
  
  environment:
    allowed_env_vars:
      - GITHUB_TOKEN
    denied_env_vars:
      - AWS_SECRET_ACCESS_KEY
```

### Error Handling

**PolicyValidator** should catch and report:

1. **Schema Errors**:
   - Missing required fields → "Missing required field: metadata.name"
   - Wrong data type → "Expected string for 'name', got int"
   - Invalid enum value → "Invalid privilege_level 'superuser' (must be 'user', 'admin', or 'root')"

2. **Business Logic Errors**:
   - Tool in both allowed and denied → "Tool 'search' appears in both allowed_tools and denied_tools (line 15)"
   - Path pattern invalid → "Invalid path pattern '/invalid[regex': regex error: ..."

3. **File Errors**:
   - File not found → "Policy file not found: /path/to/policy.yaml"
   - YAML syntax error → "YAML syntax error at line 12: unexpected ':' in mapping"

### Testing Standards

```python
# Unit: Test schema validation
def test_valid_policy_parses():
    policy_yaml = load_fixture("policies/read_only.yaml")
    policy = Policy.parse_yaml(policy_yaml)
    assert policy.metadata.name == "Read-Only Policy"

# Unit: Test error reporting
def test_invalid_policy_missing_name():
    invalid_yaml = "metadata: {}\nboundaries: {}"
    with pytest.raises(PolicyValidationError) as exc_info:
        Policy.parse_yaml(invalid_yaml)
    assert "metadata.name" in str(exc_info.value)

# Integration: Test with real policies
def test_reference_policies_load():
    for policy_file in Path("tests/fixtures/policies").glob("*.yaml"):
        policy = load_policy(policy_file)
        assert policy.metadata.name  # Has name
        assert len(policy.boundaries) > 0  # Has boundaries
```

### Libraries & Dependencies

**Core**:
- `pyyaml` (6.0+): YAML parsing
- `jsonschema` (4.0+): JSON schema validation for IDE integration
- `pydantic` (2.0+): Data validation and models

**Testing**:
- `pytest` (7.0+): Test runner
- `pytest-mock`: Mocking support

---

## Previous Story Intelligence

**story-1-1 (Framework Setup & Tool Discovery)**:
- Established project structure: `apcv/core/`, `apcv/cli/`, `apcv/tests/`
- Created Scanner interface: `core/scanners/base.py`
- Created FrameworkAdapter interface: `core/frameworks/adapter.py`
- Implemented LangGraphAdapter for tool discovery
- **For this story**: Reuse project structure, similar patterns for Policy module

**Key Patterns from story-1-1**:
- Use Pydantic for data validation (SBOM used it)
- Use pytest with fixtures for testing
- Separate parsing (loader.py) from validation (validator.py)
- Store normalized output in `.apcv/sbom/` (policy.json will join tool.json)

---

## Tasks & Subtasks

### ✅ Task 1: Define Policy Schema (Days 1-1.5)

- [ ] 1.1: Create `core/policy/schema.py` with Pydantic models
  - [ ] Metadata, ToolBoundary, FilesystemBoundary, NetworkBoundary models
  - [ ] ParameterConstraint, ParameterBoundary models
  - [ ] RateLimitBoundary, PrivilegeBoundary, ComplianceBoundary, EnvironmentBoundary
  - [ ] Root Policy model combining all boundaries
  
- [ ] 1.2: Add validation rules to models
  - [ ] Mutual exclusion: tool not in both allowed and denied
  - [ ] Path pattern validation (glob patterns)
  - [ ] Enum validation: privilege_level ∈ {user, admin, root}
  - [ ] Range validation: rate limits > 0
  
- [ ] 1.3: Export JSON schema for IDE integration
  - [ ] Generate `.schema.json` from Pydantic models
  - [ ] Schema supports VS Code autocomplete

- [ ] 1.4: Unit tests for schema
  - [ ] Test each model creates and validates
  - [ ] Test validation rules (mutual exclusion, patterns)
  - [ ] Test JSON schema export

**Definition of Done**:
- All Pydantic models pass type checking (mypy --strict)
- JSON schema exports without errors
- Unit tests pass (coverage >80%)

### ✅ Task 2: Implement Policy Loader (Days 1.5-2)

- [ ] 2.1: Create `core/policy/loader.py`
  - [ ] `load_policy(path)`: Load YAML file → Policy object
  - [ ] Handle file not found, YAML syntax errors
  - [ ] Return normalized Policy object (validated via Pydantic)
  
- [ ] 2.2: Handle YAML parsing edge cases
  - [ ] Multi-line YAML strings
  - [ ] YAML comments preservation (for error reporting)
  - [ ] YAML anchors & aliases (&, *)
  - [ ] YAML type coercion (strings that look like numbers)
  
- [ ] 2.3: Unit tests for loader
  - [ ] Test loads valid policies
  - [ ] Test handles file not found error
  - [ ] Test handles YAML syntax error
  - [ ] Test handles invalid policy structure

**Definition of Done**:
- Loader reads YAML and returns validated Policy
- Error messages include line numbers
- Coverage >80%

### ✅ Task 3: Implement Policy Validator (Days 2-2.5)

- [ ] 3.1: Create `core/policy/validator.py`
  - [ ] `PolicyValidator` class
  - [ ] `validate(policy)`: Returns ValidationResult (valid=bool, errors=[])
  - [ ] Custom error messages for each violation type
  
- [ ] 3.2: Implement validation rules
  - [ ] Schema validation (via Pydantic)
  - [ ] Business logic: mutual exclusions
  - [ ] Business logic: required field combinations
  - [ ] Business logic: allowed value ranges
  
- [ ] 3.3: Error reporting
  - [ ] Include file path, line number, field name
  - [ ] Include expected vs actual values
  - [ ] Include remediation suggestion
  - [ ] Example: "Tool 'search' appears in both allowed_tools (line 8) and denied_tools (line 12). Remove from one list."
  
- [ ] 3.4: Unit tests
  - [ ] Test validation pass for valid policies
  - [ ] Test validation fail with clear errors
  - [ ] Test each error type (schema, business logic)
  - [ ] Test edge cases

**Definition of Done**:
- PolicyValidator catches all invalid policies
- Error messages are clear and actionable
- Coverage >80%

### ✅ Task 4: Create Reference Policies (Days 2-2.5)

- [ ] 4.1: Create `tests/fixtures/policies/read_only.yaml`
  - [ ] Filesystem read-only
  - [ ] No network access
  - [ ] Limited tools
  
- [ ] 4.2: Create `tests/fixtures/policies/github_api.yaml`
  - [ ] GitHub API tools allowed
  - [ ] Network: github.com only
  - [ ] Rate limits applied
  
- [ ] 4.3: Create `tests/fixtures/policies/internal_admin.yaml`
  - [ ] All internal tools allowed
  - [ ] Internal filesystem access
  - [ ] No external network
  - [ ] Full privilege

- [ ] 4.4: Create invalid policy fixtures for error testing
  - [ ] Missing metadata
  - [ ] Tool in both allowed and denied
  - [ ] Invalid privilege_level
  - [ ] Malformed YAML

**Definition of Done**:
- 3-5 valid reference policies created
- 3-5 invalid policies for error testing
- All valid policies pass validation
- All invalid policies fail with clear errors

### ✅ Task 5: CLI Integration (Days 2.5)

- [ ] 5.1: Wire PolicyValidator into CLI
  - [ ] `apcv validate --policy <path>` loads and validates policy
  - [ ] Policy validation happens before tool discovery
  - [ ] Invalid policy → exit code 2 (error)
  
- [ ] 5.2: Save normalized policy SBOM
  - [ ] Path: `.apcv/sbom/policy.json`
  - [ ] Contents: normalized Policy object (JSON)
  - [ ] Update index.json to list policy.json
  
- [ ] 5.3: Test CLI
  - [ ] `apcv validate --agent agent.py --policy read_only.yaml`
  - [ ] Verify policy SBOM saved
  - [ ] Verify exit code 0 (success)

**Definition of Done**:
- Policy loads and validates in CLI
- Policy SBOM saved to `.apcv/sbom/policy.json`
- CLI integration tests pass

### ✅ Task 6: Documentation (Days 2.5)

- [ ] 6.1: Create `docs/POLICY_DSL.md`
  - [ ] Policy schema overview
  - [ ] Each boundary type explained
  - [ ] Example policies
  - [ ] Common patterns
  
- [ ] 6.2: Create policy template generator
  - [ ] `apcv policy-template` command (future)
  - [ ] Or: policy template files in `examples/`
  
- [ ] 6.3: Add JSON schema documentation
  - [ ] Each field explained
  - [ ] Type requirements
  - [ ] Valid value ranges

**Definition of Done**:
- Documentation clear and complete
- New user can write policy from scratch
- Examples cover all constraint types

### ✅ Task 7: Testing & Coverage (Throughout)

- [ ] 7.1: Integration tests
  - [ ] Load all reference policies
  - [ ] Validate each one
  - [ ] Verify SBOM output
  
- [ ] 7.2: Coverage reporting
  - [ ] Pytest coverage >80%
  - [ ] All error paths tested
  - [ ] All validation rules tested
  
- [ ] 7.3: Edge case tests
  - [ ] Empty policy (only metadata)
  - [ ] All constraints set
  - [ ] Conflicting constraints

**Definition of Done**:
- Coverage >80%
- All edge cases tested
- Integration tests pass

---

## File List

### New Files Created
```
apcv/
├── core/policy/__init__.py
├── core/policy/schema.py
├── core/policy/loader.py
├── core/policy/validator.py
├── tests/unit/test_policy_schema.py
├── tests/unit/test_policy_loader.py
├── tests/unit/test_policy_validator.py
├── tests/integration/test_policy_pipeline.py
├── tests/fixtures/policies/read_only.yaml
├── tests/fixtures/policies/github_api.yaml
├── tests/fixtures/policies/internal_admin.yaml
├── tests/fixtures/policies/invalid_policies/missing_metadata.yaml
├── tests/fixtures/policies/invalid_policies/conflicting_tools.yaml
├── docs/POLICY_DSL.md
└── examples/policy_template.yaml
```

---

## Change Log

- **2026-09-12** - Story created with comprehensive context

---

## Dev Notes for Implementation

### Implementation Strategy: Schema-First

1. **Define Pydantic models first** (schema-driven development)
2. **Write tests against models** (test the schema)
3. **Implement loader** (parse YAML → model)
4. **Implement validator** (add business rules beyond schema)
5. **Integrate with CLI** (wire it up)

### Key Considerations

#### 1. **Schema-Driven Validation**
Pydantic handles type checking automatically:
```python
from pydantic import BaseModel, validator

class ToolBoundary(BaseModel):
    allowed_tools: list[str] = []
    denied_tools: list[str] = []
    
    @validator('allowed_tools', 'denied_tools')
    def check_no_duplicates(cls, v):
        if len(v) != len(set(v)):
            raise ValueError("Duplicate tools not allowed")
        return v
    
    @root_validator
    def check_no_conflict(cls, values):
        allowed = set(values.get('allowed_tools', []))
        denied = set(values.get('denied_tools', []))
        if allowed & denied:  # Intersection
            raise ValueError(f"Tools in both allowed and denied: {allowed & denied}")
        return values
```

#### 2. **YAML Loading with Line Numbers**
Use PyYAML mark to track line numbers for error reporting:
```python
import yaml

def load_policy_with_lines(yaml_str):
    class LineTracker(yaml.Loader):
        pass
    
    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        # Get line number from node
        result = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node)
            value = loader.construct_object(value_node)
            result[key] = (value, key_node.start_mark.line)  # Track line
        return result
    
    LineTracker.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping
    )
    return yaml.load(yaml_str, Loader=LineTracker)
```

#### 3. **Error Messages with Context**
Include file, line, field, expected, actual:
```python
class PolicyValidationError(Exception):
    def __init__(self, message, file_path=None, line_no=None, field=None, suggestion=None):
        self.file_path = file_path
        self.line_no = line_no
        self.field = field
        self.suggestion = suggestion
        
        full_msg = f"{message}"
        if file_path and line_no:
            full_msg = f"{file_path}:{line_no}: {full_msg}"
        if suggestion:
            full_msg += f"\n  → {suggestion}"
        
        super().__init__(full_msg)
```

#### 4. **Separate Schema from Validation**
Schema (Pydantic) handles structure.  
Validator (PolicyValidator) handles business rules:
```python
# schema.py: What is valid structure?
class Policy(BaseModel):
    metadata: Metadata
    boundaries: Dict[str, any]

# validator.py: What is valid policy?
class PolicyValidator:
    def validate(self, policy: Policy) -> ValidationResult:
        # Check business rules beyond schema
        # E.g., if gdpr_compliant=true, check certain boundaries set
        pass
```

#### 5. **Test Fixtures Cover All Paths**
Create policies for:
- ✅ All fields set (maximum policy)
- ✅ Minimal fields (minimum policy)
- ✅ Each error type (invalid metadata, conflicting tools, etc.)
- ✅ Real-world patterns (github, read-only, admin)

#### 6. **JSON Schema Export for IDE**
Use Pydantic's built-in schema generation:
```python
import json

schema = Policy.schema()
# Customize for IDE (add descriptions, examples)
schema['properties']['metadata']['description'] = "Policy metadata..."
print(json.dumps(schema, indent=2))
```

Then in VS Code `.vscode/settings.json`:
```json
{
  "yaml.schemas": {
    "file:///path/to/.schema.json": "*.policy.yaml"
  }
}
```

#### 7. **Integration with story-1-1**
Policy loader follows same patterns as tool discovery:
- `loader.py` = parse YAML (like LangGraphAdapter parses AST)
- `validator.py` = validate policy (like ToolScanner validates tools)
- `schema.py` = define data structures (like SBOM schema)

#### 8. **No Side Effects During Loading**
- Don't apply policy during load (that's validation layer's job)
- Don't modify agent during policy load
- Just parse, validate, return normalized Policy object

---

## Dev Agent Record

### Implementation Plan
*To be filled during implementation*

### Technical Decisions
*To be filled during implementation*

### Completion Notes
*To be filled after all tasks complete*

---

## Status

**Current Status**: ready-for-dev  
**Ready for**: dev-story workflow  
**Depends on**: story-1-1 (project setup + tool discovery)  
**Next Step**: Run `bmad-dev-story 1-2` to begin implementation

---

**Story Created**: 2026-09-12  
**For**: Apart Research AI Incident Response Track 1 (Containment)  
**Project**: Agent Policy Conformance Validator (APCV) MVP
