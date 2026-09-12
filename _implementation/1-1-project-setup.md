# Story 1-1: Framework Setup & Tool Discovery Foundation

**Story Key**: 1-1-project-setup  
**Epic**: Week 1: Core Infrastructure  
**Status**: ready-for-dev  
**Priority**: 🔴 Critical  
**Estimate**: 3 days  
**Created**: 2026-09-12

---

## Story Overview

Establish project scaffolding, implement LangGraph AST parser, and discover static tool surface. This story lays the foundation for all downstream stories (CAP-2, CAP-3, CAP-5) by delivering the core tool discovery engine.

**Spec Checkpoint**: ✅ Completes CAP-1 (Tool Surface Discovery - static layer only)

---

## User Story

**As a** DevOps engineer  
**I want** the validator to automatically discover what tools a LangGraph Agent can invoke  
**So that** I can understand the complete capability surface before creating policy

---

## Acceptance Criteria

### AC-1: Tool Discovery Completeness
- [ ] Tool discovery finds **all** @tool decorators in LangGraph code
- [ ] No false negatives (all actual tools discovered)
- [ ] Supports decorated functions in any Python module imported by Agent

### AC-2: Output Format Compliance
- [ ] Output is valid JSON matching the SBOM schema
- [ ] JSON schema: `{version, timestamp, agent_path, tools: [{id, name, module, parameters, return_type, description}], metadata}`
- [ ] All tool metadata fields populated correctly

### AC-3: Performance Requirements
- [ ] Processing time **<10 seconds** on typical Agent code (files <50KB, <100 tools)
- [ ] Scales to 100+ tool definitions without significant slowdown
- [ ] Memory usage <100MB for typical Agent

### AC-4: Accuracy
- [ ] No false positives: undeclared/non-existent tools NOT marked as found
- [ ] Accuracy >95% on test suite of 5-10 sample LangGraph agents
- [ ] Correctly handles edge cases:
  - Dynamically added tools
  - Tools in conditional branches
  - Nested tool definitions
  - Tools from multiple modules

### AC-5: Testing
- [ ] Unit tests for each component (coverage >80%)
- [ ] Integration tests: SBOM accuracy validated against known tool sets
- [ ] Test fixtures: 5-10 sample LangGraph agents covering various patterns
- [ ] All tests pass with zero warnings

### AC-6: CI/CD Integration
- [ ] GitHub Actions workflow created and functional
- [ ] Build pipeline runs tests and code quality checks
- [ ] Automated on each push to main/dev branches

---

## Technical Requirements

### Architecture Decisions (Must Follow)

**Three-Layer Architecture**:
1. **Scan Layer**: ToolScanner discovers static capabilities
2. **Validate Layer**: (future stories) tests policies
3. **Decision Layer**: (future stories) generates verdict

**Framework Abstraction** (AD-6):
- Design `FrameworkAdapter` interface for framework-agnostic architecture
- Implement `LangGraphAdapter` for MVP
- All scanners receive adapter instance, NOT direct framework imports

**SBOM Output** (AD-3):
- Each scanner outputs independent JSON file
- Path: `.apcv/sbom/tool.json`
- Index file: `.apcv/sbom/index.json` lists all SBOM files

**CLI Entry Point** (AD-7):
- Single command: `apcv validate --agent <path> --policy <yaml>`
- Exit codes: 0=success, 1=validation fail, 2=error

### Technology Stack

| Component | Technology | Version | Notes |
|-----------|-----------|---------|-------|
| Language | Python | 3.9+ | Type hints required |
| AST Parsing | Python `ast` module | built-in | Primary method |
| Alternative Parser | tree-sitter | latest | Fallback for edge cases |
| Framework | LangGraph | 0.1.0+ | Target framework for MVP |
| Type Checking | Pydantic | 2.0+ | Data validation |
| Testing | pytest | 7.0+ | Unit and integration tests |
| Code Quality | Black, mypy, pylint | latest | Pre-commit hooks |
| CI/CD | GitHub Actions | latest | Automated testing |
| VCS | Git | latest | For tracking changes |

### Project Structure (Must Create)

