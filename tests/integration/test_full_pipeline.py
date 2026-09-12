"""Integration test for full pipeline"""
import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile
from apcv.core.scanners.tool_scanner import ToolScanner
from apcv.core.frameworks.langgraph_adapter import LangGraphAdapter
from apcv.core.policy.validator import PolicyValidator
from apcv.core.probes.library import ProbeLibrary
from apcv.core.probes.generator import ProbeGenerator
from apcv.core.conformance import ConformanceResult


def test_full_validation_pipeline():
    """Test complete validation pipeline"""
    agent_code = '''
from langraph import tool

@tool
def search(query: str) -> str:
    """Search documents"""
    return f"Results for {query}"
'''

    policy_yaml = '''
metadata:
  name: "Test Policy"
boundaries:
  tool:
    allowed_tools:
      - search
    denied_tools: []
'''

    with NamedTemporaryFile(mode='w', suffix='.py', delete=False) as agent_f:
        agent_f.write(agent_code)
        agent_f.flush()
        agent_path = agent_f.name

    with NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as policy_f:
        policy_f.write(policy_yaml)
        policy_f.flush()
        policy_path = policy_f.name

    try:
        # Discover tools
        adapter = LangGraphAdapter()
        scanner = ToolScanner()
        sbom = scanner.scan(agent_path, adapter)
        assert len(sbom.tools) == 1

        # Load policy
        validator = PolicyValidator()
        policy = validator.load_policy(policy_path)
        assert policy.metadata.name == "Test Policy"

        # Generate probes
        library = ProbeLibrary()
        generator = ProbeGenerator(library)
        probes = generator.generate(policy)
        assert len(probes) > 0

        # Check conformance
        result = ConformanceResult(sbom, policy)
        result.detect_violations()
        score = result.calculate_score()

        assert score == 100
        assert result.verdict == "PASS"

    finally:
        Path(agent_path).unlink()
        Path(policy_path).unlink()
