# Story 3-1: CLI Tool (apcv validate)

**Story Key**: 3-1-cli-tool  
**Epic**: Week 3: User Interface & CI/CD Integration  
**Status**: ready-for-dev | **Priority**: 🔵 High | **Estimate**: 2 days | **Dependencies**: story-2-3 (conformance check)

## Story Overview
Implement command-line interface for validating Agents. Support standard options, output formats (JSON, SARIF), and CI/CD pipeline integration.

**Spec Checkpoint**: ✅ Completes CAP-5 (CLI interface)

## User Story
**As a** DevOps engineer | **I want** to run `apcv validate` from CI/CD pipelines | **So that** Agent validation is automated as part of my deployment process

## Acceptance Criteria
- [ ] AC-1: CLI command: `apcv validate --agent <path> --policy <yaml> --output {json,sarif,html}`
- [ ] AC-2: Exit codes: 0 (PASS), 1 (FAIL), 2 (ERROR)
- [ ] AC-3: Output formats: JSON, SARIF, HTML
- [ ] AC-4: Integration with GitHub Actions, GitLab CI (documented)
- [ ] AC-5: Help text, examples, error handling
- [ ] AC-6: CLI tests: various option combinations
- [ ] AC-7: Performance: complete validation <2 minutes

## Technical Requirements

### CLI Command Structure
```bash
apcv validate \
  --agent <path>              # Agent code or config (required)
  --policy <path>             # Policy YAML (required)
  --output {json|sarif|html}  # Output format (default: json)
  --fail-on <score>           # Fail if compliance < threshold
  --workers <n>               # Parallel workers (default: 4)
  --timeout <s>               # Timeout per probe (default: 30)
  --verbose / --quiet         # Logging level
```

### Key Implementations
```python
@click.command()
@click.option('--agent', required=True)
@click.option('--policy', required=True)
@click.option('--output', type=click.Choice(['json', 'sarif', 'html']), default='json')
@click.option('--fail-on', type=int, default=95)
def validate(agent, policy, output, fail_on):
    # Orchestrate: discovery → generation → execution → conformance
    # Return appropriate exit code
```

## Tasks (5 tasks, 2 days)

### ✅ Task 1: Click/Typer CLI Framework
- [ ] 1.1: Set up Click (or Typer) command structure
- [ ] 1.2: Argument parsing and validation
- [ ] 1.3: Help text and examples

### ✅ Task 2: CLI Logic Orchestration
- [ ] 2.1: Load agent, policy, probe library
- [ ] 2.2: Execute pipeline: discovery → generation → execution → conformance
- [ ] 2.3: Collect results

### ✅ Task 3: Output Formatters
- [ ] 3.1: JSON formatter
- [ ] 3.2: SARIF formatter (security standard)
- [ ] 3.3: HTML formatter

### ✅ Task 4: Exit Codes & Error Handling
- [ ] 4.1: Exit 0 on PASS
- [ ] 4.2: Exit 1 on validation FAIL
- [ ] 4.3: Exit 2 on error (invalid args, file not found, etc)

### ✅ Task 5: Testing & Documentation
- [ ] 5.1: CLI tests with pytest
- [ ] 5.2: CI/CD integration examples (GitHub Actions, GitLab CI)
- [ ] 5.3: README examples

## Status: ready-for-dev
