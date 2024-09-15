def test_app_creation(test_app):
    assert test_app.config['TESTING'] == True
    assert test_app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:'

def test_index_route(test_client):
    response = test_client.get('/')
    assert response.status_code == 200
    assert b"Hello, World!" in response.data

def test_db_connection(test_db):
    assert test_db.engine.url.database == ':memory:'