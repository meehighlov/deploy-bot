from pathlib import Path

from pydantic.v1 import BaseSettings


ENV_FILE = Path(__file__).parents[1] / ".env"


class Config(BaseSettings):
    bot_token: str
    bot_owners: list[str]
    bot_unit_files_path: str = "/etc/systemd/system"
    bot_components_code_path: str = "/etc"
    bot_secrets_path: str = "/etc/secrets"

    class Config:
        env_file = ENV_FILE


config = Config()
