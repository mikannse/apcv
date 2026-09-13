"""ProbeHost — the "agent stand-in" that agent-category probes run against.

The agent probes in the rule library use pseudo-code like
`agent.call_tool('undeclared_tool', {})`. Real LangGraph agents do not expose
such a direct-call surface (tool invocation goes through the framework's
internal graph loop), so APCV provides a small host object:

  * loads the user's agent file,
  * registers every `@tool`-decorated function (identified via the same AST
    heuristic the static scanner uses — the decorator *name* is `tool`,
    regardless of which package exports it),
  * exposes `call_tool(name, args)` and a `tools` dict,
  * wraps each registered function in the wrapt tracer so every invocation is
    recorded as audit-grade evidence.

This measures "tool-surface boundary" behavior: can an undeclared tool be
reached, are parameters constrained, does a dynamic add/override succeed. It
deliberately does NOT measure LLM-level prompt-injection resistance (that is
the non-goal "adversarial audit", deferred in the SPEC).
"""
from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
from typing import Any, Callable, Dict, List

from apcv.core.execution.tracer import traced, get_traces, reset_traces


def find_tool_names(source: str) -> List[str]:
    """Return the names of `@tool`-decorated top-level functions in `source`.

    Reuses the static scanner's heuristic: a FunctionDef whose decorator_list
    contains an attribute/name spelled `tool`.
    """
    tree = ast.parse(source)
    names: List[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for dec in node.decorator_list:
            dec_name = None
            if isinstance(dec, ast.Name):
                dec_name = dec.id
            elif isinstance(dec, ast.Attribute):
                dec_name = dec.attr
            if dec_name == "tool":
                names.append(node.name)
                break
    return names


class ProbeHost:
    """A callable, traceable registry of an agent's tools."""

    def __init__(self):
        self.tools: Dict[str, Callable] = {}

    # -- registration --------------------------------------------------------

    def register(self, func: Callable) -> None:
        """Register a function, wrapped in the tracer."""
        self.tools[func.__name__] = traced(func)

    def load_agent_file(self, agent_path: str) -> int:
        """Import an agent file and register all @tool functions.

        Returns the number of tools registered. Raises ImportError/OSError if
        the file cannot be imported.
        """
        path = Path(agent_path).resolve()
        source = path.read_text(encoding="utf-8")

        # Identify tool function names via AST (decorator-name heuristic).
        names = find_tool_names(source)
        if not names:
            return 0

        # Import the module so we can grab the real function objects.
        spec = importlib.util.spec_from_file_location(path.stem, str(path))
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot import agent file: {agent_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        registered = 0
        for name in names:
            func = getattr(module, name, None)
            if callable(func):
                self.register(func)
                registered += 1
        return registered

    # -- invocation ----------------------------------------------------------

    def call_tool(self, name: str, args: Dict[str, Any]) -> Any:
        """Invoke a registered tool by name.

        Raises PermissionError when the tool is not registered — this is what
        agent probes assert against for "undeclared tool" checks.
        """
        if name not in self.tools:
            raise PermissionError(f"Tool '{name}' is not registered")
        return self.tools[name](**args)

    # -- trace access --------------------------------------------------------

    def drain_traces(self) -> List[Any]:
        """Return and clear the accumulated traces."""
        traces = get_traces()
        reset_traces()
        return traces
