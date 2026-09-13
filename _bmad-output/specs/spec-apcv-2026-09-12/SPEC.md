---
title: Agent Policy Conformance Validator (APCV)
date: 2026-09-12
project: apcv
companions:
  - probe-rules.md
  - policy-dsl-schema.md
  - architecture-diagrams.md
sources:
  - ../../../brainstorming/brainstorm-ai-agent-containment-2026-09-12/brainstorm-summary.md
  - ../../../research-outputs/PROJECT-PLAN-FINAL-2026-09-12.md
assumptions:
  - LangGraph 工具面可通过 AST 装饰器静态解析，准确率 >95%
  - 参数级追踪足以支撑 MVP 的一致性验证
  - 声明策略（YAML）由开发者负责；MVP 不做基于 IAM/IaC 的自动推断
  - 部署环境中具备 Docker
  - 合规范围聚焦于审计留痕 + 确定性验证，而非行为层面的保证
open_questions:
  - Probe 测试可接受的误报率是多少？
  - Policy DSL 应采用 Rego/OPA（业界标准，学习曲线陡峭）还是自定义 YAML（更简单）？
  - 在多租户 SaaS 部署中如何防止执行层面的交叉污染？
---

# Agent Policy Conformance Validator (APCV)

## 为什么（Why）

部署 AI Agent 的企业通常会配置权限限制与隔离策略，然后默认"Agent 已被限制"。但他们无法回答：**这些限制真的被强制执行了吗？声明策略与实际能力之间是否存在差距？**

这一信心缺口阻碍了生产部署。HuggingFace 事件与行业数据（2026 年 65% 的企业遭遇过 Agent 安全事件）证实该问题真实存在：声明的资源访问范围往往与实际访问能力不一致。

**市场定位**：目前尚不存在专门的"Agent 一致性验证器"。竞品（Microsoft Agent Governance Toolkit、Snyk、SIEM）要么覆盖面过宽，要么无法处理 Agent 特有的动态能力。EU AI Act（2026 年生效）带来法务合规压力。DevOps 团队需要的是部署前的 CI/CD 门禁，而非运行时强制。

## 能力（Capabilities）

### CAP-1: 工具面发现（四层）
**意图（Intent）**: 跨所有层发现 Agent 可用的完整工具面。  
**成功标准（Success）**: 识别 ≥99% 的工具（MCP 定义、框架定义、运行时内建、子 Agent 继承），在 LangGraph 上准确率 >95%；处理时间 <10s。

### CAP-2: 策略相对型 Probe 生成
**意图（Intent）**: 针对声明的策略自动生成越界测试用例，而非基于固定资源清单。  
**成功标准（Success）**: 对任意策略，生成 ≥15 个检验策略显式边界的探针（例如策略声明"仅访问 /data"，则探针测试对 /etc、/home、/var 的访问）；每个探针具有明确的 PASS/FAIL 语义。

### CAP-3: 隔离的 Probe 执行与参数追踪
**意图（Intent）**: 在沙箱环境中执行探针，并记录每一次带参数的工具调用。  
**成功标准（Success）**: 2 分钟内完成 20–30 个探针；记录 100% 的工具调用；参数追踪开销 <1%；Docker 隔离（只读文件系统、禁用网络、每个探针 <30s 超时）。

### CAP-4: 一致性检查与差异报告
**意图（Intent）**: 将执行轨迹与声明策略比对，输出可审计的 PASS/FAIL 判定与违规详情。  
**成功标准（Success）**: 输出机器可读的差异（JSON）、人读报告（Markdown）以及 compliance_score（0–100）；每条违规都包含工具名、参数、严重级别、修复提示。

### CAP-5: CLI 与 Web UI 双入口
**意图（Intent）**: 同时服务 DevOps（CLI 用于 CI/CD 自动化）与安全团队（Web UI 用于策略管理与可视化）。  
**成功标准（Success）**: `apcv validate --agent <path> --policy <yaml>` 可在 CI/CD 流水线中运行；Web 看板展示 Agent 列表、合规评分、执行时间线、策略编辑器；两者均支持 JSON 输入输出以便集成。

