"""LangGraph framework adapter"""
import ast
from pathlib import Path
from typing import List, Dict, Any, Optional
from apcv.core.frameworks.adapter import FrameworkAdapter
from apcv.core.scanners.capability import classify_tool
from apcv.core.utils.sbom import Tool, ToolParameter, MCPServer, SubAgent


class LangGraphAdapter(FrameworkAdapter):
    """Adapter for LangGraph framework"""

    def __init__(self):
        self.source_code: Optional[str] = None
        self.tree: Optional[ast.AST] = None

    def parse_agent_file(self, path: Path) -> ast.AST:
        """Parse Python file and return AST"""
        self.source_code = path.read_text(encoding="utf-8")
        self.tree = ast.parse(self.source_code)
        return self.tree

    def extract_tools(self, ast_tree: ast.AST) -> List[Tool]:
        """Extract @tool decorated functions from AST"""
        tools = []

        if ast_tree is None:
            return tools

        # Walk AST looking for functions with @tool decorator
        for node in ast.walk(ast_tree):
            if isinstance(node, ast.FunctionDef):
                # Check if function has @tool decorator
                for decorator in node.decorator_list:
                    decorator_name = self._get_decorator_name(decorator)
                    if decorator_name == "tool":
                        tool = self._extract_tool_from_function(node)
                        if tool:
                            tools.append(tool)
                        break

        return tools

    def extract_mcp_servers(self, ast_tree: ast.AST) -> List[MCPServer]:
        """Extract MCP connection declarations from AST (static, route A).

        Recognizes two APIs:
          * `MultiServerMCPClient({...})` — a dict literal of server name ->
            config dict (transport / url / command / args).
          * `MCPAdapter(<target>)` — a single target (URL string, or an object).

        A config that references a variable (e.g. `MultiServerMCPClient(cfg)`)
        is recorded as an unresolved entry, not silently dropped. Tool
        enumeration (what each server exposes) is NOT done here — that needs
        runtime list_tools (route B).
        """
        servers: List[MCPServer] = []

        if ast_tree is None:
            return servers

        for node in ast.walk(ast_tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not isinstance(func, ast.Name):
                continue

            if func.id == "MultiServerMCPClient":
                servers.extend(self._extract_multiserver(node))
            elif func.id == "MCPAdapter":
                servers.extend(self._extract_mcp_adapter(node))

        return servers

    def _extract_multiserver(self, call: ast.Call) -> List[MCPServer]:
        """Extract servers from a MultiServerMCPClient({...}) call."""
        if not call.args:
            return []

        arg = call.args[0]
        # Variable reference (e.g. MultiServerMCPClient(servers_config)).
        if isinstance(arg, ast.Name):
            return [MCPServer(name="<unresolved>", unresolved=True)]

        if not isinstance(arg, ast.Dict):
            return []

        servers = []
        for key, value in zip(arg.keys, arg.values):
            name = key.value if isinstance(key, ast.Constant) else "<unknown>"
            servers.append(MCPServer(name=name, **self._parse_server_config(value)))
        return servers

    def _parse_server_config(self, value: ast.expr) -> Dict[str, Any]:
        """Parse a single server's config dict into MCPServer fields."""
        transport = "unknown"
        url = ""
        command = ""
        args: List[str] = []

        if isinstance(value, ast.Dict):
            for k, v in zip(value.keys, value.values):
                if not (isinstance(k, ast.Constant) and isinstance(k.value, str)):
                    continue
                field = k.value
                if field == "transport":
                    transport = v.value if isinstance(v, ast.Constant) else "unknown"
                elif field == "url":
                    url = v.value if isinstance(v, ast.Constant) else ""
                elif field == "command":
                    command = v.value if isinstance(v, ast.Constant) else ""
                elif field == "args":
                    if isinstance(v, ast.List):
                        args = [e.value for e in v.elts if isinstance(e, ast.Constant)]

        return {"transport": transport, "url": url, "command": command, "args": args}

    def _extract_mcp_adapter(self, call: ast.Call) -> List[MCPServer]:
        """Extract a single server from an MCPAdapter(<target>) call."""
        if not call.args:
            return []

        arg = call.args[0]
        # URL string target -> http transport (inferred).
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            return [MCPServer(name=arg.value, transport="http", url=arg.value)]

        # Any other target (fastmcp.Client, MCPConfig, variable) is not
        # statically resolvable to a concrete endpoint.
        return [MCPServer(name="<unresolved>", unresolved=True)]

    def extract_subagents(self, ast_tree: ast.AST) -> List[SubAgent]:
        """Extract create_agent(...) declarations and their tools lists (static).

        Enumerates every `create_agent(tools=[...])` call — parent and child
        agents alike (they are the same function). Each becomes a SubAgent with
        the tools declared in its `tools=[...]` list. Inheritance chains (who
        invokes whom) are NOT traced — that is implicit at runtime and unreliable
        to reconstruct statically.
        """
        subagents: List[SubAgent] = []

        if ast_tree is None:
            return subagents

        for node in ast.walk(ast_tree):
            # Assigned form:  fruit_agent = create_agent(tools=[...])
            if isinstance(node, ast.Assign) and self._is_create_agent(node.value):
                name = self._target_name(node.targets[0])
                subagents.append(self._build_subagent(name, node.value))
            # Bare call form:  create_agent(tools=[...])
            elif isinstance(node, ast.Expr) and self._is_create_agent(node.value):
                subagents.append(self._build_subagent("<unnamed>", node.value))

        return subagents

    @staticmethod
    def _is_create_agent(node: ast.expr) -> bool:
        return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "create_agent"

    @staticmethod
    def _target_name(target: ast.expr) -> str:
        return target.id if isinstance(target, ast.Name) else "<unnamed>"

    def _build_subagent(self, name: str, call: ast.Call) -> SubAgent:
        """Build a SubAgent from a create_agent call's tools=[...] kwarg."""
        tools_kw = next(
            (kw for kw in call.keywords if kw.arg == "tools"),
            None,
        )
        if tools_kw is None:
            return SubAgent(name=name)

        tools, unresolved = self._parse_tools_list(tools_kw.value)
        return SubAgent(name=name, tools=tools, unresolved=unresolved)

    def _parse_tools_list(self, value: ast.expr) -> (List[str], bool):
        """Parse a create_agent tools=[...] argument into (names, unresolved).

        Handles ast.List literals (Name function refs / Constant string names).
        A variable reference marks the whole list unresolved.
        """
        if isinstance(value, ast.Name):
            return [], True

        if not isinstance(value, ast.List):
            return [], False

        names = []
        for elt in value.elts:
            if isinstance(elt, ast.Name):
                names.append(elt.id)
            elif isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                names.append(elt.value)
            # Other forms (calls, nested lists) are skipped.
        return names, False

    def _get_decorator_name(self, decorator: ast.expr) -> Optional[str]:
        """Extract decorator name from AST node"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return decorator.attr
        return None

    def _extract_tool_from_function(self, func: ast.FunctionDef) -> Optional[Tool]:
        """Extract tool metadata from function definition"""
        try:
            tool_id = func.name
            parameters = self._extract_parameters(func)

            return Tool(
                id=tool_id,
                name=tool_id,
                module=self._extract_module_path(),
                parameters=parameters,
                description=ast.get_docstring(func) or "",
                capabilities=classify_tool(func),
            )
        except Exception:
            return None

    def _extract_parameters(self, func: ast.FunctionDef) -> List[ToolParameter]:
        """Extract function parameters"""
        parameters = []

        for arg in func.args.args:
            param = ToolParameter(name=arg.arg)

            # Try to get type annotation
            if arg.annotation:
                param.type = self._get_type_string(arg.annotation)

            parameters.append(param)

        # Handle defaults
        defaults = func.args.defaults
        num_defaults = len(defaults)
        num_args = len(func.args.args)

        for i in range(num_args - num_defaults, num_args):
            param_idx = i - (num_args - num_defaults)
            parameters[i].required = False
            parameters[i].default = ast.unparse(defaults[param_idx])

        return parameters

    def _get_type_string(self, annotation: ast.expr) -> str:
        """Convert type annotation AST node to string"""
        try:
            return ast.unparse(annotation)
        except Exception:
            return "Any"

    def _extract_module_path(self) -> str:
        """Extract module path from source"""
        return "agent"
