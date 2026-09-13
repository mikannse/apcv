"""CLI main entry point"""
import json
from datetime import datetime
from pathlib import Path

import typer

from apcv.core.scanners.tool_scanner import ToolScanner
from apcv.core.frameworks.langgraph_adapter import LangGraphAdapter
from apcv.core.policy.validator import PolicyValidator
from apcv.core.probes.library import ProbeLibrary
from apcv.core.probes.generator import ProbeGenerator
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
        sbom = scanner.scan(agent, adapter)
        typer.echo(f"✅ Found {len(sbom.tools)} tools", err=True)

        # 2. Load policy
        typer.echo("📋 Step 2: Loading policy...", err=True)
        validator = PolicyValidator()
        policy_obj = validator.load_policy(policy)
        typer.echo(f"✅ Policy loaded: {policy_obj.metadata.name}", err=True)

        # 3. Generate probes
        typer.echo("📋 Step 3: Generating probes...", err=True)
        library = ProbeLibrary()
        generator = ProbeGenerator(library)
        probes = generator.generate(policy_obj)
        typer.echo(f"✅ Generated {len(probes)} probes", err=True)

        # 4. Check conformance (static: SBOM vs policy)
        typer.echo("📋 Step 4: Checking conformance...", err=True)
        result = ConformanceResult(sbom, policy_obj)
        result.detect_violations()

        # 5. Execute probes (dynamic: real boundary-violation attempts)
        execution_traces = []
        if skip_execution:
            typer.echo("⚠️  Skipping probe execution (static-only analysis)", err=True)
        else:
            typer.echo("📋 Step 5: Executing probes...", err=True)
            try:
                executor = IsolatedExecutor()
                executor.build_image_if_missing()
                execution_traces = executor.execute_shell_probes(probes, policy_obj)
                execution_traces += executor.execute_agent_probes(probes, agent, policy_obj)
                for trace in execution_traces:
                    if trace.violation:
                        result.violations.append(
                            Violation(
                                "boundary_breach",
                                f"Probe '{trace.probe_id}' breached sandbox: {trace.output.strip()[:120]}",
                                severity=trace.severity,
                            )
                        )
                typer.echo(
                    f"✅ Executed {len(execution_traces)} probes, "
                    f"{sum(1 for t in execution_traces if t.violation)} violations",
                    err=True,
                )
            except DockerUnavailableError as e:
                typer.echo(f"⚠️  {e} — falling back to static-only analysis", err=True)

        score = result.calculate_score()
        typer.echo(f"✅ Compliance Score: {score}/100 ({result.verdict})", err=True)

        # 6. Persist report (AD-8)
        report_path = _write_report(sbom, policy_obj, probes, result, execution_traces, agent)
        typer.echo(f"📁 Report saved to {report_path}", err=True)

        # Output results
        if output == "json":
            report = {
                "verdict": result.verdict,
                "compliance_score": score,
                "tools_discovered": len(sbom.tools),
                "probes_generated": len(probes),
                "probes_executed": len(execution_traces),
                "report_path": str(report_path),
                "violations": [
                    {"type": v.type, "description": v.description}
                    for v in result.violations
                ],
            }
            typer.echo(json.dumps(report, indent=2))
        else:
            typer.echo(f"Output format {output} not yet implemented", err=True)

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

    report = ExecutionReport(
        agent_path=str(Path(agent_path).absolute()),
        policy_name=policy_obj.metadata.name,
        probes_run=len(execution_traces),
        violations=[t for t in execution_traces if t.violation],
        traces=execution_traces,
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
