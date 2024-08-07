from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    db_uri: str

    nitter_host: str
    twitter_request_sleep_seconds: float = 10
    playwright_initial_cookies: str
    twitter_username: str

    images_dir: Path
    data_dir: Path

    huggingface_token: str
    custom_autotagger_model_dir: Path
    csd_pretrained_model_path: Path
