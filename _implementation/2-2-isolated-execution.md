# Story 2-2: Isolated Execution & Parameter Tracing

**Story Key**: 2-2-isolated-execution  
**Epic**: Week 2: Dynamic Validation  
**Status**: ready-for-dev | **Priority**: 🔴 Critical | **Estimate**: 3 days | **Dependencies**: story-2-1 (probe rules)

## Story Overview
Implement Docker-based probe executor, wrapt parameter tracing, and execution trace collection. Run probes in isolated, repeatable environments and record all tool invocations.

**Spec Checkpoint**: ✅ Completes CAP-3 (Isolated Probe Execution & Parameter Tracing)

## User Story
**As a** DevOps engineer | **I want** probes to run in isolated environments | **So that** we can safely test Agent boundaries without affecting production systems

## Acceptance Criteria
- [ ] AC-1: Docker image (apcv-probe) with base Agent runtime created and tested
- [ ] AC-2: IsolatedExecutor can spawn containers, inject probes, capture results
- [ ] AC-3: wrapt parameter tracing captures 100% of tool calls with <1% overhead
- [ ] AC-4: Execution trace JSONL format: timestamp, tool, args, result, policy_violation
- [ ] AC-5: Parallel probe execution (4 concurrent workers, total <60s for 30 probes)
- [ ] AC-6: Container lifecycle tests: cleanup, isolation, no cross-pollution
- [ ] AC-7: Coverage >80%, integration tests with real probes pass

## Technical Requirements

### Architecture Decisions (Must Follow)
- **Isolated Execution** (AD-3, AD-4): Docker-based isolation, read-only FS, no network
- **Parameter Tracing** (wrapt): <1% overhead, async support, zero-copy where possible
- **Parallel Execution** (AD-4): ThreadPoolExecutor or asyncio, concurrent but safe

### Project Structure
```
apcv/
├── core/
│   ├── execution/          # NEW
│   │   ├── executor.py     # IsolatedExecutor class
│   │   ├── tracer.py       # wrapt parameter tracing
│   │   └── trace_model.py  # Execution trace schema
│   └── docker/             # NEW
│       ├── Dockerfile      # apcv-probe image
│       └── entrypoint.py   # Container entry point
│
├── tests/
│   ├── unit/test_executor.py
│   ├── unit/test_tracer.py
│   └── integration/test_isolated_execution.py
│
└── docker/apcv-probe/      # Docker build context
    ├── Dockerfile
    ├── requirements.txt
    └── entrypoint.sh
```

### Key Implementations

**Dockerfile** (`docker/apcv-probe/Dockerfile`):
```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends docker.io
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENTRYPOINT ["python", "-m", "apcv.core.execution.probe_runner"]
```

**IsolatedExecutor** (`core/execution/executor.py`):
```python
class IsolatedExecutor:
    def execute_probe(self, probe: Probe) -> ExecutionTrace
    def execute_parallel(self, probes: List[Probe], workers=4) -> List[ExecutionTrace]
    def cleanup_containers(self)
```

**Parameter Tracer** (`core/execution/tracer.py`):
```python
@wrapt.decorator
def trace_parameters(wrapped, instance, args, kwargs):
    # Track function call with <1% overhead
    trace = {timestamp, function, params, result, status}
    TRACE_LOG.append(trace)
```

## Tasks & Subtasks (7 tasks, 3 days)

### ✅ Task 1: Design Docker Image & Entrypoint
- [ ] 1.1: Create Dockerfile with Python runtime
- [ ] 1.2: Create probe_runner.py entrypoint
- [ ] 1.3: Test Docker build locally

### ✅ Task 2: Implement IsolatedExecutor
- [ ] 2.1: Docker API client setup
- [ ] 2.2: Single probe execution method
- [ ] 2.3: Error handling and cleanup

### ✅ Task 3: Implement Parameter Tracing (wrapt)
- [ ] 3.1: Create @trace_parameters decorator
- [ ] 3.2: Support sync & async functions
- [ ] 3.3: Benchmark overhead (<1%)

### ✅ Task 4: Execution Trace Model
- [ ] 4.1: Pydantic model for traces
- [ ] 4.2: JSONL format definition
- [ ] 4.3: Timestamp and metadata

### ✅ Task 5: Parallel Probe Execution
- [ ] 5.1: ThreadPoolExecutor wrapper
- [ ] 5.2: 4 concurrent workers
- [ ] 5.3: Total execution <60s

### ✅ Task 6: Container Lifecycle & Isolation
- [ ] 6.1: Read-only filesystem
- [ ] 6.2: Network isolation
- [ ] 6.3: Resource limits

### ✅ Task 7: Testing & Documentation
- [ ] 7.1: Unit tests for executor, tracer
- [ ] 7.2: Integration tests with real probes
- [ ] 7.3: Documentation

## Dev Notes
- wrapt decorator must handle both sync and async (use asyncio hooks)
- Docker timeout: 30 seconds per probe
- Trace overhead measurement: profile before/after with real agents
- No `yaml.load()` - use `yaml.safe_load()` only

## Status: ready-for-dev
