import os

from flask import Flask, request
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required
from flask_migrate import Migrate
from sqlalchemy.exc import IntegrityError

from models import bcrypt, db, User, Workout
from validation import workout_error

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'local-development-key-change-before-deploying')
db.init_app(app)
bcrypt.init_app(app)
JWTManager(app)
Migrate(app, db)


def auth_error(message, status):
    return {'error': message, 'errors': [message]}, status


@app.get('/')
def index():
    return {'message': 'Workout Tracker API'}, 200


@app.post('/signup')
def signup():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return auth_error('A JSON object is required', 400)
    username, password = data.get('username'), data.get('password')
    if (
        not isinstance(username, str) or not username.strip()
        or not isinstance(password, str) or not password
    ):
        return auth_error('Username and password are required', 400)
    if data.get('password_confirmation', password) != password:
        return auth_error('Passwords do not match', 400)
    username = username.strip()
    if User.query.filter_by(username=username).first():
        return auth_error('Username already taken', 422)
    try:
        user = User(username=username)
        user.password = password
        db.session.add(user)
        db.session.commit()
        token = create_access_token(identity=str(user.id))
        return {**user.to_dict(), 'token': token, 'access_token': token, 'user': user.to_dict()}, 201
    except IntegrityError:
        db.session.rollback()
        return auth_error('Username already taken', 422)
    except Exception:
        db.session.rollback()
        app.logger.exception('Failed to create user')
        return auth_error('Unable to create user', 500)


@app.post('/login')
def login():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get('username'), str) or not isinstance(data.get('password'), str):
        return auth_error('Username and password are required', 400)
    user = User.query.filter_by(username=data['username'].strip()).first()
    if not user or not user.authenticate(data['password']):
        return auth_error('Invalid username or password', 401)
    token = create_access_token(identity=str(user.id))
    return {
        'token': token, 'access_token': token, 'user': user.to_dict()
    }, 200


@app.get('/me')
@jwt_required()
def current_user():
    user = db.session.get(User, get_jwt_identity())
    return (user.to_dict(), 200) if user else ({'error': 'User not found'}, 404)


@app.route('/workouts', methods=['GET', 'POST'])
@jwt_required()
def workouts():
    user_id = get_jwt_identity()
    if request.method == 'GET':
        try:
            page = int(request.args.get('page', '1'))
            per_page = int(request.args.get('per_page', '5'))
        except ValueError:
            return {'error': 'page and per_page must be integers'}, 400
        if page < 1 or not 1 <= per_page <= 100:
            return {'error': 'page must be positive and per_page must be between 1 and 100'}, 400
        result = Workout.query.filter_by(user_id=user_id).paginate(
            page=page, per_page=per_page, error_out=False
        )
        return {
            'workouts': [item.to_dict() for item in result.items],
            'total': result.total, 'pages': result.pages,
            'current_page': result.page,
        }, 200

    data = request.get_json(silent=True)
    error = workout_error(data)
    if error:
        return {'error': error}, 400
    workout = Workout(
        exercise=data['exercise'].strip(),
        duration_minutes=data['duration_minutes'],
        calories_burned=data['calories_burned'],
        date=data['date'].strip(), user_id=user_id,
    )
    try:
        db.session.add(workout)
        db.session.commit()
        return workout.to_dict(), 201
    except Exception:
        db.session.rollback()
        app.logger.exception('Failed to create workout')
        return {'error': 'Unable to create workout'}, 500


@app.route('/workouts/<int:workout_id>', methods=['PATCH', 'DELETE'])
@jwt_required()
def workout_detail(workout_id):
    workout = db.session.get(Workout, workout_id)
    if not workout:
        return {'error': 'Workout not found'}, 404
    if str(workout.user_id) != str(get_jwt_identity()):
        return {'error': 'Unauthorized access to this resource'}, 403
    if request.method == 'DELETE':
        db.session.delete(workout)
        db.session.commit()
        return '', 204
    data = request.get_json(silent=True)
    error = workout_error(data, partial=True)
    if error:
        return {'error': error}, 400
    for key, value in data.items():
        setattr(workout, key, value.strip() if isinstance(value, str) else value)
    try:
        db.session.commit()
        return workout.to_dict(), 200
    except Exception:
        db.session.rollback()
        app.logger.exception('Failed to update workout %s', workout_id)
        return {'error': 'Unable to update workout'}, 500
