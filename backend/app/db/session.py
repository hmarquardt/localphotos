from sqlmodel import create_engine, Session
from app.core.config import settings

# Create the SQLAlchemy engine
# connect_args is recommended for SQLite, but generally not needed for PostgreSQL
# engine = create_engine(settings.DATABASE_URL, echo=True, connect_args={"check_same_thread": False}) # echo=True for debugging SQL
engine = create_engine(settings.DATABASE_URL, echo=False)

def get_db():
    """
    FastAPI dependency that provides a database session.
    Ensures the session is closed after the request.
    """
    with Session(engine) as session:
        yield session

# Optional: Function to create tables (useful for initial setup without Alembic or for testing)
# def create_db_and_tables():
#     from sqlmodel import SQLModel
#     # Import models here if needed
#     # from app.models.user import User
#     # from app.models.image_submission import ImageSubmission
#     SQLModel.metadata.create_all(engine)