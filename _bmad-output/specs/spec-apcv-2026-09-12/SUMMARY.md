# APCV Spec 创建完成 — 总结报告

**项目**: Agent Policy Conformance Validator (APCV)  
**Spec 目录**: `d:\Projects\OCASC\_bmad-output\specs\spec-apcv-2026-09-12\`  
**完成日期**: 2026-09-12  
**状态**: ✅ 可进入开发

---

## 总览

APCV 规格说明现已完成，可交付下游消费者（架构设计、开发团队与干系人评审）。本 spec 采用 BMad Spec-Kernel 方法论创建，确保内容精简、连贯且每句承重。

---

## 产出内容

### 1. 核心内核（SPEC.md）
**用途**: 供所有下游消费者使用的机器可读契约

**内容**:
- **Why**: 问题陈述、市场定位、核心创新（策略相对型 Probe）
- **Capabilities（7 项）**: CAP-1 至 CAP-7，每项含 intent + success 信号
- **Constraints（6 项）**: 影响架构走向的设计决策（四层工具发现、策略相对型生成、确定性验证、隔离执行、MVP 范围、开发者声明策略）
- **Non-Goals（6 项）**: 显式排除项（运行时强制、提示词注入、对抗式 agent、多框架 MVP、IAM 自动推断、副作用追踪）
- **Success Signal**: 技术、产品、市场与监管四个维度的成功指标

**格式**: 5 字段内核（精简，每句承重，无装饰性内容）

---

### 2. 配套文件（承重内容）

#### probe-rules.md
**用途**: MVP 使用的硬编码探针规则目录

- 20–30 个确定性测试用例
- 类别：文件系统、工具调用、权限提升、网络、子 Agent、参数约束、速率限制
- 每条规则包含：ID、类别、描述、测试命令、预期结果
- 采用表格格式，便于查阅
- 定义了执行语义与轨迹格式

#### policy-dsl-schema.md
**用途**: 声明策略（Declared Policy）格式规格

- YAML schema 定义（tools、filesystem、network、parameters、rate_limits、privilege、compliance、environment）
- 校验规则（互斥约束、路径约束、速率限制合理性、权限一致性）
- 3 个参考示例：read-only、github-api、internal-admin
- Web UI 编辑指引
- 策略变更的版本与审计留痕

#### architecture-diagrams.md
**用途**: 系统架构的图示与文字说明

- 高层系统架构（Application → Core Engine → Adapter → Framework 各层）
- 完整数据流闭环（5 个阶段：发现 → 生成 → 执行 → 一致性 → 判定）
- 四层工具发现模型
- 参数追踪与 wrapt 集成图
- 多容器并行执行流程
- CLI 到 CI/CD 的集成
- 合规报告输出结构

---

### 3. 自校验报告（VALIDATION-REPORT.md）

**两遍校验**：

**Pass 1 — 连贯性**：对照 Spec Law 规则 1-8 逐条核验
- ✅ 全部 7 项 capability 均具备 intent 与 success
- ✅ Intent 描述的是 WHAT，而非 HOW
- ✅ 全部 6 项 constraint 确实左右了设计决策
- ✅ 6 项显式 non-goal
- ✅ Success signal 具体且可测试
- ✅ Capability ID 稳定且唯一（CAP-1 至 CAP-7）
- ✅ 文字精简（无装饰）

**Pass 2 — 保留性**：源文档中的每一条承重论断均映射到 spec
- ✅ brainstorm-summary 的论断 100% 保留
- ✅ PROJECT-PLAN 的论断 100% 保留
- ✅ 包装性（非承重）内容有意舍弃

**结论**: ✅ SPEC VALID

---

### 4. 故事拆分（stories.yaml）

**8 个可独立交付的故事**，将 7 项 capability 映射到 3 周 MVP：

| Story | Epic | Capabilities | 预估天数 | 优先级 |
|-------|------|--------------|-----------|----------|
| story-1 | 第 1 周：核心基础设施 | CAP-1 | 3 | Critical |
| story-2 | 第 1 周：策略基础 | Policy DSL | 2.5 | Critical |
| story-3 | 第 1-2 周：动态测试 | CAP-2 | 3 | Critical |
| story-4 | 第 2 周：动态验证 | CAP-3 | 3 | Critical |
| story-5 | 第 2 周：判定与报告 | CAP-4 | 3 | Critical |
| story-6 | 第 3 周：CLI 界面 | CAP-5 | 2 | High |
| story-7 | 第 3 周：Web UI | CAP-5、CAP-6 | 3 | High |
| story-8 | 第 3 周：演示与交付 | 全部 | 2 | High |

**总计**: 21.5 天 → 通过并行压缩至 15 个工作日（3 周）

**关键路径**: story-1 → story-2 → story-3 → story-4 → story-5（10 天）  
**并行**: story-6 + story-7 在 story-5 之后（3 天）  
**收尾**: story-8（2 天）

---

## Spec 目录结构

```
spec-apcv-2026-09-12/
├── SPEC.md                    ← 内核（5 字段，精简）
├── .memlog.md                 ← 权威决策日志（只追加）
├── VALIDATION-REPORT.md       ← 自校验（Spec Law + 保留性）
│
├── 配套文件（spec 自著）:
├── probe-rules.md             ← 探针目录（20-30 条规则）
├── policy-dsl-schema.md       ← 策略格式 + 示例
├── architecture-diagrams.md   ← 系统图 + 流程
│
├── stories.yaml               ← Sprint 拆分（8 个故事，3 周）
│
└── [采纳的外部配套文件 - 源自输入文档]:
    └── （在 SPEC.md frontmatter 中引用，不存放于此目录）
