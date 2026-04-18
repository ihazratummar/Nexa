from typing import Optional, Literal

from pydantic import Field

from core.models.base_model import MongoBase


class ModerationLogModel(MongoBase):
    guild_id: int = Field(..., description="Guild ID")
    moderator_id: Optional[int] = Field(None, description="Moderator ID")
    offender_id: Optional[int] = Field(None, description="Offender ID")
    action_type: Optional[Literal['Kick', 'Timeout', 'Warn', 'Mute','Ban']] = Field(None, description="Action type")
    reason: Optional[str] = Field(None, description="Reason for the action")

    resolved: bool = Field(default=False)  # ✅ important