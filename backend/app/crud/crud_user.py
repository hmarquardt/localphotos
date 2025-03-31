from sqlmodel import Session, select
from typing import Optional

from app.models.user import User, UserCreate, UserUpdate

def get_user_by_email(db: Session, *, email: str) -> Optional[User]:
    """
    Retrieves a user from the database by their email address.
    """
    statement = select(User).where(User.email == email)
    user = db.exec(statement).first()
    return user

def create_user(db: Session, *, user_in: UserCreate) -> User:
    """
    Creates a new user in the database.
    Hashes the password before storing.
    """
    from app.core.security import get_password_hash # Import here to avoid circular dependency issues

    hashed_password = get_password_hash(user_in.password)
    # Create a User instance from UserCreate, excluding the plain password
    # and adding the hashed password.
    # Note: home_location handling might need adjustment if input isn't directly compatible
    user_data = user_in.model_dump(exclude={"password"})
    db_user = User(**user_data, hashed_password=hashed_password)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, *, db_user: User, user_in: UserUpdate) -> User:
    """
    Update a user's details.
    """
    # Get the data from the input schema, excluding unset values
    update_data = user_in.model_dump(exclude_unset=True)

    # Update the user object fields
    # Note: If home_location needs specific conversion (e.g., from lat/lon to WKT),
    # it should ideally happen before calling this CRUD function, perhaps in the endpoint.
    # Assuming user_in.home_location is already in the correct format (WKT string) if provided.
    for field, value in update_data.items():
        setattr(db_user, field, value)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_google_id(db: Session, *, google_id: str) -> Optional[User]:
    """
    Retrieves a user from the database by their Google ID.
    """
    statement = select(User).where(User.google_id == google_id)
    user = db.exec(statement).first()
    return user

def update_user_google_id(db: Session, *, user: User, google_id: str, avatar_url: Optional[str] = None) -> User:
    """
    Updates an existing user's Google ID and optionally their avatar URL.
    Used for linking an existing email account to Google login.
    """
    user.google_id = google_id
    if avatar_url and not user.avatar_url: # Only update avatar if not already set
        user.avatar_url = avatar_url
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def create_user_with_google(db: Session, *, email: str, google_id: str, avatar_url: Optional[str] = None) -> User:
    """
    Creates a new user using details from Google OAuth.
    Assumes hashed_password can be null in the User model.
    """
    # Create a User instance directly
    # Note: Requires User model's hashed_password field to be nullable
    db_user = User(
        email=email,
        google_id=google_id,
        avatar_url=avatar_url,
        hashed_password=None # Set password to None initially
        # Set defaults for home_location, default_radius_km if needed, or rely on model defaults
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user