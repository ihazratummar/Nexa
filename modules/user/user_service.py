from motor.motor_asyncio import AsyncIOMotorCollection

from core.database import Database
from core.models.user_model import UserModel


class UserService:


    @classmethod
    def get_user_collection(cls) -> AsyncIOMotorCollection:
        return Database.user()

    @classmethod
    async def get_user_data(cls, user_id: int, guild_id: int) -> UserModel | None:
        """
        Get user data from database
        """
        collection = cls.get_user_collection()
        user_data = await collection.find_one({"user_id": user_id, "guild_id": guild_id})
        if user_data is None:
            return None
        return UserModel(**user_data)