```
apcv/
├── core/
│   ├── __init__.py
│   ├── scanners/
│   │   ├── __init__.py
│   │   ├── base.py              # Scanner abstract interface
│   │   ├── tool_scanner.py      # ToolScanner implementation
│   │   ├── runtime_scanner.py   # (future)
│   │   ├── network_scanner.py   # (future)
│   │   └── identity_scanner.py  # (future)
│   │
│   ├── frameworks/
│   │   ├── __init__.py
│   │   ├── adapter.py           # FrameworkAdapter abstract interface
│   │   └── langgraph_adapter.py # LangGraphAdapter (MVP)
│   │
│   └── utils/
│       ├── __init__.py
│       └── sbom.py              # SBOM schema and validation
│
├── cli/
│   ├── __init__.py
│   └── main.py                  # apcv validate command
│
├── tests/
│   ├── __init__.py
│   ├── fixtures/
│   │   ├── sample_agents/       # 5-10 test agents
│   │   │   ├── simple_agent.py
│   │   │   ├── complex_agent.py
│   │   │   └── ...
│   │   └── expected_sboms/      # Expected outputs
│   │
│   ├── unit/
│   │   ├── test_tool_scanner.py
│   │   ├── test_sbom.py
│   │   └── test_langgraph_adapter.py
│   │
│   └── integration/
│       └── test_discovery_pipeline.py
│
├── .apcv/
│   ├── sbom/                    # Generated SBOM files
│   ├── logs/                    # Execution logs
│   └── reports/                 # Report outputs
│
├── docs/
│   ├── API.md
│   ├── ARCHITECTURE.md
│   ├── QUICKSTART.md
│   └── examples/
│
├── requirements.txt             # Dependencies
├── setup.py                     # Package metadata
├── README.md
├── pytest.ini
├── pyproject.toml
├── .pre-commit-config.yaml
├── .github/
│   └── workflows/
│       ├── tests.yml            # Run tests on push
│       ├── lint.yml             # Code quality checks
│       └── release.yml          # Release automation
│
└── .gitignore
```

### Data Structures

**SBOM Schema** (JSON):
```json
{
  "version": "1.0",
  "timestamp": "2026-09-12T10:30:00Z",
  "agent_path": "/path/to/agent.py",
  "metadata": {
    "framework": "langgraph",
    "framework_version": "0.1.0",
    "python_version": "3.11"
  },
  "tools": [
    {
      "id": "tool_1",
      "name": "search_documents",
      "module": "my_agent.tools",
      "parameters": [
        {"name": "query", "type": "str", "required": true},
        {"name": "limit", "type": "int", "default": 10}
      ],
      "return_type": "str",
      "description": "Search documents by keyword"
    }
  ]
}
```

**Scanner Interface** (`core/scanners/base.py`):
```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class Scanner(ABC):
    @abstractmethod
    def scan(self, agent_path: str, adapter) -> Dict[str, Any]:
        """Scan and return SBOM in standard format"""
        pass
```

**FrameworkAdapter Interface** (`core/frameworks/adapter.py`):
```python
from abc import ABC, abstractmethod
from pathlib import Path

class FrameworkAdapter(ABC):
    @abstractmethod
    def parse_agent_file(self, path: Path) -> Dict[str, Any]:
        """Parse agent code and return AST-compatible representation"""
        pass
    
    @abstractmethod
    def extract_tools(self, ast_tree) -> list:
        """Extract tool definitions from parsed agent"""
        pass
```

---

## Development Context

### Previous Story Intelligence
**N/A** - This is the first story in the epic.

### Project Context
- **Product**: Agent Policy Conformance Validator (APCV)
- **Mission**: Verify AI Agents comply with declared policies
- **Target Users**: DevOps, Security Teams, Compliance Officers
- **Time Constraint**: 3 weeks MVP → must be disciplined about scope
- **Open Source**: Apache 2.0 license → code quality must be publication-ready

### Key Architecture Decisions This Story Must Honor

1. **Adapter Pattern** (AD-6): Design ToolScanner to work through FrameworkAdapter, NOT directly with LangGraph APIs
   - This enables multi-framework support in story 1-2
   - DO NOT hardcode LangGraph imports in ToolScanner

