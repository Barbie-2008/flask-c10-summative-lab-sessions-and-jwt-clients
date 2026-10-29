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
flask-cors = "*"

[dev-packages]

[requires]
python_version = "3.12"
```

## Installation and database setup

From the project directory, install dependencies and apply the database migration:

```bash
pipenv install
pipenv run flask --app app db upgrade
```

If signup reports `no such table: users` even though `db upgrade` says the database is up to date, the migration record may exist without the tables. Only after confirming this is a local database with no application tables, reset its migration marker and apply the migration:

```bash
pipenv run flask --app app db stamp base
pipenv run flask --app app db upgrade
```

Optionally add sample accounts and workouts:

```bash
pipenv run python seed.py
```

The seeder is safe to rerun and only adds sample data that is missing. It creates two workouts for `test_user_one` and one for `test_user_two`. Both sample accounts use `password123`; use these credentials only in local development.

If you change the models in the future, create and apply a migration:

```bash
pipenv run flask --app app db migrate -m "Describe the schema change"
pipenv run flask --app app db upgrade
```

For deployment, set a private JWT signing secret using the `JWT_SECRET_KEY` environment variable. The development fallback in the app is not suitable for production.

## Run the API

Start the Flask development server on port `3000`:

```bash
pipenv run flask --app app run --port 3000
```

The API is available at `http://127.0.0.1:3000`. The root route (`GET /`) returns a status message; it is not a web interface.

Start the React client in a second terminal:

```bash
cd client-with-jwt
npm install
npm start
```

Open `http://localhost:4000`, then sign up or log in. The dashboard lists the logged-in user's workouts and supports adding, editing, and deleting them.

## API endpoints

All request and response bodies use JSON. Protected endpoints require the JWT returned by signup or login, sent as `Authorization: Bearer <JWT_TOKEN>`.

| Method | Endpoint | Authentication | Description |
| --- | --- | --- | --- |
| `GET` | `/` | Not required | Returns an API status message. |
| `POST` | `/signup` | Not required | Creates a user. Requires `username` and `password`; checks `password_confirmation` if provided. Returns the user and an access token. |
| `POST` | `/login` | Not required | Verifies `username` and `password`; returns the user and an access token. |
| `GET` | `/me` | JWT required | Returns the authenticated user's ID and username. |
| `GET` | `/workouts` | JWT required | Lists only the authenticated user's workouts. Accepts `page` (default `1`) and `per_page` (default `5`, maximum `100`). |
| `POST` | `/workouts` | JWT required | Creates a workout. Requires `exercise`, `duration_minutes`, `calories_burned`, and `date`. |
| `PATCH` | `/workouts/<id>` | JWT required | Partially updates the specified workout if it belongs to the authenticated user. |
| `DELETE` | `/workouts/<id>` | JWT required | Deletes the specified workout if it belongs to the authenticated user. |

Workout objects include `id`, `exercise`, `duration_minutes`, `calories_burned`, `date`, and `user_id`.

## Try the API with curl

Keep the API server running in one terminal. Run these commands in a second terminal from the project directory, in order, and keep using that same terminal so `BASE_URL` and `TOKEN` remain set.

Set the API address:

```bash
export BASE_URL=http://127.0.0.1:3000
```

Check that the API is responding:

```bash

curl "$BASE_URL/"
```

Create a local account. If it already exists, skip signup and log in:

```bash
curl -i -X POST "$BASE_URL/signup" \
  -H "Content-Type: application/json" \
  -d '{"username":"demo_user","password":"password123"}'
```

Log in and store the access token. If an authenticated request returns `401` because the token expired, run this login command again and retry the request:

```bash
export TOKEN=$(curl -sS -X POST "$BASE_URL/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"demo_user","password":"password123"}' \
  | pipenv run python -c 'import json, sys; print(json.load(sys.stdin)["access_token"])')
```

Check the current user and list workouts in readable JSON. The list only includes workouts owned by the account used to log in:

```bash
curl "$BASE_URL/me" \
  -H "Authorization: Bearer ${TOKEN}"

curl -sS "$BASE_URL/workouts" \
  -H "Authorization: Bearer ${TOKEN}" \
  | pipenv run python -m json.tool
```

If this returns one workout, it belongs to the account you logged in as. To view the two seeded workouts, log in as `test_user_one` instead (`test_user_two` has one seeded workout):

```bash
export TOKEN=$(curl -sS -X POST "$BASE_URL/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"test_user_one","password":"password123"}' \
  | pipenv run python -c 'import json, sys; print(json.load(sys.stdin)["access_token"])')
```

Create a workout. The response includes its ID:

```bash
curl -i -X POST "$BASE_URL/workouts" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"exercise":"Swimming","duration_minutes":40,"calories_burned":300,"date":"2026-10-29"}'
```

Fetch the workout list again to confirm it was added. To update a workout, replace `<WORKOUT_ID>` with its ID from the list:

```bash
curl -sS "$BASE_URL/workouts" \
  -H "Authorization: Bearer ${TOKEN}" \
  | pipenv run python -m json.tool

curl -i -X PATCH "$BASE_URL/workouts/<WORKOUT_ID>" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"duration_minutes":45}'
```

Delete a workout by ID if needed:

```bash
curl -i -X DELETE "$BASE_URL/workouts/<WORKOUT_ID>" \
  -H "Authorization: Bearer ${TOKEN}"
```

## Run the tests

From the project directory:

```bash
pipenv run pytest -q test_app.py
```
