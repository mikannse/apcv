# Story 3-3: E2E Demo & Documentation

**Story Key**: 3-3-demo-docs  
**Epic**: Week 3: Demo & Delivery  
**Status**: ready-for-dev | **Priority**: 🔵 High | **Estimate**: 2 days | **Dependencies**: story-3-1, story-3-2

## Story Overview
Create end-to-end demo using GitHub incident scenario. Package MVP, documentation, and demo scripts for delivery.

**Spec Checkpoint**: ✅ Demonstrates all 7 capabilities working together

## User Story
**As a** project lead | **I want** a complete end-to-end demo and clear documentation | **So that** stakeholders understand what APCV does and how to use it

## Acceptance Criteria
- [ ] AC-1: Demo runs successfully from start to finish
- [ ] AC-2: Documentation covers user and developer workflows
- [ ] AC-3: README is clear and includes quick start
- [ ] AC-4: Example policies are provided
- [ ] AC-5: All materials are ready for public sharing
- [ ] AC-6: Demo scenario covers real-world use case
- [ ] AC-7: Deployment guide included (Docker, local, cloud)

## Demo Scenario
**GitHub Incident**: Agent with undeclared tool access
1. Create sample Agent (GitHub API access)
2. Define policy (read-only, specific tools only)
3. Run validator: `apcv validate --agent agent.py --policy policy.yaml`
4. Show violations and compliance score
5. Demonstrate Web UI dashboard
6. Show remediation suggestions

## Tasks (4 tasks, 2 days)

### ✅ Task 1: Create Demo Agent & Policy
- [ ] 1.1: Sample GitHub Agent with 5-10 tools
- [ ] 1.2: Policy YAML (read-only, limited tools)
- [ ] 1.3: Expected violations documented

### ✅ Task 2: Demo Script & Walkthrough
- [ ] 2.1: End-to-end demo script (CLI + Web UI)
- [ ] 2.2: Expected outputs documented
- [ ] 2.3: Troubleshooting guide

### ✅ Task 3: Documentation
- [ ] 3.1: README.md (project overview, quick start, examples)
- [ ] 3.2: User guide (how to use CLI + Web UI)
- [ ] 3.3: Developer guide (architecture, extension points)
- [ ] 3.4: Deployment guide (local, Docker, cloud)
- [ ] 3.5: API documentation

### ✅ Task 4: Packaging & Release
- [ ] 4.1: Create release checklist
- [ ] 4.2: Package MVP (code, docs, examples)
- [ ] 4.3: GitHub release notes and tags
- [ ] 4.4: PyPI package setup (for distribution)

## Files Created
- docs/README.md
- docs/USER_GUIDE.md
- docs/DEVELOPER_GUIDE.md
- docs/DEPLOYMENT.md
- docs/API.md
- examples/demo_agent.py
- examples/demo_policy.yaml
- examples/demo_walkthrough.md
- tests/e2e/demo_scenario.py

## Status: ready-for-dev
