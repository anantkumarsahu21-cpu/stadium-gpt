import io
import csv
import datetime
from functools import wraps
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, make_response
from database import db, User, Match, MatchEvent, PlayerStats, Incident, ParkingLot, FoodStall, AuditLog
from simulation import seed_database, simulate_tick, get_sustainability_stats, TEAMS
import ai_service

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stadium.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'fifa_world_cup_2026_stadium_secret_key_9918'

db.init_app(app)

# Initialize database schema and seed data
with app.app_context():
    seed_database()

# --- Security and Access Control Decorators ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def roles_allowed(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_role' not in session or session['user_role'] not in roles:
                return jsonify({"error": "Unauthorized access. Insufficient permissions."}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def log_audit(username, role, action, category):
    """Utility to log user actions to the system audit trail."""
    try:
        log = AuditLog(
            username=username,
            role=role,
            action=action,
            category=category,
            timestamp=datetime.datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"Failed to write audit log: {e}")

# --- Context Processors for Global Variables ---
@app.context_processor
def inject_now():
    return {'now': datetime.datetime.utcnow()}

# --- Authentication Routes ---
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['user_role'] = user.role
            
            log_audit(user.username, user.role, "User logged in successfully", "login")
            return redirect(url_for('dashboard'))
        else:
            error = "Invalid username or password credentials."
            
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    if 'username' in session:
        log_audit(session['username'], session['user_role'], "User logged out", "login")
    session.clear()
    return redirect(url_for('login'))

# --- Main Dashboard Page ---
@app.route('/dashboard')
@login_required
def dashboard():
    role = session['user_role']
    username = session['username']
    
    # Pre-fetch data needed for specific views
    matches = Match.query.all()
    players = PlayerStats.query.order_by(PlayerStats.goals.desc(), PlayerStats.assists.desc()).all()
    parking_lots = ParkingLot.query.all()
    food_stalls = FoodStall.query.order_by(FoodStall.wait_time.asc()).all()
    incidents = Incident.query.order_by(Incident.timestamp.desc()).all()
    audit_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(50).all()
    
    # Calculate group ranking / team stats for tournament view
    team_stats = {}
    for match in matches:
        if match.status == 'completed':
            for team in [match.team_a, match.team_b]:
                if team not in team_stats:
                    team_stats[team] = {"played": 0, "won": 0, "drawn": 0, "lost": 0, "gf": 0, "ga": 0, "points": 0}
            
            t1, t2 = match.team_a, match.team_b
            s1, s2 = match.score_a, match.score_b
            
            team_stats[t1]["played"] += 1
            team_stats[t2]["played"] += 1
            team_stats[t1]["gf"] += s1
            team_stats[t1]["ga"] += s2
            team_stats[t2]["gf"] += s2
            team_stats[t2]["ga"] += s1
            
            if s1 > s2:
                team_stats[t1]["won"] += 1
                team_stats[t1]["points"] += 3
                team_stats[t2]["lost"] += 1
            elif s2 > s1:
                team_stats[t2]["won"] += 1
                team_stats[t2]["points"] += 3
                team_stats[t1]["lost"] += 1
            else:
                team_stats[t1]["drawn"] += 1
                team_stats[t1]["points"] += 1
                team_stats[t2]["drawn"] += 1
                team_stats[t2]["points"] += 1

    # Fill in teams with zero matches played if not in team_stats
    for team in TEAMS:
        if team not in team_stats:
            team_stats[team] = {"played": 0, "won": 0, "drawn": 0, "lost": 0, "gf": 0, "ga": 0, "points": 0}

    # Sort rankings by points, then goal difference (GF-GA)
    sorted_rankings = sorted(
        team_stats.items(),
        key=lambda x: (x[1]["points"], x[1]["gf"] - x[1]["ga"], x[1]["gf"]),
        reverse=True
    )
    
    # Generate live AI incident command briefing if in emergency role
    active_incidents = Incident.query.filter(Incident.status != 'resolved').all()
    ai_incident_brief = ai_service.generate_incident_report_summary(active_incidents)
    
    # Match summaries logic for media/fan
    match_summaries = {}
    for m in matches:
        if m.status == 'completed':
            match_events = MatchEvent.query.filter_by(match_id=m.id).all()
            match_summaries[m.id] = ai_service.generate_match_summary(
                {"team_a": m.team_a, "team_b": m.team_b, "score_a": m.score_a, "score_b": m.score_b},
                match_events
            )
            
    sustainability = get_sustainability_stats()

    return render_template(
        'dashboard.html',
        username=username,
        role=role,
        matches=matches,
        players=players,
        parking_lots=parking_lots,
        food_stalls=food_stalls,
        incidents=incidents,
        audit_logs=audit_logs,
        rankings=sorted_rankings,
        ai_incident_brief=ai_incident_brief,
        match_summaries=match_summaries,
        sustainability=sustainability
    )

# --- Dynamic API Endpoints (IoT & Real-time Updates) ---
@app.route('/api/tick')
@login_required
def api_tick():
    """Tick IoT simulation variables and return fresh parking, food, match and active incident structures."""
    simulate_tick()
    
    parking = [{
        "id": p.id, "zone": p.zone, "capacity": p.capacity, "occupied": p.occupied,
        "type": p.type, "ev_total": p.ev_chargers_total, "ev_occupied": p.ev_chargers_occupied
    } for p in ParkingLot.query.all()]
    
    food = [{
        "id": f.id, "name": f.name, "queue_length": f.queue_length,
        "wait_time": f.wait_time, "popular_item": f.popular_item
    } for f in FoodStall.query.all()]
    
    matches = [{
        "id": m.id, "team_a": m.team_a, "team_b": m.team_b, "score_a": m.score_a, "score_b": m.score_b,
        "status": m.status, "time": m.match_time, "start": m.start_time
    } for m in Match.query.all()]
    
    active_incidents = Incident.query.filter(Incident.status != 'resolved').all()
    incidents_data = [{
        "id": i.id, "location": i.location, "category": i.category,
        "severity": i.severity, "description": i.description, "status": i.status
    } for i in active_incidents]
    
    sustainability = get_sustainability_stats()
    
    return jsonify({
        "status": "success",
        "parking": parking,
        "food": food,
        "matches": matches,
        "incidents": incidents_data,
        "sustainability": sustainability
    })

# --- AI Assistant Endpoint ---
@app.route('/api/assistant', methods=['POST'])
@login_required
def api_assistant():
    data = request.get_json() or {}
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({"reply": "I couldn't hear you clearly. Please type or speak a question."}), 400
        
    reply = ai_service.generate_stadium_reply(message)
    return jsonify({"reply": reply})

# --- Live Match Operations (Referee & Tournament Admin) ---
@app.route('/api/match/event', methods=['POST'])
@login_required
@roles_allowed(['referee', 'admin'])
def add_match_event():
    data = request.get_json() or {}
    match_id = data.get('match_id')
    event_type = data.get('type') # goal, yellow_card, red_card, var_review, injury, corner, penalty, free_kick, offside, substitution, match_start, half_time, full_time
    player_name = data.get('player_name', '').strip()
    team = data.get('team', '').strip()
    minute = data.get('minute', 0)
    details = data.get('details', '').strip()
    
    match = Match.query.get(match_id)
    if not match:
        return jsonify({"error": "Match record not found."}), 404
        
    # Standardize time
    if not minute:
        minute = match.match_time

    # Process score adjustments and status shifts
    action_description = f"Added match event '{event_type}' at {minute}'"
    
    if event_type == 'match_start':
        match.status = 'first_half'
        match.match_time = 0
        details = "Match started by referee whistle."
    elif event_type == 'half_time':
        match.status = 'halftime'
        details = "First half ended."
    elif event_type == 'match_resume':
        match.status = 'second_half'
        match.match_time = 45
        details = "Second half kicked off."
    elif event_type == 'full_time':
        match.status = 'completed'
        details = "Full time whistle blown. Match ended."
    elif event_type == 'goal':
        if team == match.team_a:
            match.score_a += 1
        elif team == match.team_b:
            match.score_b += 1
            
        # Update player stats goals count
        if player_name:
            player = PlayerStats.query.filter_by(name=player_name).first()
            if player:
                player.goals += 1
                player.match_rating = min(10.0, player.match_rating + 0.8)
                
    elif event_type == 'assist' and player_name:
        player = PlayerStats.query.filter_by(name=player_name).first()
        if player:
            player.assists += 1
            player.match_rating = min(10.0, player.match_rating + 0.4)
            
    elif event_type == 'yellow_card' and player_name:
        player = PlayerStats.query.filter_by(name=player_name).first()
        if player:
            player.yellow_cards += 1
            player.match_rating = max(1.0, player.match_rating - 0.5)
            
    elif event_type == 'red_card' and player_name:
        player = PlayerStats.query.filter_by(name=player_name).first()
        if player:
            player.red_cards += 1
            player.match_rating = max(1.0, player.match_rating - 1.5)
            
    # Save the event record
    event = MatchEvent(
        match_id=match.id,
        type=event_type,
        player_name=player_name or None,
        team=team or None,
        minute=minute,
        details=details or None
    )
    db.session.add(event)
    db.session.commit()
    
    log_audit(
        session['username'], session['user_role'],
        f"Logged event '{event_type}' for {match.team_a} vs {match.team_b}: {details}",
        "score"
    )
    
    return jsonify({
        "status": "success",
        "match": {
            "score_a": match.score_a,
            "score_b": match.score_b,
            "status": match.status,
            "time": match.match_time
        }
    })

# --- Emergency Command Center Actions (Security, Medical, Manager) ---
@app.route('/api/incident/report', methods=['POST'])
@login_required
@roles_allowed(['security', 'medical', 'manager'])
def report_incident():
    data = request.get_json() or {}
    location = data.get('location', '').strip()
    category = data.get('category', '').strip() # medical, fire, security, lost_child, equipment
    severity = data.get('severity', '').strip() # low, medium, critical
    description = data.get('description', '').strip()
    
    if not (location and category and severity and description):
        return jsonify({"error": "Missing required fields for reporting."}), 400
        
    incident = Incident(
        location=location,
        category=category,
        severity=severity,
        description=description,
        reporter=session['username'],
        status='reported'
    )
    db.session.add(incident)
    db.session.commit()
    
    log_audit(
        session['username'], session['user_role'],
        f"Reported {severity.upper()} {category} incident at {location}",
        "emergency"
    )
    
    # Generate live AI update for dashboard return
    active_incidents = Incident.query.filter(Incident.status != 'resolved').all()
    brief = ai_service.generate_incident_report_summary(active_incidents)
    
    return jsonify({
        "status": "success",
        "incident_id": incident.id,
        "brief": brief
    })

@app.route('/api/incident/resolve', methods=['POST'])
@login_required
@roles_allowed(['security', 'medical', 'manager'])
def resolve_incident():
    data = request.get_json() or {}
    incident_id = data.get('incident_id')
    new_status = data.get('status', 'resolved') # responding, resolved
    
    incident = Incident.query.get(incident_id)
    if not incident:
        return jsonify({"error": "Incident not found."}), 404
        
    incident.status = new_status
    db.session.commit()
    
    log_audit(
        session['username'], session['user_role'],
        f"Updated incident #{incident.id} status to '{new_status}'",
        "emergency"
    )
    
    active_incidents = Incident.query.filter(Incident.status != 'resolved').all()
    brief = ai_service.generate_incident_report_summary(active_incidents)
    
    return jsonify({
        "status": "success",
        "brief": brief
    })

@app.route('/api/incident/summary', methods=['GET'])
@login_required
@roles_allowed(['security', 'medical', 'manager'])
def get_incident_summary():
    active_incidents = Incident.query.filter(Incident.status != 'resolved').all()
    brief = ai_service.generate_incident_report_summary(active_incidents)
    return jsonify({"summary": brief})

# --- EV Charger Smart Parking Reserve ---
@app.route('/api/parking/reserve', methods=['POST'])
@login_required
def reserve_parking():
    data = request.get_json() or {}
    zone_name = data.get('zone', 'Zone B')
    
    lot = ParkingLot.query.filter_by(zone=zone_name).first()
    if not lot:
        return jsonify({"error": "Zone not found."}), 404
        
    if lot.ev_chargers_total > 0 and lot.ev_chargers_occupied < lot.ev_chargers_total:
        lot.ev_chargers_occupied += 1
        db.session.commit()
        log_audit(session['username'], session['user_role'], f"Reserved EV charger in {zone_name}", "sustainability")
        return jsonify({"status": "success", "occupied": lot.ev_chargers_occupied})
        
    return jsonify({"error": "No charging spots available in this zone."}), 400

# --- Smart Parking Recommendations ---
@app.route('/api/parking/recommend', methods=['POST'])
@login_required
def recommend_parking():
    data = request.get_json() or {}
    gate = data.get('gate', 'Gate A').strip()
    is_ev = data.get('is_ev', False)
    
    # Simple recommendation algorithm based on gate proximity
    # Gate A -> Zone A, Gate B -> Zone B (nearest to train, has EV), Gate C -> Zone C, Gate D -> Zone D
    rec_zone = "Zone A"
    details = "General parking adjacent to Gate A (North entrance)."
    
    if is_ev:
        rec_zone = "Zone B"
        details = "Smart EV charging lot located near Gate B (East entrance). Offers 30 chargers."
    elif gate == "Gate B":
        rec_zone = "Zone B"
        details = "General lot adjacent to Gate B, closest to the Meadowlands train station."
    elif gate == "Gate C":
        rec_zone = "Zone C"
        details = "Large general parking capacity near Gate C (South entrance and Food court)."
    elif gate == "Gate D":
        rec_zone = "Zone D"
        details = "VIP and Media parking close to Gate D. Pass authorization checked."
        
    return jsonify({
        "zone": rec_zone,
        "details": details
    })

# --- Data Report Exports ---
@app.route('/export/<report_type>')
@login_required
def export_report(report_type):
    """Generates standard CSV download datasets for analytics review."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    filename = f"{report_type}_report_{datetime.datetime.now().strftime('%Y%m%d')}.csv"
    
    if report_type == 'matches':
        writer.writerow(['Match ID', 'Team A', 'Team B', 'Score A', 'Score B', 'Status', 'Match Time (min)'])
        matches = Match.query.all()
        for m in matches:
            writer.writerow([m.id, m.team_a, m.team_b, m.score_a, m.score_b, m.status, m.match_time])
            
    elif report_type == 'incidents':
        writer.writerow(['Incident ID', 'Category', 'Severity', 'Location', 'Description', 'Reporter', 'Status', 'Timestamp'])
        incidents = Incident.query.all()
        for i in incidents:
            writer.writerow([i.id, i.category, i.severity, i.location, i.description, i.reporter, i.status, i.timestamp])
            
    elif report_type == 'players':
        writer.writerow(['Player Name', 'Team', 'Goals', 'Assists', 'Yellow Cards', 'Red Cards', 'Pass Accuracy %', 'Rating'])
        players = PlayerStats.query.all()
        for p in players:
            writer.writerow([p.name, p.team, p.goals, p.assists, p.yellow_cards, p.red_cards, p.pass_accuracy, p.match_rating])
            
    elif report_type == 'sustainability':
        writer.writerow(['Metric Category', 'Value', 'Unit'])
        stats = get_sustainability_stats()
        writer.writerow(['Electricity Usage', stats['electricity'], 'kWh'])
        writer.writerow(['Water Consumption', stats['water'], 'Liters'])
        writer.writerow(['Waste Recycled', stats['waste'], 'Tons'])
        writer.writerow(['Recycling Rate', stats['recycling_rate'], '%'])
        writer.writerow(['Estimated Carbon Footprint', stats['carbon_emissions'], 'Metric Tons CO2e'])
        
    else:
        return redirect(url_for('dashboard'))
        
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    response.headers["Content-type"] = "text/csv"
    return response

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
