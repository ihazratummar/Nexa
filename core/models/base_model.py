from datetime import datetime
from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, Field
from pydantic.v1 import ConfigDict


class PyObjectId(ObjectId):
    """Custom type for MongoDB ObjectId to work with pydantic"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, *args, **kwargs):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId {}".format(v))
        return v
    @classmethod
    def __get_pydantic_json_schema__(cls):
        return {"type": "string"}

class MongoBase(BaseModel):
    """ Base model for all MongoDB models"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(
        populate_defaults=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
    )

    def to_mongo(self, **kwargs):
        """Convert pydantic model to MongoDB model"""
        exclude_unset = kwargs.pop("exclude_unset", False)
        by_alias = kwargs.pop("by_alias", True)

        parsed = self.model_dump(
            exclude_unset=exclude_unset,
            by_alias=by_alias,
            **kwargs
        )

        if "_id" in parsed and parsed["_id"] is None:
            del parsed["_id"]

        return parsed