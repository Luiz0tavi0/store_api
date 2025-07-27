from typing import List
from uuid import UUID
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import pymongo
from store.db.mongo import db_client
from store.models.product import ProductModel
from store.schemas.product import ProductIn, ProductOut, ProductUpdate, ProductUpdateOut
from store.core.exceptions import InsertionException, NotFoundException


class ProductUsecase:
    def __init__(self) -> None:
        client = db_client.get()
        database = client.get_database()
        self.client: "AsyncIOMotorClient" = client  # type: ignore
        self.database: "AsyncIOMotorDatabase" = database  # type: ignore
        self.collection = self.database.get_collection("products")

    async def create(self, body: ProductIn) -> ProductOut:
        existing = await self.collection.find_one({"name": body.name})
        # ipdb.set_trace()
        if existing:
            raise InsertionException(f"Produto de nome '{body.name}' já existe.")
        product_model = ProductModel(**body.model_dump())
        await self.collection.insert_one(product_model.model_dump())

        return ProductOut(**product_model.model_dump())

    async def get(self, id: UUID) -> ProductOut:
        result = await self.collection.find_one({"id": id})

        if not result:
            raise NotFoundException(message=f"Product not found with filter: {id}")

        return ProductOut(**result)

    async def query(self) -> List[ProductOut]:
        return [ProductOut(**item) async for item in self.collection.find()]

    async def update(self, id: UUID, body: ProductUpdate) -> ProductUpdateOut:
        update_data = body.model_dump(exclude_none=True)
        update_data["updated_at"] = update_data.get(
            "updated_at", datetime.now(timezone.utc)
        )

        result = await self.collection.find_one_and_update(
            filter={"id": id},
            update={"$set": update_data},
            return_document=pymongo.ReturnDocument.AFTER,
        )
        if not result:
            raise NotFoundException(message=f"Produto não encontrado com id : {id}")

        return ProductUpdateOut(**result)

    async def delete(self, id: UUID) -> bool:
        product = await self.collection.find_one({"id": id})
        if not product:
            raise NotFoundException(message=f"Product not found with filter: {id}")

        result = await self.collection.delete_one({"id": id})

        return True if result.deleted_count > 0 else False


product_usecase = ProductUsecase()
