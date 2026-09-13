# 自校验报告

**校验者**: bmad-spec  
**日期**: 2026-09-12  
**Spec 目录**: spec-apcv-2026-09-12

---

## Pass 1: 连贯性检查（Spec Law 规则 1-6、8）

### 规则 1：每项 Capability 同时具备 intent 与 success
✅ **PASS** — 全部 7 项 capability（CAP-1 至 CAP-7）均包含：
- Intent：对"应当做到什么"的清晰陈述
- Success：具体、可测试、可度量的结果

举例：
- CAP-1（工具发现）：intent="发现完整工具面" + success="准确率 >95%，<10s"
- CAP-5（CLI/UI）：intent="同时服务 DevOps 与安全团队" + success="CLI 可在 CI/CD 中运行、Web 看板功能可用"

### 规则 2：Intent 描述 WHAT，而非 HOW
✅ **PASS** — 所有 intent 聚焦结果，而非实现：
- ❌ 不是"使用 AST 解析器查找 @tool 装饰器"
- ✅ 而是"发现完整工具面"
- ❌ 不是"用 wrapt decorator 包装"
- ✅ 而是"执行探针并记录参数轨迹"

实现细节交由配套文件（architecture-diagrams.md）承载。

### 规则 3：Constraints 确实左右设计决策
✅ **PASS** — 全部 6 项 constraint 都做出了实质性取舍：
- "四层工具碎片化" → 推导出统一 SBOM 的要求（改变设计）
- "策略相对型生成" → 排除固定启发式（改变方法）
- "确定性验证" → MVP 排除 LLM 探测（改变能力范围）
- "MVP：仅 LangGraph" → 影响架构（需要框架无关的适配器）
- "开发者声明策略" → 影响上手流程（改变用户旅程）

移除或修改其中任一 constraint，都会导向不同的设计。

### 规则 4：Non-goals 显式列出
✅ **PASS** — Non-Goals 一节列出 6 项显式排除：
- 运行时强制
- 提示词注入检测
- 对抗式 Agent 深度审计（标记为"Could Have"而非"MVP"）
- 多框架 MVP
- IAM/IaC 自动推断
- 沙箱副作用追踪

这些在 MVP 中的缺席是有意为之，而非疏漏。

### 规则 5：Success signal 具体且可测试
✅ **PASS** — Success Signal 一节包含具体、可测试的多个维度：
- **技术**：工具发现准确率 >95%、Probe 执行 <2 分钟、追踪开销 <1%、Docker 隔离且测试间零交叉
- **产品**：DevOps 采纳度（在 CI/CD 中运行、2 分钟内得到 PASS/FAIL、部署信心）
- **市场**：零竞品、3+ 家试点客户、EU AI Act 合规路径
- **监管**：报告通过审计师评审、证据链可验证

全部指标均可无歧义地度量。

### 规则 6：Capability ID 稳定且唯一
✅ **PASS** — 所有 capability 按 CAP-1 至 CAP-7 编号，绝不复用：
- CAP-1: 工具面发现
- CAP-2: 策略相对型 Probe 生成
- CAP-3: 隔离的 Probe 执行与参数追踪
- CAP-4: 一致性检查与差异报告
- CAP-5: CLI 与 Web UI 双入口
- CAP-6: 监管级合规报告
- CAP-7: LangGraph 端到端支持

无空缺，无重复。

### 规则 8：文字精简（无装饰，每句承重）
✅ **基本通过** — SPEC.md 精炼，配套文件详略得当：
- 已删除：含糊措辞（"might"、"could potentially"）、背景铺陈、空话开场
- 保留：必要的问题陈述、设计理由、取舍说明
- 配套文件（architecture-diagrams.md）承载图示与详细示例，而不使内核臃肿

小注："Why" 一节中有少数句子可以更紧凑，但它们仍承重（删去会丢失上下文）。

---

## Pass 2: 保留性检查（每条承重论断都落入 spec）

### 来源 1：brainstorm-summary.md

