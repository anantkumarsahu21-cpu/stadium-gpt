import pytest
from ai_service import generate_stadium_reply, generate_match_summary, generate_incident_report_summary

def test_stadium_assistant_fallback():
    # Test gate replies
    reply_gate = generate_stadium_reply("where is gate b?")
    assert "Gate B" in reply_gate
    assert "East side" in reply_gate

    # Test restroom replies
    reply_restroom = generate_stadium_reply("nearest restroom or toilet?")
    assert "restrooms" in reply_restroom.lower()

    # Test accessibility replies
    reply_ada = generate_stadium_reply("do you have wheelchair elevator or ada ramp routes?")
    assert "elevators" in reply_ada.lower() or "accessibility" in reply_ada.lower()

    # Test parking replies
    reply_parking = generate_stadium_reply("what parking zones have ev charging?")
    assert "EV Parking" in reply_parking or "Zone B" in reply_parking

def test_local_match_summarizer():
    match_info = {
        "team_a": "Argentina",
        "team_b": "Brazil",
        "score_a": 2,
        "score_b": 1
    }
    
    # Class mimicking MatchEvent attributes
    class MockEvent:
        def __init__(self, minute, type, player_name, team, details):
            self.minute = minute
            self.type = type
            self.player_name = player_name
            self.team = team
            self.details = details

    events = [
        MockEvent(12, 'goal', 'Lionel Messi', 'Argentina', 'Curling free-kick'),
        MockEvent(43, 'goal', 'Vinicius Junior', 'Brazil', 'Tap-in counter'),
        MockEvent(76, 'goal', 'Lionel Messi', 'Argentina', 'Penalty shot')
    ]
    
    summary = generate_match_summary(match_info, events)
    assert "Argentina defeated Brazil" in summary
    assert "2\u20131" in summary or "2-1" in summary or "finished" in summary or "score" in summary
    assert "Messi" in summary

def test_local_incident_summarizer():
    # Mock incident objects
    class MockIncident:
        def __init__(self, location, category, severity, description, status, timestamp):
            self.location = location
            self.category = category
            self.severity = severity
            self.description = description
            self.status = status
            self.timestamp = timestamp

    import datetime
    now = datetime.datetime.now()
    
    incidents = [
        MockIncident("Section 102", "medical", "critical", "Spectator heart issues", "reported", now)
    ]
    
    summary = generate_incident_report_summary(incidents)
    assert "active incident" in summary.lower() or "command" in summary.lower()
    assert "critical" in summary.lower()
