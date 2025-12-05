
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ARD_", env_file=".env", extra="ignore")
    artifacts_dir: str = "artifacts"
    catalog_dir: str = "data/catalogs/v0"
    constants_file: str = "data/constants.yaml"

settings = Settings()
