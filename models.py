from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    #relationship to workouts
    workouts = db.relationship('Workout', backref='user', cascade='all, delete-orphan')

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute.')

    @password.setter
    def password(self, plain_text_password):
        #automatically hash passwords using bcrypt when setting the password
        self.password_hash = bcrypt.generate_password_hash(plain_text_password).decode('utf-8')

    def authenticate(self, plain_text_password):
        #verify incomig password against the stored hash
        return bcrypt.check_password_hash(self.password_hash, plain_text_password)

    def to_dict(self):
        return{
            'id': self.id,
            'username': self.username
        }

class Workout(db.Model):
    __tablename__ = 'workouts'

    id = db.Column( db.Integer, primary_key=True)
    exercise = db.Column(db.String(100), nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    calories_burned = db.Column(db.Integer, nullable=False)
    date = db.Column(db.String(50), nullable=False)

    #foreign key linking the workout to a specific user
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'exercise': self.exercise,
            'duration_minutes': self.duration_minutes,
            'calories_burned': self.calories_burned,
            'date': self.date,
            'user_id':self.user_id
        }   