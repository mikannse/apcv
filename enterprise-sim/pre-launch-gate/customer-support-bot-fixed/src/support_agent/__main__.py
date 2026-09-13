"""CLI entry point."""
import sys

from support_agent.graph import graph


def main() -> int:
    print(f"SupportBot graph compiled: {graph is not None}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
