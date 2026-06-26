"""Configuration - env vars and defaults."""

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv():
    """Load .env from cwd, walking up to home dir. No-op if python-dotenv missing."""
    try:
        from dotenv import load_dotenv
        # search cwd first, then parent dirs up to ~
        env_path = Path(".env")
        if not env_path.exists():
            cur = Path.cwd()
            home = Path.home()
            while cur != home and cur != cur.parent:
                candidate = cur / ".env"
                if candidate.exists():
                    env_path = candidate
                    break
                cur = cur.parent
        load_dotenv(env_path, override=False)
    except ImportError:
        pass  # python-dotenv not installed, silently skip


@dataclass
class Config:
    model: str = "gpt-4o"
    api_key: str = ""
    base_url: str | None = None
    max_tokens: int = 4096
    temperature: float = 0.0
    max_context_tokens: int = 128_000
    provider: str = "openai"

    # Deployment mode: cloud / local / hybrid
    mode: str = "cloud"
    local_model: str = "qwen2.5-coder:7b"
    local_base_url: str = "http://localhost:11434/v1"

    @classmethod
    def from_env(cls) -> "Config":
        # load .env if present (won't override existing env vars)
        _load_dotenv()
        # pick up common env vars automatically
        api_key = (
            os.getenv("CORECODER_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("DEEPSEEK_API_KEY")
            or ""
        )
        return cls(
            model=os.getenv("CORECODER_MODEL", "gpt-4o"),
            mode=os.getenv("CORECODER_MODE", "cloud"),
            local_model=os.getenv("LOCAL_MODEL", "qwen2.5-coder:7b"),
            local_base_url=os.getenv("LOCAL_BASE_URL", "http://localhost:11434/v1"),
            api_key=api_key,
            base_url=os.getenv("OPENAI_BASE_URL") or os.getenv("CORECODER_BASE_URL"),
            max_tokens=int(os.getenv("CORECODER_MAX_TOKENS", "4096")),
            temperature=float(os.getenv("CORECODER_TEMPERATURE", "0")),
            max_context_tokens=int(os.getenv("CORECODER_MAX_CONTEXT", "128000")),
            provider=os.getenv("CORECODER_PROVIDER", "openai"),
        )
