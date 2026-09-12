# AI Agent Containment 黑客松项目 - 集思录总结

**日期**：2026-09-12  
**事件**：Apart Research AI Incident Response Sprint 2026 Track 1 (Containment) 项目方向选定  
**协作模式**：Creative Partner  
**状态**：已完成  

---

## 1. 项目背景与问题定义

### 核心命题
**如何在企业 AI Agent 部署前，通过静态扫描与动态探针相结合的方式，验证 Agent 的实际能力边界是否符合预声明的安全策略，产出第三方可验证证据，成为 DevSecOps 流程中的部署卡点？**

### 问题切入点
- 企业部署的 AI Agent 常基于框架（如 AgentScope、LangGraph）编写
- Agent 的完整 tool surface 分散在四层不同的代码位置，没有统一的声明与审计机制
- 现有工具缺乏从代码级静态发现、到运行时动态验证、再到策略判决的闭环能力
- HuggingFace 事件等案例表明，声明的资源访问范围与实际访问能力常存在缝隙

---

## 2. 选定的产品方向

### 产品名称
**Agent Policy Conformance Validator（Agent 策略符合性验证器）**

### 产品定位
- **类比对标**：传统应用安全中的 DevSecOps 流程（SAST + DAST + Policy Gateway）
- **部署位置**：CI/CD 流程中的部署前安全卡点，而非实时运行时拦截
- **目标用户**：企业 AI 安全团队、Agent 开发者
- **核心价值**：提供"声明 vs 实际"的可信差异报告，驱动部署决策

### 完整工作定义
该产品分为三个主要阶段：

#### 阶段 1：静态代码扫描（发现 Tool Surface）
从 Agent 代码中自动发现完整的 tool surface，覆盖四层叠加：
1. **MCP Tools**：通过 MCP Server manifest 获取
2. **Agent-Defined Function Calls**：通过框架代码解析发现
3. **Runtime 内置能力**：框架本身支持的隐式工具（如代码执行、文件访问等）
4. **Sub-Agent 继承**：多 agent 能力合成的递归声明

输出：Agent Tool SBOM（能力成分清单）

#### 阶段 2：动态策略相对探针（验证边界）
- **输入**：Declared Policy（开发者编写的声明约束，如"仅可访问 GitHub")
- **核心逻辑**：自动生成 policy 边界**之外**的探针，检验 agent 是否会越界
- **Probe 类型**：参数追踪型（instrumentation wrapper），记录工具实际调用参数
- **输出**：Execution Trace（工具调用参数日志）

#### 阶段 3：Policy Conformance 判决
- 对比 Declared Policy 与 Execution Trace
- 输出：Declared vs Actual Diff 报告
- 根据预设 policy 规则，判定 PASS / FAIL
- FAIL 时可触发部署阻断

### 核心逻辑链
```
Agent Code 
  ↓ [Static Scan]
Tool SBOM + Declared Policy
  ↓ [Probe Generation]
Policy-Relative Probes (参数边界外测试)
  ↓ [Dynamic Execution]
Execution Trace (工具调用日志)
  ↓ [Policy Conformance Check]
Declared vs Actual Diff + PASS/FAIL Decision
```

---

## 3. 核心设计决策

### Decision 1: 动态 Probe 的追踪方式
**决策**：优先实现参数追踪（Instrumentation Wrapper），暂不做 sandbox 副作用追踪

**推导过程**：
- 两种 probe 方式的权衡：
  - 参数追踪：确定性高，framework 无关，sprint 内可交付
  - Sandbox 副作用追踪：覆盖更全，但复杂度高，需要容器化环境
- 结论：参数追踪足以验证工具是否被调用及其参数是否越界，是最小可行验证集合

### Decision 2: 声明范围的责任主体
**决策**：声明能触达的资源范围由 Agent 开发者主动编写

