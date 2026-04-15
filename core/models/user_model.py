from typing import Optional, List

from pydantic import Field

from core.models.base_model import MongoBase


class UserModel(MongoBase):
    user_id: int = Field(..., description="User ID")
    guild_id: int = Field(..., description="Guild ID")
    roles: Optional[List[int]] = Field(None, description="Roles")