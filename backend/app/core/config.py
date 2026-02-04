"""
Application settings and configuration management.

This module provides:
- Centralized configuration using Pydantic
- Environment-based settings (dev, staging, production)
- Validation of required environment variables
- Secret management
"""

from pydantic import BaseSettings, validator, Field
from typing import Optional, List
from functools import lru_cache
import os


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Environment variables can be set in:
    - .env file (for development)
    - System environment (for production)
    - Docker/Kubernetes secrets
    """
    
    # ========================================================================
    # Application Settings
    # ========================================================================
    
    app_name: str = Field(default="Southern Horizons Hotel", env="APP_NAME")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    version: str = Field(default="1.0.0", env="VERSION")
    
    # ========================================================================
    # Server Settings
    # ========================================================================
    
    backend_host: str = Field(default="0.0.0.0", env="BACKEND_HOST")
    backend_port: int = Field(default=8010, env="BACKEND_PORT")
    frontend_url: str = Field(default="http://localhost:5174", env="FRONTEND_URL")
    
    # CORS settings
    cors_origins: List[str] = Field(
        default=["http://localhost:5174", "http://localhost:3000"],
        env="CORS_ORIGINS"
    )
    
    # ========================================================================
    # Database Settings
    # ========================================================================
    
    database_url: str = Field(default="sqlite:///hotel.db", env="DATABASE_URL")
    database_pool_size: int = Field(default=10, env="DATABASE_POOL_SIZE")
    database_echo: bool = Field(default=False, env="DATABASE_ECHO")  # Log SQL queries
    
    # ========================================================================
    # Security Settings
    # ========================================================================
    
    # Admin authentication
    admin_api_key: str = Field(..., env="ADMIN_API_KEY")  # Required!
    allow_dev_admin_key: bool = Field(default=False, env="ALLOW_DEV_ADMIN_KEY")
    
    # Session management
    secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        env="SECRET_KEY"
    )
    
    # Token expiration (in seconds)
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # ========================================================================
    # AI/LLM Settings
    # ========================================================================
    
    google_api_key: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    
    # LLM configuration
    llm_temperature: float = Field(default=0.7, env="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=2000, env="LLM_MAX_TOKENS")
    llm_timeout_seconds: int = Field(default=30, env="LLM_TIMEOUT_SECONDS")
    
    # ========================================================================
    # Logging Settings
    # ========================================================================
    
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_dir: str = Field(default="logs", env="LOG_DIR")
    log_json_format: bool = Field(default=True, env="LOG_JSON_FORMAT")
    
    # ========================================================================
    # Feature Flags
    # ========================================================================
    
    enable_ai_service: bool = Field(default=True, env="ENABLE_AI_SERVICE")
    enable_analytics: bool = Field(default=True, env="ENABLE_ANALYTICS")
    enable_acp: bool = Field(default=True, env="ENABLE_ACP")
    
    # ========================================================================
    # External Services
    # ========================================================================
    
    # Property Management Systems
    enable_pms_integration: bool = Field(default=False, env="ENABLE_PMS_INTEGRATION")
    pms_api_url: Optional[str] = Field(default=None, env="PMS_API_URL")
    pms_api_key: Optional[str] = Field(default=None, env="PMS_API_KEY")
    
    # Payment processing
    enable_payments: bool = Field(default=False, env="ENABLE_PAYMENTS")
    stripe_api_key: Optional[str] = Field(default=None, env="STRIPE_API_KEY")
    
    # ========================================================================
    # Performance Settings
    # ========================================================================
    
    request_timeout_seconds: int = Field(default=30, env="REQUEST_TIMEOUT_SECONDS")
    max_request_size_mb: int = Field(default=10, env="MAX_REQUEST_SIZE_MB")
    enable_caching: bool = Field(default=True, env="ENABLE_CACHING")
    cache_ttl_seconds: int = Field(default=300, env="CACHE_TTL_SECONDS")
    
    # ========================================================================
    # Validators
    # ========================================================================
    
    @validator("environment")
    def validate_environment(cls, v):
        """Ensure environment is one of the allowed values"""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of: {allowed}")
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Ensure log level is valid"""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"Log level must be one of: {allowed}")
        return v_upper
    
    @validator("secret_key")
    def validate_secret_key(cls, v, values):
        """Warn if using default secret key in production"""
        if values.get("environment") == "production" and v == "dev-secret-key-change-in-production":
            raise ValueError("You must set a custom SECRET_KEY in production!")
        return v
    
    @validator("admin_api_key")
    def validate_admin_key(cls, v, values):
        """Ensure admin key is strong in production"""
        if values.get("environment") == "production" and len(v) < 20:
            raise ValueError("ADMIN_API_KEY must be at least 20 characters in production")
        return v
    
    # ========================================================================
    # Helper Properties
    # ========================================================================
    
    @property
    def is_development(self) -> bool:
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    @property
    def database_is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")
    
    @property
    def has_google_ai(self) -> bool:
        return bool(self.google_api_key)
    
    @property
    def has_openai(self) -> bool:
        return bool(self.openai_api_key)
    
    # ========================================================================
    # Config
    # ========================================================================
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # Allow CORS_ORIGINS as comma-separated string
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str):
            if field_name == "CORS_ORIGINS":
                return [origin.strip() for origin in raw_val.split(",")]
            return raw_val


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Using @lru_cache ensures we only load settings once,
    even if this function is called multiple times.
    
    Usage:
        from app.core.config import get_settings
        
        settings = get_settings()
        print(settings.app_name)
    """
    return Settings()


def validate_settings():
    """
    Validate all settings on application startup.
    Raises an error if any required settings are missing or invalid.
    
    Call this in main.py before starting the server.
    """
    try:
        settings = get_settings()
        
        # Check critical settings
        if not settings.admin_api_key:
            raise ValueError("ADMIN_API_KEY is required!")
        
        if settings.enable_ai_service and not (settings.google_api_key or settings.openai_api_key):
            raise ValueError("AI service enabled but no API key provided (GOOGLE_API_KEY or OPENAI_API_KEY)")
        
        # Print configuration summary
        print("=" * 60)
        print(f"🏨 {settings.app_name} - Configuration Loaded")
        print("=" * 60)
        print(f"Environment:     {settings.environment}")
        print(f"Debug Mode:      {settings.debug}")
        print(f"Backend:         {settings.backend_host}:{settings.backend_port}")
        print(f"Database:        {settings.database_url}")
        print(f"Log Level:       {settings.log_level}")
        print(f"AI Service:      {'Enabled' if settings.enable_ai_service else 'Disabled'}")
        print(f"Google AI:       {'✓' if settings.has_google_ai else '✗'}")
        print(f"OpenAI:          {'✓' if settings.has_openai else '✗'}")
        print("=" * 60)
        
        return settings
        
    except Exception as e:
        print("❌ Configuration Error!")
        print(f"Error: {str(e)}")
        print("\nPlease check your .env file and environment variables.")
        raise
