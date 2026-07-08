import pytest
from app import app
from database import db, User

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            from simulation import seed_database
            seed_database()
            yield client
            
            db.session.remove()
            db.drop_all()

def test_login_flow(client):
    # Test valid credentials login
    response = client.post('/login', data=dict(username='fan1', password='fan'), follow_redirects=True)
    assert response.status_code == 200
    assert b"Sign Out" in response.data # Check dashboard base layout elements rendered
    
    # Test invalid credentials login
    response = client.post('/login', data=dict(username='fan1', password='wrong'), follow_redirects=True)
    assert response.status_code == 200
    assert b"Invalid username or password" in response.data

def test_role_restricted_endpoints(client):
    # 1. Accessing referee action without login should redirect to /login
    response = client.post('/api/match/event', json=dict(match_id=1, type='goal'), follow_redirects=True)
    assert b"Sign In" in response.data # Redirected to login
    
    # 2. Login as a Fan and try to post a Referee event -> should get 403
    client.post('/login', data=dict(username='fan1', password='fan'))
    response = client.post('/api/match/event', json=dict(match_id=1, type='goal'))
    assert response.status_code == 403
    assert b"Unauthorized access" in response.data

    # 3. Login as a Referee and call same endpoint -> should work (return 404 since match 999 doesn't exist, but bypasses 403 role check)
    client.get('/logout') # clear session
    client.post('/login', data=dict(username='referee1', password='referee'))
    
    # Try a non-existent match ID -> should return 404
    response = client.post('/api/match/event', json=dict(match_id=999, type='goal'))
    assert response.status_code == 404
    
    # Try the seeded match ID 1 -> should succeed (return 200)
    response_ok = client.post('/api/match/event', json=dict(match_id=1, type='goal', team='Argentina', player_name='Lionel Messi'))
    assert response_ok.status_code == 200