### CAP-6: 监管级合规报告
**意图（Intent）**: 生成可直接作为证据的报告，适配 GDPR/SOX/ISO27001 审计。  
**成功标准（Success）**: PDF + JSON 导出包含执行轨迹、全部探针结果、策略声明、时间戳、签名（用于证据链保全）；能够证明"Agent 于某日针对某策略接受了测试，结果为 Y"。

### CAP-7: LangGraph 端到端支持
**意图（Intent）**: 为 LangGraph Agent 提供全生命周期支持（发现、探针生成、执行、报告）。  
**成功标准（Success）**: 发现所有 @tool 装饰器与运行时能力；生成策略相对型探针；执行并追踪；端到端 2 分钟内给出判定；无需人工修改代码。

---

## 实现状态对照（2026-09-13 校准）

> 本节对照代码实际状态,标注各 CAP 的**计划范围 vs 实际完成度**。此前 git 提交
> `ad1245e` 声称 "all 8 stories implemented" 与事实不符(2-2 实为 executor stub),
> 已按真实状态修正。核心设计变更见下方"设计偏离"小节。

| 能力 | 状态 | 实际 vs 计划 |
|---|---|---|
| CAP-1 工具面发现 | ⚠️ 部分 | 四层规划:①框架层多文件=story 4.1(ready);②MCP=story 4.2;③运行时内建(裸 LangGraph 无隐式工具,deepagents middleware 属框架层变体,不单独立);④子Agent 继承=story 4.4。当前仅框架层单文件已实现 |
| CAP-2 策略相对型探针 | ⚠️ 部分 | 生成机制完成,但探针库经重构**收敛为 7 条**(tool 4 + rate_limit 3),低于"≥15 条"门槛 |
| CAP-3 隔离执行+参数追踪 | ⚠️ 部分 | Docker 隔离 + wrapt 追踪 + ProbeHost + JSONL 轨迹 + 并行**已实现**;<1% 开销从未测量;沙箱定位修正(见设计偏离) |
| CAP-4 一致性+差异报告 | ⚠️ 部分 | 一致性检查完成;缺 **Markdown 报告**和每条违规的**修复提示** |
| CAP-5 CLI + Web UI | ⚠️ 部分 | **CLI 完整**(json/sarif/html);**Web UI 未实现**(backend 为硬编码假数据,无前端) |
| CAP-6 监管级报告 | ❌ 未完成 | 仅 JSON + trace;**PDF 导出、数字签名**未做 |
| CAP-7 LangGraph 端到端 | ⚠️ 部分 | 发现→生成→执行→追踪主链路通;缺"运行时能力发现"、缺真多文件 agent 直接支持(依赖 story-9 包级扫描) |

### 设计偏离(2026-09-13 关键修正)

1. **沙箱定位**: 沙箱是**固定隔离笼子**(非 root + 无网络),**不执行策略**。原设计
   让沙箱按策略配置(denied_paths 挂载/read-only/断网),会预先拦截越界行为、摧毁检测
   能力。越界检测由 agent 探针观察真实工具行为完成,而非沙箱拦截。详见
   sprint-change-proposal-2026-09-13.md 与架构 AD-11 区域。
2. **探针类别收敛**: shell 探针(filesystem/network/privilege 共 20 条)因"测沙箱拦没拦
   是错问题"被移除;悬空探针(tool_import/dynamic/override)因语义不清被移除。探针库
   从 35 条收敛到 7 条 agent 探针。
3. **denied_paths 职责**: 不在沙箱层实现(那是部署平台的强制职责),由 agent 探针观察
   行为来检测。

## 约束（Constraints）

### 设计约束