2. **SBOM Files** (AD-3): Store tool.json independently, create index.json
   - Enables lazy-loading in validation layer (story 2)
   - DO NOT merge all SBOM data into single file

3. **Scanner Interface** (AD-2): Define common Scanner interface now
   - Runtime and Network scanners (future) will implement same interface
   - Ensures consistent composition at decision layer

4. **CLI Foundation** (AD-7): Implement stub for `apcv validate` command
   - Wire tool_scanner into CLI entry point
   - Don't need full policy handling yet, just agent discovery

### Common LLM Mistakes to Avoid

❌ **Mistake 1: Hardcoding LangGraph**
- ❌ DO NOT: Import LangGraph directly in ToolScanner
- ✅ DO: Pass LangGraphAdapter to ToolScanner, use generic Scanner interface

❌ **Mistake 2: Mixing Scanner with Validator**
- ❌ DO NOT: Put validation logic in ToolScanner
- ✅ DO: Scanner only discovers, Validator will test policies (story 2)

❌ **Mistake 3: Merging SBOM Files**
- ❌ DO NOT: Create single consolidated SBOM
- ✅ DO: Keep tool.json, runtime.json, network.json separate with index

❌ **Mistake 4: Skipping Edge Cases**
- ❌ DO NOT: Only handle simple @tool decorators
- ✅ DO: Handle nested definitions, conditional imports, dynamic tool addition

❌ **Mistake 5: No Type Hints**
- ❌ DO NOT: Write loose Python without types
- ✅ DO: Use Pydantic models, type hints on all functions (future mypy --strict pass)

❌ **Mistake 6: Inadequate Tests**
- ❌ DO NOT: "Tests can wait"
- ✅ DO: Write tests FIRST (red-green-refactor), fixtures cover >5 agent patterns

### Testing Standards

**Test Framework**: pytest  
**Coverage Target**: >80% of code  
**Test Organization**:
- `tests/unit/` - test individual components (Scanner, Adapter, SBOM)
- `tests/integration/` - test discovery end-to-end with real agents
- `tests/fixtures/` - reusable test agents and expected outputs

**Test Patterns**:
```python
# Unit: Test Scanner in isolation
def test_tool_scanner_discovers_simple_tool(mock_adapter):
    scanner = ToolScanner()
    result = scanner.scan("agent.py", mock_adapter)
    assert len(result["tools"]) == 1
    assert result["tools"][0]["name"] == "search"

# Integration: Test with real agent code
def test_discovery_end_to_end():
    agent_path = Path("tests/fixtures/sample_agents/simple_agent.py")
    adapter = LangGraphAdapter()
    scanner = ToolScanner()
    sbom = scanner.scan(str(agent_path), adapter)
    
    # Validate against expected output
    expected = load_expected_sbom("simple_agent.expected.json")
    assert sbom == expected
```

### Libraries & Dependencies

**Core**:
- `langgraph` (0.1.0+): Target framework
- `pydantic` (2.0+): Data validation and schemas

**AST & Parsing**:
- `tree-sitter` (latest): Advanced parsing for edge cases
- Python `ast` module (built-in): Primary parsing

**CLI**:
- `click` (8.0+) or `typer` (0.9+): CLI framework (recommend Typer for modern async support)

**Testing**:
- `pytest` (7.0+): Test runner
- `pytest-cov`: Coverage reporting
- `pytest-mock`: Mocking support

**Code Quality**:
- `black`: Code formatting
- `mypy`: Type checking
- `pylint`: Linting
- `pre-commit`: Git hooks

**See**: `requirements.txt` (to be created with pinned versions)

---

## Tasks & Subtasks

### ✅ Task 1: Project Setup & Repository Initialization (Days 1-1.5)

- [ ] 1.1: Create GitHub repository with Apache 2.0 license
- [ ] 1.2: Initialize Python project structure (setup.py, pyproject.toml, requirements.txt)
- [ ] 1.3: Set up pre-commit hooks (black, mypy, pylint)
- [ ] 1.4: Create folder structure (apcv/, tests/, docs/, .apcv/)
- [ ] 1.5: Initialize pytest configuration (pytest.ini)
- [ ] 1.6: Set up GitHub Actions CI/CD pipeline:
  - [ ] 1.6a: `.github/workflows/tests.yml` - Run pytest on push
  - [ ] 1.6b: `.github/workflows/lint.yml` - Run black, mypy, pylint
  - [ ] 1.6c: Initial commit to trigger first CI run

