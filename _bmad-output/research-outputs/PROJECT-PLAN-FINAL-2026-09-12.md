# Agent Policy Conformance Validator
## 完整项目规划书

**项目名称**：Agent Policy Conformance Validator（APCV）  
**项目周期**：3 周 MVP + 后续迭代  
**交付日期**：2026 年 9 月 30 日  
**研究方式**：Deep Recon（多源并行调研）  
**最后更新**：2026-09-12

---

## 目录

1. [执行摘要](#执行摘要)
2. [产品定位](#产品定位)
3. [市场和用户](#市场和用户)
4. [产品形态](#产品形态)
5. [技术架构](#技术架构)
6. [MVP 需求和范围](#mvp-需求和范围)
7. [Sprint 计划](#sprint-计划)
8. [交付物和验收标准](#交付物和验收标准)
9. [风险和缓解](#风险和缓解)

---

## 执行摘要

### 项目概述

**Agent Policy Conformance Validator** 是一个开源工具，用于**验证 AI Agent 的实际能力是否符合企业声明的政策**。

通过自动化的 Probe 测试和参数追踪，它回答关键问题：
- ✅ Agent 真的守住了权限边界吗？
- ✅ 有没有通过某种方式绕过限制？
- ✅ 审计日志是否完整、可信？
- ✅ 是否满足 EU AI Act、GDPR 等法规要求？

### 市场现状

**65% 的企业在 2026 年遭遇过 AI Agent 的安全事件**，包括：
- 越权访问
- 数据泄露
- 能力漂移

**现有工具的不足**：
- Microsoft Agent Governance Toolkit：企业级平台，但缺乏工具级的"相对验证"
- Snyk/Trivy：通用安全工具，无法处理 Agent 的动态能力
- 市场空缺：**没有专门的"Agent 符合性验证工具"**

### 核心创新点

| 创新点 | 描述 | 竞争优势 |
|------|------|---------|
| **Policy-Relative Probe** | Probe 根据声明的政策动态生成，而非固定清单 | 减少误报、提高精准度 |
| **工具发现（4 层）** | 静态 AST + 运行时拦截，发现所有工具 | 发现隐藏能力、框架通用 |
| **框架通用性** | MVP 用 LangGraph，后续自动适配其他框架 | 一套工具支持所有框架 |
| **Capability Gap Score** | 量化 Agent 的符合度（0-100） | 可视化、易于决策 |

### 项目成果

**MVP（3 周）**：
- ✅ CLI + Web UI 产品
- ✅ LangGraph 支持
- ✅ 20-30 个 Probe 规则库
- ✅ 完整审计报告
- ✅ 符合性证明

**后续**：
- ✅ 其他框架适配（AgentScope、AutoGen 等）
- ✅ LLM 辅助 Probe 生成
- ✅ Runtime Monitoring 模式

---

## 产品定位

### 问题陈述

```
现状：
  企业部署了 AI Agent
  应用了权限限制和隔离策略
  相信"Agent 被限制了"

但问题是：
  ❓ 这些限制是否真的有效？
  ❓ 有没有漏洞或绕过方式？
  ❓ 如何证明符合法规要求？

无法回答这些问题 → 无法自信地部署到生产
```

### 解决方案

```
Agent Policy Conformance Validator 提供：

1. 自动化验证
   通过 Probe 尝试突破政策边界
   记录每一步操作（参数追踪）
   
2. 可信的合规证明
   生成审计报告
   证明 GDPR/SOX/ISO27001 要求
   
3. 漏洞发现
   如果 Probe 成功绕过限制
   立即发现并报告

结果：企业可以自信地部署 Agent
```

### 用户价值主张

| 用户角色 | 主要需求 | 本产品的价值 |
|---------|---------|-----------|
| **DevOps** | 确保政策真的被执行 | 自动验证 + CI/CD 集成 |
| **安全团队** | 审计和威胁检测 | 执行追踪日志 + 漏洞报告 |
| **合规官** | 证明法规符合性 | 生成审计证明文件 |
| **产品经理** | 理解 Agent 能力范围 | 可视化仪表板 + 政策管理 |

---

## 市场和用户

### 市场规模和增长

```
AI Agent 市场：
  2025 年规模：$1.35 B
  2031 年预测：$4.57 B
  CAGR：22.16%

关键驱动：
  ✅ 企业部署加速（65% 已部署或测试）
  ✅ 法规压力（EU AI Act 2026 生效）
  ✅ 安全事件驱动（65% 企业遭遇事件）

市场成熟度：
  ✓ 企业已有真实需求
  ✓ 预算已获批（安全类工具）
  ✓ 采购决策已形成
```

### 用户分层和优先级

#### 第一优先级：DevOps 和平台团队

```
特征：
  - 最关心"能力边界执行"
  - 有编程能力
  - 集成能力强
  - 决策速度快

需求：
  - CLI 工具（与 CI/CD 集成）
  - 可脚本化（支持自动化验证）
  - 快速反馈（<1 分钟验证）

采购周期：短（1-2 周）
粘性：高（深度集成）
```

#### 第二优先级：安全团队

```
特征：
  - 需要可视化报告
  - 关心威胁检测
  - 需要审计追踪
  - 熟悉安全工具

需求：
  - Web UI（展示和决策）
  - 实时监控能力
  - 与 SIEM 集成
  - 详细的执行日志

采购周期：中等（2-4 周）
粘性：高（安全运维整合）
```

#### 第三优先级：合规和管理

```
特征：
  - 需要证明性文件
  - 关心监管符合性
  - 不直接使用工具
  - 最终决策者

需求：
  - 合规证明报告
  - 易于理解的结果
  - 审计日志
  - SLA 和 KPI

采购周期：长（4-8 周）
粘性：中等（合规证明一次性需求）
```

### 核心用户需求优先级

```
1️⃣ 执行层强制验证（最关键）
   企业需要证明"权限限制真的被执行了"
   而不仅仅是"代码中写了限制"

2️⃣ 审计和合规证明
   需要生成可信的报告来证明符合法规
   GDPR、SOX、ISO27001 要求
   
3️⃣ 实时监控和告警
   发现异常行为（能力漂移、越权尝试）
   
4️⃣ 可视化决策支持
   帮助管理层理解 Agent 能力和风险
```

### 竞争格局

#### 直接竞争者（专门工具）

```
Microsoft Agent Governance Toolkit
  优势：全 stack 企业级解决方案
  劣势：不专注于验证，配置复杂
  
Obsidian Security（通用 SaaS 安全）
  优势：已有客户群
  劣势：通用平台，无 Agent 专项
  
Zenity（通用 SaaS 安全）
  优势：已有客户群
  劣势：关注 prompt 层，不是执行层
```

#### 间接竞争者（通用工具）

```
Snyk、Trivy（容器安全）
  定位：基础设施合规
  不足：无法处理 Agent 动态能力
  
OPA/Rego（策略引擎）
  定位：通用策略语言
  不足：需要自定义集成

SIEM（Splunk、Sentinel）
  定位：通用审计和监控
  不足：无 Agent 特定的验证逻辑
```

#### 市场机会

```
✅ 高优先级市场空缺
   没有专门的"Agent 符合性验证工具"
   
✅ 强烈的市场需求信号
   65% 企业遭遇事件 = 强大的购买动机
   
✅ 法规推动
   EU AI Act 2026 生效 = 法律义务
   
✅ 框架中立
   支持多个框架 = 广泛的适用性

建议策略：
  1. 快速推出 MVP（3 周）
  2. 聚焦 DevOps 和安全团队
  3. 优先解决"执行层验证"问题
  4. 通过开源建立信任和用户基础
```

---

## 产品形态

### 双模式设计：CLI + Web UI

#### CLI 模式

**目的**：与 DevOps 和 CI/CD 流程集成

```bash
# 基础用法
apcv validate \
  --agent langgraph:./my_agent.py \
  --policy ./policy.yaml \
  --output report.json

# CI/CD 集成
apcv validate \
  --agent "$AGENT_PATH" \
  --policy "$POLICY_PATH" \
  --fail-on compliance_score < 95 \
  --format sarif > results.sarif

# 输出格式
{
  "verdict": "PASS" | "FAIL" | "WARNING",
  "compliance_score": 95,
  "probes_passed": 19,
  "probes_failed": 1,
  "failures": [
    {
      "probe_id": "fs_access_boundary",
      "severity": "critical",
      "description": "Agent 能访问 /etc/passwd"
    }
  ],
  "execution_trace": [...],
  "recommendations": [...]
}
```

**特性**：
- ✅ 快速（<5 分钟验证）
- ✅ 可脚本化（支持 shell 脚本、CI/CD 工具）
- ✅ 标准输出格式（JSON、SARIF、纯文本）
- ✅ 能与 GitHub Actions、GitLab CI 集成

#### Web UI 模式

**目的**：展示、决策、政策管理

```
Dashboard 首页：
  ├─ Agent 列表
  │  └─ 每个 Agent 的符合度卡片
  │     ├─ Compliance Score (0-100)
  │     ├─ 最后验证时间
  │     ├─ 趋势图表
  │     └─ 快速操作（重新验证、查看报告）
  │
  ├─ 政策管理
  │  ├─ 创建/编辑政策（YAML 编辑器）
  │  ├─ 应用于多个 Agent
  │  └─ 版本历史
  │
  ├─ 执行日志
  │  ├─ 所有工具调用的完整追踪
  │  ├─ 参数和返回值
  │  ├─ 时间线视图
  │  └─ 搜索/过滤能力
  │
  └─ 报告中心
     ├─ 生成合规证明文件
     ├─ 下载 PDF/JSON
     └─ 分享给利益相关方
```

**特性**：
- ✅ 可视化展示（仪表板、图表、时间线）
- ✅ 政策管理（无需编辑文件）
- ✅ 审计查询（搜索执行日志）
- ✅ 报告生成（PDF、合规证明）

### 工作流集成

```
DevOps 工作流：
  代码提交 → Git Push
    ↓
  CI/CD Pipeline 触发
    ↓
  apcv validate --agent ... --policy ...
    ↓
  ✅ PASS → 部署
  ❌ FAIL → 阻止部署 + 通知

安全团队工作流：
  打开 Web UI
    ↓
  查看所有 Agent 的符合度
    ↓
  点击某个 Agent
    ↓
  查看执行日志和失败的 Probe
    ↓
  生成合规报告
    ↓
  与法务/审计分享
```

---

## 技术架构

### 整体架构

```
┌─────────────────────────────────────────────┐
│ 应用层                                       │
├─────────────────────────────────────────────┤
│ CLI 工具          Web UI (React/Vue)        │
│ apcv command      Dashboard + Editor        │
│ JSON/SARIF 输出   Policy Manager            │
└─────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│ 核心引擎层                                   │
├─────────────────────────────────────────────┤
│ 工具发现器    Probe 生成器    验证引擎      │
│ (AST+运行时)  (规则库)       (SBOM diff)   │
│              参数追踪器      策略评估      │
│              (wrapt)         (OPA/Rego)    │
└─────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│ 适配层（框架无关）                          │
├─────────────────────────────────────────────┤
│ 统一接口：                                  │
│  ToolRegistry         ToolInterceptor      │
│  ParameterTracer      IsolatedExecutor     │
│                                            │
│ 框架适配器：                               │
│  LangGraphAdapter    (MVP)                 │
│  AgentScopeAdapter   (Sprint 2)            │
│  AutoGenAdapter      (Sprint 3)            │
└─────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│ 框架层                                       │
├─────────────────────────────────────────────┤
│ LangGraph | AgentScope | AutoGen | ...      │
└─────────────────────────────────────────────┘
```

### 核心模块

#### 1. 工具发现器 (Tool Discovery)

```python
class ToolDiscovery:
    
    def discover_static(self, agent_code_path):
        """从源代码提取工具（AST）"""
        # 1. 解析 Python AST
        # 2. 找 @tool 装饰器
        # 3. 提取参数、返回类型、约束
        return static_sbom
    
    def discover_runtime(self, agent_instance):
        """运行时拦截工具调用"""
        # 1. 装置 wrapt wrapper
        # 2. 执行 Agent
        # 3. 记录每个工具调用
        return runtime_sbom
    
    def compare(self, static_sbom, runtime_sbom):
        """对比发现差异"""
        # 1. 代码中有但运行时没有 → 未被使用
        # 2. 运行时有但代码中没有 → 隐藏能力（风险！）
        # 3. 约束不匹配 → 配置问题
        return differences
```

#### 2. Probe 生成器 (Probe Generator)

```python
class ProbeGenerator:
    
    def __init__(self):
        self.probe_library = [
            # 文件系统越权
            {"id": "fs_1", "category": "filesystem", ...},
            {"id": "fs_2", "category": "filesystem", ...},
            # 工具调用越权
            {"id": "tool_1", "category": "tool_invocation", ...},
            # 权限提升
            {"id": "priv_1", "category": "privilege_escalation", ...},
            # ... 共 20-30 个
        ]
    
    def generate_for_policy(self, policy):
        """根据政策生成针对性的 Probe"""
        # Policy-Relative 生成
        probes = []
        
        # 文件访问限制
        if policy.file_access:
            probes += self._gen_filesystem_probes(policy.file_access)
        
        # 工具限制
        if policy.allowed_tools:
            probes += self._gen_tool_probes(policy.allowed_tools)
        
        # 权限限制
        if policy.privilege_limits:
            probes += self._gen_privilege_probes(policy.privilege_limits)
        
        return probes
```

#### 3. 隔离执行器 (Isolated Executor)

```python
class IsolatedExecutor:
    
    def __init__(self, image="apcv-probe:latest"):
        self.docker_client = docker.from_env()
        self.image = image
    
    def execute_probe(self, probe):
        """在 Docker 容器中安全执行 Probe"""
        container = self.docker_client.containers.run(
            self.image,
            command=["python", "probe_runner.py"],
            environment={"PROBE_SPEC": json.dumps(probe)},
            cap_drop=["ALL"],
            read_only=True,
            tmpfs={"/tmp": "size=512m"},
            remove=True,
            timeout=30
        )
        
        return self._parse_result(container.logs())
    
    def execute_parallel(self, probes, workers=4):
        """并行执行多个 Probe"""
        with ThreadPoolExecutor(max_workers=workers) as executor:
            results = list(executor.map(self.execute_probe, probes))
        return results
```

#### 4. 参数追踪 (Parameter Tracer)

```python
import wrapt
import json

@wrapt.decorator
def trace_parameters(wrapped, instance, args, kwargs):
    """
    自动追踪所有参数和返回值
    开销：<1%
    """
    trace_record = {
        "timestamp": datetime.utcnow().isoformat(),
        "function": wrapped.__name__,
        "params": {
            "args": [str(arg)[:500] for arg in args],
            "kwargs": {k: str(v)[:500] for k, v in kwargs.items()}
        }
    }
    
    try:
        result = wrapped(*args, **kwargs)
        trace_record["result"] = str(result)[:500]
        trace_record["status"] = "success"
        return result
    except Exception as e:
        trace_record["error"] = str(e)
        trace_record["status"] = "error"
        raise
    finally:
        # 发送到追踪系统
        TRACE_LOG.append(trace_record)
```

#### 5. 符合性检查 (Conformance Checker)

```python
class ConformanceChecker:
    
    def check(self, static_sbom, runtime_sbom, policy, execution_trace):
        """
        综合检查符合性
        """
        violations = []
        
        # 1. 工具符合性
        for tool_called in execution_trace.tools:
            if tool_called not in policy.allowed_tools:
                violations.append({
                    "type": "tool_violation",
                    "tool": tool_called,
                    "severity": "critical"
                })
        
        # 2. 参数符合性
        for call in execution_trace.calls:
            if not self._check_params(call, policy):
                violations.append({
                    "type": "parameter_violation",
                    "call": call,
                    "severity": "high"
                })
        
        # 3. 隐藏能力检测
        hidden_tools = set(runtime_sbom.keys()) - set(static_sbom.keys())
        if hidden_tools:
            violations.append({
                "type": "hidden_capability",
                "tools": hidden_tools,
                "severity": "critical"
            })
        
        # 计算符合度分数
        compliance_score = max(0, 100 - len(violations) * 10)
        
        return {
            "verdict": "PASS" if compliance_score >= 95 else "FAIL",
            "compliance_score": compliance_score,
            "violations": violations
        }
```

### 技术栈选择

| 组件 | 技术选择 | 理由 |
|-----|---------|-----|
| 参数追踪 | wrapt | <1% 开销，C 扩展，成熟 |
| 隔离执行 | Docker | 标准化、可靠、跨平台 |
| 策略引擎 | OPA/Rego | 业界标准、表达力强 |
| 工具发现（AST） | Python AST + tree-sitter | 支持多种 Python 版本 |
| CLI | Click / Typer | 易用、类型提示 |
| Web UI | React/FastAPI | 现代化、性能好 |
| 数据库 | SQLite (MVP) / PostgreSQL (生产) | 简单易部署 |

---

## MVP 需求和范围

### 功能需求

#### F1. 工具发现（静态）

```
输入：Agent Python 代码路径
处理：
  1. AST 解析找 @tool 装饰器
  2. 提取参数、返回类型
  3. 查找约束注解
输出：工具列表 (JSON)

验收标准：
  ✅ 发现 LangGraph 所有工具
  ✅ 准确率 > 95%
  ✅ 处理时间 < 10 秒
```

#### F2. Policy DSL 定义

```
输入：Policy YAML 文件
格式：
  tools:
    allowed: [search, summarize]
    denied: [delete, execute]
  filesystem:
    allowed_paths: [/data]
  network:
    enabled: false
  
输出：解析后的政策对象

验收标准：
  ✅ 支持所有必要的约束类型
  ✅ 生成错误消息友好
  ✅ 支持注释和文档
```

#### F3. Probe 生成和执行

```
输入：政策对象
处理：
  1. 从规则库选择相关 Probe
  2. 在 Docker 容器中执行
  3. 记录执行结果
输出：执行结果列表

验收标准：
  ✅ 生成 20-30 个 Probe
  ✅ 全部执行成功或失败（记录原因）
  ✅ 总时间 < 2 分钟
```

#### F4. 参数追踪

```
输入：正在执行的 Agent
处理：
  1. 装置 wrapt wrapper
  2. 记录所有工具调用
  3. 收集参数和返回值
输出：执行追踪日志

验收标准：
  ✅ 记录 100% 的工具调用
  ✅ 开销 < 1%
  ✅ 能处理异步函数
```

#### F5. 符合性检查

```
输入：执行追踪 + 政策
处理：
  1. 对比工具调用 vs 允许列表
  2. 检查参数是否在范围内
  3. 检测隐藏能力
输出：违规列表 + 符合度分数

验收标准：
  ✅ 符合度分数 (0-100)
  ✅ 详细的违规报告
  ✅ 可操作的建议
```

#### F6. CLI 工具

```
命令：apcv validate

选项：
  --agent <path>        Agent 代码或配置
  --policy <path>       Policy YAML 文件
  --output <format>     输出格式 (json/sarif/html)
  --fail-on <score>     符合度不达标时失败

输出：
  - JSON 报告
  - 命令行反馈
  - Exit code (0=pass, 1=fail)

验收标准：
  ✅ 支持标准选项
  ✅ 与 CI/CD 集成
  ✅ 帮助文本清晰
```

#### F7. Web UI - 基础版

```
页面 1：Dashboard
  - Agent 列表和符合度
  - 快速操作（重新验证、查看报告）
  
页面 2：Agent 详情
  - 执行时间线
  - 失败的 Probe 详情
  - 下载报告

页面 3：Policy 编辑
  - YAML 编辑器
  - 实时验证
  - 应用到 Agent

验收标准：
  ✅ 美观、易用
  ✅ 响应时间 < 1 秒
  ✅ 支持基本的 CRUD 操作
```

#### F8. 报告生成

```
格式：
  - JSON（机读）
  - PDF（打印、分享）
  - HTML（查看）
  
内容：
  - 执行摘要
  - 符合度分数
  - 违规清单
  - 执行追踪
  - 建议和补救
  - 签署和证明

验收标准：
  ✅ 包含所有必要信息
  ✅ 可用于合规证明
  ✅ 专业外观
```

### 非功能需求

| 需求 | 目标 | 验收标准 |
|-----|------|---------|
| **性能** | 完整验证 < 2 分钟 | 包括工具发现、Probe 执行、报告 |
| **可靠性** | 可用性 99% | 容错处理，清晰的错误消息 |
| **可扩展性** | 支持 100+ 工具的 Agent | 性能不显著下降 |
| **安全性** | 隔离执行 100% | Probe 不能污染真实系统 |
| **易用性** | 新用户 < 30 分钟上手 | 文档、示例、向导 |
| **集成性** | 与主流 CI/CD 兼容 | GitHub Actions、GitLab CI 等 |

---

## Sprint 计划

### Sprint 1（第 1-2 周）：核心引擎

#### Week 1：基础设施和工具发现

**Day 1-2：项目框架搭建**
```
任务：
  □ 代码库初始化
  □ 项目结构设计
  □ 依赖管理 (requirements.txt)
  □ 测试框架 (pytest)
  □ CI/CD 流程 (GitHub Actions)
  
交付：
  - ✅ 可运行的开发环境
  - ✅ 初始化测试通过
```

**Day 3-5：工具发现器（静态）**
```
任务：
  □ AST 解析器实现
  □ @tool 装饰器识别
  □ 参数提取和签名生成
  □ 约束注解解析
  □ 单元测试 (coverage > 80%)
  
交付：
  - ✅ ToolDiscovery.discover_static()
  - ✅ 单元测试通过
  - ✅ 处理 LangGraph 工具
```

#### Week 2：Policy DSL 和 Probe 生成

**Day 6-7：Policy DSL**
```
任务：
  □ YAML Schema 定义
  □ Policy 验证器
  □ 错误处理和报告
  □ 文档和示例
  □ 集成测试
  
交付：
  - ✅ Policy 类实现
  - ✅ Schema 验证通过
  - ✅ 示例 policy 文件
```

**Day 8-10：Probe 生成器 + 规则库**
```
任务：
  □ Probe 规则库编写（20-30 个）
  □ Policy-Relative 生成逻辑
  □ Probe 类定义
  □ 集成测试
  
交付：
  - ✅ ProbeGenerator 实现
  - ✅ 20-30 个 Probe 规则
  - ✅ 能根据 Policy 生成针对性 Probe
```

### Sprint 2（第 3 周）：执行和验证

#### Week 3：隔离执行 + 符合性检查 + CLI

**Day 11-12：隔离执行和参数追踪**
```
任务：
  □ Docker 镜像构建
  □ IsolatedExecutor 实现
  □ wrapt 参数追踪集成
  □ 执行日志收集
  □ 错误处理
  
交付：
  - ✅ Docker 镜像
  - ✅ IsolatedExecutor 可运行
  - ✅ 参数追踪工作正常
```

**Day 13-14：符合性检查 + CLI**
```
任务：
  □ ConformanceChecker 实现
  □ 符合度评分算法
  □ CLI 命令行界面
  □ 输出格式（JSON、SARIF）
  □ 端到端测试
  
交付：
  - ✅ apcv validate 命令可用
  - ✅ 生成 JSON 报告
  - ✅ CLI 与 CI/CD 集成成功
```

**Day 15：集成测试 + Demo 准备**
```
任务：
  □ 完整流程端到端测试
  □ Bug 修复
  □ 性能优化
  □ 文档编写
  □ Demo 脚本准备
  
交付：
  - ✅ MVP 完整功能验证
  - ✅ 性能达标（< 2 分钟）
  - ✅ 可演示的 Demo
```

### 后续 Sprint（Week 4+）

#### Sprint 2（Week 4-5）：Web UI + 其他框架

```
Week 4：
  □ Web UI 框架搭建 (React/FastAPI)
  □ Dashboard 实现
  □ Agent 详情页
  □ 基本样式

Week 5：
  □ Policy 编辑器
  □ 报告中心
  □ AgentScope 适配器
  □ 文档完善
```

#### Sprint 3（Week 6+）：多框架 + 高级特性

```
Week 6：
  □ AutoGen 适配器
  □ 其他框架支持
  □ 性能优化
  
Week 7+：
  □ LLM 辅助 Probe 生成
  □ Runtime Monitoring 模式
  □ 高级分析和威胁检测
```

---

## 交付物和验收标准

### MVP 交付物清单

| 交付物 | 描述 | 验收标准 |
|------|------|---------|
| **代码库** | GitHub 公开 | ✅ Apache 2.0 许可 |
| **CLI 工具** | apcv 命令行工具 | ✅ 支持所有基础操作 |
| **Probe 规则库** | 20-30 个验证规则 | ✅ 覆盖关键场景 |
| **文档** | 使用文档 + 开发指南 | ✅ 新用户能独立使用 |
| **示例** | LangGraph Agent 示例 | ✅ 完整的 YAML policy 示例 |
| **测试** | 单元 + 集成测试 | ✅ 覆盖率 > 80% |
| **Docker 镜像** | apcv-probe 镜像 | ✅ 可从 DockerHub 拉取 |
| **基础 Web UI** | Dashboard + Policy 编辑器 | ✅ 美观、可用 |
| **报告系统** | JSON + PDF 生成 | ✅ 包含合规信息 |
| **研究论文** | 项目总结报告 | ✅ 符合 Apart Research 要求 |

### 验收测试

#### 功能测试
```
□ 工具发现准确率 > 95%
□ 所有 20-30 个 Probe 能生成和执行
□ 参数追踪记录 100% 的工具调用
□ 符合性检查能识别所有违规
□ CLI 命令正确执行
□ 报告格式正确和完整
```

#### 性能测试
```
□ 完整验证 < 2 分钟
□ 参数追踪开销 < 1%
□ Web UI 响应时间 < 1 秒
□ Docker 启动 < 5 秒
□ 支持 100+ 工具的 Agent
```

#### 集成测试
```
□ LangGraph 框架完全支持
□ GitHub Actions CI/CD 集成
□ Docker 执行隔离验证
□ 并行 Probe 执行正确
□ 错误处理和恢复
```

#### 安全性验证
```
□ Docker 容器完全隔离
□ 不同 Probe 间无交叉污染
□ 参数不泄露敏感信息
□ 执行日志不包含密钥
```

---

## 风险和缓解

### 技术风险

| 风险 | 概率 | 影响 | 缓解策略 |
|-----|------|------|---------|
| **LangGraph 工具发现** | 中 | 高 | 提前 PoC，准备备选方案 |
| **Docker 隔离有漏洞** | 低 | 极高 | 使用 seccomp + AppArmor 加固 |
| **Probe 生成不充分** | 中 | 中 | 建立反馈循环，持续改进规则库 |
| **性能达不到目标** | 低 | 中 | 优化 Docker 启动，并行执行 |
| **框架差异导致适配困难** | 中 | 低 | 设计好抽象接口，提前研究 |

### 项目风险

| 风险 | 概率 | 影响 | 缓解策略 |
|-----|------|------|---------|
| **3 周太紧张** | 中 | 中 | 准备降级方案，后续迭代补充 |
| **团队技能匹配** | 低 | 中 | 提前培训，知识分享 |
| **需求变更** | 中 | 低 | 冻结 MVP 范围，变更入下个 Sprint |
| **文档不足** | 低 | 低 | 代码即文档，加注释，提前写 README |

### 缓解措施

```
持续风险管理：
  ✅ 每日站会识别阻挡
  ✅ 周末风险评审
  ✅ 提前准备 Plan B
  ✅ 及时沟通升级问题
```

---

## 成功指标 (KPI)

### 功能指标
```
✅ MVP 完整交付（所有 8 项功能）
✅ 单元测试覆盖率 > 80%
✅ 集成测试全部通过
✅ 性能指标达标
  - 完整验证 < 2 分钟
  - 参数追踪开销 < 1%
  - Web UI 响应 < 1 秒
```

### 产品指标
```
✅ LangGraph 支持完整
✅ CLI + Web UI 都可用
✅ 文档清晰完整
✅ 能成功运行 End-to-End Demo
```

### 研究指标
```
✅ 论文符合 Apart Research 要求
✅ 创新点明确（Policy-Relative Probe）
✅ 市场需求得到验证
✅ 后续商业化路径清晰
```

---

## 附录：产品决策总结

### 关键决策

```
1. 产品形态：CLI + Web UI
   理由：覆盖 DevOps（CLI）和安全团队（UI）两个关键用户

2. 框架优先级：LangGraph MVP，后续其他
   理由：LangGraph 采用度广，框架通用架构可在 Sprint 2 添加

3. Probe 库：硬编码规则 + OWASP 映射
   理由：MVP 快速推出，后续迭代 LLM 辅助

4. 隔离方案：Docker
   理由：标准化、可靠、跨平台

5. 用户优先级：DevOps > 安全团队 > 合规 > 管理层
   理由：DevOps 采购快速，粘性强

6. 时间表：3 周 MVP
   理由：市场需求紧迫，快速迭代获得反馈
```

### 未来方向

```
Sprint 2+：
  ✅ 多框架支持（AgentScope、AutoGen）
  ✅ LLM 辅助 Probe 生成
  ✅ Runtime Monitoring 和告警
  ✅ 高级威胁分析
  ✅ 商业化（SaaS 或许可）

长期：
  ✅ 行业标准化（与 OWASP 合作）
  ✅ 生态集成（与 IDEs、CI/CD 工具深度集成）
  ✅ 全球部署
```

---

**文档完成时间**：2026-09-12  
**下一次更新**：Sprint 1 完成后（2026-09-26）  
**文档负责人**：Product/Engineering Lead
