import asyncio

import uvicorn
from fastapi import FastAPI

from app import mongodb, api

fastapi_app = FastAPI(title="UBBClicker API")
fastapi_app.include_router(api.root_router)


async def configure_database():
    tables = [mongodb.user]

    tasks = [table.configure() for table in tables]

    await asyncio.gather(*tasks)


async def main():
    await configure_database()

    uvicorn.run("main:fastapi_app", port=3001, reload=True)


if __name__ == "__main__":
    asyncio.run(main())
