from typing import Generic, Type, TypeVar, Optional, Any

import odmantic
import pydantic
from fastapi.encoders import jsonable_encoder
from motor.motor_asyncio import AsyncIOMotorCollection

from .. import exceptions, utils
from .. import schemas

ModelType = TypeVar("ModelType", bound=odmantic.Model)
CreateSchemaType = TypeVar("CreateSchemaType", bound=pydantic.BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=pydantic.BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self,
                 model: Type[ModelType],
                 engine: odmantic.AIOEngine,
                 *,
                 multi_max: Optional[int] = 7
                 ) -> None:
        self.model = model
        self.engine: odmantic.AIOEngine = engine

        self.multi_max = multi_max

    @property
    def collection(self) -> AsyncIOMotorCollection:
        return self.engine.get_collection(self.model)

    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        obj = self.model(**obj_in_data)
        return await self.engine.save(obj)

    async def read(self, id: schemas.PyObjectId) -> ModelType:
        model = await self.engine.find_one(self.model, self.model.id == odmantic.ObjectId(id))

        if model is None:
            raise exceptions.DocumentNotFound(id)

        return model

    async def update(self,
                     db_obj: ModelType | dict,
                     obj_in: UpdateSchemaType | dict,
                     *,
                     patch: Optional[bool] = False
                     ) -> ModelType:
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in

        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field in obj_data:
            if patch and update_data.get(field) is None:
                continue

            if field in update_data:
                setattr(db_obj, field, update_data[field])

            if field == "updated_at":
                setattr(db_obj, field, utils.datetime_now_sec())

        await self.engine.save(db_obj)
        return db_obj

    async def delete(self, id: schemas.PyObjectId) -> None:
        model = await self.read(id)
        if model is None:
            raise exceptions.DocumentNotFound(id)

        await self.engine.delete(model)

    async def save(self, obj: ModelType) -> ModelType:
        return await self.engine.save(obj)

    async def configure(self) -> None:
        await self.engine.configure_database([self.model])

    async def count(self, *queries) -> int:
        return await self.engine.count(self.model, *queries)

    async def find_many(self,
                        *queries,
                        page: Optional[int] = None,
                        limit: Optional[int] = None,
                        sort: Optional[Any] = None
                        ) -> list[ModelType]:
        if not limit:
            limit = self.multi_max

        kwargs = {}
        if page:
            kwargs["skip"] = (page - 1) * limit
            kwargs["limit"] = limit

        if sort is not None:
            kwargs["sort"] = sort

        return await self.engine.find(self.model, *queries, **kwargs)

    async def find_one(self,
                       *queries,
                       **kwargs
                       ) -> ModelType:
        return await self.engine.find_one(self.model, *queries, **kwargs)

    async def delete_collection(self) -> None:
        await self.collection.drop()


__all__ = ["CRUDBase"]
