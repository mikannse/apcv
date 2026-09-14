"""Tests for the AST-sink tool capability classifier."""
import ast
import pytest

from apcv.core.scanners.capability import classify_tool


def _tool(code: str) -> ast.FunctionDef:
    """Parse a @tool function body and return its FunctionDef node."""
    tree = ast.parse(code)
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    return fn


# -- code_exec ---------------------------------------------------------------

def test_code_exec_builtin_exec():
    fn = _tool("def f(x: str):\n    exec(x, {})\n")
    assert classify_tool(fn) == ["code_exec"]


def test_code_exec_os_system():
    fn = _tool("import os\ndef f(x: str):\n    os.system(x)\n")
    assert classify_tool(fn) == ["code_exec"]


def test_code_exec_subprocess_run():
    fn = _tool("import subprocess\ndef f(x: str):\n    subprocess.run([x], shell=True)\n")
    assert classify_tool(fn) == ["code_exec"]


# -- file read/write ---------------------------------------------------------

def test_file_read_default_open():
    fn = _tool("def f(p: str):\n    open(p)\n")
    assert classify_tool(fn) == ["file_read"]


def test_file_write_open_w_mode():
    fn = _tool("def f(p: str):\n    open(p, 'w')\n")
    assert classify_tool(fn) == ["file_write"]


def test_file_write_open_kw_mode():
    fn = _tool("def f(p: str):\n    open(p, mode='a')\n")
    assert classify_tool(fn) == ["file_write"]


def test_file_read_path_read_text():
    fn = _tool("from pathlib import Path\ndef f(p):\n    Path(p).read_text()\n")
    assert classify_tool(fn) == ["file_read"]


def test_file_write_path_write_text():
    fn = _tool("from pathlib import Path\ndef f(p):\n    Path(p).write_text('x')\n")
    assert classify_tool(fn) == ["file_write"]


def test_file_write_shutil_rmtree():
    fn = _tool("import shutil\ndef f(p):\n    shutil.rmtree(p)\n")
    assert classify_tool(fn) == ["file_write"]


# -- network -----------------------------------------------------------------

def test_network_httpx_get():
    fn = _tool("import httpx\ndef f(u):\n    httpx.get(u)\n")
    assert classify_tool(fn) == ["network"]


def test_network_requests_post():
    fn = _tool("import requests\ndef f(u):\n    requests.post(u, json={})\n")
    assert classify_tool(fn) == ["network"]


def test_network_urllib_request_urlopen():
    fn = _tool("import urllib.request\ndef f(u):\n    urllib.request.urlopen(u)\n")
    assert classify_tool(fn) == ["network"]


def test_network_socket():
    fn = _tool("import socket\ndef f():\n    socket.socket()\n")
    assert classify_tool(fn) == ["network"]


# -- multi-capability + negative --------------------------------------------

def test_multiple_capabilities():
    fn = _tool(
        "import os, httpx\ndef f(x):\n"
        "    os.system(x)\n"
        "    httpx.get(x)\n"
    )
    assert classify_tool(fn) == ["code_exec", "network"]


def test_no_capability_pure_internal():
    fn = _tool("def f(org: str, limit: int = 10):\n    return [f'{org}/repo-{i}' for i in range(limit)]\n")
    assert classify_tool(fn) == []


def test_no_capability_ignores_irrelevant_names():
    """A tool that merely mentions 'get'/'request' as data keys, not calls."""
    fn = _tool("def f(x: str):\n    return {'request': x, 'get': 1}\n")
    assert classify_tool(fn) == []
