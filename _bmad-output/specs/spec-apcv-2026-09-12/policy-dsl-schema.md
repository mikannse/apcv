# Policy DSL Schema

Declared Policy is a YAML file authored by Agent developers to declare what their Agent is allowed to do. It serves as the **baseline** against which Probes test for boundary violations.

## Schema Definition

```yaml
# policy.yaml

version: "1.0"  # Schema version

metadata:
  agent_name: github-assistant
  policy_name: github-readonly
  author: team-ai-security
  created_date: 2026-09-12
  description: "GitHub API read-only agent; no system calls"

tools:
  # Which tools can the Agent invoke?
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
  # What filesystem paths can the Agent access?
  enabled: true
  allowed_paths:
    - /data/github_repos  # Can read
    - /tmp/scratch        # Can read/write
  denied_paths:
    - /etc
    - /root
    - /home
  access_modes:
    read: true
    write: false         # No writes to /data
    execute: false
  symlink_traversal: false  # Disallow symlinks

network:
  # Network access policies
  enabled: true
  allowed_domains:
    - api.github.com
    - raw.githubusercontent.com
  denied_domains:
    - internal.company.com
    - 169.254.169.254  # AWS metadata service
  allowed_ports:
    - 443
    - 80
  denied_ports:
    - 22   # SSH
    - 3306 # MySQL
    - 6379 # Redis

parameters:
  # Constraints on tool parameters
  read_file:
    max_file_size: "10MB"
    path_pattern: "^/data/.*"    # Regex whitelist
  
  http_get:
    domain_whitelist:
      - api.github.com
      - raw.githubusercontent.com
    timeout_seconds: 30
    max_body_size: "5MB"

rate_limits:
  # Frequency and quota constraints
  read_file:
    max_calls_per_minute: 60
    max_calls_per_hour: 1000
  
  http_get:
    max_calls_per_minute: 30
    max_calls_per_hour: 500

privilege:
  # Privilege-related constraints
  allow_sudo: false
  allow_suid: false
  allow_capability_escalation: false
  required_user: "nobody"  # Run as non-root

sub_agents:
  # How do sub-agents inherit this policy?
  inheritance_mode: "strict"  # strict | relaxed | custom
  # strict = sub-agents get exact same constraints
  # relaxed = sub-agents can have subset of parent permissions
  
environment:
  # Environment variable access
  allowed_vars:
    - GITHUB_TOKEN
    - AGENT_CONFIG
  
  denied_vars:
    - AWS_SECRET_ACCESS_KEY
    - DATABASE_PASSWORD

compliance:
  # Regulatory requirements
  scopes:
    - gdpr          # EU data protection
    - sox           # Financial audit
    - iso27001      # Information security
  
  data_classification: "internal"  # public | internal | confidential | restricted

severity_levels:
  # How strict is policy enforcement?
  mode: "strict"  # strict | balanced | report-only
  # strict = any violation → FAIL + block deployment
  # balanced = critical violation → FAIL; warning violations → WARN
  # report-only = log all violations but don't block
```

## Validation Rules

1. **Mutual Exclusion**: A tool cannot be both in `allowed` and `denied`
2. **Path Constraints**: `allowed_paths` and `denied_paths` must not overlap; regex patterns must be valid
3. **Rate Limits**: `max_calls_per_minute` ≤ `max_calls_per_hour` ÷ 60
4. **Sub-agent Inheritance**: If `sub_agents.inheritance_mode = strict`, sub-agent policy must be identical or subset
5. **Privilege Sanity**: If `allow_sudo = true`, `required_user` cannot be `nobody`

## Policy DSL Examples

### Example 1: Strict Read-Only Agent

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
  enabled: false  # No network

severity_levels:
  mode: strict
```

### Example 2: GitHub API Agent (Moderate)

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

### Example 3: Internal Tool Agent (Complex)

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
    max_calls_per_hour: 10  # Limit write operations

severity_levels:
  mode: strict
```

## Policy Editing in Web UI

The Web UI provides a **YAML editor** with:

- **Syntax highlighting** for YAML
- **Real-time validation** against schema
- **Auto-completion** for known tool names, filesystem paths, domains
- **Template library** (read-only, denied, github-api, internal-admin presets)
- **Diff viewer** (before/after policy change, impact analysis)
- **Test preview** (show probes that will be generated for this policy)

## Version & Audit Trail

Policy updates are versioned; every change is logged:

```json
{
  "version": 3,
  "timestamp": "2026-09-12T14:30:00Z",
  "author": "alice@company.com",
  "change": "relaxed filesystem.allowed_paths from [/data] to [/data, /tmp/scratch]",
  "reason": "Agent needs scratch space for temp files"
}
```

This audit trail is included in compliance reports.
