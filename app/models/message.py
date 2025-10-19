from datetime import datetime

from bson import ObjectId
from pydantic import BaseModel, Field, ConfigDict, field_serializer

from .base import PyObjectId


class MessageBase(BaseModel):
    sender_type: str = Field(..., pattern="^(user|bot)$")
    content: str


class MessageCreate(MessageBase):
    pass


class MessageInDB(MessageBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    conversation_id: PyObjectId
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

    @field_serializer("id", "conversation_id")
    def serialize_objectid(self, v: ObjectId, _info):
        return str(v)
