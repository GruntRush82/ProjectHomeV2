from flask import Flask, render_template, jsonify, request
from sqlalchemy.dialects.sqlite import JSON
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKeyConstraint
from datetime import date
from flask_apscheduler import APScheduler
from reporting import sync_config
from reporting import generate_weekly_reports
from datetime import datetime, timedelta
import sys

from dotenv import load_dotenv
load_dotenv()    

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chores.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app,db)
# Initialize the scheduler
scheduler = APScheduler()
scheduler.api_enabled = True



class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    chores = db.relationship('Chore', backref='user', lazy=True)

class Chore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default = False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    day = db.Column(db.String(100), nullable=False, default = 'Monday')
    rotation_type = db.Column(db.String(10), nullable=False, default = "static")
    rotation_order = db.Column(JSON, nullable=True)

class ChoreHistory(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    chore_id = db.Column(db.Integer, db.ForeignKey('chore.id'), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    completed = db.Column(db.Boolean, nullable=False)
    day = db.Column(db.String(100), nullable=False)
    rotation_type = db.Column(db.String(10), nullable=False)

    chore = db.relationship('Chore', backref='history')


@scheduler.task('cron', id='weekly_archive',day_of_week='mon', hour=0, minute=0, misfire_grace_time=60, coalesce = True, max_instances= 1)

def weekly_archive_task(*, send_reports: bool = True):
    with app.app_context():
        today = date.today()
        if ChoreHistory.query.filter_by(date=today).first():
            print(f"Archive for {today} already exists; skipping.")
            return

        # 1. archive + reset status
        for chore in Chore.query.all():
            db.session.add(
                ChoreHistory(
                    chore_id=chore.id,
                    username=chore.user.username,
                    date=today,
                    completed=chore.completed,
                    day=chore.day,
                    rotation_type=chore.rotation_type,
                )
            )
            chore.completed = False

        # 2. advance rotating chores
        rotate_chores_once()

        db.session.commit()

        if send_reports:
            generate_weekly_reports(db.session)

        print(f"Archive+rotation complete – {today}")


def rotate_chores_once():
    rotating = Chore.query.filter_by(rotation_type="rotating").all()
    for chore in rotating:
        order = chore.rotation_order or []
        if not order:
            continue
        try:
            curr = chore.user.username
            nxt = order[(order.index(curr) + 1) % len(order)]
        except ValueError:
            continue  # current user not in list
        next_user = User.query.filter_by(username=nxt).first()
        if next_user:
            chore.user_id = next_user.id


# Start the scheduler


@app.route('/')
def home():
    return render_template('chore_tracker.html')

@app.route('/chores', methods=['GET'])
def get_chores():
    chores = Chore.query.all()  # Fetch all chores from the db
    chore_list = [
        {
            "id": chore.id, 
            "description": chore.description, 
            "completed": chore.completed, 
            "user_id": chore.user_id,
            "username": chore.user.username,  # Add the username from the user relationship
            "day" : chore.day,
            "rotation_type" : chore.rotation_type,
            "rotation_order" : chore.rotation_order or []
        }
        for chore in chores
    ]
    return jsonify(chore_list)

@app.route('/chores/<int:id>', methods=['GET'])
def get_chore(id):
    chore = Chore.query.get_or_404(id)
    return jsonify({
        "id": chore.id,
        "description": chore.description,
        "completed": chore.completed
    })



@app.route('/chores', methods=['POST'])
def add_chore():
    data = request.get_json()
    description = data.get('description')
    user_id = data.get('user_id')
    day = data.get('day') # Expecting a day of the week
    rotation_type = data.get('rotation_type','static')
    rotation_order = data.get('rotation_order',[])

    VALID_DAYS = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}

    if not description or not user_id:
        return jsonify({"error": "Description and user_id are required"}), 400
    
    if not day in VALID_DAYS:
        return jsonify({"error": "Invalid day(s) provided"}), 400



    new_chore = Chore(
        description=description, 
        user_id=user_id,
        day=day,
        rotation_type=rotation_type.lower(),
        rotation_order=rotation_order
        )
    db.session.add(new_chore)
    db.session.commit()

    # Include the username in the response
    response = {
        "id": new_chore.id, 
        "description": new_chore.description, 
        "completed": new_chore.completed, 
        "user_id": new_chore.user_id,
        "username": new_chore.user.username,  # Add username here
        "day" : day,
        "rotation_type" : new_chore.rotation_type,
        "rotation_order" : list(new_chore.rotation_order or [])
    }
    print("Rotation Order (raw):", data.get("rotation_order"))
    print("Rotation Order (parsed):", rotation_order)
    sys.stdout.flush()

    print(response)  # Log the response to check if the username is correct

    return jsonify(response), 201



@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    username = data.get('username')

    if not username:
        return jsonify({"error": "Username is required"}), 400
    
    # Check if user already exists
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"error": "Username already exists"}), 400

    new_user = User(username=username)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"id": new_user.id, "username": new_user.username}), 201

