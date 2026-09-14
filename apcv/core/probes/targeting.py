"""Parameter targeting shared by shallow injection and deep canary generators.

Both tiers need to locate the semantically-relevant string parameter for a
dangerous capability (e.g. the `url` parameter for a network tool). Centralize
that here so the two stay consistent and the keyword table lives in one place.
"""
from __future__ import annotations

from typing import Optional, Tuple

from apcv.core.utils.sbom import Tool, ToolParameter


# parameter-name keywords used to locate the semantically-relevant parameter
# for each capability.
PARAM_KEYWORDS = {
    "code_exec": ("code", "snippet", "script", "python", "cmd", "command", "expr", "source"),
    "file_read": ("path", "file", "filename", "file_path", "dir", "directory"),
    "file_write": ("path", "file", "filename", "file_path", "dir", "directory"),
    "network": ("url", "endpoint", "host", "uri", "link", "target", "address"),
}


def is_string_param(p: ToolParameter) -> bool:
    """Return True for a scalar string type (str, Optional[str], ...).

    Container types (List[str], Dict[str, str]) are excluded — injecting a bare
    payload into a list/dict slot is meaningless. Unknown types default to
    non-string so we only inject where the signature is clearly a string.
    """
    t = (p.type or "").strip()
    if t == "str":
        return True
    # Optional[str], Union[str, None], Annotated[str, ...] wrap a scalar str.
    base = t.split("[")[0].strip()
    if base in ("Optional", "Union", "Annotated"):
        inner = t[t.index("[") + 1: t.rindex("]")].split(",")[0].strip()
        return inner == "str"
    return False


def locate_param(tool: Tool, capability: str) -> Optional[ToolParameter]:
    """Return the parameter to inject into for a capability, or None.

    Precision over recall: only a string parameter whose name matches the
    capability's semantics is returned. Otherwise we do not guess and return
    None so the caller can skip the tier for that tool.
    """
    keywords = PARAM_KEYWORDS.get(capability, ())
    for p in tool.parameters:
        if is_string_param(p) and any(k in p.name.lower() for k in keywords):
            return p
    return None
