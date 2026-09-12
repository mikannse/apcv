"""Framework adapter interface"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from pathlib import Path


class FrameworkAdapter(ABC):
    """Abstract base class for framework adapters"""

    @abstractmethod
    def parse_agent_file(self, path: Path) -> Any:
        """
        Parse agent code file and return AST representation

        Args:
            path: Path to agent file

        Returns:
            AST-like representation (framework specific)
        """
        pass

    @abstractmethod
    def extract_tools(self, ast_tree: Any) -> list:
        """
        Extract tool definitions from parsed agent

        Args:
            ast_tree: Parsed agent AST

        Returns:
            List of tool definitions
        """
        pass
