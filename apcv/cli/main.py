"""CLI main entry point"""
import json
from datetime import datetime
from pathlib import Path

import typer

from apcv.core.scanners.tool_scanner import ToolScanner
from apcv.core.frameworks.langgraph_adapter import LangGraphAdapter
from apcv.core.policy.validator import PolicyValidator
from apcv.core.probes.baseline import generate_baseline_probes
from apcv.core.probes.injection import generate_injection_probes
from apcv.core.probes.denied import generate_denied_tool_probes
from apcv.core.probes.canary import generate_canary_probes
from apcv.core.conformance import ConformanceResult, Violation
from apcv.core.execution.executor import IsolatedExecutor, DockerUnavailableError
from apcv.core.execution.trace_model import ExecutionReport

app = typer.Typer(help="Agent Policy Conformance Validator")


@app.command()
def validate(
    agent: str = typer.Option(..., help="Path to Agent code"),
    policy: str = typer.Option(..., help="Path to Policy YAML"),
    output: str = typer.Option("json", help="Output format: json, sarif, or html"),
    skip_execution: bool = typer.Option(
        False, "--skip-execution", help="Skip probe execution (static-only analysis)"
    ),
    workers: int = typer.Option(4, help="Probe execution concurrency"),
):
    """Complete validation pipeline"""
    try:
        # 1. Discover tools
        typer.echo("📋 Step 1: Discovering tools...", err=True)
        adapter = LangGraphAdapter()
        scanner = ToolScanner()
        agent_path = Path(agent)
        if agent_path.is_dir():
            # A real enterprise agent is a whole codebase, not one file. Walk
            # the package and merge every module's @tool into one SBOM.
            sbom = scanner.scan_package(str(agent_path), adapter)
        else:
            sbom = scanner.scan(agent, adapter)
        typer.echo(f"✅ Found {len(sbom.tools)} tools", err=True)

        # 2. Load policy
        typer.echo("📋 Step 2: Loading policy...", err=True)
        validator = PolicyValidator()
        policy_obj = validator.load_policy(policy)
        typer.echo(f"✅ Policy loaded: {policy_obj.metadata.name}", err=True)

        # 3. Generate probes (all SBOM-driven)
        typer.echo("📋 Step 3: Generating probes...", err=True)
        # Baseline probes record each declared tool's real behavior (audit
        # evidence); derived from the SBOM.
        baseline_probes = generate_baseline_probes(sbom, policy_obj)
        # Injection probes target each string parameter with a malicious
        # payload to detect parameter-validation gaps; also SBOM-derived.
        injection_probes = generate_injection_probes(sbom, policy_obj)
        # Denied-tool probes really invoke each policy-denied tool to confirm
        # it is reachable at runtime (replaces the old hard-coded fake names).
        denied_probes = generate_denied_tool_probes(sbom, policy_obj)
        # Canary probes prove a dangerous action actually happened (deep tier),
        # directed by each tool's statically-detected capabilities.
        canary_probes = generate_canary_probes(sbom, policy_obj)
        probes = baseline_probes + injection_probes + denied_probes + canary_probes
        typer.echo(
            f"✅ Generated {len(probes)} probes "
            f"({len(baseline_probes)} baseline, {len(injection_probes)} injection, "
            f"{len(denied_probes)} denied, {len(canary_probes)} canary)",
            err=True,
        )

        # 4. Check conformance (static: SBOM vs policy)
        typer.echo("📋 Step 4: Checking conformance...", err=True)
        result = ConformanceResult(sbom, policy_obj)
        result.detect_violations()

        # 5. Execute probes (dynamic: real boundary-violation attempts)
        execution_traces = []
        if skip_execution:
            typer.echo("⚠️  Skipping probe execution (static-only analysis)", err=True)
        elif agent_path.is_dir():
            # Package-mode dynamic execution needs the agent's runtime deps
            # shipped into the probe image and a package-aware ProbeHost — a
            # separate work stream. Static discovery + conformance still runs.
            typer.echo(
                "⚠️  Directory agent: dynamic probe execution not yet supported "
                "for packages (static-only analysis)",
                err=True,
            )
        else:
            typer.echo("📋 Step 5: Executing probes...", err=True)
            try:
                executor = IsolatedExecutor()
                executor.build_image_if_missing()
                # Only agent + baseline probes run. The sandbox is a fixed
                # isolation cage, not a policy enforcer, so there are no
                # "shell" probes that self-check it — that whole category was
                # measuring the wrong thing (whether the cage blocks, when the
                # cage must NOT block to let us observe the agent).
                agent_traces = executor.execute_agent_probes(probes, agent, policy_obj)
                execution_traces = agent_traces

                for trace in agent_traces:
                    if trace.violation:
                        result.violations.append(
                            Violation(
                                "boundary_breach",
                                f"Probe '{trace.probe_id}': agent tool surface breached — {trace.output.strip()[:120]}",
                                severity=trace.severity,
                            )
                        )

                agent_violations = sum(1 for t in agent_traces if t.violation)
                baseline_count = sum(1 for t in agent_traces if t.execution == "baseline")
                typer.echo(
                    f"✅ Executed {len(execution_traces)} probes "
                    f"({len(agent_traces) - baseline_count} agent, "
                    f"{baseline_count} baseline), "
                    f"{agent_violations} agent violations",
                    err=True,
                )
            except DockerUnavailableError as e:
                typer.echo(f"⚠️  {e} — falling back to static-only analysis", err=True)

        score = result.calculate_score()
        typer.echo(f"✅ Compliance Score: {score}/100 ({result.verdict})", err=True)

        # 6. Persist report (AD-8)
        report_path = _write_report(sbom, policy_obj, probes, result, execution_traces, agent)
        typer.echo(f"📁 Report saved to {report_path}", err=True)

        # Output results (json / sarif / html)
        report = {
            "verdict": result.verdict,
            "compliance_score": score,
            "tools_discovered": len(sbom.tools),
            "probes_generated": len(probes),
            "probes_executed": len(execution_traces),
            "report_path": str(report_path),
            "agent_path": str(Path(agent).absolute()),
            "policy_name": policy_obj.metadata.name,
            "violations": [
                {"type": v.type, "description": v.description, "severity": v.severity}
                for v in result.violations
            ],
        }

        from apcv.cli.output import format_json, format_sarif, format_html

        if output == "json":
            typer.echo(format_json(report))
        elif output == "sarif":
            typer.echo(format_sarif(report))
        elif output == "html":
            typer.echo(format_html(report))
        else:
            typer.echo(f"Output format {output} not yet implemented", err=True)
            raise typer.Exit(code=2)

        exit_code = 0 if score >= 95 else (1 if score >= 70 else 2)

    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=2)

    raise typer.Exit(code=exit_code)


