---
name: Agent Policy Conformance Validator (APCV)
type: architecture-spine
purpose: build-substrate
altitude: feature
paradigm: Functional Layering
scope: 支持 LangGraph 的完整 MVP 产品，并通过可扩展的适配器模式支持其他框架
status: draft
created: 2026-09-12
updated: 2026-09-12
binds: []
sources:
  - 头脑风暴摘要（2026-09-12）
  - 项目计划（2026-09-12）
  - 工具/Probe 研究（2026-09-12）
  - 开源调研（2026-09-12）
companions: []
---

# 架构主干 — Agent Policy Conformance Validator

## 设计范式

**功能分层 + 框架抽象（Functional Layering with Framework Abstraction）**

系统按功能划分为三层，依次处理 Agent 能力验证：
- **Scan 层（扫描层）**: 在四道安全边界（Tool、Runtime、Network、Identity）上发现 Agent 的能力
- **Validate 层（验证层）**: 生成并执行越界探测（probe），捕获执行追踪（execution trace）
- **Decision 层（决策层）**: 聚合结果，计算合规得分，生成裁决与报告

通过 Adapter 模式实现框架抽象，将框架相关逻辑与核心扫描器隔离，从而支持多框架（首先支持 LangGraph，AgentScope/AutoGen 作为扩展）。

## 不变量与规则

### AD-1 — 三层功能架构
- **Binds（约束）**: 系统整体结构与数据流
- **Prevents（防止）**: 扫描、验证、决策逻辑相互混杂；组件之间边界不清
- **Rule（规则）**: Scan 层 → Validate 层 → Decision 层。每层都有明确定义的输入/输出契约。数据单向向下流动。

### AD-2 — 四个独立扫描器
- **Binds（约束）**: Scan 层的内部组织
- **Prevents（防止）**: 各边界扫描器之间紧耦合；新增边界类型需要整体重构
- **Rule（规则）**: ToolScanner、RuntimeScanner、NetworkScanner、IdentityScanner 各自实现统一的 `Scanner` 接口。每个扫描器产出独立的 SBOM 文件。在输出层进行组合。

### AD-3 — SBOM 文件 + 索引
- **Binds（约束）**: 四个扫描器输出的存储与访问方式
- **Prevents（防止）**: 强制所有维度一起加载；大型 SBOM 文件内存占用低效
- **Rule（规则）**: 每个扫描器输出独立的 JSON 文件（tool.json、runtime.json、network.json、identity.json）到 `.apcv/sbom/`。索引文件（index.json）列出所有 SBOM 文件。Validate 层按需仅加载所需文件。

### AD-4 — Validate 层：独立验证器 + 共享基础设施
- **Binds（约束）**: Validate 层的内部组织
- **Prevents（防止）**: 代码重复；验证器之间紧耦合；难以扩展新边界类型
- **Rule（规则）**: 四个独立验证器（ToolValidator、RuntimeValidator、NetworkValidator、IdentityValidator）各自实现统一的 `Validator` 接口。共享基础设施（ProbeExecutor、ParameterTracer、ProbeLibrary、PolicyEngine）通过依赖注入供所有验证器使用。

### AD-5 — Decision 层：统一一致性引擎（Conformance Engine）
- **Binds（约束）**: 验证结果如何聚合为最终裁决
- **Prevents（防止）**: 决策逻辑分散；各维度评分标准不一致
- **Rule（规则）**: 单一的 ConformanceDecisionEngine 收集全部四个验证器的结果，计算加权合规得分（0-100），生成统一的违规列表，输出最终 PASS/FAIL 裁决并以多种格式生成报告。

### AD-6 — 通过 Adapter 模式实现框架抽象
- **Binds（约束）**: 系统与各 Agent 框架的交互方式
- **Prevents（防止）**: 框架锁定；难以支持多框架；核心扫描器直接依赖框架 API
- **Rule（规则）**: 定义统一的 `FrameworkAdapter` 接口。每个框架对应一个具体适配器（LangGraphAdapter、AgentScopeAdapter 等）。所有扫描器接收 adapter 实例，保持与框架无关。MVP 仅实现 LangGraphAdapter；后续 Sprint 再增加其他适配器。

### AD-7 — CLI 接口设计
- **Binds（约束）**: 命令结构、参数选项、输出行为
- **Prevents（防止）**: 接口不清晰；参数不规范；难以集成 CI/CD
- **Rule（规则）**: 单一 `apcv validate` 命令。必需参数：`--agent`、`--policy`。可选参数：`--output`、`--format`（json/sarif/html）、`--fail-on`（得分阈值）、`--workers`（并发数）、`--timeout`。始终以表格形式输出到 stdout，并将 JSON 输出到 `.apcv/reports/`。退出码：0=PASS，1=FAIL，2=错误。

