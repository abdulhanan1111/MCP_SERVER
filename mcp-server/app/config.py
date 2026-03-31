from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Custom MCP Server"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DB_PATH: str = "app/data/mcp.db"
    AUTO_APPROVE: bool = False
    DEFAULT_ENV: str = "production"
    GROQ_API_KEY: str | None = None
    GROQ_MODEL: str = "llama-3.1-70b-versatile"
    LLM_TIMEOUT: float = 30.0

    # Define other settings like GitHub/AWS MCP endpoints or tokens here if needed

    class Config:
        env_file = ".env"

settings = Settings()