**Definition of Done**: 
- Repository initialized and functional
- First GitHub Actions workflow passes
- All tools runnable locally (pytest, black, mypy)

### ✅ Task 2: Define Data Structures & Interfaces (Days 1.5-2)

- [ ] 2.1: Create `core/utils/sbom.py` with SBOM schema (Pydantic models)
  - [ ] Tool model, Metadata model, SBOM root model
  - [ ] JSON schema export for validation
  
- [ ] 2.2: Create `core/scanners/base.py` with Scanner interface
  - [ ] Abstract `scan()` method
  - [ ] Error handling contract
  
- [ ] 2.3: Create `core/frameworks/adapter.py` with FrameworkAdapter interface
  - [ ] Abstract methods: `parse_agent_file()`, `extract_tools()`
  - [ ] Common exception types
  
- [ ] 2.4: Create unit tests for data structures
  - [ ] SBOM schema validation
  - [ ] Interface contract tests

**Definition of Done**:
- Pydantic models for SBOM compiles without errors
- JSON schema can be exported and validates real tool data
- Interface methods are abstract and enforce contract
- Tests pass 100%

### ✅ Task 3: Implement LangGraphAdapter (Days 2-2.5)

- [ ] 3.1: Create `core/frameworks/langgraph_adapter.py` implementing FrameworkAdapter
  - [ ] `parse_agent_file()`: Read Python file, return AST
  - [ ] `extract_tools()`: Walk AST looking for @tool decorators
  - [ ] Support LangGraph >=0.1.0
  
- [ ] 3.2: Handle edge cases
  - [ ] Tools in nested modules
  - [ ] Tools added dynamically
  - [ ] Tools in conditional branches
  - [ ] Preserve parameter types and defaults
  
- [ ] 3.3: Unit tests for LangGraphAdapter
  - [ ] Test with 5-10 sample agents
  - [ ] Test edge cases from AC-4
  - [ ] Performance: <1 second per agent

**Definition of Done**:
- All AC-4 edge cases handled
- Unit tests cover >80% of adapter code
- Performance <1 sec per agent file
- No hardcoded file paths (use Path objects)

### ✅ Task 4: Implement ToolScanner (Days 2.5-3)

- [ ] 4.1: Create `core/scanners/tool_scanner.py` implementing Scanner interface
  - [ ] `scan()` method takes agent_path and adapter
  - [ ] Returns properly formatted SBOM matching schema
  - [ ] Handles both single file and package imports
  
- [ ] 4.2: Output SBOM JSON
  - [ ] Save to `.apcv/sbom/tool.json`
  - [ ] Create `.apcv/sbom/index.json` listing all SBOM files
  - [ ] Metadata: timestamp, framework, Python version
  
