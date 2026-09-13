# Story 4.4: 子 Agent 工具面枚举（Sub-Agent Tool Surface Enumeration）

Status: ready-for-dev

## Story

As a 安全工程师，
I want APCV 能静态枚举 agent 代码里所有 `create_agent(...)` 声明的子 agent 及其工具列表，
so that 完整工具面（含通过子 agent 暴露的能力）能被纳入 SBOM，无需追踪运行时的委派链。

> **范围界定**: 本故事只做**可靠的静态部分**——枚举代码里每个 `create_agent(tools=[...])` 声明及其工具列表。
> **不做**「谁 invoke 谁」的继承链追踪（wrapper 函数体里 `.invoke()` 哪个 agent 变量是隐式关系，静态追踪不可靠，见 Dev Notes）。
> CAP-1 第④层「子 Agent 工具继承」的**完整形态**（层级链）需要运行时方案；本故事是它的**静态可靠子集**（枚举所有 agent 声明的工具面）。

## Acceptance Criteria

1. 能从 agent 代码 AST 识别 `create_agent(...)` 调用，提取其 `tools=[...]` 列表里的工具名
2. 每个 `create_agent` 产出为一条 `SubAgent`（尽力提取赋值变量名，否则 `<unnamed>`）
3. `tools=[...]` 里的工具名按字面量解析（`ast.Name` 函数名 / `ast.Constant` 字符串名）；列表引用变量时标记 `unresolved=True`，不静默忽略
4. 提取结果写入 SBOM 的 `sub_agents` 字段（新增，向后兼容——默认空列表）
5. 单文件 `scan()` 与包级 `scan_package()` 都能产出 sub_agents

## Tasks / Subtasks

- [ ] Task 1: 新增 `SubAgent` 数据模型 + SBOM.sub_agents 字段 (AC 4)
  - [ ] 1.1 `SubAgent(name, tools, unresolved)` Pydantic 模型
  - [ ] 1.2 `SBOM` 加 `sub_agents: List[SubAgent] = []`
- [ ] Task 2: 子 agent 提取器 (AC 1,2,3)
  - [ ] 2.1 识别 `create_agent(...)` 调用，取 `tools=` 关键字参数
  - [ ] 2.2 解析 tools 列表里的 `ast.Name` / `ast.Constant` 元素为工具名
  - [ ] 2.3 列表是变量引用 → `unresolved=True`
  - [ ] 2.4 尽力提取赋值变量名（`fruit_agent = create_agent(...)`）
- [ ] Task 3: 接入 scan / scan_package (AC 5)
  - [ ] 3.1 `scan()` 提取 tools 后，也提取 sub_agents 并入 SBOM
  - [ ] 3.2 `scan_package()` 合并各文件的 sub_agents
- [ ] Task 4: 测试 (AC 1-5)
  - [ ] 4.1 单元测试：单子 agent / 多子 agent / 变量引用降级 / 无 create_agent 时为空

## Dev Notes

### 要识别的 API 形态（来自 langchain.agents）

```python
from langchain.agents import create_agent

@tool
def fruit_info(fruit_name: str) -> str: ...

# 子 agent 声明:create_agent(tools=[...])
fruit_agent = create_agent(
    model="gpt-5.4-mini",
    tools=[fruit_info],                    # ← 工具列表是 ast.List 字面量
    prompt="You are a fruit expert.",
)
```

关键事实：`create_agent` 和父 agent 的创建是**同一个函数**，所以扫描所有 `create_agent(tools=[...])` 即可拿到**所有 agent（父的、子的）各自的工具清单**。

### 为什么不做「谁 invoke 谁」的继承链追踪

子 agent 被父 agent 引用，是通过 wrapper 函数体里的一行 `fruit_agent.invoke(...)`——这是**隐式**关系，代码里没有"声明这个 wrapper 属于这个子 agent"的语句。静态追踪它需要靠猜变量名（`fruit_agent` 可任意命名、可跨文件 import、可藏分支里），**不可靠、易漏、易错**。因此本故事只枚举 `create_agent(tools=[...])` 这个**明确声明点**。

### 提取策略（AST 层面）

- `ast.walk` 找 `ast.Call`，`func` 是 `ast.Name` 且 `id == "create_agent"`
- 取 `tools=` 关键字参数（`kw.arg == "tools"`）
- 若 tools 是 `ast.List` 字面量：遍历 `elts`，`ast.Name` → `id`；`ast.Constant`(str) → `value`；其它（调用/子脚本）→ 跳过
- 若 tools 是变量（`ast.Name`）→ `unresolved=True`
- 赋值变量名：`create_agent` 所在 `ast.Assign` 且 value 是该 call → 取 `targets[0].id`；否则 `<unnamed>`

### 数据模型设计

`SubAgent` 字段：
- `name: str` —— 赋值变量名（如 `fruit_agent`），或 `<unnamed>`
- `tools: List[str]` —— 该 agent 的 tools 列表里的工具名
- `unresolved: bool = False` —— tools 引用了变量、无法静态解析

### 关键设计约束

- **复用现有 AST 机制**，不 import、不执行——纯静态
- **SBOM 向后兼容**：`sub_agents` 默认空列表
- **不追踪继承链**：只枚举声明点，这是本故事的边界

### 要改的文件（精确）

| 文件 | 动作 | 说明 |
|---|---|---|
| [apcv/core/utils/sbom.py](apcv/core/utils/sbom.py) | UPDATE | 新增 SubAgent + SBOM.sub_agents |
| [apcv/core/frameworks/langgraph_adapter.py](apcv/core/frameworks/langgraph_adapter.py) | UPDATE | 新增 `extract_subagents(ast_tree)` 方法 |
| [apcv/core/scanners/tool_scanner.py](apcv/core/scanners/tool_scanner.py) | UPDATE | scan()/scan_package() 接入 sub_agents |

### References

- create_agent 用法 [Source: langchain docs — langgraph/use-subgraphs]
- 现有 MCPServer 模式（参考同类实现）[Source: apcv/core/utils/sbom.py#MCPServer]
- 现有 extract_mcp_servers 模式 [Source: apcv/core/frameworks/langgraph_adapter.py#extract_mcp_servers]
- 调研结论 [Source: sprint-status.yaml epic-4 #4-4-subagent-inheritance]

## Dev Agent Record

### Agent Model Used

（待 dev-story 填充）

### Debug Log References

### Completion Notes List

### File List
