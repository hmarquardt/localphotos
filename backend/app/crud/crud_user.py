from sqlmodel import Session, select
from typing import Optional

from app.models.user import User, UserCreate

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