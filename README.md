# LocalPhoto - Share Nearby Photos

LocalPhoto is a web application that allows users to submit photos tagged with their current location. Other users can then view photos submitted nearby on an interactive map.

## Features

*   **User Authentication:** Register, login via email/password or Google OAuth.
*   **Photo Submission:** Upload photos with descriptions, automatically tagged with the user's current location. Option to use device camera.
*   **Interactive Map:** View nearby photo submissions on a Leaflet map. Adjust search radius.
*   **User Profiles:** View user email, avatar, and manage profile settings (avatar URL, default map location, default search radius).
*   **Submission Management:** View own submissions on profile page, edit descriptions (within 10 mins), delete submissions.
*   **Voting:** Thumbs up/down on submissions displayed on the map.

## Tech Stack

**Backend:**

*   **Framework:** FastAPI
*   **Database:** PostgreSQL with PostGIS extension
*   **ORM:** SQLModel
*   **Geospatial:** GeoAlchemy2, Shapely
*   **Authentication:** JWT, Passlib (for passwords), Authlib (for Google OAuth)
*   **Migrations:** Alembic
*   **Dependencies:** `requirements.txt` (managed via pip)

**Frontend:**

*   **Structure:** Vanilla HTML, CSS, JavaScript (Single Page Application style)
*   **Mapping:** Leaflet.js
*   **Styling:** Bootstrap 5
*   **HTTP Client:** Axios
*   **Routing:** Simple hash-based routing (`main.js`)

**Infrastructure:**

*   **Image Storage:** AWS S3 (requires configuration)

## Setup

**Prerequisites:**

*   Python 3.10+
*   PostgreSQL database with PostGIS extension enabled.
*   AWS Account with S3 bucket and IAM credentials (for image uploads).
*   Google Cloud Platform project with OAuth 2.0 credentials (for Google login).

**1. Clone the Repository:**

```bash
git clone <your-repository-url>
cd localphoto
```

**2. Backend Setup:**

*   **Create & Activate Virtual Environment:**
    ```bash
    python -m venv hm_venv
    source hm_venv/bin/activate # On Windows use `hm_venv\Scripts\activate`
    ```
*   **Install Dependencies:**
    ```bash
    pip install -r backend/requirements.txt
    ```
*   **Configure Environment Variables:**
    *   Copy `backend/.env.example` (if it exists) or create `backend/.env`.
    *   Fill in the required values (see `.env` section below).
*   **Database Setup:**
    *   Ensure your PostgreSQL server is running.
    *   Create a database (e.g., `localphoto_db`).
    *   Enable the PostGIS extension: `CREATE EXTENSION postgis;` (run this command connected to your *newly created database*).
    *   Update the `DATABASE_URL` in `backend/.env`.
*   **Run Database Migrations:**
    ```bash
    cd backend
    alembic upgrade head
    cd ..
    ```

**3. Frontend Setup:**

*   No build step required for the current vanilla JS setup. Files are served directly.

## Running the Application

**1. Start the Backend Server:**

*   Navigate to the `backend` directory:
    ```bash
    cd backend
    ```
*   Run the Uvicorn server (ensure your virtual environment is active):
    ```bash
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```
    The backend API will be available at `http://localhost:8000`.

**2. Serve the Frontend:**

*   You need a simple HTTP server to serve the `frontend` directory.
*   **Using Python's built-in server (for development):**
    *   Navigate to the project root directory (`localphoto`).
    *   Run the server (ensure your virtual environment is active or Python is in your PATH):
        ```bash
        python -m http.server 8080 --directory frontend
        ```
*   Access the application in your browser at `http://localhost:8080`.

## Environment Variables (`backend/.env`)

Create a `.env` file in the `backend` directory with the following variables:

```dotenv
# PostgreSQL Database URL
# Example: postgresql://user:password@host:port/database_name
DATABASE_URL=postgresql://localphoto_user:your_password@localhost:5432/localphoto_db

# JWT Settings
JWT_SECRET=your_very_strong_jwt_secret # CHANGE THIS! Generate a strong random key
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Google OAuth Settings
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret
# Ensure this matches the redirect URI configured in Google Cloud Console AND the backend code
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback

# Session Middleware Secret Key
SESSION_SECRET_KEY=your_very_strong_session_secret # CHANGE THIS! Generate a strong random key

# Frontend URL (for redirects, e.g., after Google login)
FRONTEND_URL=http://localhost:8080

# AWS S3 Settings
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
S3_BUCKET_NAME=your_unique_s3_bucket_name
AWS_REGION=your_aws_region # e.g., us-east-1
```

**Important:** Never commit your `.env` file to version control. Add it to your `.gitignore` file.

## Database Migrations (Alembic)

Alembic is used to manage database schema changes.

*   **Apply Migrations:** `cd backend && alembic upgrade head`
*   **Create a New Migration:** `cd backend && alembic revision --autogenerate -m "Your migration message"` (Run this after changing SQLModel models in `backend/app/models/`)
*   **Check Migration Status:** `cd backend && alembic current`

## API

The API documentation (Swagger UI) is automatically generated by FastAPI and available at `http://localhost:8000/docs` when the backend server is running.

Key endpoint prefixes:

*   `/api/v1/auth/`: Login, registration, Google OAuth flow.
*   `/api/v1/users/`: User profile operations.
*   `/api/v1/submissions/`: Creating submissions, fetching nearby, voting.

## TODO / Future Enhancements

*   Implement proper JWT verification in API dependencies (replace placeholder `get_current_active_user`).
*   Add password reset functionality.
*   Implement user roles/permissions if needed.
*   Refine S3 error handling (e.g., delete S3 object if DB save fails).
*   Consider using CloudFront for S3 image delivery.
*   Add pagination for submission lists.
*   Improve UI/UX.
*   Write more comprehensive tests.
*   Implement background tasks (e.g., locking submissions after 10 mins).