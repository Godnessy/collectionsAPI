import pytest
from app import create_app, db, socketio
from app.models import User, Case, Notification, Email
from app.socket import is_user_active, send_live_notification
from flask_socketio import SocketIOTestClient

@pytest.fixture(scope='module')
def test_app():
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'API_KEY': 'test_api_key'
    })
    
    with app.app_context():
        db.create_all()
    
    yield app
    
    with app.app_context():
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='module')
def test_client(test_app):
    return test_app.test_client()

@pytest.fixture(scope='module')
def test_db(test_app):
    return db

@pytest.fixture(scope='function')
def setup_test_data(test_app, test_db):
    with test_app.app_context():
        debtor = User(name="Test Debtor", email="debtor@test.com", address="123 Test St")
        creditor = User(name="Test Creditor", email="creditor@test.com")
        test_db.session.add_all([debtor, creditor])
        test_db.session.commit()

        case = Case(debtor_id=debtor.id, creditor_id=creditor.id, status="active", is_active=True)
        test_db.session.add(case)
        test_db.session.commit()

        yield debtor, creditor, case

        test_db.session.query(Email).delete()
        test_db.session.query(Notification).delete()
        test_db.session.query(Case).delete()
        test_db.session.query(User).delete()
        test_db.session.commit()

def test_receive_notification(test_client, setup_test_data):
    _, creditor, case = setup_test_data
    
    notification_data = {
        'case_id': case.id,
        'address_status': 'invalid',
        'reason': 'Moved'
    }
    
    response = test_client.post('/api/v1/notifications', 
                                json=notification_data, 
                                headers={'Authorization': 'test_api_key'})
    
    assert response.status_code == 201
    assert b'Notification received and processed' in response.data

    notification = Notification.query.filter_by(case_id=case.id).first()
    assert notification is not None
    assert notification.address_status == 'invalid'
    assert notification.reason == 'Moved'

    updated_case = Case.query.get(case.id)
    assert updated_case.is_active == False
    assert updated_case.halt_reason == 'Moved'

    email = Email.query.filter_by(case_id=case.id, sent_to_user_id=creditor.id).first()
    assert email is not None
    assert email.message == 'Debtor Address is invalid'

def test_get_user_cases(test_client, setup_test_data):
    _, creditor, case = setup_test_data
    
    response = test_client.get(f'/api/v1/user/{creditor.id}/case', 
                               headers={'Authorization': 'test_api_key'})
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'cases' in data
    assert len(data['cases']) == 1
    assert data['cases'][0]['id'] == case.id

def test_websocket_notification(test_app, setup_test_data):
    _, creditor, case = setup_test_data

    with test_app.test_client() as client:
        socketio_test_client = socketio.test_client(test_app, flask_test_client=client)
        socketio_test_client.emit('register', {'user_id': str(creditor.id)})
        
        assert is_user_active(creditor.id)
        
        notification_data = {
            'case_id': case.id,
            'message': f'Case {case.id} has been updated due to an invalid address.'
        }
        
        send_live_notification(str(creditor.id), notification_data)
        
        received = socketio_test_client.get_received()
        assert len(received) > 0
        assert received[0]['name'] == 'new_notification'
        assert received[0]['args'][0] == notification_data

def test_unauthorized_access(test_client):
    response = test_client.post('/api/v1/notifications', 
                                json={}, 
                                headers={'Authorization': 'wrong_key'})
    
    assert response.status_code == 401
    assert b'Unauthorized' in response.data

def test_missing_fields(test_client):
    response = test_client.post('/api/v1/notifications', 
                                json={'case_id': 1}, 
                                headers={'Authorization': 'test_api_key'})
    
    assert response.status_code == 400
    assert b'Missing required fields' in response.data