@app.route('/chores/<int:id>', methods=['PUT'])
def update_chore(id):
    chore = Chore.query.get_or_404(id)
    if chore is None:
        return jsonify({"error": "Chore not found"}), 404
    

    data = request.get_json()
    print(data)
    description = data.get('description')
    completed = data.get('completed')

    if description is not None:
        chore.description = description
    if completed is not None:
        chore.completed = completed

    db.session.commit()
    return jsonify({"id": chore.id, "description": chore.description, "completed": chore.completed}), 201

@app.route('/chores/archive', methods=['POST'])
def archive_chores():
    chores = Chore.query.all()
    for chore in chores:
        # Add a record to ChoreHistory
        chore_history = ChoreHistory(
            chore_id=chore.id,
            username=chore.user.username,
            date=date.today(),
            completed=chore.completed,
            day=chore.day,
            rotation_type=chore.rotation_type
        )
        db.session.add(chore_history)
        # Reset the chore's status to incomplete
        chore.completed = False

    db.session.commit()
    return jsonify({"message": "All chores archived and reset"}), 200

@app.route('/archive', methods=['GET'])
def get_archive():
    history = ChoreHistory.query.all()
    history_list = [
        {
            "id" : record.id,
            "chore_id" : record.chore_id,
            "username" : record.username,
            "date" : record.date.strftime('%Y-%m-%d'),
            "completed" : record.completed,
            "day" : record.day,
            "rotation_type" : record.rotation_type
        }
        for record in history
    ]
    return jsonify(history_list)

@app.route('/chores/clear-archive', methods=['DELETE'])
def clear_archive():
    # Delete all records from the ChoreHistory table
    ChoreHistory.query.delete()
    db.session.commit()
    return jsonify({"message": "Chore history cleared successfully"}), 200



@app.route('/chores/<int:id>', methods=['DELETE'])
def delete_chore(id):
    chore = Chore.query.get_or_404(id)
    
    # Delete associated ChoreHistory entries
    ChoreHistory.query.filter_by(chore_id=chore.id).delete()

    db.session.delete(chore)
    db.session.commit()
    return jsonify({"message": "Chore deleted"}), 200

@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    user_list = [{"id": user.id, "username": user.username} for user in users]
    return jsonify(user_list)

@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    #Find the user by ID
    user = User.query.get_or_404(id)
    #delete all chores associated with this user
    Chore.query.filter_by(user_id=id).delete()

    #Delete the User
    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": f"{user.username} and all their chores have been deleted"}), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad request"}), 400

@app.route('/chores/reset', methods=['POST'])
def manual_weekly_reset():
    body        = request.get_json(silent=True) or {}
    send_flag   = bool(body.get("generate_reports"))

    # --- 1️⃣ wipe out any archive rows for *today* -------------------------
    ChoreHistory.query.filter_by(date=date.today()).delete()
    db.session.commit()            # make sure they’re really gone

    # --- 2️⃣ run the same weekly task (it will now proceed) ---------------
    weekly_archive_task(send_reports=send_flag)

    return jsonify({
        "message": "Week archived & rotated",
        "reports_sent": send_flag,
        "date": str(date.today())
    }), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        sync_config(db.session)
    scheduler.init_app(app)
    scheduler.start()
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
    
    