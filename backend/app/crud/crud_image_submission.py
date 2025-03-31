from sqlmodel import Session, select
from sqlalchemy.sql.expression import func # Use func for SQL functions
from geoalchemy2.functions import ST_DistanceSphere, ST_MakePoint # Import GeoAlchemy functions
from typing import List, Optional # Import Optional

from app.models.image_submission import ImageSubmission, ImageSubmissionCreate, ImageSubmissionUpdate # Import Update schema
from app.models.user import User # Needed for type hinting user object
import datetime

def create_image_submission(db: Session, *, submission_in: ImageSubmissionCreate, user: User, image_url: str) -> ImageSubmission:
    """
    Create a new image submission in the database.
    """
    # Convert lat/lon to WKT format for GeoAlchemy2 POINT
    # SRID=4326 is assumed based on the model definition
    location_wkt = f'SRID=4326;POINT({submission_in.longitude} {submission_in.latitude})'

    # Calculate expiration date (e.g., 3 days from now)
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(days=3)

    # Create the database model instance
    db_submission = ImageSubmission(
        description=submission_in.description,
        location=location_wkt,
        image_url=image_url, # Provided after S3 upload
        expires_at=expires_at,
        user_id=user.id,
        # Defaults for thumbs_up_count, thumbs_down_count, is_locked are handled by the model
    )

    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    return db_submission

def get_nearby_submissions(db: Session, *, latitude: float, longitude: float, radius_km: float) -> List[ImageSubmission]:
    """
    Get image submissions within a certain radius of a given point,
    filtering out expired ones.
    """
    # Convert radius from km to meters
    radius_meters = radius_km * 1000

    # Create a POINT geometry for the center location using ST_MakePoint
    # Note: Longitude comes first in ST_MakePoint(x, y)
    center_point = ST_MakePoint(longitude, latitude)
    # Set SRID explicitly if needed, though often inferred or handled by GeoAlchemy
    # center_point = func.ST_SetSRID(center_point, 4326) # Usually not needed if column has SRID

    # Get current time to filter expired submissions
    now = datetime.datetime.utcnow()

    # Build the query using ST_DistanceSphere for accurate distance calculation
    # ST_DistanceSphere returns distance in meters
    statement = (
        select(ImageSubmission)
        .where(ImageSubmission.expires_at > now)
        .where(
            ST_DistanceSphere(
                ImageSubmission.location, # The geometry column in the table
                center_point              # The point we created
            ) <= radius_meters
        )
        .order_by(ImageSubmission.uploaded_at.desc()) # Optional: order by newest first
    )

    results = db.exec(statement).all()
    return results

def get_submission_by_id(db: Session, *, submission_id: int) -> Optional[ImageSubmission]:
    """
    Get an image submission by its ID.
    """
    statement = select(ImageSubmission).where(ImageSubmission.id == submission_id)
    submission = db.exec(statement).first()
    return submission

def update_submission(db: Session, *, db_submission: ImageSubmission, submission_in: ImageSubmissionUpdate) -> Optional[ImageSubmission]:
    """
    Update an image submission's description, only if within the 10-minute window.
    Returns the updated submission or None if the update is disallowed.
    """
    # Check if the submission is within the editable time window (e.g., 10 minutes)
    editable_until = db_submission.uploaded_at + datetime.timedelta(minutes=10)
    if datetime.datetime.utcnow() > editable_until:
        # Optionally, could also check an is_locked flag if we set one via background task
        return None # Indicate update is not allowed

    # Update only the allowed fields (description in this case)
    update_data = submission_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "description": # Only allow description update
             setattr(db_submission, field, value)
        # Add other updatable fields here if needed in the future

    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    return db_submission

def delete_submission(db: Session, *, submission_id: int) -> Optional[ImageSubmission]:
    """
    Delete an image submission by its ID.
    Returns the deleted submission object or None if not found.
    """
    db_submission = get_submission_by_id(db=db, submission_id=submission_id)
    if not db_submission:
        return None

    # --- Placeholder for S3 Deletion Logic ---
    # Before deleting from DB, delete the corresponding file from S3
    # Example: await delete_from_s3(db_submission.image_url)
    print(f"Placeholder: Would delete {db_submission.image_url} from S3 now.")
    # --- End Placeholder ---

    db.delete(db_submission)
    db.commit()
    # The object is expired after commit, so we return the object fetched before delete
    return db_submission

def add_thumbs_up(db: Session, *, submission_id: int) -> Optional[ImageSubmission]:
    """
    Increment the thumbs_up_count for a submission.
    Returns the updated submission or None if not found.
    """
    db_submission = get_submission_by_id(db=db, submission_id=submission_id)
    if not db_submission:
        return None

    # Simple increment - no duplicate check for now
    db_submission.thumbs_up_count += 1
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    return db_submission

def add_thumbs_down(db: Session, *, submission_id: int) -> Optional[ImageSubmission]:
    """
    Increment the thumbs_down_count for a submission.
    Returns the updated submission or None if not found.
    """
    db_submission = get_submission_by_id(db=db, submission_id=submission_id)
    if not db_submission:
        return None

    # Simple increment - no duplicate check for now
    db_submission.thumbs_down_count += 1
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    return db_submission