"""Pre-launch security gate: scan a LangGraph agent PACKAGE against a policy.

A real enterprise agent is a whole codebase, not one file. This thin CI
integration wraps APCV: it walks the package, scans every Python module for
@tool definitions, merges them into a single SBOM, runs the conformance check
against the release baseline, and exits non-zero on failure so CI can block
the merge.

Usage:
    python gate.py --agent customer-support-bot --policy policy/release_baseline.yaml
Exit codes:
    0  PASS (compliance >= 95)
    1  WARN (70 <= score < 95)
    2  FAIL (score < 70)
"""
import argparse
import json
import sys
from pathlib import Path

# Make the repo's `apcv` importable regardless of where gate.py is invoked
# from (CI checkout roots vary). gate.py sits at <repo>/enterprise-sim/pre-launch-gate/.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from apcv.core.scanners.tool_scanner import ToolScanner
from apcv.core.frameworks.langgraph_adapter import LangGraphAdapter
from apcv.core.policy.validator import PolicyValidator
from apcv.core.conformance import ConformanceResult


def scan_package(pkg_dir: Path):
    """Scan every .py file under pkg_dir and merge into one SBOM.

    Thin wrapper over the built-in ToolScanner.scan_package() (story 4.1).
    Returns (sbom, n_files) for the report's `files_scanned` field.
    """
    scanner = ToolScanner()
    adapter = LangGraphAdapter()
    sbom = scanner.scan_package(str(pkg_dir), adapter)
    n_files = len([p for p in sorted(pkg_dir.rglob("*.py"))
                   if not any(part in ("tests", "__pycache__") for part in p.parts)])
    return sbom, n_files


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="APCV pre-launch gate (package scan)")
    p.add_argument("--agent", required=True, help="path to agent package")
    p.add_argument("--policy", required=True, help="path to policy YAML")
    p.add_argument("--output", default="json", choices=["json", "text"])
    args = p.parse_args(argv)

    pkg = Path(args.agent).resolve()
    if not pkg.is_dir():
        print(f"error: --agent must be a package directory: {pkg}", file=sys.stderr)
        return 2

    sbom, n_files = scan_package(pkg)
    policy = PolicyValidator().load_policy(args.policy)

    result = ConformanceResult(sbom, policy)
    result.detect_violations()
    score = result.calculate_score()

    report = {
        "agent": str(pkg),
        "files_scanned": n_files,
        "tools_discovered": len(sbom.tools),
        "tools": [
            {"name": t.name, "source": t.module,
             "description": (t.description or "").strip().splitlines()[0][:80]}
            for t in sorted(sbom.tools, key=lambda x: x.name)
        ],
        "violations": [
            {"type": v.type, "severity": v.severity, "description": v.description}
            for v in result.violations
        ],
        "compliance_score": score,
        "verdict": result.verdict,
    }

    if args.output == "json":
        print(json.dumps(report, indent=2))
    else:
        print(f"agent={pkg.name}  tools={len(sbom.tools)}  score={score}  "
              f"verdict={result.verdict}")
        for v in result.violations:
            print(f"  [{v.severity}] {v.type}: {v.description}")

    return 0 if score >= 95 else (1 if score >= 70 else 2)


if __name__ == "__main__":
    raise SystemExit(main())
