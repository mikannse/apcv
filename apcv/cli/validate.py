"""Main CLI orchestration"""
import typer
from pathlib import Path
from apcv.core.scanners.tool_scanner import ToolScanner
from apcv.core.frameworks.langgraph_adapter import LangGraphAdapter
from apcv.core.policy.validator import PolicyValidator
from apcv.core.probes.library import ProbeLibrary
from apcv.core.probes.generator import ProbeGenerator
from apcv.core.conformance import ConformanceResult

app = typer.Typer(help="Agent Policy Conformance Validator")


@app.command()
def validate(
    agent: str = typer.Option(..., help="Path to Agent code"),
    policy: str = typer.Option(..., help="Path to Policy YAML"),
    output: str = typer.Option("json", help="Output format"),
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

        # 4. Check conformance
        typer.echo("📋 Step 4: Checking conformance...", err=True)
        result = ConformanceResult(sbom, policy_obj)
        result.detect_violations()
        score = result.calculate_score()
        typer.echo(f"✅ Compliance Score: {score}/100 ({result.verdict})", err=True)

        # Output results
        if output == "json":
            import json
            report = {
                "verdict": result.verdict,
                "compliance_score": score,
                "tools_discovered": len(sbom.tools),
                "probes_generated": len(probes),
                "violations": [{"type": v.type, "description": v.description} for v in result.violations]
            }
            typer.echo(json.dumps(report, indent=2))

        exit_code = 0 if score >= 95 else (1 if score >= 70 else 2)
        raise typer.Exit(code=exit_code)

    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=2)


if __name__ == "__main__":
    app()