def _write_report(sbom, policy_obj, probes, result, execution_traces, agent_path):
    """Persist a full execution report to .apcv/reports/ (AD-8)."""
    report_dir = Path(".apcv/reports")
    report_dir.mkdir(parents=True, exist_ok=True)

    agent_name = Path(agent_path).stem
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    # Collect tool-invocation recordings from all agent probes (audit evidence).
    records = []
    for trace in execution_traces:
        records.extend(trace.records)

    report = ExecutionReport(
        agent_path=str(Path(agent_path).absolute()),
        policy_name=policy_obj.metadata.name,
        probes_run=len(execution_traces),
        violations=[t for t in execution_traces if t.violation],
        traces=execution_traces,
        records=records,
    )

    report_path = report_dir / f"{timestamp}_{agent_name}.json"
    report_path.write_text(
        json.dumps(report.model_dump(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return report_path


@app.command()
def web(
    host: str = typer.Option("127.0.0.1", help="Host to bind the UI server"),
    port: int = typer.Option(8000, help="Port to bind the UI server"),
):
    """Start the Web UI dashboard (FastAPI + uvicorn)"""
    import uvicorn
    from apcv.web.backend import app as web_app

    typer.echo(f"🌐 APCV Web UI running on http://{host}:{port}", err=True)
    uvicorn.run(web_app, host=host, port=port)


if __name__ == "__main__":
    app()
