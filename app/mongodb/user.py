from .base import CRUDBase
from .connection import connection
from .. import schemas, models


class CRUDUser(CRUDBase[models.User, schemas.UserCreate, schemas.UserUpdate]):
    async def register(self, user: schemas.UserCreate):
        print("Registering user")
        return await self.create(user)


user = CRUDUser(models.User, connection.engine)