**推导过程**：
- 不能依赖自动推断（IAM/IaC）作为首发能力，应作为后续调研方向
- 开发者声明是 DevSecOps 流程的标准做法（类比 container security policy）
- 支持开发者声明的工具链：DSL 定义 + YAML 配置 + IDE 集成

### Decision 3: 策略触发部署阻断的规则
**决策**：将 Policy 层显式纳入产品，定义什么样的 diff 结果触发阻断

**推导过程**：
- Diff 报告本身只是信息呈现，需要策略规则驱动自动决策
- Policy Rules 示例：
  - "如果检测到未声明的系统调用（bash 工具），FAIL"
  - "如果参数访问范围超出声明的资源列表 10%，WARN"
  - "如果发现提权工具调用，FAIL"
- 支持可配置的严格度等级（Strict / Balanced / Report-Only）

### Decision 4: Probe 生成的相对性（关键洞察）
**决策**：Probe 内容以 declared policy 为基准自动生成，而非固定的危险资源列表

**推导过程**：
- 早期讨论误区：定义通用危险资源清单（~/.ssh, /etc/passwd 等）进行测试
- 用户纠正：不同 agent 有不同的安全边界，关键是检验是否超出**自己声明的边界**
- 示例：
  - Agent 声明"仅访问 /data 目录" → probe 生成访问 /etc、/home 的测试
  - Agent 声明"仅能调用 read_file 工具" → probe 生成调用 delete_file 的测试
- 这一决策同时解决了**可信度**和**覆盖率**问题

### Decision 5: Sprint 优先级调整
**决策**：MCP 层反而排后（已有 manifest 规范，可见性最高）；UI 是必要的，不是可砍选项

**推导过程**：
- 初期误区：以为 MCP 是优先工作
- 用户纠正：真正的 tool surface 在代码里（框架内置 + 开发者自定义），不在 MCP
- 企业 agent 主要基于框架编写，MCP 的采用度不如 framework 工具
- Sprint 优先级应为：
  1. Framework 工具扫描引擎
  2. Dynamic probe 执行框架 + 参数追踪
  3. UI 呈现 declared vs actual diff
  4. Policy 决策引擎
  5. MCP 层支持（作为可选扩展）

### Decision 6: Adversarial Agent as Validator 的地位
**决策**：从 Won't 移入 Could，定位为"深度审计模式"，与确定性 probe（CI/CD gate）互补而非替代

**推导过程**：
- 早期：对 adversarial agent（一个 agent 骚扰另一个找边界）持谨慎态度
- Coach 提议：自动化攻击过程变成证据链
- 用户顾虑：agent 行为受 prompt 影响，可信度存疑
- 最终共识：
  - 确定性 probe（参数级） = 部署卡点（高可信）
  - Adversarial agent = 深度安全评估（发现边界的灰区）
  - 两者服务不同的用户需求

---

## 4. 产品结构与工作流程

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Codebase                            │
│  (Framework: LangGraph, AgentScope, 或自定义)                │
└────┬──────────┬──────────────┬──────────────┬────────────────┘
     │          │              │              │
     ▼          ▼              ▼              ▼
 MCP Tools   Agent-Defined  Runtime Built-in Sub-Agent
 (manifest)  Function Calls  Capabilities   Tools
     │          │              │              │
     └──────────┴──────────────┴──────────────┘
              │
              ▼
     ┌─────────────────────┐
     │  Static Scanner     │
     │  (Framework-aware)  │
     └────────┬────────────┘
              │
              ▼
     ┌─────────────────────┐
     │  Agent Tool SBOM    │
     │  (完整能力清单)      │
     └────────┬────────────┘
              │
         ┌────▼────┐
         │          │
         ▼          ▼
  Declared    Probe Generator
  Policy      (Policy-relative)
         │          │
         └────┬─────┘
              ▼
     ┌─────────────────────┐
     │  Instrumentation    │
     │  Wrapper Probes     │
     │  (参数追踪)         │
     └────────┬────────────┘
              │
              ▼
    ┌──────────────────────┐
    │  Agent Execution     │
    │  with Tracing        │
    └────────┬─────────────┘
             │
             ▼
    ┌──────────────────────┐
    │  Execution Trace     │
    │  (工具调用日志)      │
    └────────┬─────────────┘
             │
             ▼
    ┌──────────────────────┐
    │  Conformance Check   │
    │  (Diff 对比)         │
    └────────┬─────────────┘
             │
             ▼
    ┌──────────────────────┐
    │  Policy Validator    │
    │  (规则判决)          │
    └────────┬─────────────┘
             │
    ┌────────▼────────┐
    │  PASS / FAIL    │
    │  Diff Report    │
    │  + Deployment   │
    │    Gate Signal  │
    └─────────────────┘
