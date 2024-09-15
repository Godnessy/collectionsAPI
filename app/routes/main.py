from flask import Blueprint, request, jsonify, current_app
from app.models import db, Notification, Case, User
from services.email_service import create_email_notification
from app.socket import send_notification
from datetime import datetime, timezone
from functools import wraps

main = Blueprint('main', __name__)

def require_api_key(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        if request.headers.get('Authorization') == current_app.config['API_KEY']:
            return view_function(*args, **kwargs)
        else:
            return jsonify({'error': 'Unauthorized'}), 401
    return decorated_function

@main.route('/')
def index():
    return "sessions live"

@main.route('/api/v1/notifications', methods=['POST'])
@require_api_key
def receive_notification():
    data = request.json
    
    # Validate incoming data
    if not all(key in data for key in ['case_id', 'address_status', 'reason']):
        return jsonify({'error': 'Missing required fields, please include at least case_id, address_status and reason fields.'}), 400

    # Create new notification
    new_notification = Notification(
        case_id=data['case_id'],
        address_status=data['address_status'],
        reason=data['reason'],
        timestamp=datetime.now(timezone.utc)
    )

    # Add to database
    db.session.add(new_notification)
    
    # Update associated case
    case = Case.query.get(data['case_id'])
    if case:
        if case.updated_at.tzinfo is None:  # If updated_at is naive, make it UTC aware
            case.updated_at = case.updated_at.replace(tzinfo=timezone.utc)
        if new_notification.timestamp > case.updated_at:
            case.is_active = False
            case.halt_reason = data['reason']
            case.updated_at = new_notification.timestamp
            debtor = User.query.get(case.debtor_id)
            if debtor:
                debtor.address_status = 'invalid'
                debtor.address = None

        create_email_notification(creditor.id, case.id)

        current_app.logger.info(f"Notification received for case {data['case_id']}")
# ... (after sending WebSocket notification)
        current_app.logger.info(f"WebSocket notification sent for case {case.id}")
        # ... (after creating email notification)
        current_app.logger.info(f"Email notification created for case {case.id}")
    
    try:
        db.session.commit()
        
        # Send WebSocket notification
        if case:
            creditor = User.query.get(case.creditor_id)
            if creditor:
                notification_data = {
                    'case_id': case.id,
                    'message': f'Case {case.id} has been updated due to an invalid address.'
                }
                send_notification(str(creditor.id), notification_data)
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

    return jsonify({'message': 'Notification received and processed'}), 201

@main.route('/api/v1/create_test_data', methods=['POST'])
@require_api_key
def create_test_data():
    # Create a test user and attached to case
    test_user = User(name="Test Debtor", email="test3@example.com", address='Test Address 3')
    db.session.add(test_user)
    db.session.flush()  # This will assign an ID to test_user

    test_case = Case(
        debtor_id=3,  # This is a placeholder, as we don't have a real debtor
        creditor_id=test_user.id,
        status="active",
        is_active=True,
    )
    db.session.add(test_case)
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Test data created successfully',
            'user_id': test_user.id,
            'case_id': test_case.id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500