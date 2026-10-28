# Workout Tracker API

A Flask REST API for registering users, authenticating with JSON Web Tokens (JWT), and managing each user's workouts. User passwords are stored as bcrypt hashes. Workout list results support pagination, and workout updates and deletes enforce ownership.

## Requirements

- Python 3.12
- Pipenv

The project dependencies are declared in `Pipfile`:

```toml
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]
flask = "*"
flask-sqlalchemy = "*"
flask-migrate = "*"
flask-restful = "*"
flask-bcrypt = "*"
flask-jwt-extended = "*"
pytest = "*"

[dev-packages]

[requires]
python_version = "3.12"
```

## Installation and database setup

From the project directory:

```bash
pipenv install
```

Apply the existing database migration to create the tables:

```bash
pipenv run flask --app app db upgrade
```

If you change the models in the future, generate a new migration and apply it:

```bash
pipenv run flask --app app db migrate -m "Describe the schema change"
pipenv run flask --app app db upgrade
```

Optionally populate the database with sample users and workouts after applying migrations:

```bash
pipenv run python seed.py
```

The seeder is safe to rerun: it adds sample users and workouts only when they are missing and preserves existing records. Both sample accounts use the password `password123`; use these credentials only in local development.

For local development, the app falls back to a development-only JWT secret. Set a private secret through the `JWT_SECRET_KEY` environment variable before deploying:

```bash
export JWT_SECRET_KEY="$(pipenv run python -c 'import secrets; print(secrets.token_hex(32))')"
```

## Run the API

Start the Flask development server on port `5555`:

```bash
pipenv run flask --app app run --port 5555
```

The API is then available at `http://127.0.0.1:5555`.

The root URL (`GET /`) returns a short API status message. It does not provide a web interface.

## API endpoints

All request and response bodies use JSON. For protected endpoints, send the token returned by `POST /login` in the `Authorization` header:

```text
Authorization: Bearer <access_token>
```

| Method | Endpoint | Authentication | Description |
| --- | --- | --- | --- |
| `GET` | `/` | Not required | Returns an API status message. |
| `POST` | `/signup` | Not required | Creates a user. Requires `username` and `password` (and checks `password_confirmation` when provided); returns the public user, `token`, and `access_token`. |
| `POST` | `/login` | Not required | Verifies `username` and `password`; returns the public user, `token`, and `access_token`. |
| `GET` | `/me` | JWT required | Returns the authenticated user's `id` and `username`. |
| `GET` | `/workouts` | JWT required | Lists only the authenticated user's workouts. Accepts `page` (default `1`) and `per_page` (default `5`) query parameters; returns workouts and pagination metadata. |
| `POST` | `/workouts` | JWT required | Creates a workout for the authenticated user. Requires `exercise`, `duration_minutes`, `calories_burned`, and `date`. |
| `PATCH` | `/workouts/<id>` | JWT required | Partially updates the specified workout if it belongs to the authenticated user. |
| `DELETE` | `/workouts/<id>` | JWT required | Deletes the specified workout if it belongs to the authenticated user. |

Workout objects include `id`, `exercise`, `duration_minutes`, `calories_burned`, `date`, and `user_id`. The date is stored as a string (for example, `"2026-10-01"`).