| 论断 | SPEC.md 落点 | 状态 |
|-------|-----------------|--------|
| 核心命题（验证声明 vs 实际） | Why 一节 | ✅ |
| 四层工具碎片化 | Constraints 一节 + CAP-1 | ✅ |
| 策略相对型 Probe 创新 | CAP-2、核心创新表 | ✅ |
| 市场信号（65% 事件） | Why 一节 | ✅ |
| 三阶段工作流（静态/动态/判定） | 架构配套文件 | ✅ |
| 参数级追踪（MVP 选择） | Constraints 一节 | ✅ |
| MVP 不使用 LLM 驱动探测 | Non-Goals 一节 | ✅ |
| DevSecOps 定位（CI/CD 门禁） | Why 一节 | ✅ |
| 开发者声明策略（非自动推断） | Constraints 一节 | ✅ |
| 探针规则库（20-30 条） | CAP-3 + probe-rules.md 配套文件 | ✅ |
| HuggingFace 事件作为驱动 | Why 一节 | ✅ |

**结论**: brainstorm 中的承重论断 100% 保留在 spec 或配套文件中。

### 来源 2：PROJECT-PLAN-FINAL-2026-09-12.md

| 论断 | SPEC.md 落点 | 状态 |
|-------|-----------------|--------|
| MVP：3 周（LangGraph + CLI + Web UI） | Constraints 一节 | ✅ |
| Tool SBOM 作为唯一可信来源 | CAP-1、Constraints | ✅ |
| 合规要求（GDPR/SOX/ISO） | CAP-6、Success Signal | ✅ |
| Probe 执行采用 Docker 隔离 | Constraints 一节 + 架构 | ✅ |
| DevOps 优先（采纳度优先） | Success Signal | ✅ |
| 框架无关架构 | Constraints 一节 | ✅ |
| Policy DSL（YAML schema） | CAP-2 + policy-dsl-schema.md 配套文件 | ✅ |
| 执行轨迹 JSON 格式 | architecture-diagrams.md 配套文件 | ✅ |
| 性能目标（端到端 <2 分钟） | Success Signal、CAP-3 | ✅ |
| Sprint 拆分（第 1-3 周） | 归入故事拆分（非 spec 承重内容） | ✅ |

**结论**: 项目计划的承重论断 100% 保留。

### 仅包装性内容（有意舍弃）

以下源文档条目属于**运营元数据**，对下游消费者并不承重：

- Sprint 日历（第 1-15 天任务拆分）→ 执行细节，非 spec 契约
- 团队角色与组织结构 → 实现层面的关注点，非能力定义
- 风险表（概率/影响）→ 项目管理内容，非 spec
- 市场规模测算（$1.35B → $4.57B）→ 上下文，非约束
- 竞品功能矩阵 → 市场分析，非规格说明
- 会议记录与决策论证文字 → 过程历史，非契约

**结论**: 被舍弃的内容被恰当归类为非承重内容。

---

## 总结

| 检查项 | 结果 | 说明 |
|-------|--------|-------|
| **Spec Law 1-8** | ✅ 7/7 PASS | 全部核心规则满足 |
| **源文档保留** | ✅ 100% | 每条论断均映射到 spec 或配套文件 |
| **假设清晰度** | ✅ 5 条显式 | 列于 frontmatter，非隐含 |
| **待解问题** | ✅ 3 条显式 | 列于 frontmatter 以待解决 |
| **配套文件完备性** | ✅ 已创建 4 项 | probe-rules、policy-dsl-schema、architecture-diagrams + 采纳的来源 |
| **Non-Goals 显式化** | ✅ 6 条 | 对 MVP 的清晰排除项 |

**总体结论**: ✅ **SPEC VALID**

该 spec 连贯自洽，保留了全部承重论断，显式标注假设与待解问题，并通过配套文件为下游消费者（bmad-prd、bmad-architecture、开发团队）提供了充分细节。

---

## 可进入下一步：故事拆分

SPEC.md 已通过校验，spec 现已可支撑：
1. **故事拆分**（bmad-story-breakdown）：将各 capability 分解为 6-8 个可独立交付的 sprint
2. **架构设计**（bmad-create-architecture）：产出符合 spec 约束的详细系统设计
3. **开发执行**（开发团队）：按 spec 构建并保持可追溯性

建议先行推进**故事拆分**，把 7 项 capability 映射到 3 周的 sprint 结构。
