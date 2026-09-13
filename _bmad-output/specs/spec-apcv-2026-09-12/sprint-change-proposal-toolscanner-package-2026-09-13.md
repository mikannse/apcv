# Sprint Change Proposal — 纳入 ToolScanner 包级扫描

- **日期**: 2026-09-13
- **变更类型**: 新增范围(将已发现的局限正式纳入 backlog)
- **协作模式**: Incremental(逐条批准)
- **涉及能力**: CAP-1(工具面发现)——框架层包级补全

---

## Section 1: Issue Summary

### 问题陈述

APCV 的 `ToolScanner.scan()` 目前**只扫描单个 Python 文件**。但真实企业 Agent 是一整个代码库(多文件、多模块)。此前这一局限仅在 sprint-status 的 `completion_note` 和 SPEC 状态表里被当作"已知局限"提及,**不是正式可追踪的 backlog 条目**。

### 触发原因

提交 `enterprise-sim/pre-launch-gate` 时,其 README 明确指出:

> "APCV 核心的 `ToolScanner` 目前**单文件扫描**,`gate.py` 是对它的薄集成——遍历整个包,扫描每个 `.py` 模块里的 `@tool`,合并成一份 SBOM。"

即:包级扫描能力当前**外置**在一个 CI 集成脚本里,而不是 APCV 核心能力。这是 CAP-1 的一个真实缺口。

### 核心认知

包级扫描不是"锦上添花",而是 APCV 从"单文件 demo"走向"真实企业 Agent 验证"的必经之路——真实 Agent 是包,不是单文件。

---

## Section 2: Impact Analysis

### Epic 影响

新增 **story-9「包级工具面扫描」**,归入 **epic-4「Sprint 2: Package-Level Discovery」**(新建)。不动现有 epic-1/2/3 的顺序与内容。

### Story 影响

| Story | 影响 |
|---|---|
| story-1(工具发现) | 无回改;story-9 是对它 CAP-1 的补全 |
| story-9(新增) | 新条目,2 天工作量,backend-team |

### Artifact 冲突

| Artifact | 变更 |
|---|---|
| stories.yaml | 新增 story-9(AC/工作量/优先级) |
| sprint-status.yaml | 新增 epic-4 + 2-4-package-scanning 条目(status: backlog) |
| SPEC.md | CAP-1 状态行更新为"包级扫描已纳入 story-9" |
| ARCHITECTURE-SPINE.md | 延后事项新增"包级工具面扫描(story-9)"条目 |

无 PRD/UX 冲突(纯后端扫描能力)。

### 技术影响

- `ToolScanner.scan()` 需支持目录输入 + 递归 AST 解析 + SBOM 合并
- `Tool` 需增加 `source_file` 字段(来源文件定位)
- `gate.py` 薄集成将被内建能力取代(重构)

---

## Section 3: Recommended Approach

**方案一「直接调整」——新增 story 到现有计划。**

- 无代码回滚,无 MVP 范围收缩
- 这是"把已识别的真实缺口正式化",工作量约 2 天
- 风险低:纯增量,向后兼容单文件扫描

---

## Section 4: Detailed Change Proposals

### 提案 1 — stories.yaml 新增 story-9

- id: story-9
- title: 包级工具面扫描(Package-Level Tool Surface Scanning)
- epic: Sprint 2: 多文件/包级发现
- AC: 包目录递归扫描 / 来源文件标注 / 单文件向后兼容 / gate.py 取代 / 多文件测试覆盖
- estimate_days: 2,priority: high

### 提案 2 — sprint-status.yaml 新增 epic-4 + story-9 条目

- epic-4(Sprint 2: Package-Level Discovery,status: backlog)
- 2-4-package-scanning(status: backlog)

### 提案 3 — SPEC.md 更新 CAP-1 状态行

将"多文件包级扫描靠 enterprise-sim/gate.py 薄集成"改为"**包级(多文件)扫描已纳入 story-9(Sprint 2)**";CAP-7 行同步标注"依赖 story-9 包级扫描"。

### 提案 4 — ARCHITECTURE-SPINE.md 延后事项补条目

新增"包级工具面扫描(story-9)"条目,说明 ToolScanner 单文件局限、包级扫描延后至 Sprint 2、当前靠 gate.py 绕过。

---

## Section 5: Implementation Handoff

### 变更范围分类:**Minor**(纯文档 + 新增 backlog 条目,无代码实现)

### 执行者:Developer agent(文档已改完,代码实现是后续 sprint)

### 成功标准

- stories.yaml / sprint-status.yaml / SPEC.md / ARCHITECTURE-SPINE.md 四处一致地记录 story-9
- story-9 有完整 AC,可被后续 sprint 直接领取
- 文档与代码不再"包级扫描只是注记"地脱节
