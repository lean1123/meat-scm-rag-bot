from datetime import datetime

from bson import ObjectId
from pydantic import BaseModel, Field, ConfigDict, field_serializer

from .base import PyObjectId


class ConversationBase(BaseModel):
    email: str
    facilityID: str
    title: str = Field(..., max_length=100)


class ConversationCreate(ConversationBase):
    pass


class ConversationInDB(ConversationBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

    @field_serializer("id")
    def serialize_id(self, v: ObjectId, _info):
        return str(v)
