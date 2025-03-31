from sqlmodel import SQLModel, Field, Column, Relationship
from typing import Optional, Any
from geoalchemy2 import Geometry
from geoalchemy2.elements import WKBElement # Import WKBElement
from geoalchemy2.shape import to_shape # Import to_shape for serialization
from pydantic import computed_field # Import computed_field
import datetime

# Forward reference for the relationship
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .user import User

class ImageSubmissionBase(SQLModel):
    description: Optional[str] = Field(default=None, max_length=256)
    # Location stored as a POINT geometry
    location: Any = Field(sa_column=Column(Geometry(geometry_type='POINT', srid=4326))) # Changed type hint from str to Any
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
    # Allow arbitrary types like WKBElement during schema generation,
    # even though we exclude/compute the field for the final output.
    model_config = {"arbitrary_types_allowed": True}
    id: int
    user_id: int
    # Exclude the original 'location' field (WKBElement) from the response model
    # It's still available internally for the computed_field below.
    location: WKBElement | None = Field(default=None, exclude=True)
    # Optionally include user details if needed
    # user: Optional["UserRead"] = None

    # Use computed_field to provide the WKT string representation in the response.
    @computed_field(return_type=str) # Explicitly set return type for clarity
    @property
    def location_wkt(self) -> str:
        """
        Computes the WKT string representation from the internal WKBElement.
        """
        # self.location refers to the excluded field populated by SQLModel/SQLAlchemy
        if isinstance(self.location, WKBElement):
            try:
                shape = to_shape(self.location)
                return shape.wkt # Return WKT string
            except Exception as e:
                print(f"Error computing location field: {e}")
                return "Error: Invalid location data" # Fallback string
        elif isinstance(self.location, str):
             # Handle cases where it might already be a string (less likely for read)
             return self.location
        # Fallback if it's neither WKBElement nor string
        return "Error: Unknown location format"

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