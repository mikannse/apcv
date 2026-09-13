# Story 4.1: 包级工具面扫描（Package-Level Tool Surface Scanning）

Status: ready-for-dev

## Story

As a DevOps 工程师，
I want APCV 能直接扫描整个 Agent 代码库（多文件/多模块）而非单个文件，
so that 对真实企业 Agent 做上线前验证时无需手写遍历脚本（gate.py 这类薄集成）。

## Acceptance Criteria

1. ToolScanner 能对包目录递归发现所有 `.py` 模块中的 `@tool`，合并为一份 SBOM
2. 合并后的 SBOM 每条工具标注来源文件（`module` 字段 = 包内相对路径，如 `tools/crm.py`）
3. 单文件扫描 `scan()` 向后兼容：签名、行为、现有测试全部不变
4. gate.py 的本地 `scan_package()` 被内建的 `ToolScanner.scan_package()` 取代，gate.py 的 CLI 行为（退出码 0/1/2、JSON 输出）保持不变
5. 多文件包 / 嵌套目录 / 跨模块去重 / 目录跳过 / 单文件降级 五类场景有测试覆盖

## Tasks / Subtasks

- [ ] Task 1: 在 ToolScanner 内建 `scan_package()` (AC 1,2,3)
  - [ ] 1.1 将 gate.py 的 `scan_package()` 核心逻辑迁入 `ToolScanner`（见 Dev Notes 的迁移清单）
  - [ ] 1.2 `scan_package()` 返回 SBOM（与 `scan()` 一致），来源用 `module` 字段
  - [ ] 1.3 保留 `scan()` 不动，仅新增方法
- [ ] Task 2: 重构 gate.py 调用内建能力 (AC 4)
  - [ ] 2.1 删除 gate.py 本地 `scan_package()` 函数
  - [ ] 2.2 改为 `ToolScanner().scan_package(...)`，保持 CLI 输出格式与退出码不变
- [ ] Task 3: 测试 (AC 5)
  - [ ] 3.1 单元测试 `scan_package`（tmp_path 构造真实包结构）
  - [ ] 3.2 集成测试：对 enterprise-sim/customer-support-bot 包扫描，工具数 + 来源标注正确

## Dev Notes

### 核心事实：这段逻辑已经写好了，在 gate.py 里

**不要重写、不要重新设计**——包级扫描的正确逻辑已存在于
[enterprise-sim/pre-launch-gate/gate.py:34-57](enterprise-sim/pre-launch-gate/gate.py#L34-L57)。
本故事的本质是**把它从薄集成内建进 ToolScanner**，让 gate.py 变成纯调用方。

### 迁移清单（从 gate.py 逐条搬，别改语义）

1. `pkg_dir.rglob("*.py")` + `sorted()` —— 保证确定性顺序
2. 跳过路径段含 `tests` 或 `__pycache__` 的文件
3. 对每个 `.py` 调 `scanner.scan(str(py), adapter)`，捕获 `SyntaxError / ValueError / UnicodeDecodeError` → **跳过该文件继续**（不整体失败）
4. 来源标注：`py.relative_to(pkg_dir).as_posix()` 存入 `tool.module`
5. 去重：`seen_names` set，跳过 `tools/__init__.py` re-export 造成的重复工具
6. 合并进 `create_empty_sbom(str(pkg_dir), framework="langgraph")` 返回的 SBOM

### 设计决策（必须遵守，避免纠结）

- **复用 `module` 字段存来源，不新增 `source_file` 字段。** `Tool.module` 的语义本就是"工具所在模块"（见 [apcv/core/utils/sbom.py:19](apcv/core/utils/sbom.py#L19)），gate.py 已验证它足以承载来源定位。新增 `source_file` 会造成 module/source_file 双字段语义重叠。
- **`scan_package()` 返回 `SBOM`**，与 `scan()` 一致（不是 gate.py 现在的 `(sbom, n_files)` 元组）。gate.py 需要文件数时自己 `len(list(pkg.rglob("*.py")))` 统计。
- **`scan()` 方法一个字都不改。** 单文件扫描是现有 `apcv validate` 的主路径，`test_tool_scanner.py` 的 4 个测试依赖它。

### 要改的文件（精确）

| 文件 | 动作 | 说明 |
|---|---|---|
| [apcv/core/scanners/tool_scanner.py](apcv/core/scanners/tool_scanner.py) | UPDATE | 新增 `scan_package(self, pkg_dir, adapter)` 方法 |
| [enterprise-sim/pre-launch-gate/gate.py](enterprise-sim/pre-launch-gate/gate.py) | UPDATE | 删除本地 `scan_package`，调用 `ToolScanner().scan_package` |

### 向后兼容（不破坏的）

- `apcv validate` CLI 用 `scanner.scan()` 单文件路径 → 不受影响
- `test_tool_scanner.py` 现有 4 个测试（scan 单文件）必须继续通过
- gate.py 的 CLI 契约（`--agent`/`--policy`/`--output`、退出码 0=PASS/1=WARN/2=FAIL、JSON 字段 `files_scanned`/`tools_discovered`/`tools[].source`）保持不变

### 测试模式（AC 5）

参考 [tests/unit/test_tool_scanner.py](tests/unit/test_tool_scanner.py) 的 fixture 风格，但包级测试用 `tmp_path` 构造真实目录结构：

```python
def test_scan_package(tmp_path, scanner, adapter):
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "crm.py").write_text(
        'from langchain_core.tools import tool\n@tool\ndef get_customer(x: str) -> str:\n    """c"""\n    return x\n'
    )
    sbom = scanner.scan_package(str(tmp_path), adapter)
    assert len(sbom.tools) == 1
    assert sbom.tools[0].module == "tools/crm.py"   # 来源标注
```

必测五类场景：多文件、嵌套目录（`tools/sub/`）、`__init__.py` re-export 去重、`tests/` 跳过、单文件 SyntaxError 降级（不整体失败）。

### Project Structure Notes

- 遵循既有分层：扫描逻辑归 `apcv/core/scanners/`，gate.py 只是 CI 集成薄壳
- `scan_package` 是 `ToolScanner` 的具体方法（不在 `Scanner` ABC 里，ABC 只要求 `scan`）——不必改 [base.py](apcv/core/scanners/base.py)

### References

- 迁移来源逻辑 [Source: enterprise-sim/pre-launch-gate/gate.py#L34-L57]
- Tool 模型 [Source: apcv/core/utils/sbom.py#L15-L22]
- 单文件扫描现状 [Source: apcv/core/scanners/tool_scanner.py#L16-L51]
- 现有测试模式 [Source: tests/unit/test_tool_scanner.py]
- 故事来源 [Source: _bmad-output/specs/spec-apcv-2026-09-12/stories.yaml#story-9]
- 架构延后事项 [Source: _bmad-output/architecture/architecture-apcv-2026-09-12/ARCHITECTURE-SPINE.md#延后事项]

## Dev Agent Record

### Agent Model Used

（待 dev-story 填充）

### Debug Log References

### Completion Notes List

### File List