### AD-8 — 输出格式与报告
- **Binds（约束）**: CLI 的输出内容以及为审计保存的内容
- **Prevents（防止）**: 信息丢失；合规状态不清晰；历史分析困难
- **Rule（规则）**: 终端输出 = 人类可读的表格（工具 SBOM、违规项、合规得分）。自动保存到 `.apcv/reports/{timestamp}_{agent_name}.json` = 完整执行追踪 + 元数据。其他格式（SARIF、PDF、HTML）通过 `--format` 参数按需生成。

### AD-9 — 策略 DSL 设计
- **Binds（约束）**: 策略的声明语法与结构
- **Prevents（防止）**: 策略定义含糊；难以组合可复用的策略
- **Rule（规则）**: 基于 YAML 的声明式格式，包含五个部分：`metadata` 以及四个 `boundaries`（tool、runtime、network、identity）。每个边界指定 `allowed` 和 `denied` 列表，外加约束条件（路径模式、域名白名单等）。

### AD-10 — Web UI 架构
- **Binds（约束）**: Web 接口结构与数据模型
- **Prevents（防止）**: 前后端紧耦合；难以扩展新的可视化功能
- **Rule（规则）**: 后端：FastAPI + 基于文件的存储（.apcv/reports/）。前端：消费后端 API 的 React/Vue 仪表盘。仪表盘展示：带合规卡片的 Agent 列表、历史趋势、策略编辑器、执行时间线、报告导出。MVP 采用单进程部署；未来可将前后端分离。

### AD-11 — 错误处理与日志
- **Binds（约束）**: 各层如何处理与记录错误
- **Prevents（防止）**: 静默失败；调试困难；错误上下文丢失
- **Rule（规则）**: 三级错误处理：静默失败（scanner 出错 → 记录日志 + 继续执行）、非致命错误（probe 超时 → 标记 WARNING + 继续执行）、致命错误（策略无效 → 立即停止 + 以 2 退出）。所有日志以结构化 JSON 格式写入 `.apcv/logs/{timestamp}.log`。

## 一致性约定

| 关注点 | 约定 |
|---------|-----------|
| **命名** | 类：PascalCase（ToolScanner、ConformanceDecisionEngine）。函数/变量：snake_case。文件：lowercase_with_underscores.py。 |
| **数据格式** | SBOM：JSON Schema 2020-12。报告：UTF-8 JSON。日志：JSON Lines（每行一个 JSON 对象）。 |
| **配置** | 策略文件：YAML（人类可读、可版本管理）。运行时配置：环境变量 + CLI 参数（CLI 参数覆盖环境变量）。 |
| **状态管理** | 尽可能使用不可变数据结构。状态变更需显式记录日志。Scanner 之间不共享可变状态。 |
| **错误处理** | 异常传播时携带上下文（文件名、行号、操作名）。自定义异常继承自基类 `APCVException`。所有异常在重新抛出前先记录日志。 |
| **异步** | Probe 执行：并发（使用 ThreadPoolExecutor 或 asyncio）。工具调用拦截：必须通过 wrapt + asyncio hooks 同时支持同步与异步工具。 |

## 技术栈

| 名称 | 版本 | 用途 |
|------|---------|---------|
| Python | 3.9+ | 编程语言 |
| LangGraph | 0.1.0+ | Agent 框架（MVP） |
| wrapt | 1.14+ | 参数拦截 |
| Docker Python SDK | 6.0+ | Probe 沙箱隔离 |
| OPA/Rego | 0.45+ | 策略求值（首选），MVP 也可用 AgenticContract |
| FastAPI | 0.100+ | Web UI 后端 |
| React | 18+ | Web UI 前端 |
| Pydantic | 2.0+ | 数据校验 |
| pytest | 7.0+ | 测试 |

## 结构种子

