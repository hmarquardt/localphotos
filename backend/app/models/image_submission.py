from sqlmodel import SQLModel, Field, Column, Relationship
from typing import Optional
from geoalchemy2 import Geometry
import datetime

# Forward reference for the relationship
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .user import User

class ImageSubmissionBase(SQLModel):
    description: Optional[str] = Field(default=None, max_length=256)
    # Location stored as a POINT geometry
    location: str = Field(sa_column=Column(Geometry(geometry_type='POINT', srid=4326)))
    image_url: str # URL from S3 storage
    uploaded_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    expires_at: datetime.datetime
    thumbs_up_count: int = Field(default=0)
    thumbs_down_count: int = Field(default=0)
    is_locked: bool = Field(default=False) # Locked after 10 mins

class ImageSubmission(ImageSubmissionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)

    # Define the relationship back to the User model
    user: "User" = Relationship(back_populates="submissions") # Assuming User model will have a 'submissions' relationship field

# Pydantic models for API input/output
class ImageSubmissionCreate(SQLModel):
    description: Optional[str] = Field(default=None, max_length=256)
    # Location might be received as lat/lon pair or WKT string from frontend
    latitude: float
    longitude: float
    # image_url will be set after upload to S3

class ImageSubmissionRead(ImageSubmissionBase):
    id: int
    user_id: int
    # Optionally include user details if needed
    # user: Optional["UserRead"] = None

class ImageSubmissionUpdate(SQLModel):
    # Only description can be updated within the time limit
    description: Optional[str] = Field(default=None, max_length=256)

# Need to add 'submissions' relationship to User model later
# In backend/app/models/user.py, add:
# from typing import List
# from .image_submission import ImageSubmission
# class User(UserBase, table=True):
#     ... # other fields
#     submissions: List["ImageSubmission"] = Relationship(back_populates="user")