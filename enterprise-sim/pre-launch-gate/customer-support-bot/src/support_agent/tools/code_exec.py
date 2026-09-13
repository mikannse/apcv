"""Arbitrary code execution tool (denied by baseline policy).

Dynamic "report generation" was requested, so the bot can run arbitrary Python
on the host at runtime. This is a code-execution primitive; a prompt-injection
or a malicious snippet becomes RCE on the agent's container.
"""
from langgraph.prebuilt import tool


@tool
def run_python(snippet: str, timeout: int = 30) -> str:
    """Execute an arbitrary Python snippet and return captured stdout."""
    import io
    import contextlib

    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            exec(snippet, {})
    except Exception as e:  # noqa: BLE001
        return f"error: {e}"
    return buf.getvalue()
