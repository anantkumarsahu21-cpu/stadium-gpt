import random
import datetime
from database import db, User, Match, MatchEvent, PlayerStats, ParkingLot, FoodStall, Incident, AuditLog

# Initial Seed Data definitions
ROLES = ['fan', 'manager', 'security', 'medical', 'referee', 'admin', 'media']

TEAMS = ['Argentina', 'Brazil', 'USA', 'Mexico', 'England', 'France', 'Germany', 'Spain']

INITIAL_PLAYERS = [
    # Argentina
    {"name": "Lionel Messi", "team": "Argentina", "goals": 4, "assists": 3, "rating": 8.9, "accuracy": 91.2},
    {"name": "Lautaro Martinez", "team": "Argentina", "goals": 2, "assists": 1, "rating": 7.5, "accuracy": 82.1},
    {"name": "Emiliano Martinez", "team": "Argentina", "goals": 0, "assists": 0, "rating": 8.2, "accuracy": 78.4, "clean_sheets": 3},
    
    # Brazil
    {"name": "Vinicius Junior", "team": "Brazil", "goals": 3, "assists": 2, "rating": 8.4, "accuracy": 87.5},
    {"name": "Rodrygo", "team": "Brazil", "goals": 2, "assists": 1, "rating": 7.3, "accuracy": 85.0},
    {"name": "Alisson Becker", "team": "Brazil", "goals": 0, "assists": 0, "rating": 7.8, "accuracy": 81.2, "clean_sheets": 2},
    
    # USA
    {"name": "Christian Pulisic", "team": "USA", "goals": 3, "assists": 1, "rating": 8.1, "accuracy": 86.4},
    {"name": "Folarin Balogun", "team": "USA", "goals": 1, "assists": 1, "rating": 7.0, "accuracy": 79.5},
    {"name": "Matt Turner", "team": "USA", "goals": 0, "assists": 0, "rating": 7.2, "accuracy": 70.1, "clean_sheets": 1},
    
    # England
    {"name": "Harry Kane", "team": "England", "goals": 5, "assists": 2, "rating": 8.7, "accuracy": 84.8},
    {"name": "Jude Bellingham", "team": "England", "goals": 2, "assists": 3, "rating": 8.5, "accuracy": 89.2},
    {"name": "Jordan Pickford", "team": "England", "goals": 0, "assists": 0, "rating": 7.5, "accuracy": 75.0, "clean_sheets": 2},
    
    # France
    {"name": "Kylian Mbappe", "team": "France", "goals": 5, "assists": 1, "rating": 8.8, "accuracy": 88.0},
    {"name": "Antoine Griezmann", "team": "France", "goals": 1, "assists": 4, "rating": 8.3, "accuracy": 90.1},
    {"name": "Mike Maignan", "team": "France", "goals": 0, "assists": 0, "rating": 8.0, "accuracy": 83.4, "clean_sheets": 3}
]

PARKING_ZONES = [
    {"zone": "Zone A", "capacity": 1500, "occupied": 1120, "type": "General"},
    {"zone": "Zone B", "capacity": 300, "occupied": 240, "type": "EV Charging", "ev_chargers_total": 30, "ev_chargers_occupied": 24},
    {"zone": "Zone C", "capacity": 2000, "occupied": 1650, "type": "General"},
    {"zone": "Zone D", "capacity": 200, "occupied": 95, "type": "VIP / Media", "ev_chargers_total": 10, "ev_chargers_occupied": 5}
]

FOOD_STALLS = [
    {"name": "Taco Arena", "cuisine": "Mexican Street Food", "queue_length": 14, "wait_time": 8, "popular_item": "Carne Asada Tacos ($12)"},
    {"name": "Burger Box", "cuisine": "Gourmet Burgers", "queue_length": 25, "wait_time": 15, "popular_item": "Championship Double ($15)"},
    {"name": "Halal Goals", "cuisine": "Middle Eastern Gyros", "queue_length": 18, "wait_time": 10, "popular_item": "Chicken Over Rice ($13)"},
    {"name": "Pizza Kick", "cuisine": "Italian Slices", "queue_length": 8, "wait_time": 4, "popular_item": "Classic Pepperoni Slice ($6)"}
]

