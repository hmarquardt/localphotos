from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload # Import selectinload
from typing import Any, List # Import List

from app.db.session import get_db
from app.models.user import User, UserRead, UserUpdate
from app.models.image_submission import ImageSubmissionRead # Import submission read model
from app.crud import crud_user # Import user CRUD functions
# Assuming a dependency function exists to get the current user
# from app.api.deps import get_current_active_user

# --- Reusing Placeholder Dependency (Replace with actual implementation later) ---
# Placeholder for the dependency - replace with actual implementation
async def get_current_active_user(db: Session = Depends(get_db)) -> User:
    # In a real app, this would verify JWT and fetch user
    # For now, returning the first user found for basic testing (NOT FOR PRODUCTION)
    user = db.query(User).first()
    if not user:
        # Use 401 Unauthorized if no user is found based on token in a real scenario
        raise HTTPException(status_code=401, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    return user
# --- End Placeholder ---


router = APIRouter()

@router.get("/me", response_model=UserRead)
def read_users_me(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get current user details.
    """
    # The dependency already provides the current user object
    return current_user

@router.put("/me", response_model=UserRead)
def update_user_me(
    *,
    db: Session = Depends(get_db),
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update own user details.
    """
    # Note: If home_location is provided in user_in and needs conversion
    # (e.g., from lat/lon to WKT string), it should happen here before
    # passing to the CRUD function. Assuming user_in.home_location is WKT if present.

    user = crud_user.update_user(db=db, db_user=current_user, user_in=user_in)
    return user

@router.get("/me/submissions", response_model=List[ImageSubmissionRead])
def read_user_me_submissions(
    db: Session = Depends(get_db), # Add db session dependency
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get submissions for the current user.
    """
    # SQLModel/SQLAlchemy relationship loading should make submissions available
    # Ensure relationship loading is configured correctly if issues arise (e.g., selectinload)
    # Explicitly fetch the user with their submissions to ensure they are loaded
    statement = (
        select(User)
        .where(User.id == current_user.id)
        .options(selectinload(User.submissions)) # Eagerly load submissions
    )
    user_with_submissions = db.exec(statement).first()

    if not user_with_submissions:
         # Should not happen if current_user exists, but good practice
         raise HTTPException(status_code=404, detail="User not found")

    return user_with_submissions.submissions