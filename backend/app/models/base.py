from sqlmodel import SQLModel, Field
from typing import Optional
import datetime

# You can add common fields like ID or timestamps here if desired
# class BaseSQLModel(SQLModel):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
#     updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)