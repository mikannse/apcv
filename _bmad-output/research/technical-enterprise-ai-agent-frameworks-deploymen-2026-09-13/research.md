---
title: 'technical research: 企业主流AI应用开发框架与部署方式'
type: 'technical'
topic: '企业主流AI应用开发框架与部署方式'
decision: '确定APCV模拟测试环境应包含哪些真实开源组件与攻击场景'
source: 'native-run (deep, 4 assistants, 2026-09-13)'
status: final
preset: 'deep'
validation: 'normal'
created: '2026-09-13'
updated: '2026-09-13'
---

# Technical Research: 企业主流 AI 应用开发框架与部署方式

**Decision this research serves:** 为 APCV 确定企业级模拟测试环境选用的真实开源组件与攻击场景。

## 执行摘要（选型结论）

**选定 Dify 作为 APCV 企业模拟环境的核心 AI 应用。** 理由（均有本 run 一手来源）：

1. **企业采用证据充分**：155K+ GitHub stars、发布活跃（v1.17.1, 2026-09-10, GitHub API 一手）；Dify 官网列出 Maersk/Adobe/PayPal/Mercedes-Benz 等大型企业（logo wall，可信度中）
2. **部署形态即企业形态**：官方 docker-compose 含 api/worker/web/PostgreSQL/Redis/向量库 多服务，真实复刻企业内网微服务拓扑，无需人为搭建
3. **攻击面齐全**：工具调用、HTTP 请求节点（间接联网面）、知识库文件读写、插件/工具市场（供应链面）、API key 体系（凭证链面）——覆盖 APCV 五类 probe 规则（filesystem/network/privilege/rate_limit/tool）
4. **可自托管、隔离部署**：完全离线可用（模型接本地 Ollama/mock），适合做受控靶场

**备选/补充组件**（按需后续加入，非第一版必需）：
- n8n（fair-code 许可，204K stars，HTTP 节点+凭证管理，作为"内部服务替 agent 联网"的第二跳）
- Verdaccio（MIT，轻量私有 registry，"留言板"信道，第一版可用 Dify 自带存储变量替代）

## 关键发现（按维度）

### D1 框架采用度
- LangChain《State of AI Agents》(2026-06-12, n>1300)：51% 受访者已有 agent 在生产、78% 有计划；**生产中最普遍的权限控制是"只读工具权限"+"敏感动作需人工审批"** —— 这正是 APCV 应验证的 conformance 面 [1]
- LangGraph 有具名企业生产案例（LinkedIn/Uber/Klarna/Elastic）[2]；CrewAI"65% Fortune 500"为营销口径，不可作数 [3]
- Microsoft 官方宣布 Agent Framework 为 Semantic Kernel/AutoGen 后继（2025-10-07）[4]
- n8n：SAP 2026-05 投资、$5.2B 估值（Wikipedia 转述一手融资报道）[5]

### D2 工具集成面（APCV 应建模的攻击面，MCP 规范与安全研究一手来源）
- MCP 已成 agent↔tool 事实标准（官方文档列 ChatGPT/VS Code/Cursor 客户端）[6]
- 规范自身与 Invariant Labs 确认的攻击类：**tool poisoning / shadowing / rug pull** [7]、**confused deputy**（OAuth 代理）[6]、**SSRF via OAuth discovery**（打到 169.254.169.254/内网 Redis）[6]、**one-click server 安装 RCE** [6]、**token passthrough 反模式** [6]
- OWASP GenAI Top 10 2025：LLM01 Prompt Injection、LLM06 Excessive Agency [8]
- 上述六类 = APCV 攻击场景库的分类学依据

### D3 部署形态
- 企业以 K8s/容器 + 托管运行时为主；工具执行沙箱收敛到专用编排器：**kubernetes-sigs/agent-sandbox**（CRD+controller，gVisor/Kata runtimeClass，SIG Apps 官方项目）[9]、Modal Sandboxes [10]、E2B [11]
- Bedrock AgentCore 安全文档给出企业控制点清单：IAM、resource-based policy、confused-deputy 防护、数据保护 [12]
- 注意（负面发现）：LangChain 调查**不含**基础设施数据；"多数企业在 K8s 跑 agent"仍是推断而非证据

### D4 组件生态健康度（GitHub API 一手核查，2026-09-13）
- ✅ 绿灯：Dify (v1.17.1)、OpenHands (MIT, v1.18.0)、Verdaccio (MIT, v6.10.3, 仅41 open issues)、garak (NVIDIA, Apache-2.0)、LangGraph (MIT)
- ⚠️ n8n：fair-code 非 OSI 开源，内部测试可用，再分发需审查许可
- ❌ **MinIO 仓库已 archived**（2026-04 后无推送、无 release）——从候选中剔除
- ❌ `Azure/PyRIT` 是 archived 空壳，活仓库在 `microsoft/PyRIT`

## 未决问题（不阻塞部署决策）
- 2026-05 至 07 OpenAI/HF 事件时间线未找到公开一手来源证实（用户描述，本 run 未验证）——作为行为模式灵感使用，不作为事实引用
- Dify/n8n 近期 CVE 未扫（WebSearch 会话内退化）；部署前按默认安全配置即可
- 各组件资源占用无一手数据；实测后再定 CI 档位

## 来源表
[1] https://www.langchain.com/stateofaiagents | LangChain | 2026-06-12 | 访问 2026-09-13
[2] https://www.langchain.com/built-with-langgraph | LangChain | 访问 2026-09-13
[3] https://www.crewai.com/ | CrewAI (营销) | 访问 2026-09-13
[4] https://devblogs.microsoft.com/agent-framework/semantic-kernel-and-microsoft-agent-framework/ | Microsoft | 2025-10-07 | 访问 2026-09-13
[5] https://en.wikipedia.org/wiki/N8n | Wikipedia | ed. 2026-09-07 | 访问 2026-09-13
[6] https://modelcontextprotocol.io/specification/2025-06-18/basic/security_best_practices | MCP 官方 | rev 2025-11-25 | 访问 2026-09-13
[7] https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks | Invariant Labs | 2025-04-01 | 访问 2026-09-13
[8] https://genai.owasp.org/llm-top-10/ | OWASP | 2025-03/07 | 访问 2026-09-13
[9] https://raw.githubusercontent.com/kubernetes-sigs/agent-sandbox/main/README.md | Kubernetes SIGs | 2026-09-13 | 访问 2026-09-13
[10] https://modal.com/docs/guide/sandbox | Modal | 访问 2026-09-13
[11] https://docs.e2b.dev/ | E2B | 访问 2026-09-13
[12] https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/security.html | AWS | GA 期文档 | 访问 2026-09-13
[13] https://api.github.com/repos/langgenius/dify (+releases) | GitHub API | 观测 2026-09-13
[14] https://api.github.com/repos/n8n-io/n8n | GitHub API | 观测 2026-09-13
[15] https://api.github.com/repos/All-Hands-AI/OpenHands | GitHub API | 观测 2026-09-13
[16] https://api.github.com/repos/verdaccio/verdaccio | GitHub API | 观测 2026-09-13
[17] https://api.github.com/repos/NVIDIA/garak | GitHub API | 观测 2026-09-13
[18] https://api.github.com/repos/minio/minio | GitHub API (archived) | 观测 2026-09-13
[19] https://api.github.com/repos/Azure/PyRIT vs microsoft/PyRIT | GitHub API | 观测 2026-09-13
