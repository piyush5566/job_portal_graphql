# Job Portal Web Application

A full-featured job portal web application built with Flask, allowing job seekers to find and apply for jobs, employers to post job listings, and administrators to manage the entire platform.

Live Deployment: https://jobportal-production-fcd5.up.railway.app

## Features

- **User Management**
  - Multiple user roles: Job Seekers, Employers, and Administrators
  - Secure authentication with password strength requirements
  - Profile management

- **Job Management**
  - Job posting with company logo support
  - Advanced job search functionality
  - Job applications with resume upload
  - Application status tracking

- **Admin Features**
  - User management
  - Job listing moderation
  - Application oversight
  - System monitoring

- **Additional Features**
  - Email notifications
  - Contact form
  - Secure file uploads (Local & GCS)
  - Role-based access control

## Technology Stack

- **Backend**: Python/Flask
- **Database**: SQLite (configurable for other databases)
- **ORM**: SQLAlchemy
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Security**: Flask-Talisman, CSRF protection
- **File Storage(Resume)**: Local storage with GCS support
- **Email**: Flask-Mail
- **Testing**: Pytest

## Prerequisites

- Python 3.8+
- Poetry (Python dependency management tool)

## Installation

1.  Clone the repository:
    ```bash
    git clone <repository-url>
    cd job_portal
    ```

2.  Install Poetry (if not already installed):
    ```bash
    # Windows PowerShell
    (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

    # Linux/macOS
    curl -sSL https://install.python-poetry.org | python3 -
    ```

3.  Install dependencies using Poetry:
    ```bash
    poetry install
    ```

4.  Activate the Poetry virtual environment:
    ```bash
    poetry shell
    ```

5.  Create a `.env` file in the project root based on `.env.example` (if provided) or the structure below:
    ```dotenv
    # Flask Core
    SECRET_KEY=your_very_strong_random_secret_key # Generate a strong key
    APP_ENV=development # or production, testing

    # Database
    SQLALCHEMY_DATABASE_URI=sqlite:///jobportal.db # Or your production DB URI
    SQLALCHEMY_TRACK_MODIFICATIONS=False

    # Email (Example using Gmail App Password)
    MAIL_SERVER=smtp.gmail.com
    MAIL_PORT=587
    MAIL_USE_TLS=True
    MAIL_USERNAME=your_email@gmail.com
    MAIL_PASSWORD=your_gmail_app_password # Use an App Password if 2FA is enabled
    MAIL_DEFAULT_SENDER=your_email@gmail.com
    CONTACT_EMAIL_RECIPIENT=your_contact_email@gmail.com # Where contact form messages go

    # Google Cloud Storage (Optional)
    GCS_BUCKET_NAME=your-gcs-bucket-name # Required if ENABLE_GCS_UPLOAD=True
    ENABLE_GCS_UPLOAD=False # Set to True to enable resume uploads to GCS
    # Ensure GOOGLE_APPLICATION_CREDENTIALS environment variable is set if using GCS
    ```
    **Note:** Ensure you replace placeholder values with your actual configuration. For production, use environment variables instead of a `.env` file for sensitive data.

5.  Initialize the database (if using Flask-Migrate):
    ```bash
    # flask db init # Run only once to initialize migrations
    flask db migrate -m "Initial migration" # Create migration script
    flask db upgrade # Apply migrations to the database
    ```
    If not using Flask-Migrate, the database tables might be created automatically when the app starts (check `app.py`).

## Running the Application

