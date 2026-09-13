# Story 4.2: MCP 端点清单静态解析（MCP Endpoint Discovery）

Status: ready-for-dev

## Story

As a 安全工程师，
I want APCV 能从 agent 代码里静态提取出 MCP 连接声明（连接了哪些 MCP server、什么 transport、指向哪），
so that 审计 agent 的外部攻击面（尤其 http transport + url 是 SSRF/数据外传潜在面），无需运行 agent 或连接 server。

> **范围界定**: 本故事走**路线 A（纯静态）**——只解析代码里的 MCP 连接声明，产出「MCP 端点清单」。
> **不枚举**每个 server 实际暴露的工具（那需要 `await client.get_tools()` 运行时问 server，是路线 B，不在本故事）。
> CAP-1 四层中的第②层「MCP 工具面发现」的**完整形态**是路线 B；本故事是它的**静态前置**（先知道连了哪些 server，才能谈枚举其工具）。

## Acceptance Criteria

1. 能从 agent 代码 AST 中识别 `MultiServerMCPClient({...})` 调用，提取每个 server 的 name / transport / url / command
2. 能从 agent 代码 AST 中识别 `MCPAdapter(...)` 调用（单 server 形态），提取其 target
3. 提取结果写入 SBOM 的 `mcp_servers` 字段（新增字段，向后兼容——现有 SBOM 该字段默认空列表）
4. 内联 dict 字面量能完整解析；配置引用变量（如 `MultiServerMCPClient(servers_config)`）时，标记「检测到但无法静态解析」而非静默忽略
5. 单文件 `scan()` 与包级 `scan_package()` 都能产出 MCP 端点（两者复用同一提取逻辑）

## Tasks / Subtasks

- [ ] Task 1: 新增 `MCPServer` 数据模型 + SBOM.mcp_servers 字段 (AC 3)
  - [ ] 1.1 `MCPServer(name, transport, url, command, args)` Pydantic 模型
  - [ ] 1.2 `SBOM` 加 `mcp_servers: List[MCPServer] = []`
- [ ] Task 2: MCP 提取器 (AC 1,2,4)
  - [ ] 2.1 识别 `MultiServerMCPClient(dict)` 调用，遍历 dict 字面量提取 server
  - [ ] 2.2 识别 `MCPAdapter(target)` 调用，提取单 server
  - [ ] 2.3 变量引用 → 产出「无法解析」标记
- [ ] Task 3: 接入 scan / scan_package (AC 5)
  - [ ] 3.1 `scan()` 提取完 tools 后，也提取 mcp_servers 并入 SBOM
  - [ ] 3.2 `scan_package()` 合并各文件的 mcp_servers
- [ ] Task 4: 测试 (AC 1-5)
  - [ ] 4.1 单元测试：MultiServerMCPClient 多 server / MCPAdapter 单 server / 变量引用降级 / 无 MCP 时 mcp_servers 为空

## Dev Notes

### 要识别的两种 API（来自 langchain MCP 文档）

**旧 API `MultiServerMCPClient`**（from `langchain_mcp_adapters.client`）:
```python
client = MultiServerMCPClient(
    {
        "math": {"transport": "stdio", "command": "python", "args": ["/path/math_server.py"]},
        "weather": {"transport": "http", "url": "http://localhost:8000/mcp"},
    }
)
```
参数是一个 **dict 字面量**：key = server 名，value = dict（含 `transport` + `url` 或 `command`/`args`）。

**新 API `MCPAdapter`**（from `langchain.mcp`，LangChain v1.4.0 起）:
```python
adapter = MCPAdapter("https://some-server.com/mcp")   # URL 字符串 target
adapter = MCPAdapter(fastmcp_client)                    # 或 fastmcp.Client / MCPConfig
```
参数是**单个 target**（URL 字符串 / client 对象），transport 由 target 推断。

### 提取策略（AST 层面）

- `ast.walk` 找 `ast.Call`，`func` 是 `ast.Name` 且 `id in ("MultiServerMCPClient", "MCPAdapter")`
- `MultiServerMCPClient`：取第一个位置参数，若为 `ast.Dict` 字面量，遍历 keys（server 名）+ values（含 transport/url/command/args 的 dict）
- `MCPAdapter`：取第一个位置参数，若为 `ast.Constant`（字符串 URL）→ transport="http"（URL 推断）；若为变量/调用 → 标记「无法静态解析」
- **变量引用**（`MultiServerMCPClient(servers_config)`，参数是 `ast.Name`）→ 产出一条 `MCPServer(name="<unresolved>", transport="unknown")` 并附带「unresolved」标志，不静默忽略

### 数据模型设计

`MCPServer` 字段：
- `name: str` —— server 名（dict key；MCPAdapter 单 server 时用 URL 或 "<unresolved>"）
- `transport: str` —— "stdio" | "http" | "unknown"
- `url: str = ""` —— http transport 时
- `command: str = ""` —— stdio transport 时
- `args: List[str] = []` —— stdio transport 时
- `unresolved: bool = False` —— 配置引用了变量、无法静态解析时为 True

### 关键设计约束

- **复用现有 AST 机制**，不引入运行时/网络——保持纯静态
- **SBOM 向后兼容**：`mcp_servers` 默认空列表，现有测试、报告、`gate.py` 不受影响
- **不枚举工具**：这是路线 A 的边界，不要试图 `get_tools()` 或 import MCP 包

### 要改的文件（精确）

| 文件 | 动作 | 说明 |
|---|---|---|
| [apcv/core/utils/sbom.py](apcv/core/utils/sbom.py) | UPDATE | 新增 MCPServer + SBOM.mcp_servers |
| [apcv/core/frameworks/langgraph_adapter.py](apcv/core/frameworks/langgraph_adapter.py) | UPDATE | 新增 `extract_mcp_servers(ast_tree)` 方法 |
| [apcv/core/scanners/tool_scanner.py](apcv/core/scanners/tool_scanner.py) | UPDATE | scan()/scan_package() 接入 mcp_servers 提取 |

### References

- MCP 配置 API 形态 [Source: langchain docs — deepagents/mcp, langchain/mcp]
- 现有 Tool 模型 [Source: apcv/core/utils/sbom.py#L15-L22]
- 现有 AST 提取模式 [Source: apcv/core/frameworks/langgraph_adapter.py#L22-L41]
- 调研结论 [Source: sprint-status.yaml epic-4 #4-2-mcp-discovery]

## Dev Agent Record

### Agent Model Used

（待 dev-story 填充）

### Debug Log References

### Completion Notes List

### File List
