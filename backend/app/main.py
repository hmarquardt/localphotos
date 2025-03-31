from fastapi import FastAPI
from app.api.v1.endpoints import auth # Import the auth router

app = FastAPI(title="LocalPhoto API")

@app.get("/")
async def read_root():
    """
    Root endpoint providing a welcome message.
    """
    return {"message": "Welcome to the LocalPhoto API!"}

# Include the authentication router
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])

# Add other routers and configurations below as needed