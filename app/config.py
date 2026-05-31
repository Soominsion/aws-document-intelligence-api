from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Cloud-native Document Intelligence API"
    environment: str = "local"
    summarization_model: str = "sshleifer/distilbart-cnn-12-6"
    huggingface_home: str = ".cache/huggingface"
    min_text_length_for_model: int = 80
    max_summary_length: int = 160
    min_summary_length: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
