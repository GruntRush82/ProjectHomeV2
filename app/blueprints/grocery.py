"""Grocery list routes."""

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models.grocery import GroceryItem

grocery_bp = Blueprint("grocery", __name__)


@grocery_bp.route("/grocery", methods=["GET"])
def get_grocery():
    items = GroceryItem.query.order_by(GroceryItem.created_at).all()
    return jsonify([
        {
            "id": i.id,
            "item_name": i.item_name,
            "added_by": i.added_by,
            "created_at": i.created_at.isoformat() if i.created_at else None,
        }
        for i in items
    ])


@grocery_bp.route("/grocery", methods=["POST"])
def add_grocery():
    data = request.get_json()
    item_name = data.get("item_name", "").strip()
    added_by = data.get("added_by", "").strip()
    if not item_name or not added_by:
        return jsonify({"error": "item_name and added_by are required"}), 400
    item = GroceryItem(item_name=item_name, added_by=added_by)
    db.session.add(item)
    db.session.commit()
    return jsonify({
        "id": item.id,
        "item_name": item.item_name,
        "added_by": item.added_by,
    }), 201


@grocery_bp.route("/grocery/<int:id>", methods=["DELETE"])
def delete_grocery(id):
    item = GroceryItem.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Item deleted"}), 200


@grocery_bp.route("/grocery/clear", methods=["DELETE"])
def clear_grocery():
    GroceryItem.query.delete()
    db.session.commit()
    return jsonify({"message": "Grocery list cleared"}), 200


@grocery_bp.route("/grocery/send", methods=["POST"])
def send_grocery():
    data = request.get_json()
    recipient = data.get("recipient_username", "").strip()
    if not recipient:
        return jsonify({"error": "recipient_username is required"}), 400

    try:
        from reporting import _send_email, _load_config
    except ImportError:
        return jsonify({"error": "Email service not configured"}), 500

    cfg = _load_config()
    user_block = cfg.get(recipient)
    if not user_block or not user_block.get("email"):
        return jsonify({"error": f"No email configured for {recipient}"}), 400

    items = GroceryItem.query.order_by(GroceryItem.created_at).all()
    if not items:
        return jsonify({"error": "Grocery list is empty"}), 400

    from email.message import EmailMessage

    lines = ["Grocery List", "=" * 30, ""]
    for i in items:
        lines.append(f"  - {i.item_name}  (added by {i.added_by})")
    lines.append("")
    lines.append("-- Felker Family Hub")

    msg = EmailMessage()
    msg["Subject"] = "Grocery List from Felker Family Hub"
    msg["To"] = user_block["email"]
    msg.set_content("\n".join(lines))
    _send_email(msg)

    GroceryItem.query.delete()
    db.session.commit()
    return jsonify({"message": f"Grocery list sent to {recipient}"}), 200
