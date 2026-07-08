import os
import pytest
from app import app
from database import db, User, Match, MatchEvent, Incident, ParkingLot

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

def test_user_creation(client):
    with app.app_context():
        u = User(username='test_referee', role='referee')
        u.set_password('referee123')
        db.session.add(u)
        db.session.commit()
        
        user = User.query.filter_by(username='test_referee').first()
        assert user is not None
        assert user.role == 'referee'
        assert user.check_password('referee123') is True
        assert user.check_password('wrong_pass') is False

def test_match_and_events(client):
    with app.app_context():
        m = Match(team_a='Argentina', team_b='Brazil', score_a=0, score_b=0, status='scheduled')
        db.session.add(m)
        db.session.commit()
        
        match = Match.query.filter_by(team_a='Argentina').first()
        assert match is not None
        
        # Log a goal event
        e = MatchEvent(match_id=match.id, type='goal', player_name='Messi', team='Argentina', minute=10)
        db.session.add(e)
        match.score_a += 1
        db.session.commit()
        
        assert match.score_a == 1
        assert len(match.events) == 1
        assert match.events[0].player_name == 'Messi'

def test_incident_creation(client):
    with app.app_context():
        inc = Incident(
            location='Section 102',
            category='medical',
            severity='critical',
            description='Spectator collapsed in Row D',
            reporter='security1',
            status='reported'
        )
        db.session.add(inc)
        db.session.commit()
        
        saved_inc = Incident.query.filter_by(category='medical').first()
        assert saved_inc is not None
        assert saved_inc.severity == 'critical'
        assert saved_inc.status == 'reported'
