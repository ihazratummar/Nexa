from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class InfractionHistory(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    reason: str
    rule_triggered: Optional[str] = None

class UserInfraction(BaseModel):
    guild_id: str
    user_id: str
    warning_count: int = Field(default=0)
    history: List[InfractionHistory] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
