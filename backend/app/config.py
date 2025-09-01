"""
Configuration settings for SecurityA backend
"""
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "SecurityA"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # Database
    database_url: str = Field(env="DATABASE_URL")
    database_echo: bool = Field(default=False, env="DATABASE_ECHO")
    database_pool_size: int = Field(default=10, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=20, env="DATABASE_MAX_OVERFLOW")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    redis_db: int = Field(default=0, env="REDIS_DB")
    
    # Security
    secret_key: str = Field(env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # Azure OAuth2
    azure_client_id: str = Field(env="AZURE_CLIENT_ID")
    azure_client_secret: str = Field(env="AZURE_CLIENT_SECRET")
    azure_tenant_id: str = Field(env="AZURE_TENANT_ID")
    azure_redirect_uri: str = Field(env="AZURE_REDIRECT_URI")
    
    # Azure Cloud Services
    azure_subscription_id: Optional[str] = Field(default=None, env="AZURE_SUBSCRIPTION_ID")
    azure_resource_group: Optional[str] = Field(default=None, env="AZURE_RESOURCE_GROUP")
    
    # OpenAI
    openai_api_key: str = Field(env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    
    # Azure OpenAI
    azure_openai_endpoint: Optional[str] = Field(default=None, env="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: Optional[str] = Field(default=None, env="AZURE_OPENAI_API_KEY")
    azure_openai_api_version: Optional[str] = Field(default=None, env="AZURE_OPENAI_API_VERSION")
    openai_max_tokens: int = Field(default=2000, env="OPENAI_MAX_TOKENS")
    openai_temperature: float = Field(default=0.7, env="OPENAI_TEMPERATURE")
    
    # CORS
    cors_origins: list[str] = Field(default=["http://localhost:3000"], env="CORS_ORIGINS")
    
    # File Storage
    storage_type: str = Field(default="azure", env="STORAGE_TYPE")
    storage_connection_string: Optional[str] = Field(default=None, env="STORAGE_CONNECTION_STRING")
    azure_storage_connection_string: Optional[str] = Field(default=None, env="AZURE_STORAGE_CONNECTION_STRING")
    storage_container: str = Field(default="securitya-reports", env="STORAGE_CONTAINER")
    azure_storage_container: str = Field(default="securitya-reports", env="AZURE_STORAGE_CONTAINER")
    
    # Azure Key Vault
    azure_key_vault_url: Optional[str] = Field(default=None, env="AZURE_KEY_VAULT_URL")
    
    # Monitoring
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")
    
    # Rate Limiting
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=3600, env="RATE_LIMIT_WINDOW")
    
    # Email Configuration
    smtp_host: Optional[str] = Field(default=None, env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_username: Optional[str] = Field(default=None, env="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    smtp_tls: bool = Field(default=True, env="SMTP_TLS")
    
    # Scan Configuration
    max_concurrent_scans: int = Field(default=5, env="MAX_CONCURRENT_SCANS")
    scan_timeout_minutes: int = Field(default=30, env="SCAN_TIMEOUT_MINUTES")
    retention_days: int = Field(default=90, env="RETENTION_DAYS")
    
    # AI Configuration
    ai_analysis_enabled: bool = Field(default=True, env="AI_ANALYSIS_ENABLED")
    ai_chat_enabled: bool = Field(default=True, env="AI_CHAT_ENABLED")
    ai_report_generation_enabled: bool = Field(default=True, env="AI_REPORT_GENERATION_ENABLED")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
