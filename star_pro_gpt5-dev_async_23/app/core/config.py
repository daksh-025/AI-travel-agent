from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):    
    # MongoDB Configuration
    mongodb_url: str
    database_name: str = "staicey"
    
    # Connection Pooling Configuration
    max_pool_size: int = 50
    min_pool_size: int = 5
    max_idle_time_ms: int = 30000
    wait_queue_timeout_ms: int = 2500
    connect_timeout_ms: int = 10000
    server_selection_timeout_ms: int = 5000
    socket_timeout_ms: int = 20000
    heartbeat_frequency_ms: int = 10000
    retry_writes: bool = True
    retry_reads: bool = True
    write_concern: str = "majority"
    read_concern: str = "majority"
    
    # JWT Configuration
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 120  # 2 hours
    reset_token_expire_minutes: int = 30
    frontend_base_url: Optional[str] = None
    
    # Application Configuration
    app_name: str = "Staiz Backend"
    app_version: str = "1.0.0"
    debug: bool = False  # Set to False for production
    
    # CORS Configuration
    cors_origins: List[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]
    
    # Security Configuration
    password_min_length: int = 6
    bcrypt_rounds: int = 12
    
    # Redis Configuration for LangChain Memory
    redis_url: str = "redis://localhost:6379"
    redis_db: str = "staicey"
    redis_max_connections: int = 5
    redis_retry_on_timeout: bool = True
    redis_socket_timeout: int = 5
    redis_connection_timeout: int = 5
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    open_api_model_name: str = "gpt-5"
    
    # Pinecone Configuration
    pinecone_api_key: Optional[str] = None
    pinecone_environment: str = "us-east1-gcp"
    
    # SerpAPI Configuration
    serpapi_api_key: Optional[str] = None
    max_iteration_agent: int = 8
    
    # Tavily Configuration
    tavily_api_key: Optional[str] = None
    
    # Apify Configuration
    apify_token: Optional[str] = None
    
    # Performance Optimization Flags
    use_async_agent: bool = False  # Use optimized AsyncSimpleAgent (parallel tool execution)

    # SMTP / Email Configuration
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True
    smtp_from_email: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Allow extra fields without validation errors


# Create settings instance
settings = Settings()
