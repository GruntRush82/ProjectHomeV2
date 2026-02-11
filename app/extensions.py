"""Shared extension instances.

Created here (uninitialized) to avoid circular imports.
Each extension is initialized in create_app() via init_app().
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_apscheduler import APScheduler

db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO()
scheduler = APScheduler()