1.  **Development mode (using Flask's built-in server):**
    Ensure `APP_ENV` is set to `development` in your `.env` file or environment.
    ```bash
    # If you're already in the Poetry shell
    python run.py

    # Or using Poetry run without activating the shell
    poetry run python run.py
    ```
    The application will typically be available at `http://127.0.0.1:5000`. The Flask development server will auto-reload on code changes.

2.  **Production mode (using Gunicorn):**
    Ensure `APP_ENV` is set to `production`.
    * Run Gunicorn for the web application:
        ```bash
        # If you're already in the Poetry shell
        gunicorn --workers 4 --bind 0.0.0.0:5000 --timeout 120 --access-logfile - --error-logfile - "app:create_app()"

        # Or using Poetry run without activating the shell
        poetry run gunicorn --workers 4 --bind 0.0.0.0:5000 --timeout 120 --access-logfile - --error-logfile - "app:create_app()"
        ```
    Adjust `--workers` based on your server's CPU cores. The application will be available at `http://<your-server-ip>:5000`.

## Testing

The project uses `pytest` for running automated tests. The tests are located in the `tests/` directory.

1.  **Prerequisites:** Ensure you have installed all dependencies using `poetry install`, as testing libraries are included in the dev dependencies. Make sure your `.env` file or environment variables are configured appropriately for a testing environment (e.g., setting `APP_ENV=dev_testing` or `APP_ENV=prod_testing`). The test configuration often overrides some settings (like CSRF protection).

2.  **Running Tests:** Navigate to the project root directory in your terminal and run:
    ```bash
    # If you're already in the Poetry shell
    pytest

    # Or using Poetry run without activating the shell
    poetry run pytest

    # To run with coverage report
    poetry run pytest --cov=. --cov-report=term-missing
    ```
    Pytest will automatically discover and run the tests in the `tests/` directory.

## Project Structure

- `app.py`: Application factory (`create_app`) and core configuration.
- `run.py`: Script to run the development server.
- `models.py`: SQLAlchemy database models (e.g., `User`, `Job`, `Application`).
- `forms.py`: WTForms form definitions for user input and validation.
- `extensions.py`: Initialization of Flask extensions (like `db`, `mail`, `login_manager`).
- `config.py`: Configuration classes for different environments (Development, Production, Testing).
- `logging_config.py`: Configuration for application logging.
- `utils.py`: Utility functions or classes.
- `pyproject.toml`: Poetry configuration file with project metadata and dependencies.
- `.env` / `.env.example`: Environment variable configuration files.
- `instance/`: Instance folder, often contains SQLite database file.
- `static/`: Static files (CSS, JavaScript, images, uploaded files like logos).
- `templates/`: Jinja2 HTML templates.
- `tests/`: Automated tests (using pytest).
- `blueprints/`: Directory containing application modules (Blueprints).
  - `main/`: Core application routes (home, about, contact).
  - `auth/`: Authentication routes (login, register, logout).
  - `jobs/`: Job listing and application routes.
  - `job_seeker/`: Routes specific to job seekers (profile, applications).
  - `employer/`: Routes specific to employers (posting jobs, managing applications).
  - `admin/`: Administrator panel routes.
  - `utils/`: Utility routes (if any).
- `migrations/`: Database migration scripts (if using Flask-Migrate).

## Security Features

- Password hashing using Werkzeug's security helpers .
- CSRF protection via Flask-WTF.
- HTTP Security Headers via Flask-Talisman (including Content Security Policy - CSP).
- Secure session cookie configuration.
- File upload validation (checking extensions, potentially size limits).
- Role-based access control using Flask-Login or custom decorators.

## Logging

The application uses Python's built-in `logging` module, configured in `logging_config.py`. By default, it may log to:
- Console output.
- Files (e.g., `logs/job_portal.log`, `logs/errors.log` - check `logging_config.py` for specifics).
Log levels and handlers are configurable based on the environment (`APP_ENV`).


## Database Migrations

Database migrations are handled with Flask-Migrate:
```bash
# If you're already in the Poetry shell
# Create a new migration
flask db migrate -m "Migration message"

# Apply migrations
flask db upgrade

# Or using Poetry run without activating the shell
# Create a new migration
poetry run flask db migrate -m "Migration message"

# Apply migrations
poetry run flask db upgrade
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
