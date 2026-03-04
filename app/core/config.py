from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "chatui-template-with-htmx"
    auth_mode: str = "dev_demo"  # proxy | dev_demo
    jwt_header_name: str = "X-Forwarded-JWT"
    jwt_algorithm: str = "HS256"
    jwt_secret: str = "dev-secret-change-me"
    jwt_issuer: str = "chatui-dev"
    jwt_audience: str = "chatui"

    # Chat guard rails
    max_message_length: int = 4000

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
