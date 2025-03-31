from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware # Import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware # Import CORSMiddleware
from app.api.v1.endpoints import auth, submissions, users # Import routers
from app.core.config import settings # Import settings

app = FastAPI(title="LocalPhoto API")

# CORS Middleware Configuration
# IMPORTANT: In production, replace "*" with the specific origins of your frontend
# e.g., origins = ["http://localhost:8080", "https://yourdomain.com"]
origins = [
    "http://localhost:8080",    # Allow the frontend dev server
    "http://127.0.0.1:8080",  # Allow the frontend dev server via IP
    # Add other origins like your production frontend URL later
    # "https://yourdomain.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True, # Allow cookies/auth headers
    allow_methods=["*"],    # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],    # Allow all headers
)


# Add Session Middleware (after CORS, before routers)
# IMPORTANT: Change the secret_key in production!
app.add_middleware(
    SessionMiddleware, secret_key=settings.SESSION_SECRET_KEY
)

@app.get("/")
async def read_root():
    """
    Root endpoint providing a welcome message.
    """
    return {"message": "Welcome to the LocalPhoto API!"}

# Include the authentication router
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(submissions.router, prefix="/api/v1/submissions", tags=["submissions"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])

# Add other routers and configurations below as needed