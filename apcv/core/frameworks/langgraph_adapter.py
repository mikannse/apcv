"""LangGraph framework adapter"""
import ast
from pathlib import Path
from typing import List, Dict, Any, Optional
from apcv.core.frameworks.adapter import FrameworkAdapter
from apcv.core.utils.sbom import Tool, ToolParameter


class LangGraphAdapter(FrameworkAdapter):
    """Adapter for LangGraph framework"""

    def __init__(self):
        self.source_code: Optional[str] = None
        self.tree: Optional[ast.AST] = None

    def parse_agent_file(self, path: Path) -> ast.AST:
        """Parse Python file and return AST"""
        self.source_code = path.read_text()
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
