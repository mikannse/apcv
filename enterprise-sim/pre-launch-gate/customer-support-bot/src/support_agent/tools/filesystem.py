"""Raw host filesystem access (denied by baseline policy).

The bot reads/writes files by absolute path "to load config and cache reports".
That reaches /etc, /var/run/secrets and any mounted volumes -- arbitrary
read/write persistence and secret exposure.
"""
from pathlib import Path

from langgraph.prebuilt import tool


@tool
def read_host_file(path: str) -> str:
    """Read a file from the container/host filesystem by absolute path."""
    return Path(path).read_text(errors="replace")


@tool
def write_report(file_path: str, content: str) -> str:
    """Write content to an arbitrary filesystem path (persist a report)."""
    p = Path(file_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return str(p)
