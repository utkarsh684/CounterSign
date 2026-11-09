"""Application configuration loaded using Pydantic Settings v2.

Adheres strictly to the principle that missing credentials should produce
a clean disconnected/configuration-needed state rather than an unhandled crash.
"""

from typing import List, Literal, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core Environment
    APP_NAME: str = "Countersign"
    ENVIRONMENT: Literal["development", "sandbox", "production"] = "sandbox"
    DEBUG: bool = True
    APP_BASE_URL: str = "http://localhost:8000"
    FRONTEND_BASE_URL: str = "http://localhost:5173"
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    # Database Configuration (MySQL 8.4 default, sqlite fallback for tests)
    DATABASE_URL: str = Field(
        default="mysql+pymysql://root:root@localhost:3306/countersign",
        description="Database connection string",
    )
    SQL_ECHO: bool = False

    # Security & Authentication
    JWT_SECRET: str = Field(
        default="countersign_super_secret_jwt_key_must_be_changed_in_prod_1234567890",
        description="HMAC secret for signing JWTs",
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    MANDATE_HMAC_SECRET: str = Field(
        default="countersign_mandate_hmac_secret_key_fixed_for_integrity_hash_12345",
        description="Secret key used for HMAC signing of compiled financial mandates",
    )
    AGENT_API_KEY: str = Field(
        default="cs_agent_live_99a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4",
        description="Default API key for the Countersign Ops Agent",
    )

    # Global Security Kill Switch
    KILL_SWITCH_ENABLED: bool = False

    # PayPal Sandbox Configuration
    PAYPAL_ENVIRONMENT: Literal["SANDBOX"] = "SANDBOX"
    PAYPAL_BASE_URL: str = "https://api-m.sandbox.paypal.com"
    PAYPAL_CLIENT_ID: Optional[str] = Field(default=None, description="PayPal Sandbox Client ID")
    PAYPAL_CLIENT_SECRET: Optional[str] = Field(default=None, description="PayPal Sandbox Client Secret")
    PAYPAL_WEBHOOK_ID: Optional[str] = Field(default=None, description="Registered PayPal Webhook ID")

    # AI Configuration (Provider-independent layer)
    AI_PROVIDER: Literal["gemini", "openai", "anthropic", "deterministic_mock"] = "deterministic_mock"
    AI_MODEL: str = "gemini-1.5-flash"
    AI_API_KEY: Optional[str] = Field(default=None, description="API Key for the chosen AI provider")

    # Demo Mode
    DEMO_MODE: bool = True

    @property
    def is_paypal_configured(self) -> bool:
        return bool(self.PAYPAL_CLIENT_ID and self.PAYPAL_CLIENT_SECRET)

    @property
    def is_ai_configured(self) -> bool:
        if self.AI_PROVIDER == "deterministic_mock":
            return True
        return bool(self.AI_API_KEY)


settings = Settings()
