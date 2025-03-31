from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlmodel import Session
from typing import Optional, Any, List # Import List
import boto3
import uuid
from botocore.exceptions import ClientError # Import ClientError for boto3 exceptions

from app.db.session import get_db
from app.models.user import User
from app.models.image_submission import ImageSubmissionCreate, ImageSubmissionRead, ImageSubmissionUpdate # Import Update schema
from app.crud import crud_image_submission
# Assuming a dependency function exists to get the current user
# from app.api.deps import get_current_active_user
from app.models.user import User # Temporary: Replace with actual dependency import
from app.core.config import settings # Import settings for AWS credentials

# Placeholder for the dependency - replace with actual implementation
async def get_current_active_user(db: Session = Depends(get_db)) -> User:
    # In a real app, this would verify JWT and fetch user
    # For now, returning the first user found for basic testing (NOT FOR PRODUCTION)
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found for placeholder dependency")
    return user


router = APIRouter()

@router.post("/", response_model=ImageSubmissionRead, status_code=status.HTTP_201_CREATED)
async def create_submission(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    # Use Form(...) for fields alongside File(...)
    description: Optional[str] = Form(None),
    latitude: float = Form(...),
    longitude: float = Form(...),
    image: UploadFile = File(...)
) -> Any:
    """
    Create new image submission. Requires authentication.
    Handles image upload and saves metadata.
    """
    # Basic validation for the uploaded file (can be expanded)
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    # --- S3 Upload Logic ---
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION
    )
    bucket_name = settings.S3_BUCKET_NAME

    # Generate a unique filename using UUID and preserve original extension
    file_extension = image.filename.split('.')[-1] if '.' in image.filename else 'jpg' # Default to jpg if no extension
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    object_key = f"submissions/{unique_filename}" # Store in a 'submissions' folder in the bucket

    try:
        s3_client.upload_fileobj(
            image.file,       # The file-like object from UploadFile
            bucket_name,      # Bucket name
            object_key,       # Key (path/filename) in the bucket
            ExtraArgs={'ContentType': image.content_type} # Set content type for proper browser handling
        )
        # Construct the URL (consider using CloudFront in production for better performance/security)
        image_url = f"https://{bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{object_key}"
        print(f"Successfully uploaded {object_key} to {bucket_name}. URL: {image_url}")

    except ClientError as e:
        print(f"S3 Upload Error: {e}") # Log the error
        raise HTTPException(status_code=500, detail="Failed to upload image to storage.")
    except Exception as e: # Catch other potential errors during upload
        print(f"Unexpected error during S3 upload: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred during image upload.")
    finally:
        # Ensure the file cursor is closed, though FastAPI might handle this
        await image.close()
    # --- End S3 Upload Logic ---

    submission_in = ImageSubmissionCreate(
        description=description,
        latitude=latitude,
        longitude=longitude
    )

    try:
        submission = crud_image_submission.create_image_submission(
            db=db,
            submission_in=submission_in,
            user=current_user,
            image_url=image_url
        )
        return submission
    except Exception as e:
        # Basic error handling, can be more specific
        print(f"Error creating submission: {e}") # Log the error
        # Consider deleting the uploaded S3 object if DB save fails
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create image submission.",
        )

@router.get("/nearby", response_model=List[ImageSubmissionRead])
def get_nearby_submissions_endpoint(
    *,
    db: Session = Depends(get_db),
    latitude: float,
    longitude: float,
    radius_km: float = 5.0 # Default radius of 5km
    # No authentication needed for this endpoint as per plan (can be added later if required)
    # current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve image submissions within a specified radius (in kilometers)
    of a given latitude and longitude. Filters out expired submissions.
    """
    try:
        submissions = crud_image_submission.get_nearby_submissions(
            db=db,
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km
        )
        return submissions
    except Exception as e:
        # Basic error handling for potential DB or GeoAlchemy errors
        print(f"Error fetching nearby submissions: {e}") # Log the error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not fetch nearby submissions.",
        )

@router.get("/{submission_id}", response_model=ImageSubmissionRead)
def get_submission(
    *,
    db: Session = Depends(get_db),
    submission_id: int,
    # Optional: Add authentication if needed to view specific submissions
    # current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get details of a specific image submission by ID.
    """
    submission = crud_image_submission.get_submission_by_id(db=db, submission_id=submission_id)
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    # Optional: Check if submission is expired and return 404 or different status?
    return submission


@router.put("/{submission_id}", response_model=ImageSubmissionRead)
def update_submission_endpoint(
    *,
    db: Session = Depends(get_db),
    submission_id: int,
    submission_in: ImageSubmissionUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update an image submission (e.g., description). Requires authentication.
    Only allowed within the first 10 minutes and by the owner.
    """
    db_submission = crud_image_submission.get_submission_by_id(db=db, submission_id=submission_id)
    if not db_submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    if db_submission.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this submission")

    updated_submission = crud_image_submission.update_submission(
        db=db, db_submission=db_submission, submission_in=submission_in
    )

    if updated_submission is None:
        # CRUD function returns None if update is disallowed (e.g., time limit exceeded)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Update time limit exceeded (10 minutes)."
        )

    return updated_submission


@router.delete("/{submission_id}", response_model=ImageSubmissionRead)
def delete_submission_endpoint(
    *,
    db: Session = Depends(get_db),
    submission_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Delete an image submission. Requires authentication.
    Only allowed by the owner.
    """
    db_submission = crud_image_submission.get_submission_by_id(db=db, submission_id=submission_id)
    if not db_submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    if db_submission.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this submission")

    # The CRUD function handles S3 deletion placeholder and DB deletion
    deleted_submission = crud_image_submission.delete_submission(db=db, submission_id=submission_id)

    if deleted_submission is None:
         # Should not happen if checks above pass, but good practice
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found during delete")

    # Return the details of the deleted object
    return deleted_submission


@router.post("/{submission_id}/thumbs_up", response_model=ImageSubmissionRead)
def thumbs_up_submission(
    *,
    db: Session = Depends(get_db),
    submission_id: int,
    # No authentication needed for now, but could add:
    # current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Add a thumbs up to a submission.
    """
    updated_submission = crud_image_submission.add_thumbs_up(db=db, submission_id=submission_id)
    if not updated_submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    return updated_submission


@router.post("/{submission_id}/thumbs_down", response_model=ImageSubmissionRead)
def thumbs_down_submission(
    *,
    db: Session = Depends(get_db),
    submission_id: int,
    # No authentication needed for now
) -> Any:
    """
    Add a thumbs down to a submission.
    """
    updated_submission = crud_image_submission.add_thumbs_down(db=db, submission_id=submission_id)
    if not updated_submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    return updated_submission