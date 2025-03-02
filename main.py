import asyncio

from app import mongodb, schemas


async def main():
    user_db = await mongodb.user.create(schemas.UserCreate(nickname="oskar", password="kutas"))

    print(user_db)


if __name__ == "__main__":
    asyncio.run(main())
