# Agent Policy Conformance Validator (APCV)

**在部署前验证 AI Agent 是否符合其声明的策略。**

[English](README.md) | [中文](README.zh-CN.md)

APCV 是一个 MVP,用于根据安全与能力策略验证 LangGraph Agent。它发现 Agent 可以调用哪些工具,生成针对性的测试探针,在隔离环境中运行,并报告策略违规及其修复建议。

## 快速开始

```bash
# 安装依赖(由 uv 管理的虚拟环境)
uv sync

# 依据策略验证 Agent
uv run apcv validate --agent tests/fixtures/sample_agents/simple_agent.py \
                     --policy tests/fixtures/policies/read_only.yaml

# 在 Web UI 中查看结果(FastAPI 仪表盘,地址 http://127.0.0.1:8000)
uv run apcv web
```

## 特性

- **工具面发现(四层)**: 框架层 `@tool`(单文件 + 包级 `scan_package`)、MCP 端点清单、子 Agent 工具面枚举
- **策略 DSL**: 用 YAML 声明能力与边界(默认拒绝)
- **探针执行**: 策略相对型 agent 探针 + baseline 审计探针,在隔离 Docker 沙箱中执行
- **参数追踪**: wrapt 记录每次工具调用的参数,产出审计证据 (JSONL)
- **合规性检查**: 将 Agent 行为与声明的策略进行比对
- **CLI 工具**: `apcv validate --output json|sarif|html`
- **Web UI**: FastAPI 仪表盘(stub — 尚未接真实报告数据)

## 项目结构

```
apcv/
├── core/
│   ├── scanners/          # 工具发现(单文件 + 包级)
│   ├── frameworks/        # 框架适配器 (LangGraph)
│   ├── policy/            # 策略 DSL 与校验
│   ├── probes/            # 测试探针(agent + baseline)
│   ├── execution/         # 沙箱执行器 + 追踪器 + ProbeHost
│   └── utils/             # SBOM 数据模型
│
├── cli/                    # CLI 接口(validate / web)
├── web/                    # FastAPI 后端(stub)
├── tests/                  # 测试套件
└── docker/                 # apcv-probe 沙箱镜像
```

## 文档

- [架构主干](_bmad-output/architecture/architecture-apcv-2026-09-12/ARCHITECTURE-SPINE.md)
- [产品规格 (SPEC)](_bmad-output/specs/spec-apcv-2026-09-12/SPEC.md)
- [Policy DSL Schema](_bmad-output/specs/spec-apcv-2026-09-12/policy-dsl-schema.md)
- [探针规则](_bmad-output/specs/spec-apcv-2026-09-12/probe-rules.md)
- [Sprint 状态](_implementation/sprint-status.yaml)

## License

Apache 2.0
