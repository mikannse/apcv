# 上线前安全门禁（pre-launch-gate）

模拟企业真实场景：**一个完整的 LangGraph agent 应用在发布流水线里接受 APCV 卡点检查**。
纯静态验证，不需要任何运行环境。

## 被测对象是什么样

一个真实的企业 agent 是**一整个代码库**，不是单个文件：

```
customer-support-bot/                    # SupportBot v2.3.0 发布候选
├── pyproject.toml                       依赖与打包（langgraph/langchain/pydantic-settings）
├── Dockerfile                           多阶段镜像构建
├── .env.example                         密钥注入点（CRM token / admin-scoped token…）
├── deploy/k8s-deployment.yaml           Deployment + Service + 禁出网 NetworkPolicy
├── src/support_agent/
│   ├── graph.py                         LangGraph 状态机（intent → respond | escalate）
│   ├── state.py                         类型化图状态
│   ├── config.py                        env 驱动配置
│   ├── nodes/                           图节点（intent / respond / escalate）
│   └── tools/                           工具面（门禁扫描对象）
│       ├── knowledge.py  search_help_articles   ✓ 白名单
│       ├── crm.py        get_customer_profile   ✓ 白名单
│       ├── ticketing.py  create_support_ticket  ✓ 白名单
│       ├── external.py   fetch_external_url     ✗ 未批准外联
│       ├── code_exec.py  run_python             ✗ 任意代码执行
│       ├── filesystem.py read_host_file/write_report  ✗ 任意文件读写
│       └── internal_api.py call_internal_api/list_repos ✗ 特权内网调用 + 越界残留
└── tests/test_tools.py
```

`customer-support-bot-fixed/` 是同一应用 v2.3.1（删除越权模块后的修复版）。

## 卡点：`gate.py`

APCV 核心的 `ToolScanner` 目前单文件扫描，`gate.py` 是对它的薄集成——遍历整个包，
扫描每个 `.py` 模块里的 `@tool`，合并成一份 SBOM（工具带来源文件定位），再跑 conformance：

```
整个 package ──> gate.py ──> 逐模块 @tool 扫描 ──> 合并 SBOM ──> 对 policy 判定 ──> 退出码
```

```bash
python gate.py --agent customer-support-bot --policy policy/release_baseline.yaml
# 退出码: 0=PASS  1=WARN  2=FAIL  （CI 用退出码决定流水线通断）
```

## 实测结果

| 版本 | 扫描 | 结果 |
|---|---|---|
| v2.3.0 | 18 文件 → 9 工具 | **FAIL** score 45，退出码 2：5× critical（代码执行/外联/文件读写/特权调用）+ 1× high（list_repos 复制粘贴残留） |
| v2.3.1 | 14 文件 → 3 工具 | **PASS** score 100，退出码 0 |

关键点：门禁抓到的不只是"危险工具"，还有**越界残留**（`list_repos` 是 dev-bot 复制来的，
根本不属于客服 agent 的范围）——这正是静态卡点相对人工 review 的价值：连"不该存在的
能力"都拦得住。

## GitHub Actions 接入

```yaml
- name: APCV pre-launch gate
  run: |
    python gate.py \
      --agent customer-support-bot \
      --policy policy/release_baseline.yaml --output json > apcv-report.json
  # 非零退出码自动 fail 整个 job；报告作为 artifact 上传
```

## 本次顺带修复的 APCV 缺陷

真实代码库必然含中文注释/特殊字符，原实现 `read_text()` 未指定编码，在 Windows/GBK
环境直接崩。已修复两处：
- `apcv/core/frameworks/langgraph_adapter.py` → `read_text(encoding="utf-8")`
- `apcv/core/policy/validator.py` → `open(..., encoding="utf-8")`
