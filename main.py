import uvicorn
from fastapi import FastAPI

from app import api

fastapi_app = FastAPI(title="UBBClicker API")
fastapi_app.include_router(api.root_router)


def main():
    # SQLite tables are already created in app/__init__.py
    uvicorn.run("main:fastapi_app", port=3001, reload=True)


if __name__ == "__main__":
    main()