```

---

## Memlog 中沉淀的关键决策

`.memlog.md` 文件（只追加的权威日志）保留了：

1. **核心问题**: 验证 Agent 的声明能力与实际能力是否一致
2. **四层碎片化**: MCP + 框架定义 + 运行时 + 子 Agent
3. **策略相对型创新**: 探针随声明边界自适应（而非固定启发式）
4. **MVP 约束**: 仅 LangGraph、参数级追踪、硬编码探针、开发者声明策略
5. **假设**: 5 条显式假设（LangGraph 可静态解析、参数追踪足够、Docker 可用、由开发者声明策略、合规关注审计留痕）
6. **待解问题**: 3 条显式（误报阈值、Policy DSL 语言选择、多租户隔离）

---

## 下游消费者

本 spec 可直接喂给：

1. **bmad-create-architecture**: 产出符合 spec 约束的详细系统设计
2. **开发团队**: 按 spec 构建并保持可追溯性
3. **QA/测试**: 基于 success 信号制定验证计划
4. **产品/市场**: 市场定位、对外口径、竞品分析
5. **法务/合规**: 将监管要求（GDPR/SOX/ISO）映射到 spec

---

## 质量指标

| 指标 | 目标 | 达成 |
|--------|--------|----------|
| Spec Law 合规 | 8/8 规则 | ✅ 8/8 |
| 源文档保留 | 100% 承重论断 | ✅ 100% |
| Capability 数量 | ≥5 | ✅ 7 |
| Constraint 清晰度 | 每条左右设计 | ✅ 6/6 |
| Non-Goals 显式化 | ≥3 条 | ✅ 6 |
| Success Signal 具体度 | 无歧义可测试 | ✅ 是 |
| 假设显式化 | 命名隐藏假设 | ✅ 5 |
| 待解问题记录 | 命名未决缺口 | ✅ 3 |
| 故事拆分覆盖 | 全部 capability 映射 | ✅ 100% |
| 故事可行性 | 3 周 MVP 现实可行 | ✅ 21.5 天 → 15 个工作日 |

---

## 后续步骤

### 即时（1 周内）
1. **干系人评审**: 分享 SPEC.md + 执行摘要
2. **敲定待解问题**: 决定误报阈值、Policy DSL 语言、多租户方案
3. **确认故事拆分**: 与开发团队确认 sprint 安排与依赖关系
4. **指派故事 Owner**: 为每个故事指定负责人

### 第 1-3 周（Sprint 执行）
- 按 stories.yaml 的 sprint 计划推进
- 每个故事通过 spec_checkpoint 回链到 SPEC.md
- 决策产生时更新 .memlog.md
- 每周校验：我们是否仍对齐 spec？

### MVP 之后（Sprint 2+）
- **多框架支持**: 加入 AgentScope、AutoGen（架构已预留）
- **LLM 辅助探针生成**: 动态探针生成（标记为"Could Have"）
- **运行时监控**: 从部署前扩展到运行时持续监视
- **商业化路径**: SaaS 服务、开源社区建设

---

## 可交付的文件

```
d:\Projects\OCASC\_bmad-output\specs\spec-apcv-2026-09-12\

├── SPEC.md                      [阅读: 干系人、开发团队、架构]
├── stories.yaml                 [阅读: 开发团队负责人、项目经理]
├── VALIDATION-REPORT.md         [阅读: QA、架构评审人]
├── .memlog.md                   [维护: 未来的决策追加到此]
├── probe-rules.md               [阅读: 后端团队、QA]
├── policy-dsl-schema.md         [阅读: 后端团队、策略团队]
└── architecture-diagrams.md     [阅读: 全体技术干系人]
```

---

## 总结

✅ **SPEC 已完成并通过校验**

**4 步已完成**：
1. ✅ **SPEC.md 已创建**（5 字段内核，7 项 capability、6 项 constraint、6 项 non-goal）
2. ✅ **配套文件已创建**（probe-rules、policy-dsl-schema、architecture-diagrams）
3. ✅ **自校验通过**（Spec Law 8/8，源文档保留 100%）
4. ✅ **故事拆分完成**（8 个故事，3 周，MVP 可行）

**可用于**:
- 架构设计 sprint
- 开发团队入场
- 干系人评审
- 3 周 MVP 执行

**信心等级**: 🟢 高 — Spec 连贯自洽，保留了全部承重论断，显式标注假设与缺口，并为下游消费者提供了充分细节。

---

**创建者**: bmad-spec skill  
**方法论**: BMad Spec-Kernel  
**日期**: 2026-09-12  
**面向**: Apart Research AI Incident Response Track 1 (Containment) - Agent Policy Conformance Validator MVP
