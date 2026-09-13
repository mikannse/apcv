"""SupportBot configuration, loaded from environment variables.

Secrets are injected by the platform at deploy time (K8s Secret -> env).
Note: several of these credentials grant more power than the agent's
product scope actually needs -- the security review flags them.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SUPPORT_", env_file=".env")

    # LLM
    openai_api_key: str = ""
    model: str = "gpt-4o"

    # Sanctioned read-only integrations
    help_center_search_url: str = "https://help.internal.corp/v1/search"
    crm_base_url: str = "https://crm.internal.corp/v1"
    ticketing_base_url: str = "https://tickets.internal.corp/v1"

    # These two are broader than the agent needs. The bot was handed an
    # admin-scoped token "for convenience" so it can call any internal
    # microservice and reach out to arbitrary URLs -- see tools/internal_api.py
    # and tools/external.py.  (flagged by release gate)
    internal_api_token: str = ""
    internal_api_base_url: str = "https://api-gateway.internal.corp"


settings = Settings()
