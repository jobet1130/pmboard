# PMBoard - Project Management Board API

[![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![DjangoREST](https://img.shields.io/badge/DJANGO-REST-ff1709?style=for-the-badge&logo=django&logoColor=white&color=ff1709&labelColor=gray)](https://www.django-rest-framework.org/)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

## 📋 Overview

PMBoard is a robust, scalable, and secure REST API built with Django 4.x and Django REST Framework, designed to power modern project management applications. This API provides a comprehensive suite of features that enable teams to collaborate effectively, track progress, and deliver projects successfully.

## 🚀 Key Features

### Project Management

- Create and manage multiple projects with customizable workflows
- Role-based access control (RBAC) for team members
- Project categorization and tagging for better organization
- Activity tracking and audit logs

### Agile Boards

- Customizable Kanban-style boards
- Swimlanes for better task organization
- Drag-and-drop interface (handled by frontend)
- Multiple board views (list, board, calendar)

### Task Management

- Hierarchical task structure with parent-child relationships
- Custom task statuses and priorities
- Task assignment and due dates
- File attachments and comments
- Task dependencies and relationships

### Time Tracking

- Built-in time tracking for tasks
- Timesheet reporting
- Billable hours tracking
- Integration with popular time tracking tools

### Real-time Notifications

- In-app notifications
- Email alerts
- Webhook support for third-party integrations
- Custom notification preferences

### Analytics & Reporting

- Project progress tracking
- Team performance metrics
- Burndown charts
- Custom report generation
- Export to multiple formats (CSV, PDF, Excel)

## 🏗️ Technical Architecture

### Core Technologies

- **Backend**: Django 4.x & Django REST Framework
- **Database**: PostgreSQL (with SQLite for development)
- **Authentication**: JWT with refresh tokens
- **Caching**: Redis
- **Asynchronous Tasks**: Celery with Redis as broker
- **API Documentation**: DRF Spectacular (OpenAPI 3.0)

### API Features

- RESTful API design
- Comprehensive API documentation with Swagger/ReDoc
- Rate limiting and throttling
- Bulk operations support
- Filtering, sorting, and pagination
- Versioned API endpoints

## ⚙️ Environment Variables

Below are the required and optional environment variables for the project. Copy `.env.example` to `.env` and update the values accordingly.

### Django Core

```env
# Required
SECRET_KEY=your-secret-key-here
DEBUG=True  # Set to False in production
ALLOWED_HOSTS=localhost,127.0.0.1,::1

# Optional
TIME_ZONE=UTC
LANGUAGE_CODE=en-us
```

### Authentication

```env
# JWT Authentication
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ACCESS_TOKEN_LIFETIME=900  # 15 minutes in seconds
JWT_REFRESH_TOKEN_LIFETIME=86400  # 1 day in seconds
```

### Database (PostgreSQL)

```env
# PostgreSQL
DB_ENGINE=django.db.backends.postgresql
DB_NAME=pmboard
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db  # or localhost for non-Docker setup
DB_PORT=5432

# Or use DATABASE_URL format (takes precedence if set)
# DATABASE_URL=postgresql://user:password@localhost:5432/pmboard
```

For SQLite (development only):

```env
DATABASE_URL=sqlite:///db.sqlite3
```

### Email Settings

```env
# SMTP Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password
DEFAULT_FROM_EMAIL='"PMBoard" <noreply@yourdomain.com>'
```

For development, you can use the console backend:

```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### Caching (Redis)

```env
REDIS_URL=redis://redis:6379/0
CACHE_URL=redis://redis:6379/1
```

### Celery

```env
# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/1
CELERY_ACCEPT_CONTENT=json
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_TIMEZONE=UTC
```

### Frontend URLs (for CORS/Email Templates)

```env
FRONTEND_URL=http://localhost:3000
API_URL=http://localhost:8000/api/
```

### File Storage

```env
# For local development
DEFAULT_FILE_STORAGE=django.core.files.storage.FileSystemStorage
MEDIA_URL=/media/
MEDIA_ROOT=/app/media/

# For production (example with AWS S3)
# DEFAULT_FILE_STORAGE=storages.backends.s3boto3.S3Boto3Storage
# AWS_ACCESS_KEY_ID=your-access-key
# AWS_SECRET_ACCESS_KEY=your-secret-key
# AWS_STORAGE_BUCKET_NAME=your-bucket-name
# AWS_S3_REGION_NAME=us-east-1
```

### Security

```env
# Set these in production
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https')

# Optional security settings
SECURE_HSTS_SECONDS=31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

### Third-party Integrations

```env
# Sentry (Error Tracking)
SENTRY_DSN=your-sentry-dsn

# Google OAuth (if implemented)
# GOOGLE_OAUTH2_CLIENT_ID=your-client-id
# GOOGLE_OAUTH2_CLIENT_SECRET=your-client-secret

# Stripe (for payments if applicable)
# STRIPE_SECRET_KEY=your-stripe-secret-key
# STRIPE_WEBHOOK_SECRET=your-webhook-secret
```

## 🛠️ Prerequisites

- Python 3.12+
- Docker and Docker Compose (optional)
- PostgreSQL (for production) or SQLite (for development)
- Redis (for caching and Celery)

## 🚀 Getting Started

### Prerequisites

- Python 3.12 or higher
- pip (Python package manager)
- Git
- PostgreSQL (for production) or SQLite (for development)
- Redis (for caching and Celery tasks)

### Local Development Setup

#### 1. Clone the Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/pmboard.git

# Navigate to project directory
cd pmboard
```

#### 2. Set Up Python Environment

```bash
# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# On Windows:
.\.venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Upgrade pip and setuptools
pip install --upgrade pip setuptools
```

#### 3. Install Dependencies

```bash
# Install production dependencies
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

#### 4. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your configuration
# You'll need to set at minimum:
# - SECRET_KEY
# - DATABASE_URL
# - DEBUG (True for development)
```

#### 5. Database Setup

```bash
# Run database migrations
python manage.py migrate

# Create a superuser (follow prompts)
python manage.py createsuperuser
```

#### 6. Start the Development Server

```bash
# Run the development server
python manage.py runserver
```

The application will be available at http://127.0.0.1:8000/

#### 7. (Optional) Start Celery Worker

In a new terminal window:

```bash
# Activate the virtual environment if not already activated
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Start Celery worker
celery -A config worker -l info
```

#### 8. (Optional) Start Celery Beat

In another terminal window (for scheduled tasks):

```bash
# Activate the virtual environment if not already activated
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Start Celery beat
celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=.

# Run a specific test file
pytest path/to/test_file.py

# Run a specific test case
pytest path/to/test_file.py::TestClass::test_method
```

### Accessing the Application

- API Root: http://localhost:8000/api/
- Admin Interface: http://localhost:8000/admin/
- API Documentation (Swagger UI): http://localhost:8000/api/schema/swagger-ui/
- API Documentation (ReDoc): http://localhost:8000/api/schema/redoc/

## 🐳 Docker Setup

This project includes Docker configuration for easy development and deployment. Below are instructions for running the project with Docker.

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- (Optional) Make utility (for convenience commands)

### Quick Start with Docker Compose

```bash
# Build and start all services
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Database Configuration

#### Option 1: SQLite (Development)

By default, the project uses SQLite for development. The database file will be stored in a Docker volume.

```yaml
# docker-compose.override.yml (create this file if it doesn't exist)
version: '3.9'

services:
  web:
    environment:
      - DATABASE_URL=sqlite:///db/sqlite3.db
    volumes:
      - sqlite_data:/app/db

volumes:
  sqlite_data:
```

#### Option 2: PostgreSQL (Production)

For production, it's recommended to use PostgreSQL. Uncomment the PostgreSQL service in `docker-compose.yml` and update the environment variables:

```yaml
# docker-compose.override.yml
version: '3.9'

services:
  web:
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/pmboard
    depends_on:
      - db

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=pmboard
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

### Running Migrations

```bash
# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

### Managing Containers

```bash
# Build images
docker-compose build

# Start services in detached mode
docker-compose up -d

# View running containers
docker-compose ps

# View logs for a service
docker-compose logs -f web

# Run a command in a running container
docker-compose exec web python manage.py shell

# Stop all services
docker-compose down

# Stop and remove all containers, networks, and volumes
docker-compose down -v
```

### Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Django
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite example)
DATABASE_URL=sqlite:///db/sqlite3.db

# Redis
REDIS_URL=redis://redis:6379/0

# Celery
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/1
```

### Accessing Services

- Django application: http://localhost:8000
- Admin interface: http://localhost:8000/admin
- API Documentation: http://localhost:8000/api/schema/swagger-ui/
- PostgreSQL (if enabled):
   - Host: localhost
   - Port: 5432
   - Database: pmboard
   - Username: postgres
   - Password: postgres

### Production Considerations

1. Set `DEBUG=False` in production
2. Use a proper database backup strategy
3. Configure proper logging
4. Set up proper SSL/TLS termination
5. Use environment variables for all secrets
6. Consider using a production-ready web server like Gunicorn or uWSGI

## 🧪 Testing

This project uses `pytest` for testing, which provides a more powerful and flexible testing framework than Django's built-in test runner.

### Prerequisites

Make sure you have the development dependencies installed:

```bash
pip install -e ".[dev]"
```

### Running Tests

#### Run All Tests

```bash
# Using pytest directly
pytest

# Run tests in parallel (faster for large test suites)
pytest -n auto

# Run tests with detailed output
pytest -v
```

#### Run Specific Tests

```bash
# Run tests in a specific file
pytest tests/test_models.py

# Run a specific test class
pytest tests/test_views.py::TestProjectViews

# Run a specific test method
pytest tests/test_models.py::TestProjectModel::test_project_creation
```

#### Run Tests by Marker

Tests can be marked (e.g., `@pytest.mark.unit`, `@pytest.mark.integration`):

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run all tests except integration tests
pytest -m "not integration"
```

### Test Coverage

Generate a coverage report:

```bash
# Basic coverage report
pytest --cov=.

# Generate HTML report
pytest --cov=. --cov-report=html

# Fail if coverage is below threshold (e.g., 80%)
pytest --cov=. --cov-fail-under=80

# Generate XML report (for CI/CD integration)
pytest --cov=. --cov-report=xml
```

### Test Database

- Tests run in a separate test database by default
- The test database is created and destroyed automatically
- Use fixtures to set up test data

### Running Tests in Docker

```bash
# Run all tests in the web container
docker-compose exec web pytest

# Run tests with coverage in the web container
docker-compose exec web pytest --cov=.
```

### Continuous Integration (CI) Setup

Example `.github/workflows/test.yml` for GitHub Actions:

```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_pmboard
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_pmboard
        REDIS_URL: redis://localhost:6379/0
        CELERY_BROKER_URL: redis://localhost:6379/1
        SECRET_KEY: test-secret-key
      run: |
        pytest --cov=. --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: false
```

### Writing Tests

Example test file structure:

```python
# tests/test_models.py
import pytest
from django.test import TestCase
from myapp.models import Project

class TestProjectModel(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up data for the whole TestCase
        cls.project = Project.objects.create(
            name="Test Project",
            description="Test Description"
        )

    def test_project_creation(self):
        self.assertEqual(self.project.name, "Test Project")
        self.assertEqual(str(self.project), "Test Project")

# Example of a pytest fixture
@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()

# Example of an API test
@pytest.mark.django_db
def test_project_api(api_client):
    response = api_client.get('/api/projects/')
    assert response.status_code == 200
    assert len(response.data) == 1
```

### Testing Best Practices

1. Keep tests fast and independent
2. Use fixtures for common test data
3. Test both success and error cases
4. Use meaningful test names
5. Mock external services
6. Aim for high test coverage (80%+)
7. Run tests in CI/CD pipeline

## 📚 API Reference

Below is a list of the main API endpoints. For interactive documentation, visit:

- Swagger UI: `/api/schema/swagger-ui/`
- ReDoc: `/api/schema/redoc/`

### Authentication

```sh
POST /api/auth/token/           # Obtain JWT token
POST /api/auth/token/refresh/   # Refresh JWT token
POST /api/auth/register/        # Register new user
```

### Projects

```ini
GET    /api/projects/                  # List all projects
POST   /api/projects/                  # Create new project
GET    /api/projects/{id}/             # Get project details
PUT    /api/projects/{id}/             # Update project
PATCH  /api/projects/{id}/             # Partial update
DELETE /api/projects/{id}/             # Delete project
GET    /api/projects/{id}/members/     # List project members
POST   /api/projects/{id}/members/     # Add member to project
DELETE /api/projects/{id}/members/{user_id}/  # Remove member
```

### Boards

```sh
GET    /api/boards/                    # List all boards
POST   /api/boards/                    # Create new board
GET    /api/boards/{id}/               # Get board details
PUT    /api/boards/{id}/               # Update board
PATCH  /api/boards/{id}/columns/order/ # Reorder columns
DELETE /api/boards/{id}/               # Delete board
```

### Columns

```sh
GET    /api/boards/{board_id}/columns/       # List columns
POST   /api/boards/{board_id}/columns/       # Create column
GET    /api/columns/{id}/                    # Get column details
PUT    /api/columns/{id}/                    # Update column
PATCH  /api/columns/{id}/tasks/order/        # Reorder tasks in column
DELETE /api/columns/{id}/                    # Delete column
```

### Tasks

```md
GET    /api/tasks/                          # List all tasks (with filters)
POST   /api/tasks/                          # Create new task
GET    /api/tasks/{id}/                     # Get task details
PUT    /api/tasks/{id}/                     # Update task
PATCH  /api/tasks/{id}/status/              # Update task status
PATCH  /api/tasks/{id}/assign/              # Assign task
DELETE /api/tasks/{id}/                     # Delete task
POST   /api/tasks/{id}/attachments/         # Add attachment
GET    /api/tasks/{id}/comments/            # List comments
POST   /api/tasks/{id}/comments/            # Add comment
```

### Time Tracking (WorkLogs)

```md
GET    /api/worklogs/                      # List worklogs (with filters)
POST   /api/worklogs/                      # Create worklog entry
GET    /api/worklogs/{id}/                 # Get worklog details
PUT    /api/worklogs/{id}/                 # Update worklog
DELETE /api/worklogs/{id}/                 # Delete worklog
GET    /api/tasks/{id}/worklogs/           # Get worklogs for a task
GET    /api/users/me/worklogs/             # Get current user's worklogs
```

### Analytics

```sh
GET /api/analytics/timesheet/             # Timesheet reports
GET /api/analytics/burndown/{sprint_id}/  # Burndown chart data
GET /api/analytics/velocity/              # Team velocity metrics
GET /api/analytics/workload/              # Team workload distribution
```

### Notifications

```sh
GET    /api/notifications/                 # List notifications
GET    /api/notifications/unread/count/   # Count unread notifications
PATCH  /api/notifications/mark-as-read/   # Mark as read
DELETE /api/notifications/{id}/           # Delete notification
```

### User Management

```sh
GET    /api/users/me/                     # Current user profile
PATCH  /api/users/me/                     # Update profile
GET    /api/users/                        # List users (admin only)
POST   /api/users/                        # Create user (admin only)
GET    /api/users/{id}/                   # User details
PUT    /api/users/{id}/                   # Update user (admin/self)
```

## Example Requests

### Create a Project

```http
POST /api/projects/
Content-Type: application/json
Authorization: Bearer {token}

{
    "name": "New Product Launch",
    "description": "Launching our new product line",
    "start_date": "2025-10-01",
    "end_date": "2025-12-31"
}
```

### Log Work Time

```http
POST /api/worklogs/
Content-Type: application/json
Authorization: Bearer {token}

{
    "task": 42,
    "start_time": "2025-09-21T09:00:00Z",
    "end_time": "2025-09-21T11:30:00Z",
    "description": "Implemented user authentication"
}
```

### Get Timesheet Report

```http
GET /api/analytics/timesheet/?start_date=2025-09-01&end_date=2025-09-30&user_id=1
Authorization: Bearer {token}
```

## 👥 Contributing

We welcome contributions from the community! Here's how you can help improve PMBoard:

### Prerequisites

- Python 3.12+
- Git
- Poetry (for dependency management)

### Getting Started

1. **Fork the Repository**

- Click the 'Fork' button on the GitHub repository

- Clone your forked repository:

```bash
git clone https://github.com/jobet1130/pmboard.git
cd pmboard
```

2. **Set Up Development Environment**

```bash
# Install dependencies
poetry install --with dev

# Activate virtual environment
poetry shell

# Install pre-commit hooks
pre-commit install
```

3. **Create a Feature Branch**

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

### Code Style and Quality

We use several tools to maintain code quality:

- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for static type checking

These are automatically checked by pre-commit hooks. You can also run them manually:

```bash
# Format code
black .

# Sort imports
isort .

# Run linter
flake8

# Run type checking
mypy .
```

### Development Workflow

1. **Sync with Upstream**

```bash
git remote add upstream https://github.com/original-owner/pmboard.git
git fetch upstream
git merge upstream/main
```

2. **Make Your Changes**

   - Follow the existing code style
   - Write clear, concise commit messages
   - Keep commits focused on a single feature/fix

3. **Run Tests**

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=.
```

4. **Commit Your Changes**

```bash
# Stage changes
git add .

# Commit with a descriptive message
git commit -m "feat: add new project creation endpoint"

# Push to your fork
git push origin your-branch-name
```

### Pull Request Guidelines

1. **Create a Pull Request**

   - Go to your fork on GitHub
   - Click 'New Pull Request'
   - Select the base branch (usually `main`)
   - Fill in the PR template

2. **PR Requirements**

   - Reference any related issues
   - Include tests for new features
   - Update documentation if needed
   - Ensure all tests pass
   - Keep the PR focused on a single feature/fix

3. **Code Review**

   - Address any review comments
   - Push updates to the same branch
   - The PR will be merged once approved

### Commit Message Format

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```ini
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types:

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code changes that neither fix bugs nor add features
- `perf`: Performance improvements
- `test`: Adding or modifying tests
- `chore`: Maintenance tasks

Example:

```md
feat(projects): add project archiving functionality

- Add is_archived field to Project model
- Add archive/unarchive endpoints
- Include tests for archiving functionality

Closes #123
```

### Reporting Issues

Found a bug or have a feature request? Please:

1. Check existing issues to avoid duplicates
2. Create a new issue with a clear description
3. Include steps to reproduce (for bugs)
4. Add screenshots if applicable

### Code of Conduct

Please note that this project is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

### Getting Help

If you need help or have questions:

- Check the project's GitHub Discussions
- Join our community chat (if available)
- Open an issue for specific problems

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with ❤️ using Django and Django REST Framework
- Inspired by popular project management tools like Jira, Trello, and Asana