- [ ] 4.3: Performance optimization
  - [ ] Cache parsed AST if same file queried twice
  - [ ] Lazy-load modules (don't import, just parse)
  - [ ] Verify <10 seconds for typical Agent (AC-3)
  
- [ ] 4.4: Unit & integration tests
  - [ ] Test with 5-10 sample agents
  - [ ] Verify SBOM accuracy (AC-4)
  - [ ] Verify performance (AC-3)
  - [ ] Test error handling (invalid paths, syntax errors)

**Definition of Done**:
- AC-1, AC-2, AC-3, AC-4 all pass
- Integration tests pass with real sample agents
- Coverage >80%
- SBOM files generated correctly at .apcv/sbom/

### ✅ Task 5: CLI Integration (Days 2.5-3)

- [ ] 5.1: Create `cli/main.py` with entry point
  - [ ] Command: `apcv validate --agent <path> --policy <yaml>`
  - [ ] Wire ToolScanner into CLI
  - [ ] Output human-readable table + JSON report
  - [ ] Exit codes: 0=success, 1=fail, 2=error
  
- [ ] 5.2: Create `setup.py` entry point
  - [ ] Install command creates `apcv` executable
  - [ ] `python -m apcv.cli` works
  
- [ ] 5.3: Test CLI
  - [ ] `apcv validate --agent tests/fixtures/simple_agent.py --policy /dev/null`
  - [ ] Verify SBOM JSON written to reports/
  - [ ] Exit code correct

**Definition of Done**:
- `apcv validate` command runs successfully
- CLI help text clear
- Test fixtures discoverable by CLI

### ✅ Task 6: Create Test Fixtures (Throughout)

- [ ] 6.1: Create 5-10 sample LangGraph agents in `tests/fixtures/sample_agents/`
  - [ ] simple_agent.py: 2-3 tools, straightforward
  - [ ] complex_agent.py: 10+ tools, nested, dynamic
  - [ ] edge_case_agents.py: Covers AC-4 edge cases
  
- [ ] 6.2: Create expected SBOM outputs for each agent
  - [ ] Store in `tests/fixtures/expected_sboms/`
  - [ ] Use for integration test validation
  
- [ ] 6.3: Create mock LangGraphAdapter for unit tests
  - [ ] Allows testing ToolScanner without real LangGraph

**Definition of Done**:
- 5-10 sample agents created
- Each has corresponding expected SBOM
- All fixtures can be imported without errors

### ✅ Task 7: CI/CD Pipeline Setup (Throughout)

- [ ] 7.1: GitHub Actions: `tests.yml`
  - [ ] Run pytest on every push
  - [ ] Report coverage
  - [ ] Fail if coverage <80%
  
- [ ] 7.2: GitHub Actions: `lint.yml`
  - [ ] Run black, mypy, pylint
  - [ ] Auto-fix with black if needed
  - [ ] Fail on mypy strict errors or pylint high severity
  
- [ ] 7.3: Test locally first
  - [ ] `pytest` runs all tests
  - [ ] `black --check apcv/ tests/` passes
  - [ ] `mypy apcv/ --strict` passes
  - [ ] `pylint apcv/` no high-severity errors

**Definition of Done**:
- All GitHub Actions workflows pass
- Local test/lint commands pass
- First push triggers successful CI run

### ✅ Task 8: Documentation (Throughout)

- [ ] 8.1: Create `docs/ARCHITECTURE.md`
  - [ ] Explain Scanner-Adapter pattern
  - [ ] Why SBOM files are separate
  - [ ] How to extend with new scanners
  
- [ ] 8.2: Create `docs/QUICKSTART.md`
  - [ ] Install: `pip install apcv`
  - [ ] Usage: `apcv validate --agent my_agent.py --policy policy.yaml`
  - [ ] Example output
  
- [ ] 8.3: Update `README.md`
  - [ ] Project description
  - [ ] Quick links to docs
  - [ ] License info

**Definition of Done**:
- Docs are clear and complete
- New contributor can follow QUICKSTART
- Architecture rationale documented

---

## File List

### New Files Created
```
apcv/
├── core/__init__.py
├── core/scanners/__init__.py
├── core/scanners/base.py
├── core/scanners/tool_scanner.py
├── core/frameworks/__init__.py
├── core/frameworks/adapter.py
├── core/frameworks/langgraph_adapter.py
├── core/utils/__init__.py
├── core/utils/sbom.py
├── cli/__init__.py
├── cli/main.py
├── tests/__init__.py
├── tests/unit/test_tool_scanner.py
├── tests/unit/test_sbom.py
├── tests/unit/test_langgraph_adapter.py
├── tests/integration/test_discovery_pipeline.py
├── tests/fixtures/sample_agents/simple_agent.py
├── tests/fixtures/sample_agents/complex_agent.py
├── tests/fixtures/expected_sboms/simple_agent.expected.json
├── tests/fixtures/expected_sboms/complex_agent.expected.json
├── docs/ARCHITECTURE.md
├── docs/QUICKSTART.md
├── .github/workflows/tests.yml
├── .github/workflows/lint.yml
├── requirements.txt
├── setup.py
├── pyproject.toml
├── pytest.ini
├── .pre-commit-config.yaml
├── README.md
└── .gitignore
```

---

## Change Log

- **2026-09-12** - Story created with comprehensive context

---

## Dev Notes for Implementation

### Implementation Strategy: Red-Green-Refactor

1. **RED**: Write failing tests first for each task
2. **GREEN**: Implement minimal code to make tests pass
3. **REFACTOR**: Improve structure while keeping tests green

### Key Implementation Considerations

#### 1. **Adapter Pattern is Critical**
The whole system depends on FrameworkAdapter abstraction. DO NOT skip this:
- ToolScanner receives `adapter` as parameter
- ToolScanner calls `adapter.parse_agent_file()` and `adapter.extract_tools()`
- This makes testing easy (mock adapter) and enables multi-framework support

#### 2. **AST Parsing Robustness**
Python's `ast` module is your primary tool:
```python
import ast

tree = ast.parse(source_code)
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == "tool":
                # Found a @tool decorator
```

Fallback to tree-sitter for edge cases (multiple decorators, complex expressions)

#### 3. **SBOM Schema Validation**
Use Pydantic to validate all SBOM data:
```python
from pydantic import BaseModel

class Tool(BaseModel):
    id: str
    name: str
    parameters: list = []
    
class SBOM(BaseModel):
    version: str
    tools: list[Tool]
```

This ensures type safety and makes JSON serialization automatic.

#### 4. **Performance: <10 Seconds**
For typical agents (<50KB, <100 tools):
- Parse once, cache AST → reuse for multiple queries
- Don't import the agent module (just parse source)
- Use lazy evaluation for large import trees

#### 5. **Test Fixtures are Your Safety Net**
Create diverse sample agents to catch edge cases:
- Simple agent: 2-3 basic tools
- Complex agent: nested modules, 10+ tools, conditional imports
- Edge case agents: dynamic tools, aliased imports, nested functions

Run all fixtures through ToolScanner, validate SBOM matches expected output.

#### 6. **No False Positives**
AC-4 requires accuracy >95%, no false positives. This means:
- Only report tools that are actually decorated with `@tool`
- Don't report functions just because they look like tools
- Don't report tools from other packages unless actually imported

#### 7. **CLI Wiring is Simple**
The CLI just calls ToolScanner → serialize SBOM → save JSON → print table:
```python
@click.command()
@click.option('--agent', required=True)
@click.option('--policy', required=True)
def validate(agent, policy):
    adapter = LangGraphAdapter()
    scanner = ToolScanner()
    sbom = scanner.scan(agent, adapter)
    
    # Save SBOM JSON
    sbom_path = Path(".apcv/sbom/tool.json")
    sbom_path.parent.mkdir(parents=True, exist_ok=True)
    sbom_path.write_text(sbom.json())
    
    # Print table
    print_sbom_table(sbom)
    
    return 0  # Success
```

#### 8. **Logging & Error Handling**
- Log all steps (file parsed, X tools found, SBOM saved)
- Catch and log exceptions with context (file, operation, error)
- Never silently fail — always inform user what went wrong

#### 9. **Git Strategy**
- Use conventional commits: `feat: implement ToolScanner` 
- Small, focused commits (one feature per commit)
- All tests passing before each commit
- Create PR after Task 8 (whole story reviewed together)

### Debugging Tips

**If test fails**: 
1. Check sample agent file exists and is valid Python
2. Verify adapter returns correct AST representation
3. Print actual vs expected SBOM to diff
4. Use `pdb` debugger to step through AST walk

**If performance is slow**:
1. Profile with `cProfile` to find bottleneck
2. Check if you're importing modules (don't! just parse)
3. Verify caching is working
4. Consider tree-sitter for large files

**If SBOM doesn't match**:
1. Compare JSON structure vs expected
2. Check parameter extraction (types, defaults)
3. Verify decorator detection (might be aliased as `@t` instead of `@tool`)

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
**Next Step**: Run `bmad-dev-story 1-1` to begin implementation

---

**Story Created**: 2026-09-12  
**For**: Apart Research AI Incident Response Track 1 (Containment)  
**Project**: Agent Policy Conformance Validator (APCV) MVP
