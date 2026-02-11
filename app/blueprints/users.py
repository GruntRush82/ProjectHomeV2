"""User routes — CRUD."""

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models.user import User
from app.models.chore import Chore

users_bp = Blueprint("users", __name__)


@users_bp.route("/users", methods=["GET"])
def get_users():
    users = User.query.all()
    return jsonify([
        {"id": u.id, "username": u.username}
        for u in users
    ])


@users_bp.route("/users", methods=["POST"])
def create_user():
    data = request.get_json()
    username = data.get("username")

    if not username:
        return jsonify({"error": "Username is required"}), 400

    existing = User.query.filter_by(username=username).first()
    if existing:
        return jsonify({"error": "Username already exists"}), 400

    new_user = User(username=username)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"id": new_user.id, "username": new_user.username}), 201


@users_bp.route("/users/<int:id>", methods=["DELETE"])
def delete_user(id):
    user = User.query.get_or_404(id)
    Chore.query.filter_by(user_id=id).delete()
    db.session.delete(user)
    db.session.commit()
    return jsonify({
        "message": f"{user.username} and all their chores have been deleted"
    }), 200
