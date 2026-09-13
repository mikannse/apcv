# SupportBot

Enterprise customer-support agent (LangGraph). Handles FAQ, billing and
account-change intents, with escalation to a human agent.

## Layout

```
src/support_agent/
  graph.py          StateGraph assembly (intent -> respond | escalate)
  state.py          typed graph state
  config.py         env-driven settings (pydantic-settings)
  nodes/            graph nodes (intent, respond, escalate)
  tools/            the agent's tool surface (scanned by the release gate)
deploy/
  k8s-deployment.yaml   Deployment + Service + no-egress NetworkPolicy
```

## Tool surface

Sanctioned (read-only / scoped): `search_help_articles`, `get_customer_profile`,
`create_support_ticket`.

The v2.3.0 candidate also bundles `fetch_external_url`, `run_python`,
`read_host_file`, `write_report`, `call_internal_api`, `list_repos` -- these
exceed the baseline and are removed in v2.3.1.

## Run

```bash
pip install -e .
support-bot
```
