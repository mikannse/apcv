"""Tests for dynamic injection probe generation."""
from apcv.core.probes.injection import generate_injection_probes, _is_string_param
from apcv.core.scanners.tool_scanner import ToolScanner
from apcv.core.frameworks.langgraph_adapter import LangGraphAdapter
from apcv.core.policy.validator import PolicyValidator


SAMPLE_AGENT = "tests/fixtures/sample_agents/simple_agent.py"
SAMPLE_POLICY = "tests/fixtures/policies/read_only.yaml"


def _sbom():
    return ToolScanner().scan(SAMPLE_AGENT, LangGraphAdapter())


def _policy():
    return PolicyValidator().load_policy(SAMPLE_POLICY)


def test_is_string_param():
    assert _is_string_param("str")
    assert _is_string_param("Optional[str]")
    assert not _is_string_param("int")
    assert not _is_string_param("List[str]")
    assert not _is_string_param("Dict[str, str]")
    assert not _is_string_param("")  # unknown -> non-string


def test_generates_per_string_param_times_payloads():
    sbom = _sbom()
    probes = generate_injection_probes(sbom, _policy())

    # search_documents(query:str) -> 3 payloads
    # get_issue(issue_id:int)   -> 0 (int, not injected)
    # list_repos(user:str, limit:int=10) -> 3 (user only)
    assert len(probes) == 6

    # All three tools are covered appropriately.
    ids = {p.id for p in probes}
    assert "inject_search_documents_query_cmd" in ids
    assert "inject_search_documents_query_sql" in ids
    assert "inject_search_documents_query_path" in ids
    assert "inject_list_repos_user_cmd" in ids
    # get_issue has no string parameter -> no probes.
    assert not any("get_issue" in i for i in ids)
    # limit is int -> no probes.
    assert not any("limit" in i for i in ids)


def test_probe_shape():
    probes = generate_injection_probes(_sbom(), _policy())
    assert all(p.execution == "agent" for p in probes)
    assert all(p.category == "parameter" for p in probes)
    assert all(p.severity in ("critical", "high") for p in probes)
    ids = [p.id for p in probes]
    assert len(ids) == len(set(ids))


def test_test_command_is_valid_python():
    """Every generated test_command must be exec-able against a ProbeHost."""
    probes = generate_injection_probes(_sbom(), _policy())
    for p in probes:
        # Compiling catches syntax errors from bad payload escaping.
        compile(p.test_command, "<probe>", "exec")


def test_payload_reaches_real_tool():
    """The generated command actually invokes the real tool (no fake names)."""
    probes = generate_injection_probes(_sbom(), _policy())
    cmd = next(p for p in probes if p.id == "inject_search_documents_query_cmd")
    assert "search_documents" in cmd.test_command
    assert "$(rm -rf /)" in cmd.test_command
