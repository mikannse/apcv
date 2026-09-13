"""Tests for the wrapt parameter tracer."""
from apcv.core.execution.tracer import traced, get_traces, reset_traces


def test_traced_records_sync_call():
    reset_traces()

    @traced
    def add(a: int, b: int) -> int:
        return a + b

    assert add(1, 2) == 3

    traces = get_traces()
    assert len(traces) == 1
    assert traces[0].tool == "add"
    assert traces[0].status == "ok"
    assert traces[0].result == "3"
    assert traces[0].args == {"a": 1, "b": 2}


def test_traced_records_error():
    reset_traces()

    @traced
    def boom():
        raise ValueError("kaboom")

    try:
        boom()
    except ValueError:
        pass

    traces = get_traces()
    assert len(traces) == 1
    assert traces[0].status == "error"
    assert "ValueError" in traces[0].result


def test_reset_clears_buffer():
    reset_traces()

    @traced
    def f():
        return 1

    f()
    assert len(get_traces()) == 1
    reset_traces()
    assert len(get_traces()) == 0