```

### 数据流与用户交互流程

#### 流程 A：初始部署检查（CI/CD Gate）
```
1. 开发者提交 Agent 代码 + Declared Policy YAML
   ↓
2. CI 系统自动触发 Validator
   ↓
3. [Static Scan] 解析框架代码，提取 Tool SBOM
   ↓
4. [Probe Gen] 根据 Policy 自动生成边界外测试集
   ↓
5. [Dynamic Exec] 在沙箱环境运行 probes，记录 Execution Trace
   ↓
6. [Conformance] 对比 SBOM vs Actual Calls，生成 Diff Report
   ↓
7. [Policy Check] 应用 policy rules，判定 PASS/FAIL
   ↓
8. 输出：
   - 如果 PASS → 部署继续
   - 如果 FAIL → 阻断部署，输出详细差异报告
```

#### 流程 B：迭代修复工作流
```
1. 开发者收到 FAIL 报告（含具体差异和违反的 policy rule）
   ↓
2. 选择：
   a) 修改 Agent 代码（移除越界工具调用）
   b) 扩展 Declared Policy（承认这些工具是需要的）
   ↓
3. 重新提交，自动重新验证
   ↓
4. 直到 PASS
```

#### 流程 C：深度审计（可选，Could 范围）
```
1. 对于高敏感 agent，启用 Adversarial Agent Mode
   ↓
2. 多轮自适应探测，捕捉 prompt-dependent 边界情况
   ↓
3. 生成"灰区边界"报告（覆盖率热力图）
   ↓
