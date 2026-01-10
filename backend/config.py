"""Runtime configuration utilities for the backend."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() == "true"


@dataclass
class Settings:
    """Lightweight settings container that reads from environment variables."""

    mongo_url: str = field(default_factory=lambda: os.getenv("MONGO_URL", "mongodb://localhost:27017"))
    db_name: str = field(default_factory=lambda: os.getenv("DB_NAME", "nowhere_digital"))

    sendgrid_api_key: str = field(default_factory=lambda: os.getenv("SENDGRID_API_KEY", ""))
    sendgrid_from_email: str = field(default_factory=lambda: os.getenv("SENDGRID_FROM_EMAIL", "noreply@nowheredigital.ae"))
    sender_email: str = field(default_factory=lambda: os.getenv("SENDER_EMAIL", "hello@nowheredigital.ae"))
    admin_email: str = field(default_factory=lambda: os.getenv("ADMIN_EMAIL", "admin@nowheredigital.ae"))

    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    default_ai_model: str = field(default_factory=lambda: os.getenv("DEFAULT_AI_MODEL", "gpt-4o"))
    ai_provider: str = field(default_factory=lambda: os.getenv("AI_PROVIDER", "openai"))
    emergent_llm_key: str = field(default_factory=lambda: os.getenv("EMERGENT_LLM_KEY", "sk-test-default-api-key"))

    stripe_api_key: str = field(default_factory=lambda: os.getenv("STRIPE_API_KEY", "sk_test_stripe"))

    twilio_account_sid: str = field(default_factory=lambda: os.getenv("TWILIO_ACCOUNT_SID", ""))
    twilio_auth_token: str = field(default_factory=lambda: os.getenv("TWILIO_AUTH_TOKEN", ""))
    twilio_verify_service: str = field(default_factory=lambda: os.getenv("TWILIO_VERIFY_SERVICE", ""))
    twilio_phone_number: str = field(default_factory=lambda: os.getenv("TWILIO_PHONE_NUMBER", ""))

    jwt_secret: str = field(default_factory=lambda: os.getenv("JWT_SECRET", "your-secret-key-change-in-production"))
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 24 * 60 * 60

    cors_origins: List[str] = field(default_factory=lambda: [
        "http://localhost:3000",
        "https://ai-business-os-1.preview.emergentagent.com",
    ])

    api_prefix: str = field(default_factory=lambda: os.getenv("API_PREFIX", "/api"))
    debug: bool = field(default_factory=lambda: _env_flag("DEBUG", False))

    max_file_size: int = 10 * 1024 * 1024
    allowed_file_types: List[str] = field(default_factory=lambda: [
        "image/jpeg",
        "image/png",
        "image/gif",
        "application/pdf",
    ])

    rate_limit_requests: int = 100
    rate_limit_period: int = 60

    email_templates_dir: str = field(default_factory=lambda: os.getenv("EMAIL_TEMPLATES_DIR", "email_templates"))


settings = Settings()
