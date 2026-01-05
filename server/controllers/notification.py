from flask import Blueprint, request, jsonify, g
from queries.notification import NotificationQueryManager
from queries.user import UserQueryManager
from db_connection import DbPool
from constants import UserRole
from middleware.auth import role_required, token_required

bp = Blueprint('notification', __name__)

@bp.get('/<int:user_id>')
@token_required
def get_notifications(user_id):
    if g.user_id != user_id:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)

            user = user_manager.get_user_by_id(user_id)
            if not user:
                return jsonify({"status": "error", "message": "User not found"}), 404
            
            notification_manager = NotificationQueryManager(cur)
            notifications = notification_manager.get_notifications_by_user(user_id)

        return jsonify({"status": "success", "notifications": notifications}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.post('/<int:notification_id>/read')
@token_required
def mark_notification_as_read(notification_id):
    try:
        with DbPool.cursor() as cur:
            notification_manager = NotificationQueryManager(cur)
            notification = notification_manager.get_notification(notification_id)

            if not notification:
                return jsonify({"status": "error", "message": "Notification not found"}), 404
            
            isAdmin = g.role == UserRole.ADMIN.value

            if not isAdmin and notification['user_id'] != g.user_id:
                return jsonify({"status": "error", "message": "Unauthorized"}), 403

            notification_manager.mark_notification_as_read(notification_id)
        return jsonify({"status": "success", "message": "Notification marked as read"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500