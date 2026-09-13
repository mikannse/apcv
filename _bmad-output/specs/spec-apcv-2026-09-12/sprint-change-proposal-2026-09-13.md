# Sprint Change Proposal — 补齐动态验证执行管线

- **日期**: 2026-09-13
- **变更类型**: 实现缺陷修正(story 2-2 虚假完成 → 真实实现)
- **协作模式**: Incremental(逐条批准)
- **涉及能力**: CAP-3(隔离执行 + 参数追踪)、CAP-4(一致性检查消费轨迹)、CAP-6(审计证据)

---

## Section 1: Issue Summary

### 问题陈述

APCV 的 `apcv validate` 流水线目前是**"只审题、不监考"**:

1. Step 3 生成 20–30 条探针,但生成的探针**从未被执行**——`IsolatedExecutor` 是 stub,返回 `"Probe execution not yet implemented"`,全项目**零调用点**。
2. Step 4 的一致性检查只比对 **SBOM(工具名列表)与 Policy**,从未消费执行轨迹。
3. 因此"合规分数"只反映**声明层面**的一致性(工具名对不对),**完全测不到 Agent 的实际越界行为**(合法名字背后藏着 `open('/etc/passwd')` 这类动作)。

### 触发原因

Story 2-2「隔离执行与参数追踪」以 stub 形态被标记为完成:

| 证据 | 内容 |
|---|---|
| git 历史 | 提交 `13cc63a` 自述 "executor **stub**",但 `ad1245e` 宣称 "all 8 stories implemented" |
| story 文档 | [2-2-isolated-execution.md](../../_implementation/2-2-isolated-execution.md) 7 条 AC 全部 `[ ]` 未勾选 |
| sprint-status | 2-2 永久停在 `ready-for-dev` |
| 代码 | [executor.py](../../apcv/core/executor.py) 是 stub;`tracer.py` / Dockerfile / `core/execution/` 包均不存在 |

### 核心认知(本次讨论澄清,必须固化)

> **分工边界**:APCV 验证 Agent 的越界**行为**(它企图做什么),部署平台负责生产环境的**强制**(门怎么锁)。动态验证的沙箱不是"生产环境的预演",而是"安全观察室"——安全地观察 Agent 代码的真实行为。

> **静态 vs 动态**:静态检查比的是"工具**名字**对不对"(字符串匹配,一读一个准但只能查表面);动态验证比的是"工具**行为**对不对"(真执行,能查出合法名字背后藏着的越界动作)。安全工具只信 Agent 自报的名字,等于让嫌疑人自填证词。

---

## Section 2: Impact Analysis

### Epic 影响

| Epic | 结论 |
|---|---|
| epic-2「动态验证」 | **实际未完成**。2-1(探针规则)✅ 真完成;2-2(隔离执行)❌ stub;2-3(一致性)⚠️ 半完成(检查器存在,但"消费执行轨迹"的输入端从未存在) |
| epic-3「界面与演示」 | 3-1(CLI)需在 Step 3/4 间接线执行器;3-2(Web UI)应改读 `.apcv/reports/` 真实报告(本轮之后);3-3(演示)的"FAIL 判定"依赖真执行,顺序不变 |

**无需新增 epic、无需重排顺序。** 关键路径 story-1→2→3→4→5 恢复原样。

### Artifact 冲突

| Artifact | 冲突 | 处理 |
|---|---|---|
| ARCHITECTURE-SPINE.md | ProbeExecutor 在 `core/infrastructure/`,story 2-2 写的是 `core/execution/` | 采纳 story 文档(更晚、更具体),见提案 2 |
| stories.yaml / SPEC | CAP-3 定义仍有效,无需求变更 | 冲突在**状态层面**,非需求层面 |
| sprint-status.yaml | 全部停在 `ready-for-dev`,未反映真实进度 | 回退,见提案 1 |
| fixture | `from langraph import tool` 拼错 | 阶段二 import 会炸,见提案 4 |
| .gitignore | 已有 `.apcv/` 条目(第 60 行) | **无需改动** |

### 技术影响

