from flask import Blueprint, request, jsonify, current_app
from app.models import db, Notification, Case, User
from app.services.email_service import create_email_notification
from app.socket import send_live_notification,  is_user_active
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
    return "session is live"

@main.route('/api/v1/notifications', methods=['POST'])
@require_api_key
def receive_notification():
    data = request.json
    
    # Validate incoming data
    if not all(key in data for key in ['case_id', 'address_status', 'reason']):
        return jsonify({'error': 'Missing required fields, please include at least case_id, address_status and reason fields.'}), 400

    new_notification = Notification(
        case_id=data['case_id'],
        address_status=data['address_status'],
        reason=data['reason'],
        timestamp=datetime.now(timezone.utc)
    )

    db.session.add(new_notification)
    
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
        creditor = User.query.get(case.creditor_id)
        create_email_notification(creditor.id, case.id)
    
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
                if is_user_active(creditor.id):
                    send_live_notification(str(creditor.id), notification_data)
                    current_app.logger.info(f"Notification received for case {data['case_id']}")

        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

    return jsonify({'message': 'Notification received and processed'}), 201

@main.route('/api/v1/create_test_data', methods=['POST'])
@require_api_key
def create_test_data():
    test_user = User(name="Test Debtor", email="test3@example.com", address='Test Address 3')
    db.session.add(test_user)
    db.session.flush()  # This will assign an ID to test_user

    test_case = Case(
        debtor_id=3, #place holder id 
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
            'cas`e_id': test_case.id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    

@main.route('/api/v1/user/<int:user_id>/case',methods=['GET'])
@require_api_key
def get_user_cases(user_id):
    cases = Case.query.filter_by(creditor_id=user_id).all()
    cases_data=[]
    for case in cases:
        latest_notification = Notification.query.filter_by(case_id=case.id).order_by(Notification.timestamp.desc()).first()
        case_data= {
            'id': case.id,
            'debtor_id': case.debtor_id,
            'status': case.status,
            'is_active': case.is_active,
            'halt_reason': case.halt_reason,
            'created_at': case.created_at.isoformat(),
            'updated_at': case.updated_at.isoformat(),
            'latest_notification': {
                'address_status': latest_notification.address_status,
                'reason': latest_notification.reason,
                'timestamp': latest_notification.timestamp.isoformat()
            } if latest_notification else None
        }
        cases_data.append(case_data)
        
    return jsonify({
        'user_id': user_id,
        'cases': cases_data
    }), 200