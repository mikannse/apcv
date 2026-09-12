"""CLI main entry point"""
import typer
from pathlib import Path
from apcv.core.scanners.tool_scanner import ToolScanner
from apcv.core.frameworks.langgraph_adapter import LangGraphAdapter

app = typer.Typer(help="Agent Policy Conformance Validator")


@app.command()
def validate(
    agent: str = typer.Option(..., help="Path to Agent code"),
    policy: str = typer.Option(
        None, help="Path to Policy YAML (optional for this phase)"
    ),
    output: str = typer.Option(
        "json", help="Output format: json, sarif, or html"
    ),
):
    """Validate an Agent against a policy"""
    try:
        # Initialize components
        adapter = LangGraphAdapter()
        scanner = ToolScanner()

        # Scan agent for tools
        typer.echo(f"📋 Scanning {agent}...", err=True)
        sbom = scanner.scan(agent, adapter)

        # Print results
        typer.echo(f"\n✅ Found {len(sbom.tools)} tools:")
        for tool in sbom.tools:
            typer.echo(f"  - {tool.name} ({len(tool.parameters)} parameters)")

        if output == "json":
            typer.echo(sbom.json(indent=2))
        else:
            typer.echo(f"Output format {output} not yet implemented")

        # Save SBOM
        sbom_dir = Path(".apcv/sbom")
        sbom_dir.mkdir(parents=True, exist_ok=True)
        sbom_file = sbom_dir / "tool.json"
        sbom_file.write_text(sbom.json())
        typer.echo(f"\n📁 SBOM saved to {sbom_file}", err=True)

    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=2)


if __name__ == "__main__":
    app()

