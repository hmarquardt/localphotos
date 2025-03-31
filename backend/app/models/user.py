from sqlmodel import SQLModel, Field, Column, Relationship
from typing import Optional, List
from geoalchemy2 import Geometry

# Forward reference for the relationship
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .image_submission import ImageSubmission

class UserBase(SQLModel):
    email: str = Field(index=True, unique=True)
    avatar_url: Optional[str] = None
    # Define home_location with GeoAlchemy2 Geometry type
    # SRID 4326 is standard for GPS coordinates (WGS 84)
    home_location: Optional[str] = Field(
        default=None,
        sa_column=Column(Geometry(geometry_type='POINT', srid=4326), nullable=True)
    )
    default_radius_km: float = Field(default=5.0) # Default radius in kilometers

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    google_id: Optional[str] = Field(default=None, unique=True, index=True) # For Google OAuth

    # Define the one-to-many relationship to ImageSubmission
    submissions: List["ImageSubmission"] = Relationship(back_populates="user")

# Pydantic models for API input/output (can add more specific ones later)
class UserCreate(UserBase):
    password: str # Plain password during creation

class UserRead(UserBase):
    id: int
    # Optionally include submissions in the read model if needed later
    # submissions: List["ImageSubmissionRead"] = []

class UserUpdate(SQLModel):
    avatar_url: Optional[str] = None
    home_location: Optional[str] = None # Expecting WKT string or similar for input
    default_radius_km: Optional[float] = None