- 引入 Docker SDK 作为执行依赖(SPEC 假设"部署环境具备 Docker",成立)
- 新增 `apcv/core/execution/` 包、`docker/apcv-probe/` 构建上下文
- CLI 增加执行步骤 + `--skip-execution` 兜底 + `--workers`
- 报告落盘 `.apcv/reports/`(AD-8,当前完全未实现)

---

## Section 3: Recommended Approach

**推荐:方案一「直接调整」+ 状态修正。**

- Story 2-2 的规格无缺陷,只是从未兑现——不需要改需求,只需"把已写好的 story 真正做完"
- 无代码需回滚,接线点干净
- MVP 范围不动

### 工作量与风险

| 项 | 估算 |
|---|---|
| 阶段一(执行管线骨架) | ~1 天 |
| 阶段二(ProbeHost + wrapt 追踪) | ~2-3 天 |
| 合计 | ~3-4 天 |
| 主要风险 | Docker Desktop on Windows 集成、ProbeHost 协议的自有性(非 LangGraph 官方 API) |

### 探针定位修正(本次讨论的关键产出)

原设计把"环境型探针(23 条 shell)"当安全探针,是**过度设计**。修正后:

| 类别 | 数量 | 修正后的定位 |
|---|---|---|
| Shell 型(fs/network/privilege) | 23 | **降级**:不是安全探针,只作 executor 的普通单元/管线测试;`sandbox.py` 翻译逻辑用纯单元测试覆盖(不启动容器) |
| Agent 型(tool/parameter) | 12 | **核心价值**:经 ProbeHost 真实执行,测 Agent 越界行为 |

---

## Section 4: Detailed Change Proposals

### 提案 1 — sprint-status.yaml 状态回退 ✅ 已批准

**文件**: `_implementation/sprint-status.yaml`

```yaml
OLD:
  2-2-isolated-execution:
    status: "ready-for-dev"

NEW:
  2-2-isolated-execution:
    status: "in-progress"
    last_updated: "2026-09-13"
    note: "correct-course 2026-09-13: AC 全部未兑现(executor stub、无 tracer/Dockerfile),状态回退,见 sprint-change-proposal"

  2-3-conformance-check:
    status: "review"   # 检查器本体已交付,但"消费执行轨迹"的一端待 2-2 完成后补接线
```

**理由**:诚实反映状态,防止后续 sprint 基于"全部完成"的错误前提规划。不改写 git 历史。

---

### 提案 2 — 架构路径调和 ✅ 已批准

**决定**:采纳 story 2-2 文档的 `core/execution/` + `docker/apcv-probe/`,而非架构主干的 `core/infrastructure/`。

**文件**: `_bmad-output/architecture/architecture-apcv-2026-09-12/ARCHITECTURE-SPINE.md`

结构种子中 `infrastructure/` 块改为 `execution/` 块;能力映射表 "在隔离沙箱中执行 probe" 指向 `core/execution/executor.py`。

**遗留偏差(仅记录,本轮不动)**:架构主干的 AD-2/AD-9 假设四边界(tool/runtime/network/identity),实际 DSL 是五类边界(tool/filesystem/network/privilege/rate_limit),且只有 ToolScanner 存在——主干标 `status: draft` 且从未对齐现实,留待架构正式化时处理。

---

### 提案 3 — 阶段一:执行管线骨架 ✅ 已批准

**目标**:打通"生成探针 → 执行 → 落盘"这根管子。

**新增文件**:
```
apcv/core/execution/
├── __init__.py
├── executor.py        # IsolatedExecutor(Docker 执行器,从 apcv/core/executor.py 迁入并重写)
└── sandbox.py         # 策略 → Docker 参数翻译(纯函数,单元测试覆盖)

docker/apcv-probe/
├── Dockerfile         # python:3.11-slim + 依赖,非 root 用户
├── requirements.txt
└── entrypoint.py      # 容器入口:收探针 → 执行 → 回传 trace
```

