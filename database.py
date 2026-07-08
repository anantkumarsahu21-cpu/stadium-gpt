import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='fan') # fan, manager, security, medical, referee, admin, media
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Match(db.Model):
    __tablename__ = 'matches'
    id = db.Column(db.Integer, primary_key=True)
    team_a = db.Column(db.String(100), nullable=False)
    team_b = db.Column(db.String(100), nullable=False)
    score_a = db.Column(db.Integer, default=0)
    score_b = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='scheduled') # scheduled, first_half, halftime, second_half, completed
    start_time = db.Column(db.String(100), nullable=True)
    match_time = db.Column(db.Integer, default=0) # minute of match
    events = db.relationship('MatchEvent', backref='match', lazy=True, cascade="all, delete-orphan")

class MatchEvent(db.Model):
    __tablename__ = 'match_events'
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('matches.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False) # goal, yellow_card, red_card, var_review, injury, corner, penalty, free_kick, offside, substitution
    player_name = db.Column(db.String(100), nullable=True)
    team = db.Column(db.String(100), nullable=True)
    minute = db.Column(db.Integer, nullable=False)
    details = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class PlayerStats(db.Model):
    __tablename__ = 'player_stats'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    team = db.Column(db.String(100), nullable=False)
    goals = db.Column(db.Integer, default=0)
    assists = db.Column(db.Integer, default=0)
    yellow_cards = db.Column(db.Integer, default=0)
    red_cards = db.Column(db.Integer, default=0)
    minutes_played = db.Column(db.Integer, default=0)
    pass_accuracy = db.Column(db.Float, default=80.0) # percentage
    match_rating = db.Column(db.Float, default=6.0) # scale 1-10
    clean_sheets = db.Column(db.Integer, default=0)

class Incident(db.Model):
    __tablename__ = 'incidents'
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(100), nullable=False) # Section 101, Gate B, Parking Zone A, etc.
    category = db.Column(db.String(50), nullable=False) # medical, fire, security, lost_child, equipment
    severity = db.Column(db.String(20), nullable=False) # low, medium, critical
    description = db.Column(db.Text, nullable=False)
    reporter = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='reported') # reported, responding, resolved
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    summary = db.Column(db.Text, nullable=True) # AI generated incident summary

class ParkingLot(db.Model):
    __tablename__ = 'parking_lots'
    id = db.Column(db.Integer, primary_key=True)
    zone = db.Column(db.String(50), unique=True, nullable=False) # Zone A, Zone B, etc.
    capacity = db.Column(db.Integer, nullable=False)
    occupied = db.Column(db.Integer, default=0)
    type = db.Column(db.String(50), default='General') # General, EV Charging, VIP, Media
    ev_chargers_total = db.Column(db.Integer, default=0)
    ev_chargers_occupied = db.Column(db.Integer, default=0)

class FoodStall(db.Model):
    __tablename__ = 'food_stalls'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    cuisine = db.Column(db.String(100), nullable=False)
    queue_length = db.Column(db.Integer, default=0)
    wait_time = db.Column(db.Integer, default=0) # in minutes
    popular_item = db.Column(db.String(100), nullable=True)
    price_level = db.Column(db.String(10), default='$$')

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(50), nullable=False) # security, score, emergency, login, sustainability
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
