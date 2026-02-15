"""Felker Family Hub — application factory."""

from flask import Flask, session

from app.config import Config, TestConfig
from app.extensions import db, migrate, socketio, scheduler


def create_app(testing=False):
    """Create and configure the Flask application."""
    flask_app = Flask(__name__)

    # Load configuration
    if testing:
        flask_app.config.from_object(TestConfig)
    else:
        flask_app.config.from_object(Config)

    # Initialise extensions
    db.init_app(flask_app)
    migrate.init_app(flask_app, db)
    socketio.init_app(
        flask_app, async_mode="eventlet" if not testing else "threading"
    )

    if not testing:
        flask_app.config["SCHEDULER_API_ENABLED"] = Config.SCHEDULER_API_ENABLED
        scheduler.init_app(flask_app)
        scheduler.start()

    # Import models so Alembic / create_all() can see them
    with flask_app.app_context():
        import app.models  # noqa: F401

    # Register blueprints
    _register_blueprints(flask_app)

    # Register before-request hook for IP trust / PIN auth
    _register_auth_hook(flask_app)

    # Inject current_user into all templates
    _register_context_processors(flask_app)

    # Register error handlers
    _register_error_handlers(flask_app)

    return flask_app


def _register_blueprints(flask_app):
    """Import and register all blueprints."""
    from app.blueprints.auth import auth_bp
    from app.blueprints.calendar_bp import calendar_bp
    from app.blueprints.chores import chores_bp
    from app.blueprints.grocery import grocery_bp
    from app.blueprints.users import users_bp
    from app.blueprints.bank import bank_bp

    flask_app.register_blueprint(auth_bp)
    flask_app.register_blueprint(calendar_bp)
    flask_app.register_blueprint(chores_bp)
    flask_app.register_blueprint(grocery_bp)
    flask_app.register_blueprint(users_bp)
    flask_app.register_blueprint(bank_bp)


def _register_auth_hook(flask_app):
    """Register the IP-trust before-request hook."""
    from app.blueprints.auth import require_trusted_ip

    flask_app.before_request(require_trusted_ip)


def _register_context_processors(flask_app):
    """Make current_user and idle_timeout available in every template."""
    from app.models.user import User

    @flask_app.context_processor
    def inject_current_user():
        user_id = session.get("current_user_id")
        user = db.session.get(User, user_id) if user_id else None
        idle_timeout_ms = flask_app.config.get("IDLE_TIMEOUT_MINUTES", 5) * 60 * 1000
        return dict(current_user=user, idle_timeout_ms=idle_timeout_ms)


def _register_error_handlers(flask_app):
    """Register JSON error handlers."""
    from flask import jsonify

    @flask_app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Resource not found"}), 404

    @flask_app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": "Bad request"}), 400
