from app import app, db
from models import User, Workout

with app.app_context():
    print("Creating sample users if they do not already exist...")
    sample_users = {}
    for username in ('test_user_one', 'test_user_two'):
        user = User.query.filter_by(username=username).first()
        if user is None:
            user = User(username=username)
            user.password = 'password123'
            db.session.add(user)
        sample_users[username] = user
    db.session.commit()

    print("Creating sample workouts if they do not already exist...")
    sample_workouts = [
        ('Morning Jog', 30, 220, '2026-10-01', 'test_user_one'),
        ('Weightlifting', 45, 310, '2026-10-02', 'test_user_one'),
        ('Cycling', 60, 500, '2026-10-02', 'test_user_two'),
    ]
    for exercise, duration, calories, date, username in sample_workouts:
        user = sample_users[username]
        existing_workout = Workout.query.filter_by(
            user_id=user.id,
            exercise=exercise,
            date=date,
        ).first()
        if existing_workout is None:
            db.session.add(Workout(
                exercise=exercise,
                duration_minutes=duration,
                calories_burned=calories,
                date=date,
                user_id=user.id,
            ))
    db.session.commit()

    print("Database seeded successfully!")