4. 作为补充审计证据
```

### 输出交付物

| 输出物 | 格式 | 用途 | 消费者 |
|-------|------|------|--------|
| Tool SBOM | JSON | 透明声明 agent 能力 | 安全审计、合规检查 |
| Execution Trace | JSON Lines | 记录 probe 运行结果 | 事后取证、审计日志 |
| Declared vs Actual Diff | Markdown + JSON | 可视化差异、机器判决 | 开发者、CICD 系统 |
| Policy Conformance Report | HTML + JSON | 部署决策依据 | DevOps、安全团队 |
| Coverage Heatmap | HTML | 边界覆盖度评估 | 安全审计（深度模式） |

---

## 5. MoSCoW 范围

### Must Have（Sprint 核心交付）

- [ ] **Framework Tool Scanner**
  - 支持至少一个主流框架（LangGraph 或 AgentScope）的工具发现
  - 输出结构化 Tool SBOM（含工具名、签名、声明的参数范围）
  - 框架无关的解析策略（避免硬编码特定框架）

- [ ] **Policy Declaration Schema**
  - YAML/JSON DSL 定义声明策略（资源范围、工具白名单、参数约束）
  - 支持至少 3 种基础规则类型（Allow / Deny / Constrain）
  - Schema 验证 + IDE 智能提示（或文档示例）

- [ ] **Probe Generator & Executor**
  - 根据 Policy 自动生成边界外 probes（参数级别）
  - Instrumentation wrapper 捕获工具调用参数
  - 支持隔离执行环境（Docker 或进程沙箱）

- [ ] **Conformance Check Engine**
  - 对比 SBOM 与 Execution Trace，生成 Declared vs Actual Diff
  - Diff 以 JSON 结构化输出，便于机器判决
  - 支持可配置的匹配规则（精确 / 前缀 / 参数范围等）

- [ ] **Policy Validator & Decision Gate**
  - 应用 policy rules 对 Diff 进行判决
  - 输出 PASS / FAIL + violation details
  - 支持 3 种严格度模式：Strict / Balanced / Report-Only

- [ ] **基础 UI**（命令行或 Web）
  - 展示 Tool SBOM（树形结构）
  - 展示 Diff Report（对比视图）
  - 展示 Policy Conformance 结果（PASS/FAIL + violations）
  - 支持导出为 PDF / JSON

- [ ] **Demo 场景 + 演示代码**
  - HuggingFace 微缩版复现（见下章节）
  - 可独立运行、可重现的演示脚本

### Should Have（优先补充）

- [ ] **多框架支持**
  - 扩展至 2-3 个其他框架（AutoGen、CAMEL 等）
  - 抽象共同的扫描模式，提升框架适配效率

- [ ] **Advanced Policy Features**
  - 参数范围约束（如文件路径正则匹配）
  - 工具调用频率限制
  - 上下文感知的条件规则（A 工具调用后才允许 B）

- [ ] **Coverage Scoring**
  - 计算 probe 对 policy 边界的覆盖度量
  - 输出覆盖热力图，指导测试补充

- [ ] **Integration with CI/CD**
  - GitHub Actions / GitLab CI 官方集成
  - 支持 webhook 触发、PR comment 反馈

### Could Have（后续方向）

- [ ] **Adversarial Agent as Deep Validator**
  - 自动化多轮探测，发现灰区边界
  - Prompt-aware 适应性测试

- [ ] **IAM/IaC 自动推断**
  - 从 Kubernetes RBAC / AWS IAM policy 自动推导 agent declared policy
  - 反向映射：生成 IaC 规则以自动执行 policy

- [ ] **Multi-Agent Ability Composition**
  - 支持 sub-agent 的递归能力声明与合成验证
  - 调用链追踪（A agent 调用 B agent 调用 C 的工具链）

- [ ] **Runtime Monitoring Mode**
  - 从部署前卡点扩展到运行时监控
  - 持续采样 agent 调用，与 policy 进行实时对标

- [ ] **Behavioral Analysis with LLM**
  - 用 LLM 解析 execution trace，生成自然语言风险描述
  - 异常行为的自动化分类

### Won't（明确不在本 Sprint）

- 实时 sandbox 副作用追踪（如文件系统写入监控）— 复杂度高，参数追踪足以应对初期需求
- 通用 agent 安全框架（如 AIOS）— 超出 sprint 范围
- Agent 运行时沙箱隔离 — 这是部署环保的事，不是 validator 的事

### 调研后决定

- [ ] **单框架 vs 框架无关的可扩展性权衡**
  - Sprint 内实现一个框架的完整支持，还是用抽象层支持多个（但可能不完整）？
  - 建议：第一版单框架（LangGraph）完整，后续再做适配器

- [ ] **业界现有工作的对标**
  - Agent SBOM 概念是否已有相关工作？
  - 参数追踪的工具链现状？
  - 竞品分析（MLflow Model Registry、Hugging Face Model Card 的启示）

- [ ] **企业部署环境的具体限制**
  - Agent 运行在容器、VM 还是 serverless？
  - 是否支持网络隔离、文件系统只读等约束？
  - Policy 声明是否需要适配企业 IAM 系统？

- [ ] **法规合规性映射**
  - GDPR / SOX / ISO27001 中对 agent 能力审计的要求
  - 该 validator 是否满足相关合规检查清单？

---

## 6. 关键洞察与突破点

### 洞察 1：Agent Tool Surface 的四层叠加问题
**问题所在**：企业 agent 的完整能力分散在四个不同的位置，没有统一的声明机制。

**四层结构**：
1. MCP Tool（最可见，有 manifest）
2. Agent-Defined Function Call（框架代码中定义）
3. Runtime 内置能力（框架隐含的系统调用能力）
4. Sub-Agent 继承（多 agent 协作时的能力合成）

**突破**：Agent SBOM 概念整合四层，成为唯一可信源（Single Source of Truth）。

**用户贡献**：指出真正的 tool surface 在代码里，而非 MCP 最可见的部分。这纠正了初期对优先级的误判。

---

### 洞察 2：Policy-Relative Probe 的相对性（关键纠正）
**初期误区**：定义通用危险资源清单（~/.ssh, /etc/passwd 等），对所有 agent 进行相同的安全测试。

**问题**：这种通用列表无法适应不同 agent 的不同安全边界，导致误报与漏报并存。

**突破**：Probe 内容以 declared policy 为基准动态生成。

**示例对比**：
- ❌ 通用做法：测试所有 agent 是否能访问 /etc/passwd
- ✅ Policy-Relative：Agent 声明"仅访问 /data" → 测试是否能访问 /etc、/home、/var 等边界外路径

**效果**：
- **可信度提升**：测试的是 agent 是否守住自己承诺的边界，而非某个固定的安全线
- **覆盖率优化**：不同 agent 的覆盖焦点不同，减少无关测试
- **False Positive 减少**：严格边界的 agent 和宽松边界的 agent 用不同的测试集

**用户贡献**：多次纠正对"边界"定义的理解，明确"边界是相对于 declared policy 的"。

---

### 洞察 3：可信度与采用阻力的二元对立
**两个硬伤**：
1. **可信度问题**：Agent 行为依赖 prompt，同一 agent 用不同 prompt 可能表现不同。baseline 和 coverage 会变化，PASS 结果是否可信？
2. **采用阻力**：企业为什么要相信这个 validator？false positive 会导致部署延迟。

**突破方案**：确定性 Probe（参数级） + Policy-Relative 生成

**推导逻辑**：
- 参数级追踪不依赖 agent 的推理逻辑，而是直接检查工具是否被调用及参数是否越界
- Policy-relative 确保测试集与业务声明直接绑定（减少主观性）
- 示例：即使 prompt 改变，工具是否被调用这一事实不变；参数是否超范围这一约束也不变

**结果**：
- ✅ 可信度高（确定性强）
- ✅ 采用易（对标传统 DevSecOps）
- ⚠️ 权衡：不能捕捉 prompt-dependent 的灰区（通过 Could 中的 Adversarial Mode 补充）

---

### 洞察 4：企业 Agent 场景的定位纠正
**初期定位**：实时拦截工具调用（类似 App Store 的安全审核）。

**问题**：企业部署有多样化的流程和风险接纳度，一刀切的实时拦截不适用。

**用户纠正**：企业场景应类比**传统应用安全的 CICD 流程**，而非端点防护。

**重新定位**：
- **时机**：部署前的 CI/CD gate，而非运行时
- **决策权**：安全团队定义 policy，开发者选择接纳或修复
- **证据形式**：可审计的 Diff 报告 + PASS/FAIL，而非黑箱决策
- **回溯**：支持部署前审查与部署后追溯

**示例工作流**：
```
Commit → Push → CI Trigger Validator → 检测到违反 policy → 
Notify 开发者 → 开发者修改 Policy OR 修改代码 → 重新验证 → PASS → Merge → Deploy
```

**效果**：符合企业安全治理的标准流程，低采用阻力。

---

### 洞察 5：真正的 Tool Surface 在框架代码里，不在 MCP
**初期误区**：以为 MCP 是 agent 能力的主要来源，优先做 MCP 支持。

**事实调查**：企业 agent 主要基于框架（LangGraph、AgentScope）编写，框架内置了大量工具（代码执行、文件访问等）。MCP 的采用度并未如预期高。

**纠正推导**：
- MCP 是最可见的（有 manifest 规范）
- 但不是最重要的（大多数 agent 工具来自框架 + 开发者自定义）
- 框架工具的发现需要代码解析，MCP 工具的发现只需读 manifest
- **优先级应该反转**：框架 >> 开发者自定义 > MCP

**用户贡献**：直接指出"真正的 tool surface 在代码里"，提示我们重新理解问题结构。

---

### 洞察 6：Adversarial Agent 的角色再定义
**初期态度**：谨慎，不确定是否必要。

**Coach 提议**：自动化攻击过程，生成证据链。

**用户质疑**：Agent 行为受 prompt 影响，可信度有问题。

**最终共识**：两种互补的验证模式
- **模式 A（部署卡点）**：确定性 probe（参数级） → PASS/FAIL 决策 → 高可信、低覆盖
- **模式 B（深度审计）**：Adversarial Agent → 发现灰区 → 补充建议 → 低自动化、高洞察

**结论**：从"要么有要么没有"改为"两个用途，两个服务不同客户需求"。

---

## 7. Demo 场景

### Demo 场景：HuggingFace 微缩版复现

**背景**：再现一个真实安全事件的简化版本，展示 Validator 如何有效检测。

**场景设定**：
- Agent 声明："仅能访问 GitHub repository 的公开信息"
- Declared Policy YAML：
  ```yaml
  resources:
    allowed_domains: ["github.com/api"]
    allowed_tools: ["read_file", "http_get"]
    denied_tools: ["bash", "ssh"]
  constraints:
    read_file:
      path_pattern: "^/workspace/github_.*"
    http_get:
      domain_whitelist: ["api.github.com", "raw.githubusercontent.com"]
  ```

**Agent 代码（简化示例）**：
```python
# agent.py
tools = [
    GitHubReadTool(),
    HttpGetTool(),
    BashExecuteTool(),  # ❌ 未声明！
]