def seed_database():
    """Initializes schema and seeds defaults if table counts are empty."""
    db.create_all()
    
    # 1. Users Seed
    if User.query.count() == 0:
        for r in ROLES:
            username = f"{r}1"
            # Simple password identical to role name for ease of testing
            u = User(username=username, role=r)
            u.set_password(r)
            db.session.add(u)
        db.session.commit()
        print("Users seeded successfully.")

    # 2. Player Stats Seed
    if PlayerStats.query.count() == 0:
        for p_data in INITIAL_PLAYERS:
            p = PlayerStats(
                name=p_data["name"],
                team=p_data["team"],
                goals=p_data["goals"],
                assists=p_data["assists"],
                match_rating=p_data["rating"],
                pass_accuracy=p_data["accuracy"],
                minutes_played=270, # standard group stage duration
                clean_sheets=p_data.get("clean_sheets", 0)
            )
            db.session.add(p)
        db.session.commit()
        print("Player statistics seeded.")

    # 3. Parking Lot Seed
    if ParkingLot.query.count() == 0:
        for lot_data in PARKING_ZONES:
            lot = ParkingLot(
                zone=lot_data["zone"],
                capacity=lot_data["capacity"],
                occupied=lot_data["occupied"],
                type=lot_data["type"],
                ev_chargers_total=lot_data.get("ev_chargers_total", 0),
                ev_chargers_occupied=lot_data.get("ev_chargers_occupied", 0)
            )
            db.session.add(lot)
        db.session.commit()
        print("Parking lots seeded.")

    # 4. Food Stalls Seed
    if FoodStall.query.count() == 0:
        for fs_data in FOOD_STALLS:
            stall = FoodStall(
                name=fs_data["name"],
                cuisine=fs_data["cuisine"],
                queue_length=fs_data["queue_length"],
                wait_time=fs_data["wait_time"],
                popular_item=fs_data["popular_item"]
            )
            db.session.add(stall)
        db.session.commit()
        print("Food stalls seeded.")

    # 5. Matches Seed
    if Match.query.count() == 0:
        matches_data = [
            {"team_a": "Argentina", "team_b": "Brazil", "score_a": 2, "score_b": 1, "status": "completed", "time": 90, "start": "July 8, 19:00"},
            {"team_a": "USA", "team_b": "Mexico", "score_a": 0, "score_b": 0, "status": "first_half", "time": 32, "start": "July 9, 03:00"},
            {"team_a": "England", "team_b": "France", "score_a": 0, "score_b": 0, "status": "scheduled", "time": 0, "start": "July 9, 21:00"},
            {"team_a": "Germany", "team_b": "Spain", "score_a": 0, "score_b": 0, "status": "scheduled", "time": 0, "start": "July 10, 18:00"}
        ]
        
        for m_data in matches_data:
            m = Match(
                team_a=m_data["team_a"],
                team_b=m_data["team_b"],
                score_a=m_data["score_a"],
                score_b=m_data["score_b"],
                status=m_data["status"],
                match_time=m_data["time"],
                start_time=m_data["start"]
            )
            db.session.add(m)
        db.session.commit()
        
        # Add a couple of initial events for completed Argentina vs Brazil match
        completed_match = Match.query.filter_by(status='completed').first()
        if completed_match:
            e1 = MatchEvent(match_id=completed_match.id, type='goal', player_name='Lionel Messi', team='Argentina', minute=12, details='Fabulous curling free-kick into top left corner')
            e2 = MatchEvent(match_id=completed_match.id, type='goal', player_name='Vinicius Junior', team='Brazil', minute=43, details='Clinical tap-in after a counter-attack cross')
            e3 = MatchEvent(match_id=completed_match.id, type='goal', player_name='Lionel Messi', team='Argentina', minute=76, details='Penalty shot sent down the center')
            e4 = MatchEvent(match_id=completed_match.id, type='yellow_card', player_name='Rodrygo', team='Brazil', minute=81, details='Late tactical foul in midfielder area')
            db.session.add_all([e1, e2, e3, e4])
            db.session.commit()
            
        print("Matches and events seeded.")


def simulate_tick():
    """Simulates active environment fluctuations for IoT components (runs on API poll triggers)."""
    # 1. Update Food Stall queue lengths and times slightly
    stalls = FoodStall.query.all()
    for stall in stalls:
        change = random.choice([-2, -1, 0, 1, 2])
        stall.queue_length = max(0, stall.queue_length + change)
        stall.wait_time = max(0, int(stall.queue_length * 0.6))
        
    # 2. Update parking lots spaces
    lots = ParkingLot.query.all()
    for lot in lots:
        change = random.randint(-4, 4)
        lot.occupied = max(0, min(lot.capacity, lot.occupied + change))
        if lot.ev_chargers_total > 0:
            charger_change = random.choice([-1, 0, 1])
            lot.ev_chargers_occupied = max(0, min(lot.ev_chargers_total, lot.ev_chargers_occupied + charger_change))

    # 3. Simulate active first half match minute increments
    live_match = Match.query.filter(Match.status.in_(['first_half', 'second_half'])).first()
    if live_match:
        live_match.match_time += 1
        if live_match.match_time >= 45 and live_match.status == 'first_half':
            live_match.status = 'halftime'
        elif live_match.match_time >= 90 and live_match.status == 'second_half':
            live_match.status = 'completed'
            
    db.session.commit()


def get_sustainability_stats():
    """Generates simulated environmental KPI statistics for the Green Stadium dashboard."""
    # Anchored values fluctuated slightly by current hour
    base_electricity = 18500 # kWh
    base_water = 92000 # Liters
    base_waste = 4.2 # Tons
    
    fluctuation = random.uniform(-0.05, 0.05)
    
    return {
        "electricity": round(base_electricity * (1 + fluctuation), 1),
        "water": round(base_water * (1 + fluctuation), 1),
        "waste": round(base_waste * (1 + fluctuation), 2),
        "recycling_rate": round(68.5 + random.uniform(-1.5, 1.5), 1),
        "carbon_emissions": round(12.4 * (1 + fluctuation), 2) # CO2 metric tons
    }
