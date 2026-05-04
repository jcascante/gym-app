from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    backend_log_level: str = "info"
    data_dir: Path = Path("./data")
    definitions_dir: Path = Path("./definitions")
    schemas_dir: Path = Path("./schemas")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
