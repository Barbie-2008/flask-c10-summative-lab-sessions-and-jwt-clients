import runpy

import pytest
from app import app, db
from models import User, Workout

@pytest.fixture
def app_client():
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True
    app.config['JWT_SECRET_KEY'] = 'test_secret_key_that_is_at_least_32_bytes'

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()


def _login(client, username):
    client.post('/signup', json={
        'username': username,
        'password': 'password123'
    })
    response = client.post('/login', json={
        'username': username,
        'password': 'password123'
    })
    return {'Authorization': f"Bearer {response.get_json()['access_token']}"}


def test_signup_and_model_protection(app_client):
    # Test user signup
    response = app_client.post('/signup', json={
        'username': 'test_user',
        'password': 'securepassword123'
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data['username'] == 'test_user'
    assert 'id' in data
    assert data['token'] == data['access_token']
    assert data['user']['username'] == 'test_user'
    assert app_client.get(
        '/me', headers={'Authorization': f"Bearer {data['token']}"}
    ).get_json()['username'] == 'test_user'
    user = User.query.filter_by(username='test_user').first()
    assert user.password_hash != 'securepassword123'
    assert user.authenticate('securepassword123')

    #test duplicate signup
    duplicate_res = app_client.post('/signup', json={
        'username': 'test_user',
        'password': 'anotherpassword'
    })
    assert duplicate_res.status_code == 422
    assert duplicate_res.get_json()['errors']

def test_login_endpoint(app_client):
    """Tests Login with correct and incorrect credentials (Rubric: Auth Login)"""
    app_client.post('/signup', json={
        'username': 'login_user',
        'password': 'mypassword'
    })

    # Successful login
    login_res = app_client.post('/login', json={
        'username': 'login_user',
        'password': 'mypassword'
    })
    assert login_res.status_code == 200
    token_data = login_res.get_json()
    assert 'access_token' in token_data
    assert token_data['token'] == token_data['access_token']
    assert token_data['user']['username'] == 'login_user'

    # Failed login (wrong password)
    bad_login = app_client.post('/login', json={
        'username': 'login_user',
        'password': 'wrongpassword'
    })
    assert bad_login.status_code == 401


def test_check_session_me_endpoint(app_client):
    """Tests the /me endpoint to keep users logged in (Rubric: Check Session / Me)"""
    app_client.post('/signup', json={
        'username': 'session_user',
        'password': 'password123'
    })
    login_res = app_client.post('/login', json={
        'username': 'session_user',
        'password': 'password123'
    })
    token = login_res.get_json()['access_token']

    # Access /me with JWT header
    headers = {'Authorization': f'Bearer {token}'}
    me_res = app_client.get('/me', headers=headers)
    assert me_res.status_code == 200
    assert me_res.get_json()['username'] == 'session_user'


def test_workout_crud_and_pagination(app_client):
    """Tests Workout CRUD operations and pagination (Rubric: Additional Resource & CRUD/Pagination)"""
    app_client.post('/signup', json={'username': 'gym_user', 'password': 'password123'})
    token = app_client.post('/login', json={'username': 'gym_user', 'password': 'password123'}).get_json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    # 1. CREATE Workout (POST)
    post_res = app_client.post('/workouts', headers=headers, json={
        'exercise': 'Weightlifting',
        'duration_minutes': 45,
        'calories_burned': 320,
        'date': '2026-10-05'
    })
    assert post_res.status_code == 201
    workout_id = post_res.get_json()['id']

    # 2. READ Workouts with Pagination (GET)
    get_res = app_client.get('/workouts?page=1&per_page=5', headers=headers)
    assert get_res.status_code == 200
    data = get_res.get_json()
    assert 'workouts' in data
    assert 'total' in data
    assert len(data['workouts']) == 1
    assert data['workouts'][0]['exercise'] == 'Weightlifting'

    # 3. UPDATE Workout (PATCH)
    patch_res = app_client.patch(f'/workouts/{workout_id}', headers=headers, json={
        'duration_minutes': 60
    })
    assert patch_res.status_code == 200
    assert patch_res.get_json()['duration_minutes'] == 60

    # 4. DELETE Workout (DELETE)
    del_res = app_client.delete(f'/workouts/{workout_id}', headers=headers)
    assert del_res.status_code == 204


def test_protected_routes_and_data_isolation(app_client):
    """Tests route security and data isolation between users (Rubric: Protected Routes)"""
    # Create User 1 and a workout
    app_client.post('/signup', json={'username': 'user_one', 'password': 'password123'})
    token1 = app_client.post('/login', json={'username': 'user_one', 'password': 'password123'}).get_json()['access_token']
    
    w_res = app_client.post('/workouts', headers={'Authorization': f'Bearer {token1}'}, json={
        'exercise': 'Running', 'duration_minutes': 30, 'calories_burned': 250, 'date': '2026-10-06'
    })
    workout_id = w_res.get_json()['id']

    # Create User 2
    app_client.post('/signup', json={'username': 'user_two', 'password': 'password123'})
    token2 = app_client.post('/login', json={'username': 'user_two', 'password': 'password123'}).get_json()['access_token']

    # Test unauthorized access without token
    no_auth_res = app_client.get('/workouts')
    assert no_auth_res.status_code == 401

    # Test cross-user modification (User 2 tries to update User 1's workout -> must return 403 Forbidden)
    forbidden_res = app_client.patch(f'/workouts/{workout_id}', headers={'Authorization': f'Bearer {token2}'}, json={
        'exercise': 'Hacked Run'
    })
    assert forbidden_res.status_code == 403 


def test_root_and_invalid_auth_payloads(app_client):
    root_res = app_client.get('/')
    assert root_res.status_code == 200
    assert root_res.get_json()['message'] == 'Workout Tracker API'

    invalid_signup = app_client.post(
        '/signup', data='not json', content_type='application/json'
    )
    assert invalid_signup.status_code == 400

    invalid_login = app_client.post(
        '/login', data='not json', content_type='application/json'
    )
    assert invalid_login.status_code == 400


def test_all_protected_routes_require_authentication(app_client):
    protected_requests = (
        ('get', '/me'),
        ('get', '/workouts'),
        ('post', '/workouts'),
        ('patch', '/workouts/1'),
        ('delete', '/workouts/1'),
    )
    for method, path in protected_requests:
        response = getattr(app_client, method)(path, json={})
        assert response.status_code == 401, f'{method.upper()} {path}'


def test_workout_validation_pagination_and_ownership(app_client):
    owner_headers = _login(app_client, 'workout_owner')
    other_headers = _login(app_client, 'workout_other')
    workout_data = {
        'exercise': 'Running',
        'duration_minutes': 30,
        'calories_burned': 250,
        'date': '2026-10-06',
    }

    invalid_create = app_client.post(
        '/workouts', headers=owner_headers, json={'exercise': 'Running'}
    )
    assert invalid_create.status_code == 400

    created = app_client.post(
        '/workouts', headers=owner_headers, json=workout_data
    )
    assert created.status_code == 201
    workout_id = created.get_json()['id']

    invalid_page = app_client.get(
        '/workouts?page=zero', headers=owner_headers
    )
    assert invalid_page.status_code == 400
    invalid_page_size = app_client.get(
        '/workouts?per_page=101', headers=owner_headers
    )
    assert invalid_page_size.status_code == 400

    ownership_change = app_client.patch(
        f'/workouts/{workout_id}',
        headers=owner_headers,
        json={'user_id': 2},
    )
    assert ownership_change.status_code == 400
    assert db.session.get(Workout, workout_id).user_id == created.get_json()['user_id']

    invalid_update = app_client.patch(
        f'/workouts/{workout_id}',
        headers=owner_headers,
        json={'duration_minutes': -1},
    )
    assert invalid_update.status_code == 400

    forbidden_delete = app_client.delete(
        f'/workouts/{workout_id}', headers=other_headers
    )
    assert forbidden_delete.status_code == 403
    other_users_workouts = app_client.get(
        '/workouts', headers=other_headers
    ).get_json()
    assert other_users_workouts['total'] == 0


def test_seed_is_idempotent_and_preserves_existing_data(app_client):
    existing_user = User(username='keep_me')
    existing_user.password = 'password123'
    db.session.add(existing_user)
    db.session.commit()
    existing_workout = Workout(
        exercise='Existing Workout',
        duration_minutes=20,
        calories_burned=100,
        date='2026-10-07',
        user_id=existing_user.id,
    )
    db.session.add(existing_workout)
    db.session.commit()

    runpy.run_path('seed.py')
    assert User.query.filter_by(username='keep_me').count() == 1
    assert Workout.query.filter_by(exercise='Existing Workout').count() == 1
    assert User.query.count() == 3
    assert Workout.query.count() == 4

    runpy.run_path('seed.py')
    assert User.query.count() == 3
    assert Workout.query.count() == 4