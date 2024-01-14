from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    db_uri: str

    nitter_host: str
    nitter_request_sleep_seconds: float = 10
    twitter_username: str

    images_dir: Path

    huggingface_token: str
