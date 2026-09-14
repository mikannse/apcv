"""Tool capability classifier (static, AST-sink based).

Detects the dangerous capabilities a tool's function body actually exercises,
so the probe generator can decide which deep canary probes to emit.

Precision over recall: a capability is only reported when the AST contains a
concrete sink call. Naming/docstring heuristics are deliberately NOT used here
— the canary decision must rest on observed behavior, not developer intent, so
that a wrongly-inferred capability never blocks a good agent at the gate.

Capabilities:
  * code_exec  — executes arbitrary code (exec/eval/compile, os.system,
                 subprocess.*)
  * file_read  — reads files (open() in read mode, os.open, Path.read_text, ...)
  * file_write — writes/removes files (open() in write mode, Path.write_text,
                 os.remove, shutil.*)
  * network    — makes network requests (httpx/requests/urllib/socket, ...)
"""
from __future__ import annotations

import ast
from typing import List, Optional, Tuple


# -- bare builtin names that are dangerous on their own ----------------------

_EXEC_BUILTINS = {"exec", "eval", "compile"}


# -- object-prefixed sinks: object_path -> set of dangerous attribute names ---

_SINKS = {
    "os": {
        "system": "code_exec",
        "popen": "code_exec",
        "spawnl": "code_exec",
        "spawnv": "code_exec",
        "execl": "code_exec",
        "execv": "code_exec",
        "open": "file_read",      # os.open defaults to O_RDONLY; write flags need int parsing (deferred)
        "read": "file_read",
        "write": "file_write",
        "remove": "file_write",
        "unlink": "file_write",
        "rmdir": "file_write",
    },
    "subprocess": {
        "run": "code_exec",
        "Popen": "code_exec",
        "call": "code_exec",
        "check_call": "code_exec",
        "check_output": "code_exec",
    },
    "shutil": {
        "copy": "file_write",
        "copyfile": "file_write",
        "copy2": "file_write",
        "move": "file_write",
        "rmtree": "file_write",
    },
    "httpx": {
        "request": "network",
        "get": "network",
        "post": "network",
        "put": "network",
        "delete": "network",
        "patch": "network",
        "head": "network",
        "stream": "network",
    },
    "requests": {
        "request": "network",
        "get": "network",
        "post": "network",
        "put": "network",
        "delete": "network",
        "patch": "network",
        "head": "network",
    },
    "urllib": {
        "urlopen": "network",
        "urlretrieve": "network",
    },
    "urllib.request": {
        "urlopen": "network",
        "urlretrieve": "network",
    },
    "socket": {
        "socket": "network",
    },
    "http.client": {
        "request": "network",
    },
}

# Highly-specific method names that are safe to match on the attribute alone
# (no false positives in practice — these only appear on file/network objects).
_UNPREFIXED_SINKS = {
    "read_text": "file_read",
    "read_bytes": "file_read",
    "write_text": "file_write",
    "write_bytes": "file_write",
}

# open() mode characters that imply writing (in addition to default read).
_WRITE_MODE_CHARS = ("w", "a", "x", "+")


def classify_tool(func_node: ast.FunctionDef) -> List[str]:
    """Return the sorted list of capabilities for a tool function body.

    Args:
        func_node: the ast.FunctionDef of a `@tool`-decorated function.

    Returns:
        Sorted, de-duplicated capability names (e.g. ["code_exec", "network"]).
    """
    caps = set()

    for call in ast.walk(func_node):
        if not isinstance(call, ast.Call):
            continue
        cap = _classify_call(call)
        if cap:
            caps.add(cap)

    return sorted(caps)


def _classify_call(call: ast.Call) -> Optional[str]:
    """Classify a single call node, or None if it is not a known sink."""
    if isinstance(call.func, ast.Name):
        return _classify_bare_call(call.func.id, call)

    if isinstance(call.func, ast.Attribute):
        obj_path = _resolve_attribute_path(call.func.value)
        attr = call.func.attr

        # Unprefixed, highly-specific method names (Path.read_text etc).
        if attr in _UNPREFIXED_SINKS:
            return _UNPREFIXED_SINKS[attr]

        # Object-prefixed sinks keyed by the full resolved path.
        if obj_path in _SINKS and attr in _SINKS[obj_path]:
            cap = _SINKS[obj_path][attr]
            # open() needs its mode argument inspected to split read vs write.
            if attr == "open" and cap == "file_read":
                return _open_mode_capability(call)
            return cap

    return None


def _classify_bare_call(name: str, call: ast.Call) -> Optional[str]:
    """Classify a bare (non-attribute) call such as exec(), eval(), open()."""
    if name in _EXEC_BUILTINS:
        return "code_exec"
    if name == "open":
        return _open_mode_capability(call)
    return None


def _resolve_attribute_path(value: ast.expr) -> str:
    """Resolve a dotted object path to a dotted string, e.g. urllib.request.

    Returns '' if the value is not a simple name/attribute chain (e.g. a call
    result, subscript, or variable-of-unknown-type).
    """
    if isinstance(value, ast.Name):
        return value.id
    if isinstance(value, ast.Attribute):
        parent = _resolve_attribute_path(value.value)
        return f"{parent}.{value.attr}" if parent else value.attr
    return ""


def _open_mode_capability(call: ast.Call) -> str:
    """Decide file_read vs file_write for an open(...) call from its mode arg.

    open(path, mode=...) — a literal write-mode string implies write; anything
    else (read-mode literal, no mode, or a variable) defaults to read, since
    open() without a mode is read-only. Precision over recall: we would rather
    miss a write than wrongly flag a read as a write.
    """
    mode = _open_mode_arg(call)
    if mode is None:
        return "file_read"
    return "file_write" if any(c in mode for c in _WRITE_MODE_CHARS) else "file_read"


def _open_mode_arg(call: ast.Call) -> Optional[str]:
    """Return the literal string value of open()'s mode argument, or None."""
    # Positional: open(path, mode) -> call.args[1]
    if len(call.args) >= 2:
        arg = call.args[1]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            return arg.value
    # Keyword: open(path, mode='w') -> call.keywords
    for kw in call.keywords:
        if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
            if isinstance(kw.value.value, str):
                return kw.value.value
    return None
