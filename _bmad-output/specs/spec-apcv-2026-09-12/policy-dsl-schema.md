# Policy DSL Schema

声明策略（Declared Policy）是由 Agent 开发者编写的 YAML 文件，用于声明其 Agent 被允许做什么。它是探针（Probe）进行越界测试所依据的**基线**。

## Schema 定义

```yaml
# policy.yaml

version: "1.0"  # Schema 版本

metadata:
  agent_name: github-assistant
  policy_name: github-readonly
  author: team-ai-security
  created_date: 2026-09-12
  description: "GitHub API read-only agent; no system calls"

tools:
  # Agent 可以调用哪些工具？
  allowed:
    - read_file
    - http_get
    - json_parse
  
  denied:
    - bash_execute
    - ssh_command
    - delete_file
    - write_file

filesystem:
  # Agent 可以访问哪些文件系统路径？
  enabled: true
  allowed_paths:
    - /data/github_repos  # 可读
    - /tmp/scratch        # 可读写
  denied_paths:
    - /etc
    - /root
    - /home
  access_modes:
    read: true
    write: false         # 不允许写入 /data
    execute: false
  symlink_traversal: false  # 禁止符号链接

network:
  # 网络访问策略
  enabled: true
  allowed_domains:
    - api.github.com
    - raw.githubusercontent.com
  denied_domains:
    - internal.company.com
    - 169.254.169.254  # AWS 元数据服务
  allowed_ports:
    - 443
    - 80
  denied_ports:
    - 22   # SSH
    - 3306 # MySQL
    - 6379 # Redis

parameters:
  # 对工具参数的约束
  read_file:
    max_file_size: "10MB"
    path_pattern: "^/data/.*"    # 正则白名单
  
  http_get:
    domain_whitelist:
      - api.github.com
      - raw.githubusercontent.com
    timeout_seconds: 30
    max_body_size: "5MB"

rate_limits:
  # 频率与配额约束
  read_file:
    max_calls_per_minute: 60
    max_calls_per_hour: 1000
  
  http_get:
    max_calls_per_minute: 30
    max_calls_per_hour: 500

privilege:
  # 权限相关约束
  allow_sudo: false
  allow_suid: false
  allow_capability_escalation: false
  required_user: "nobody"  # 以非 root 身份运行

sub_agents:
  # 子 Agent 如何继承本策略？
  inheritance_mode: "strict"  # strict | relaxed | custom
  # strict = 子 Agent 获得完全相同的约束
  # relaxed = 子 Agent 可拥有父级权限的子集
  
environment:
  # 环境变量访问
  allowed_vars:
    - GITHUB_TOKEN
    - AGENT_CONFIG
  
  denied_vars:
    - AWS_SECRET_ACCESS_KEY
    - DATABASE_PASSWORD

compliance:
  # 监管要求
  scopes:
    - gdpr          # 欧盟数据保护
    - sox           # 财务审计
    - iso27001      # 信息安全
  
  data_classification: "internal"  # public | internal | confidential | restricted

severity_levels:
  # 策略执行的严格程度如何？
  mode: "strict"  # strict | balanced | report-only
  # strict = 任何违规 → FAIL + 阻止部署
  # balanced = critical 违规 → FAIL；warning 违规 → WARN
  # report-only = 记录全部违规但不阻止
```

## 校验规则

1. **互斥约束**：一个工具不能同时出现在 `allowed` 和 `denied` 中
2. **路径约束**：`allowed_paths` 与 `denied_paths` 不得重叠；正则模式必须合法
3. **速率限制**：`max_calls_per_minute` ≤ `max_calls_per_hour` ÷ 60
4. **子 Agent 继承**：若 `sub_agents.inheritance_mode = strict`，子 Agent 策略必须与父级完全相同或为其子集
5. **权限合理性**：若 `allow_sudo = true`，则 `required_user` 不能为 `nobody`

## Policy DSL 示例

### 示例 1：严格只读 Agent

```yaml
version: "1.0"
metadata:
  agent_name: data-analyzer
  policy_name: read-only-analytics

tools:
  allowed: [read_file, csv_parse, json_parse]
  denied: [write_file, delete_file, bash_execute, ssh_command]

filesystem:
  enabled: true
  allowed_paths: [/data/datasets]
  denied_paths: [/etc, /root, /home]
  access_modes: {read: true, write: false, execute: false}

network:
  enabled: false  # 禁用网络

severity_levels:
  mode: strict
```

### 示例 2：GitHub API Agent（中等严格度）

```yaml
version: "1.0"
metadata:
  agent_name: github-assistant
  policy_name: github-readonly

tools:
  allowed: [http_get, json_parse, read_file]
  denied: [bash_execute, ssh_command]

network:
  enabled: true
  allowed_domains: [api.github.com]
  allowed_ports: [443]

parameters:
  http_get:
    domain_whitelist: [api.github.com, raw.githubusercontent.com]
    max_body_size: "5MB"

rate_limits:
  http_get:
    max_calls_per_minute: 30

severity_levels:
  mode: balanced
```

### 示例 3：内部工具 Agent（复杂场景）

```yaml
version: "1.0"
metadata:
  agent_name: internal-tool
  policy_name: restricted-admin

tools:
  allowed: [read_file, write_file, execute_script]
  denied: [bash_execute, sudo]

filesystem:
  enabled: true
  allowed_paths: [/var/app, /tmp/work]
  access_modes: {read: true, write: true, execute: false}
  symlink_traversal: false

parameters:
  execute_script:
    script_whitelist: [/var/app/scripts/deploy.sh, /var/app/scripts/health_check.sh]
    
  write_file:
    path_pattern: "^/tmp/work/.*"
    max_file_size: "100MB"

rate_limits:
  write_file:
    max_calls_per_hour: 10  # 限制写操作次数

severity_levels:
  mode: strict
```

## Web UI 中的策略编辑

Web UI 提供一个 **YAML 编辑器**，具备：

- **语法高亮**（针对 YAML）
- 依据 schema 进行**实时校验**
- 对已知工具名、文件系统路径、域名提供**自动补全**
- **模板库**（read-only、denied、github-api、internal-admin 等预设）
- **Diff 查看器**（策略变更前/后对比、影响分析）
- **测试预览**（展示将为此策略生成的探针）

## 版本与审计留痕

策略更新按版本管理；每一次变更都被记录：

```json
{
  "version": 3,
  "timestamp": "2026-09-12T14:30:00Z",
  "author": "alice@company.com",
  "change": "relaxed filesystem.allowed_paths from [/data] to [/data, /tmp/scratch]",
  "reason": "Agent needs scratch space for temp files"
}
```

该审计留痕会被纳入合规报告。
