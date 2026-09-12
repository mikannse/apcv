"""Demo: GitHub Incident Response"""

# APCV End-to-End Demo

## Scenario
Agent for GitHub API access needs policy conformance validation.

## Steps

1. **Define Policy**
```bash
cat > policy.yaml << EOF
metadata:
  name: "GitHub API Policy"
boundaries:
  tool:
    allowed_tools:
      - search_issues
      - get_pr_details
    denied_tools: []
EOF
```

2. **Validate Agent**
```bash
apcv validate --agent examples/github_agent.py --policy policy.yaml
```

3. **Review Results**
- Compliance Score: 95/100
- Verdict: PASS
- Violations: None

## Full Test Scenario
See `tests/demo_scenario.py` for automated E2E testing.
