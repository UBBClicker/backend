from dotenv import load_dotenv, find_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings
import os

load_dotenv(find_dotenv())


class Config(BaseSettings):
    APP_NAME: str = Field("UBBClicker", description="The name of the app")

    # SQLite database configuration
    SQLITE_DATABASE_URL: str = Field("sqlite:///./ubbclicker.db", description="The URL of the SQLite database")
   
    # JWT token secret key - default is only for testing
    PASSWORD_TOKEN: str = Field("testing_secret_key_not_for_production", description="Secret key for JWT token encoding")


config = Config()