```
apcv/
├── core/                          # 核心引擎
│   ├── scanners/
│   │   ├── base.py               # Scanner 抽象接口
│   │   ├── tool_scanner.py
│   │   ├── runtime_scanner.py
│   │   ├── network_scanner.py
│   │   └── identity_scanner.py
│   │
│   ├── validators/
│   │   ├── base.py               # Validator 抽象接口
│   │   ├── tool_validator.py
│   │   ├── runtime_validator.py
│   │   ├── network_validator.py
│   │   └── identity_validator.py
│   │
│   ├── decision/
│   │   ├── conformance_engine.py  # ConformanceDecisionEngine
│   │   └── scoring.py            # 评分逻辑
│   │
│   ├── execution/                # 2026-09-13 调和:采纳 story 2-2 布局
│   │   ├── executor.py           # IsolatedExecutor（Docker 沙箱执行器）
│   │   ├── sandbox.py            # 策略 → Docker 运行参数（纯函数）
│   │   ├── tracer.py             # 基于 wrapt 的参数拦截
│   │   └── trace_model.py        # 执行轨迹 schema（JSONL）
│   │
│   └── frameworks/
│       ├── adapter.py            # FrameworkAdapter 抽象接口
│       ├── langgraph_adapter.py  # LangGraphAdapter（MVP）
│       └── agentscope_adapter.py # AgentScopeAdapter（未来）
│
├── cli/
│   ├── main.py                   # apcv validate 命令入口
│   ├── output.py                 # 表格格式化、报告生成
│   └── config.py                 # CLI 参数解析
│
├── web/
│   ├── backend/
│   │   ├── app.py               # FastAPI 应用
│   │   ├── api/
│   │   │   ├── reports.py
│   │   │   ├── policies.py
│   │   │   └── agents.py
│   │   └── models.py            # Pydantic 模型
│   │
│   └── frontend/
│       ├── src/
│       │   ├── components/
│       │   ├── pages/
│       │   └── App.tsx
│       └── package.json
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── docs/
│   ├── architecture/
│   ├── api/
│   ├── user_guide/
│   └── examples/
│
├── config/
│   └── probe_library.yaml        # Probe 模板
│
└── requirements.txt
```

## 能力 → 架构映射

| 能力/领域 | 所在位置 | 受哪些决策约束 |
|---|---|---|
| 跨框架发现 Agent 工具 | Scanner 层 + FrameworkAdapter | AD-2、AD-6 |
| 拦截工具调用并捕获参数 | ParameterTracer | AD-11（异步支持）、核心设计 |
| 为四个边界生成策略相关 probe | ProbeLibrary + Validators | AD-4 |
| 在隔离沙箱中执行 probe | core/execution/executor.py | Docker SDK，安全性依据 AD-11 |
| 依据策略评估执行追踪 | PolicyEngine | OPA/Rego 或 AgenticContract，AD-9 |
| 跨维度计算合规得分 | ConformanceDecisionEngine | AD-5、评分算法 |
| 面向 CI/CD 集成的 CLI 接口 | cli/main.py | AD-7、AD-8 |
| Web UI 仪表盘与策略编辑器 | web/backend + frontend | AD-10 |
| 持久化验证结果以供审计 | .apcv/reports/ | AD-3、AD-8 |
| 记录所有操作日志以便调试 | .apcv/logs/ | AD-11 |

## 延后事项

- **LangGraph 之外的多框架支持**: AgentScope、AutoGen 适配器延后至 Sprint 2。架构通过 Adapter 模式予以支持（AD-6）。
- **LLM 辅助的 Probe 生成**: 当前为静态 probe 库（30-50 个 probe）。动态/对抗性 probe 生成延后至 Sprint 2。参考：Garak 框架集成。
- **高级策略特性**: 条件规则（如 "if A then B"）、时序约束、委托链延后至 Sprint 2。
- **运行时监控模式（Runtime Monitoring Mode）**: MVP 仅做部署前验证。持续运行时监控延后至 Sprint 2+。
- **合规报告自动化**: MVP 中 SBOM/审计证明为手动生成。自动化合规映射（NIST、EU AI Act、ISO）延后至 Sprint 2。
- **高安全沙箱**: MVP 使用 Docker（操作系统级隔离）。gVisor（系统调用过滤）、Firecracker（微虚拟机）针对高风险 Agent 延后至 Sprint 2。
  - **沙箱定位（2026-09-13 修正）**: 沙箱是**固定隔离笼子**（非 root + 无网络），**不执行策略**。denied_paths / read-only / 断网等限制属于部署平台的强制职责，APCV 不通过沙箱去"预先拦截"——否则会掩盖 Agent 的真实越界行为，摧毁检测能力。越界检测由 agent 探针观察真实工具行为完成，而非由沙箱拦截。gVisor/Firecracker 的价值在于**更强的隔离强度**（防止逃逸污染宿主机），而非**更细的策略执行**。
- **水平扩展**: MVP 为单进程。分布式执行与云部署延后至生产阶段。
