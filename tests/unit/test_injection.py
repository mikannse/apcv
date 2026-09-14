"""Tests for shallow injection probe generation."""
from apcv.core.probes.injection import generate_injection_probes
from apcv.core.probes.targeting import is_string_param
from apcv.core.scanners.tool_scanner import ToolScanner
from apcv.core.frameworks.langgraph_adapter import LangGraphAdapter
from apcv.core.policy.validator import PolicyValidator
from apcv.core.policy.schema import Policy, Metadata
from apcv.core.utils.sbom import SBOM, Tool, ToolParameter, Metadata as SBOMetadata


SAMPLE_AGENT = "tests/fixtures/sample_agents/simple_agent.py"
SAMPLE_POLICY = "tests/fixtures/policies/read_only.yaml"


def _sbom():
    return ToolScanner().scan(SAMPLE_AGENT, LangGraphAdapter())


def _policy():
    return PolicyValidator().load_policy(SAMPLE_POLICY)


def _cap_sbom(tools):
    return SBOM(agent_path="/a.py", metadata=SBOMetadata(framework="langgraph"),
                tools=tools)


def test_is_string_param():
    def p(t):
        return ToolParameter(name="x", type=t)
    assert is_string_param(p("str"))
    assert is_string_param(p("Optional[str]"))
    assert not is_string_param(p("int"))
    assert not is_string_param(p("List[str]"))
    assert not is_string_param(p("Dict[str, str]"))
    assert not is_string_param(p(""))  # unknown -> non-string


def test_generic_payloads_for_tools_without_capabilities():
    """sample agent tools are pure string logic -> generic payload suite."""
    probes = generate_injection_probes(_sbom(), _policy())

    # search_documents(query:str) -> 3 payloads
    # get_issue(issue_id:int)   -> 0 (int, not injected)
    # list_repos(user:str, limit:int=10) -> 3 (user only)
    assert len(probes) == 6

    ids = {p.id for p in probes}
    assert "inject_search_documents_query_cmd" in ids
    assert "inject_search_documents_query_sql" in ids
    assert "inject_search_documents_query_path" in ids
    assert "inject_list_repos_user_cmd" in ids
    assert not any("get_issue" in i for i in ids)
    assert not any("limit" in i for i in ids)


def test_capability_directed_payload_for_code_exec():
    tool = Tool(id="run_python", name="run_python", module="tools",
                parameters=[ToolParameter(name="snippet", type="str")],
                capabilities=["code_exec"])
    probes = generate_injection_probes(_cap_sbom([tool]), _policy())

    assert len(probes) == 1
    p = probes[0]
    # Semantically-correct payload: valid Python, not a shell fragment.
    assert "__import__('os').system" in p.test_command
    assert "snippet" in p.test_command
    assert p.severity == "critical"


def test_capability_directed_payload_for_network():
    tool = Tool(id="fetch_external_url", name="fetch_external_url", module="tools",
                parameters=[ToolParameter(name="url", type="str")],
                capabilities=["network"])
    probes = generate_injection_probes(_cap_sbom([tool]), _policy())

    assert len(probes) == 1
    assert "169.254.169.254" in probes[0].test_command
    assert probes[0].severity == "critical"


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
        compile(p.test_command, "<probe>", "exec")


def test_payload_reaches_real_tool():
    """The generated command actually invokes the real tool (no fake names)."""
    probes = generate_injection_probes(_sbom(), _policy())
    cmd = next(p for p in probes if p.id == "inject_search_documents_query_cmd")
    assert "search_documents" in cmd.test_command
    assert "$(rm -rf /)" in cmd.test_command