def agent_function(query: str):
    # 大部分情况下遵守 policy
    result = tools["http_get"](f"https://api.github.com/repos/{query}")
    
    # 但隐含的逻辑可能调用未声明的工具
    if "install" in query:
        os.system("pip install ...")  # ❌ Bash 工具调用
    return result
```

**Validator 执行过程**：

1. **Static Scan 阶段**：
   ```json
   {
     "tool_sbom": [
       {"name": "GitHubReadTool", "source": "agent-defined", "params": ["repo", "path"]},
       {"name": "HttpGetTool", "source": "agent-defined", "params": ["url"]},
       {"name": "BashExecuteTool", "source": "framework-builtin", "params": ["command"]}
     ]
   }
   ```
   ⚠️ 检测到 BashExecuteTool，不在 Declared Policy 中

2. **Probe Generation 阶段**：
   ```
   Policy 声明：deny bash / ssh
   自动生成 probe：
   - 调用 bash_tool("pip install requests")
   - 调用 bash_tool("ssh-keygen")
   - 调用 http_get("https://forbidden.com")
   ```

3. **Dynamic Execution 阶段**：
   ```
   运行 agent 与 probes，记录 execution trace：
   [
     {"tool": "http_get", "args": ["https://api.github.com/..."], "result": "success"},
     {"tool": "bash", "args": ["pip install requests"], "result": "execution_detected"},
     {"tool": "bash", "args": ["ssh-keygen"], "result": "execution_detected"},
     {"tool": "http_get", "args": ["https://api.internal.company.com"], "result": "403_forbidden"}
   ]
   ```

4. **Conformance Check 阶段**：
   ```json
   {
     "declared_tools": ["read_file", "http_get"],
     "actual_tools_used": ["read_file", "http_get", "bash"],
     "diff": {
       "undeclared": ["bash"],
       "violations": [
         {"rule": "denied_tools", "tool": "bash", "count": 2, "severity": "CRITICAL"}
       ]
     }
   }
   ```

5. **Policy Validation 阶段**：
   ```
   Policy Rule: IF undeclared_tool OR critical_violation THEN FAIL
   Result: ❌ FAIL
   
   Reason: Tool 'bash' is not in declared_tools and is in denied_tools list
   Violation Count: 2 calls detected
   
   Action: ⛔ Block Deployment
   
   Recommended Fix:
   1. Remove BashExecuteTool from agent code, OR
   2. Add 'bash' to declared_tools & update policy justification
   ```

**UI 展示（Markdown Report）**：
```markdown
# Agent Conformance Report
**Status**: ❌ FAIL  
**Date**: 2026-09-12  
**Agent**: github-assistant  
**Policy**: github-readonly  

