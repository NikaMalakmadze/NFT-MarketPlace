
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv()

BASE_DIR: Path = Path(__file__).resolve().parent

FILES_FOLDER_NAME: str = 'uploads'
APP_FILES_FOLDER_NAME: str = 'app-files'
ALLOWED_EXTENSIONS: set[str] = {'png', 'jpg', 'jpeg', 'gif', 'jfif'}

class DbSettings(BaseModel):
    SQLALCHEMY_DATABASE_URI: str = os.environ.get('DATABASE_URL') or 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    UPLOAD_FOLDER: Path = BASE_DIR / "app" / FILES_FOLDER_NAME
    APP_FILES: Path = BASE_DIR / "app" / APP_FILES_FOLDER_NAME

class JWT(BaseModel):
    PRIVATE_KEY: Path = BASE_DIR / "certs" / "private.pem"
    PUBLIC_KEY: Path = BASE_DIR / "certs" / "public.pem"
    ALGORITHM: str = 'RS256'
    JWT_ACCESS_TOKEN_EXPIRES: int = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES_MINUTES'))
    JWT_REFRESH_TOKEN_EXPIRES: int = int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES_MINUTES'))

class App(BaseModel):
    MAX_ROYALTIES: float = 10.00

class Settings(BaseSettings):
    SECRET_KEY: str
    DEBUG: bool = True
    TESTING: bool = False

    db: DbSettings = DbSettings()
    jwt: JWT = JWT()
    app: App = App()

    model_config = SettingsConfigDict(env_file='.env', extra='allow')

settings = Settings()

def prepare_folders() -> None:
    db_folder = BASE_DIR / os.environ.get('DATABASE_FOLDER_NAME')
    os.makedirs(db_folder, exist_ok=True)
    os.makedirs(settings.db.UPLOAD_FOLDER, exist_ok=True)