**四层工具碎片化**：Agent 能力分散于 MCP manifest（最易见）、框架代码（@tool 装饰器）、运行时隐式工具、子 Agent 委派之中。统一的 Tool SBOM 是唯一可信来源；遗漏任何一层都意味着策略验证的虚假信心。

**策略相对型生成，而非固定启发式**：探针内容必须随声明策略而变化（声明"仅 read_file"的 agent 与声明"完整文件系统访问"的 agent 会得到不同的探针）。确定性优先于适应性：使用参数级追踪（wrapt 插桩），而非 LLM 驱动的探针。

**面向审计的确定性验证**：合规证据必须可复现且非主观。参数轨迹（调用了什么 + 传入了什么参数）是事实；行为解读不是。轨迹由标准库记录，而非自定义的副作用监控器。

**隔离执行，零交叉污染**：每个 Probe 在干净的 Docker 容器中运行；测试之间无状态泄漏；环境一致保证轨迹可比较。

### 实现约束

**MVP 仅支持 LangGraph**：3 周迭代内框架支持仅限 LangGraph。架构必须框架无关（适配器模式），以便后续迭代支持 AgentScope、AutoGen 等，无需重新设计。

**Probe 规则库：硬编码规则（MVP）**：20–30 条硬编码探针，覆盖文件系统访问、工具调用、权限提升、网络访问等类别。LLM 辅助的探针生成推迟为"Could Have"（MVP 之后）。

**开发者声明策略**：开发者以 YAML 编写声明策略；MVP 不做基于 IAM/IaC 的自动推断。这符合 DevSecOps 惯例（容器安全策略由人工编写），并避免错误的 IAM-to-Agent 映射。

**性能目标**：完整验证 <2 分钟（工具发现 + 探针生成 + 执行 + 报告）。延迟预算：静态扫描 10s、探针生成 5s、执行 60s、报告 5s。

## 非目标（Non-Goals）

- **运行时强制**：APCV 负责验证；部署平台负责强制。超出范围。
- **提示词注入检测**：属于独立的安全层；不是 Probe 的职责。
- **对抗式 Agent 深度审计**：基于 LLM 的多轮探测是非确定性的。标记为"Could Have"留待后续。MVP 仅使用确定性参数级测试。
- **多框架 MVP**：仅 LangGraph；其余在 Sprint 2+。
- **IAM/IaC 自动推断**：策略声明由人工负责（MVP）。IAM 反向映射到策略是"Could Have"的未来方向。
- **沙箱副作用追踪**：文件系统写入、网络连接等超出参数追踪范围的内容不会被捕获。参数调用已足以判定策略一致性。

## 成功信号（Success Signal）

**技术层面**：工具发现准确率 >95%；Probe 执行 <2 分钟；追踪开销 <1%；Docker 隔离且测试间零污染；compliance_score 与人工审计结论一致。

**产品层面**：DevOps 在 CI/CD 合并前运行 `apcv validate`；2 分钟内获得 PASS/FAIL + 可审计差异；从而有信心将 Agent 推进到生产环境，或识别出需修复的能力缺口，无需额外的人工安全评审。

**市场层面**：该细分领域零竞品；企业 DevOps 团队 4 周内即可采用（落地阻力低）；来自 3+ 家试点客户（内部 + 外部）的积极信号；EU AI Act 合规路径清晰。

**监管层面**：生成的报告通过合规评审（审计师接受参数轨迹作为证据）；证据链（谁在何时运行了什么测试）得以保全且机器可验证。

---

## 后续步骤（Next Steps）

1. **验证配套文件**：创建 `probe-rules.md`（20–30 条规则目录）、`policy-dsl-schema.md`（YAML 规格）、`architecture-diagrams.md`（系统图）。
2. **故事拆分**：将 MVP 分解为 6–8 个可独立交付的故事（第 1 周：发现 + policy DSL；第 2 周：探针生成 + 执行；第 3 周：CLI + UI）。
3. **启动 Sprint 1**：框架脚手架、LangGraph @tool 抽取的 AST 解析器 PoC。
