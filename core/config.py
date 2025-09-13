

from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    DATABASE_URL: str = "postgresql://inquiro:inquiro@localhost:9090/email_classification"
    OPENAI_API_KEY: str = ""
    LANGSMITH_TRACING: str = "false"
    LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGSMITH_API_KEY: str = "lsv2_pt_***"
    LANGSMITH_PROJECT: str = "default"

    model_config = {"env_file": ".env"}

settings = Settings()