**CLI 接线**([main.py](../../apcv/cli/main.py)):Step 3/4 之间插入 Step 3.5「Executing probes...」;新增 `--skip-execution`(无 Docker 退回纯静态 + WARNING)与 `--workers`。

**报告落盘**(补 AD-8):每次运行写 `.apcv/reports/{timestamp}_{agent}.json`。

**验收**:执行管线通、报告落盘、`--skip-execution` 兜底、测试全绿。

---

### 提案 4 — 阶段二:ProbeHost + wrapt 追踪 ✅ 已批准(方案 A)

**目标**:让 12 条 Agent 型探针活起来,产出 CAP-6 审计证据。

**新增文件**:
```
apcv/core/execution/
├── probe_host.py     # ProbeHost:收集 @tool 函数 → 暴露 call_tool/tools
├── tracer.py         # wrapt 钩子:记录 (时间戳, 工具名, 参数, 结果)
└── trace_model.py    # ExecutionTrace/TraceRecord Pydantic 模型 + JSONL 读写
```

**ProbeHost 协议**:
```python
class ProbeHost:
    tools: dict                          # 名字 → 真实函数
    def register(func)                   # 收集 @tool 函数
    @traced
    def call_tool(name, args)            # 查注册表;未注册 → PermissionError
    def load_agent_file(path)            # import 用户 agent,自动注册所有 @tool
```

**JSONL 轨迹**(审计录像):
```json
{"ts": "2026-09-13T...", "tool": "search_documents", "args": {"query": "$(rm -rf /)"}, "result": "...", "status": "ok"}
```

**fixture 修复**:[simple_agent.py](../../tests/fixtures/sample_agents/simple_agent.py) 的 `from langraph import tool` → `from langgraph import tool`(阶段二真实 import 必须;测试内联字符串不 import,可不动)。

**边界声明(写入 SPEC)**:ProbeHost 是 APCV 自有协议,测的是**工具集合层越界**(能否调到不该调的、参数有无约束),**测不到**"LLM 是否被诱导调用"(属非目标"对抗式审计",SPEC 已排除)。

---

### 提案 5 — 探针可执行性分类 ✅ 已批准(经修正)

**问题**:探针命令分两类,盲目 `exec` 会误报。

**解决**:给 [probe.py](../../apcv/core/probes/probe.py) 增加显式 `execution` 字段(`"shell" | "agent"`),执行器据此分流。不靠 `category` 硬编码,保证加新探针时作者必须声明执行方式。

**修正后的分类语义**:
- `shell` 型:降级为 executor 的管线测试(非安全探针)
- `agent` 型:核心安全探针,经 ProbeHost 执行

**.gitignore**:核实已有 `.apcv/` 条目,**无需改动**。

---

## Section 5: Implementation Handoff

### 变更范围分类:**Moderate**

涉及 backlog 状态修正 + 跨 story 接线 + 架构文档更新 + 新增执行子系统,但需求无变更、无新增 story、无战略转向。

### 执行顺序

1. **提案 1**(状态回退)— 立即可做,无依赖
2. **提案 2**(架构路径)— 立即可做
3. **提案 3**(阶段一骨架)— 依赖 2
4. **提案 4**(阶段二 ProbeHost)— 依赖 3
5. **提案 5**(探针分类)— 与 3/4 并行

### 成功标准

- `apcv validate` 端到端输出「N 次越界尝试,M 次被抓」的真实执行结果(而非仅"生成了 N 条探针")
- 报告落盘 `.apcv/reports/`,含 JSONL 参数轨迹,可作审计证据
- Story 2-2 的 7 条 AC 全部真实勾选,状态更新为 `done`
- Story 2-3 补上"消费执行轨迹"的接线
- 单元测试覆盖 sandbox 翻译逻辑、ProbeHost 协议、executor 归因;Docker 集成测试带 `@pytest.mark.docker` 标记
- README 的 "Isolated Execution" 承诺名副其实

### 遗留(本轮不做)

- Web UI(3-2)改读真实报告 — 下一轮
- SARIF/HTML 输出格式(3-1 AC 的一部分)
- 架构主干四边界 vs 现实五边界的对齐 — 架构正式化时
