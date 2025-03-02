from dotenv import load_dotenv, find_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

load_dotenv(find_dotenv())


class Config(BaseSettings):
    APP_NAME: str = Field("UBBClicker", description="The name of the app")

    PASSWORD_TOKEN: str


config = Config()
