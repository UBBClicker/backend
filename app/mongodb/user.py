from .base import CRUDBase
from .connection import connection
from .. import schemas, models


class CRUDUser(CRUDBase[models.User, schemas.UserCreate, schemas.UserUpdate]):
    pass


user = CRUDUser(models.User, connection.engine)
