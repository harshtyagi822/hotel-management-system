# Hotel Management Backend

Flask + MySQL (SQLAlchemy ORM) backend for the Hotel Management System.

## Quick Start (Local Development)

1. Create environment:
   - Copy `./.env.example` to `./.env`.
   - Update secrets and MySQL connection details.

2. Install dependencies:
   - `pip install -r requirements.txt`

3. Run backend:
   - `python app.py`

Health check:
- `GET /api/health`

## Environment Variables

See `./.env.example`.

Key variables:
- `SECRET_KEY`
- `JWT_SECRET_KEY`
- `FRONTEND_URL`
- `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`

JWT:
- `JWT_ACCESS_TOKEN_EXPIRES_MINUTES` (default: 20)
- `JWT_REFRESH_TOKEN_EXPIRES_DAYS` (default: 7)

## Database Setup

This project uses Flask-Migrate (Alembic). Ensure MySQL is reachable using the values from `.env`.

## Authentication

- Register: `POST /api/auth/register`
- Login: `POST /api/auth/login`
- Refresh access token: `POST /api/auth/refresh`
- Profile: `GET /api/auth/profile`

## Deployment

Production uses Gunicorn + Docker.

- `Dockerfile`
- `docker-compose.yml`
- `gunicorn.conf.py`

## API Documentation

- `API_DOCUMENTATION.md`

