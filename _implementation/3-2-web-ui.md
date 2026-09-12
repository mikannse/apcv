# Story 3-2: Web UI (Dashboard, Policy Editor, Reports)

**Story Key**: 3-2-web-ui  
**Epic**: Week 3: User Interface & Visualization  
**Status**: ready-for-dev | **Priority**: 🔵 High | **Estimate**: 3 days | **Dependencies**: story-2-3 (conformance check)

## Story Overview
Implement web dashboard showing Agent list, compliance scores, execution timelines, policy editor, and report generation. Built with React + FastAPI.

**Spec Checkpoint**: ✅ Completes CAP-5, CAP-6 (Web UI interface)

## User Story
**As a** security team lead | **I want** a dashboard showing all Agents and their compliance status | **So that** I can quickly identify policy violations and manage Agent policies

## Acceptance Criteria
- [ ] AC-1: Dashboard displays Agent list with compliance scores
- [ ] AC-2: Agent detail page shows execution timeline and violations
- [ ] AC-3: Policy editor is functional and validates input
- [ ] AC-4: Reports can be generated and downloaded (PDF, JSON, HTML)
- [ ] AC-5: UI is responsive and accessible
- [ ] AC-6: Key user journeys are tested (E2E)
- [ ] AC-7: Performance: page load <2 seconds

## Technical Requirements

### Tech Stack
- **Backend**: FastAPI + file-based storage (.apcv/reports/)
- **Frontend**: React 18+ + TypeScript + TailwindCSS
- **Testing**: Playwright for E2E

### Key Pages
1. **Dashboard**: Agent list, compliance cards, trends
2. **Agent Detail**: Execution timeline, violations, fix suggestions
3. **Policy Editor**: YAML editor with real-time validation
4. **Report Center**: PDF/JSON/HTML export

### Project Structure
```
apcv/
├── web/                    # NEW
│   ├── backend/            # FastAPI
│   │   ├── main.py
│   │   ├── models.py
│   │   └── routes/
│   │
│   ├── frontend/           # React
│   │   ├── src/
│   │   │   ├── pages/Dashboard, AgentDetail, PolicyEditor
│   │   │   ├── components/ComplianceCard, Timeline, etc.
│   │   │   └── App.tsx
│   │   └── package.json
│   │
│   └── tests/
│       └── e2e/            # Playwright
│
└── docs/WEB_UI.md
```

## Tasks (5 tasks, 3 days)

### ✅ Task 1: FastAPI Backend Setup
- [ ] 1.1: FastAPI app with CORS
- [ ] 1.2: API endpoints for Agent data
- [ ] 1.3: Policy management endpoints

### ✅ Task 2: React Frontend Setup
- [ ] 2.1: Create React app with TypeScript
- [ ] 2.2: TailwindCSS styling
- [ ] 2.3: Component architecture

### ✅ Task 3: Dashboard & Agent Detail Pages
- [ ] 3.1: Dashboard page with Agent list
- [ ] 3.2: Agent detail page with timeline
- [ ] 3.3: Violations display and fix hints

### ✅ Task 4: Policy Editor & Report Export
- [ ] 4.1: YAML editor with Monaco
- [ ] 4.2: Real-time policy validation
- [ ] 4.3: PDF/JSON/HTML export

### ✅ Task 5: Testing & Deployment
- [ ] 5.1: Playwright E2E tests (critical journeys)
- [ ] 5.2: Responsive design tests
- [ ] 5.3: Deployment guide (Docker Compose)

## Status: ready-for-dev