## Summary
- Tool SBOM: 3 tools discovered
- Declared: 2 tools
- Violations: 1 critical

## Tool Analysis
✅ GitHubReadTool (Declared)
✅ HttpGetTool (Declared)
❌ BashExecuteTool (NOT DECLARED, IN DENIED LIST)

## Execution Trace
| Tool | Arguments | Count | Policy Status |
|------|-----------|-------|---------------|
| http_get | api.github.com/* | 5 | ✅ PASS |
| bash | pip install requests | 1 | ❌ FAIL |
| bash | ssh-keygen | 1 | ❌ FAIL |

## Violations
- **Critical**: Undeclared tool 'bash' invoked 2 times
- **Critical**: Tool 'bash' is in denied_tools list

## Deployment Decision
🚫 Deployment blocked due to policy violations

## Developer Actions
Choose one:
1. **Fix Code**: Remove bash calls, re-run validation
2. **Extend Policy**: Justify why bash is needed, update policy, re-run validation
```

**Demo 价值**：
- ✅ 可重现：提供完整代码 + Policy 配置
- ✅ 真实感：基于实际安全事件
- ✅ 可验证：清晰的输入 → 过程 → 输出
- ✅ 传播性：可轻松用于论文、演讲、社区讨论

---

## 8. 待调研问题清单

### 技术调研

1. **Framework Coverage**
   - [ ] LangGraph 中工具定义和注册的完整机制是什么？
   - [ ] AgentScope 的工具接口规范是什么？
   - [ ] 如何通过 AST 解析统一提取不同框架的工具定义？
   - [ ] 是否存在框架通用的工具注册中心或元数据库？

2. **Parameter Tracking Instrumentation**
   - [ ] Python 中如何实现无损的 instrumentation wrapper（性能开销 < 5%）？
   - [ ] 是否需要使用 bytecode instrumentation (如 ctypes hook) 还是高层 wrapper 足够？
   - [ ] 对异步工具调用的追踪是否可行？

3. **Runtime 内置能力的发现**
   - [ ] 框架隐含支持的系统调用能力（代码执行、文件访问等）如何安全地发现？
   - [ ] 是否需要在沙箱环境中"试探"还是从框架源码解析？
   - [ ] 能否构建框架能力的预定义库？

4. **Execution Sandbox**
   - [ ] 采用何种隔离方案（Docker / systemd-nspawn / 进程沙箱）？
   - [ ] 沙箱内如何模拟被 agent 调用的外部资源（GitHub API、数据库等）？
   - [ ] 超时控制、资源限制的设置是什么？

### 业界现状调研

5. **竞品和相关工作**
   - [ ] 是否存在已有的 Agent SBOM 或类似概念的工作？
   - [ ] MLflow、Hugging Face Model Card 等对"模型能力声明"的做法有哪些启示？
   - [ ] 安全审计工具链（如 Snyk、Trivy）中的 policy engine 设计可否参考？

6. **企业 Agent 部署现状**
   - [ ] 主流企业如何部署 Agent（容器化? Kubernetes? Serverless）？
   - [ ] 现有 Agent 框架是否支持能力声明或权限控制机制？
   - [ ] 企业 DevSecOps 流程中对 Agent 的安全卡点需求是什么？

7. **法规与合规**
   - [ ] GDPR / SOX / ISO27001 中对 AI Agent 能力审计的具体要求是什么？
   - [ ] 该 Validator 的输出是否可直接用于合规检查清单？
   - [ ] 是否需要支持审计追踪日志格式标准（如 CAIQ）？

### 产品决策调研

8. **实现优先级的权衡**
   - [ ] 第一个版本是支持一个框架完整，还是多个框架不完整？
   - [ ] 数据驱动决策：用户最关心的框架排名是什么？

9. **Policy Declaration 的学习曲线**
   - [ ] 企业开发者能否快速理解和编写 declared policy？
   - [ ] 是否需要提供 policy 模板库？
   - [ ] IDE 智能提示集成的优先级？

10. **Diff Report 的可视化设计**
    - [ ] 对技术和非技术用户来说，什么样的 diff 展示最有效？
    - [ ] 是否需要风险评分、补救建议等额外信息？

### 用户研究

11. **用户访谈**
    - [ ] 目标企业（AI 安全团队、DevSecOps）对该工具的认知需求是什么？
    - [ ] False Positive 率的可接纳阈值是多少？
    - [ ] 部署到 CICD 前需要哪些预热或试用期？

---

## 9. 后续建议的下一步

### 立即行动（下周）

1. **调研与范围明确**
   - 与 1-2 个企业 AI 团队进行 20 分钟 user interview，验证 policy conformance validator 的真实需求
   - 对比 LangGraph vs AgentScope 的工具机制，选定第一个支持框架
   - 列举该框架中前 10 个最常用工具，评估解析复杂度

2. **原型设计**
   - 绘制详细的系统架构图（输入 → 处理 → 输出）
   - 明确 4 个核心模块的接口定义（Scanner / ProbeGen / Executor / Validator）
   - 梳理 demo 场景的完整代码框架（Python 示例）

3. **技术可行性验证**
   - PoC 1：能否通过 AST 解析从 LangGraph Agent 代码中提取工具列表？（预期 1 天）
   - PoC 2：能否实现参数级追踪的 instrumentation wrapper？（预期 1-2 天）
   - PoC 3：Policy YAML 的 schema 设计与验证？（预期半天）

### Sprint 执行建议（2-3 周）

4. **分阶段交付**
   - **Week 1-2**: 完成 Must Have 中的"Framework Scanner + Tool SBOM" 与 "Policy Declaration"
   - **Week 2-3**: 完成 "Probe Generator + Executor" 与基础 "Conformance Check"
   - **Week 3**: 集成 UI、完善 Demo、产出 Report

5. **测试与验证**
   - 为每个模块编写单元测试（目标：>80% 覆盖率）
   - 用 5-10 个真实 Agent 示例进行集成测试
   - 获取用户反馈并迭代

6. **文档与演讲材料**
   - 技术文档：架构、API、使用指南
   - 安全白皮书：为什么这个问题重要？方案如何解决？
   - 演讲 Slide：控制在 15-20 分钟能讲完

### 冲刺后的优化（Could 范围推进）

7. **多框架扩展**
   - 基于第一版的框架无关抽象层，快速适配第二个框架
   - 建立框架插件生态（社区贡献）

8. **高级功能补充**
   - Coverage scoring 与热力图
   - Adversarial Agent 深度审计模式
   - CICD 集成（GitHub Actions 官方模板）

9. **生态合作**
   - 与 LangGraph、AgentScope 官方沟通，争取原生集成
   - 向 OWASP / CIS 等安全组织投稿相关指南
   - 开源社区反馈循环

---

## 总结：项目精髓

这个项目的关键创新在于**从"固定安全基线"思维转向"相对于声明的符合性验证"思维**。不是问"Agent 是否安全"（主观），而是问"Agent 是否守住了自己承诺的边界"（客观可验证）。

结合**四层工具发现**（SBOM）与**参数级动态验证**（Probe），产出**企业可信的部署卡点**。

这种"声明 + 验证 + 决策"的流程，完全映射了传统 DevSecOps（SAST + DAST + Policy），降低了企业采用阻力，同时为 AI Agent 的可审计性提供了新的基础设施。
