from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse # Needed for redirect
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session
from typing import Any
from authlib.integrations.starlette_client import OAuth, OAuthError # Import Authlib
import uuid # For generating placeholder password/state

from app import crud
from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.models.token import Token
from app.models.user import User, UserCreate, UserRead # Import User model
from app.core.config import settings # Import settings for OAuth config

# Configure Authlib OAuth client
oauth = OAuth()
oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

router = APIRouter()

@router.post("/login", response_model=Token)
def login_for_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = crud.crud_user.get_user_by_email(db, email=form_data.username) # Use email as username
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.email} # Use email as the JWT subject
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=UserRead)
def register_new_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate
) -> Any:
    """
    Create new user.
    """
    user = crud.crud_user.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system.",
        )
    user = crud.crud_user.create_user(db=db, user_in=user_in)
    return user


@router.get("/google")
async def login_via_google(request: Request):
    """
    Initiate Google OAuth login flow.
    """
    redirect_uri = settings.GOOGLE_REDIRECT_URI # Use configured redirect URI
    # Generate a random state string (optional but recommended for security)
    state = str(uuid.uuid4())
    request.session['oauth_state'] = state # Store state in session
    return await oauth.google.authorize_redirect(request, redirect_uri, state=state)


@router.get("/google/callback", response_model=Token)
async def google_auth_callback(request: Request, db: Session = Depends(get_db)):
    """
    Handle the callback from Google after user authorization.
    """
    # Check state for CSRF protection (optional but recommended)
    # received_state = request.query_params.get('state')
    # stored_state = request.session.pop('oauth_state', None)
    # if not stored_state or stored_state != received_state:
    #     raise HTTPException(status_code=400, detail="Invalid state parameter")

    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as error:
        print(f"OAuth Error: {error.error}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f'Could not validate Google credentials: {error.error}',
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_info = token.get('userinfo')
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not fetch user info from Google.',
            headers={"WWW-Authenticate": "Bearer"},
        )

    google_id = user_info.get('sub')
    email = user_info.get('email')
    avatar_url = user_info.get('picture') # Get avatar URL

    if not email:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Email not provided by Google.',
        )

    # --- User Lookup/Creation Logic ---
    # 1. Check if user exists by google_id
    user = crud.crud_user.get_user_by_google_id(db, google_id=google_id) # Needs implementation

    if not user:
        # 2. If not found by google_id, check by email
        user = crud.crud_user.get_user_by_email(db, email=email)
        if user:
            # 2a. User exists with this email but no google_id - link account
            # Ensure user doesn't already have a different google_id? (optional check)
            user = crud.crud_user.update_user_google_id(db, user=user, google_id=google_id, avatar_url=avatar_url) # Needs implementation
        else:
            # 2b. No user found by email or google_id - create new user
            # Note: Requires User model hashed_password to be nullable
            # and crud function to handle null password
            user = crud.crud_user.create_user_with_google(
                db,
                email=email,
                google_id=google_id,
                avatar_url=avatar_url
            ) # Needs implementation

    if not user:
         # Should not happen if CRUD functions work correctly
         raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Could not retrieve or create user account.',
        )

    # --- Generate JWT Token ---
    access_token = create_access_token(
        data={"sub": user.email} # Use email as subject
    )

    # Return the token (frontend will handle storage and redirection)
    return {"access_token": access_token, "token_type": "bearer"}

# Note: Need to add Starlette SessionMiddleware to the main FastAPI app
# for request.session to work for state management.