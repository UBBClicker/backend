from typing import Optional

from motor import motor_asyncio, core
from odmantic import AIOEngine
from pymongo.driver_info import DriverInfo

from ..config import config


class MongoConnection:
    _instance: Optional["MongoConnection"] = None

    def __init__(
            self,
            mongo_uri: str,
            database: str,
            driver_info: DriverInfo,
    ):
        if MongoConnection._instance is not None:
            raise RuntimeError("Use 'get_connection' to access the MongoConnection instance.")

        self.client = motor_asyncio.AsyncIOMotorClient(
            mongo_uri,
            driver=driver_info,
        )
        self.engine = AIOEngine(client=self.client, database=database)

    def get_database(self) -> core.AgnosticDatabase:
        return self.client[self.engine.database.name]

    async def ping_database(self):
        await self.get_database().command("ping")

    @classmethod
    def get_connection(
            cls,
            mongo_uri: str,
            database: str,
            driver_info: DriverInfo,
    ) -> "MongoConnection":
        if cls._instance is None:
            cls._instance = cls(
                mongo_uri=mongo_uri,
                database=database,
                driver_info=driver_info,
            )
        return cls._instance

    @classmethod
    def close_connection(cls):
        if cls._instance is not None:
            cls._instance.client.close()
            cls._instance = None


connection = MongoConnection.get_connection(
    config.MONGO_URI, config.MONGO_DATABASE, DriverInfo(config.APP_NAME)
)

__all__ = ["connection"]
