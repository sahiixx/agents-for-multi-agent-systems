from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # Database
    mongo_url: str = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    db_name: str = os.getenv("DB_NAME", "nowhere_digital")
    
    # Email Settings
    sendgrid_api_key: str = os.getenv("SENDGRID_API_KEY", "")
    sendgrid_from_email: str = os.getenv("SENDGRID_FROM_EMAIL", "noreply@nowheredigital.ae")
    sender_email: str = os.getenv("SENDER_EMAIL", "hello@nowheredigital.ae")
    admin_email: str = os.getenv("ADMIN_EMAIL", "admin@nowheredigital.ae")
    
    # AI Settings
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    default_ai_model: str = os.getenv("DEFAULT_AI_MODEL", "gpt-4o")
    ai_provider: str = os.getenv("AI_PROVIDER", "openai")
    emergent_llm_key: str = os.getenv("EMERGENT_LLM_KEY", "sk-emergent-8A3Bc7c1f91F43cE8D")
    
    # Payment Settings
    stripe_api_key: str = os.getenv("STRIPE_API_KEY", "sk_test_emergent")
    
    # SMS Settings
    twilio_account_sid: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    twilio_auth_token: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    twilio_verify_service: str = os.getenv("TWILIO_VERIFY_SERVICE", "")
    twilio_phone_number: str = os.getenv("TWILIO_PHONE_NUMBER", "")
    
    # Security
    jwt_secret: str = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 24 * 60 * 60  # 24 hours
    
    # CORS
    cors_origins: List[str] = [
        "http://localhost:3000",
        "https://ai-business-os-1.preview.emergentagent.com"
    ]
    
    # API Settings
    api_prefix: str = "/api"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # File Upload
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: List[str] = ["image/jpeg", "image/png", "image/gif", "application/pdf"]
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # seconds
    
    # Email Templates
    email_templates_dir: str = "email_templates"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create global settings instance
settings = Settings()