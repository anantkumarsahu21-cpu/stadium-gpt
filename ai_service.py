import os
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Attempt to configure Gemini API
HAS_GEMINI = False
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_KEY)
        # We will use gemini-1.5-flash or gemini-2.5-flash
        model = genai.GenerativeModel('gemini-1.5-flash')
        HAS_GEMINI = True
        print("Gemini API configured successfully.")
    except Exception as e:
        print(f"Failed to configure Gemini API, falling back to local NLP: {e}")

STADIUM_KNOWLEDGE_BASE = """
You are the FIFA World Cup 2026 AI Stadium Assistant for MetLife Stadium (referred to as FIFA Stadium NYNJ).
Here are the official stadium configurations and details:
- Gates:
  * Gate A (North): General entry, closest to Parking Lots A & B. Has ADA entrance and elevator access.
  * Gate B (East): Public transport hub. Directly adjacent to the Meadowlands Rail Station and Guest Services (Lost & Found).
  * Gate C (South): Food Court Plaza entrance, closest to Parking Lot C.
  * Gate D (West): VIP & Media entrance, closest to Parking Lot D (VIP/Media parking). Has elevator access.
- Restrooms:
  * Section 102 (ADA accessible, family room, baby changing stations).
  * Section 118 (Men and Women restrooms).
  * Section 204 (ADA accessible, Men and Women restrooms).
  * Section 224 (Men and Women restrooms).
- Food Stalls & Cuisine:
  * Taco Arena (Section 110): Mexican street tacos, nachos, and churros.
  * Burger Box (Section 124): Premium beef burgers, vegetarian patties, and dynamic fries.
  * Halal Goals (Section 208): Halal gyro, chicken over rice, shawarma, and falafel.
  * Pizza Kick (Section 230): Italian style pizza slices and garlic knots.
- Wheelchair & Accessibility Routes:
  * Elevators: Located at Gate A (North) and Gate D (West).
  * ADA Ramps: Located near Sections 101 and 120.
  * Accessible Seating: Available in Row WC of Sections 102, 115, 204, and 222.
- Lost & Found:
  * Located at the Guest Services desk near Section 128 (immediately inside Gate B).
- Emergency Exits & Exits:
  * Main Exits: Gates A, B, C, and D are the primary emergency exit pathways.
  * Procedures: In an emergency, look for the flashing neon floor arrows that lead to the nearest Gate. Avoid elevators.
- Public Transport & Rideshare:
  * Train: Meadowlands Rail Station is directly outside Gate B. Direct shuttle trains to Secaucus Junction run every 10 minutes post-match.
  * NJ Transit Bus: Route 351 runs from Port Authority Terminal in NYC directly to the stadium parking Lot K.
  * Rideshare (Uber/Lyft/Taxi): Drop-off and pick-up zone is designated at Parking Lot E.
- Parking Zones:
  * Zone A (North): General parking, close to Gate A.
  * Zone B (North-East): EV Parking with 30 active smart chargers. Reservation required.
  * Zone C (South): General and bus parking, close to Gate C.
  * Zone D (West): Reserved VIP & Media parking. Pass holders only.
"""

def generate_stadium_reply(query: str) -> str:
    """
    Responds to stadium operations and navigation queries from fans or staff.
    Uses Gemini API if available, otherwise falls back to the smart local NLP parser.
    """
    clean_query = query.strip().lower()
    
    if HAS_GEMINI:
        try:
            prompt = f"{STADIUM_KNOWLEDGE_BASE}\n\nUser Question: {query}\n\nAnswer the user's question accurately, politely, and concisely using the facts above. Keep your answer under 3-4 sentences. If the question is not about the stadium or tournament, politely redirect them."
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Gemini API call failed, using local fallback: {e}")
            # Fall through to local fallback

    # --- LOCAL SMART NLP FALLBACK ENGINE ---
    # Keyword analysis
    
    # 1. Gates
    if "gate a" in clean_query:
        return "Gate A is located on the North side of the stadium. It serves as a general entry point, is closest to Parking Lots A & B, and offers an ADA entrance with elevator access."
    elif "gate b" in clean_query:
        return "Gate B is located on the East side of the stadium. It is adjacent to the Meadowlands Rail Station and is the closest entrance to the Guest Services desk (Lost & Found)."
    elif "gate c" in clean_query:
        return "Gate C is located on the South side of the stadium, right next to the Food Court Plaza and closest to Parking Lot C."
    elif "gate d" in clean_query:
        return "Gate D is on the West side of the stadium. It is reserved for VIPs, media representatives, and suite holders, with direct access to Parking Lot D and elevator access."
    elif "gate" in clean_query:
        return "The stadium has four main gates: Gate A (North - ADA entry/General), Gate B (East - Train station & Lost/Found), Gate C (South - Food Court), and Gate D (West - VIP & Media)."

    # 2. Restrooms
    if any(k in clean_query for k in ["restroom", "toilet", "bathroom", "washroom", "wc"]):
        if "wheelchair" in clean_query or "ada" in clean_query or "accessible" in clean_query or "family" in clean_query:
            return "Accessible and family restrooms are located at Section 102 (field level) and Section 204 (concourse level). Both include baby changing tables and wider entry points."
        return "Restrooms are distributed throughout the stadium. Recommended locations: Section 118 and 224 for general restrooms, and Sections 102 and 204 for ADA-accessible and family restrooms."

    # 3. Accessibility / Wheelchair
    if any(k in clean_query for k in ["wheelchair", "ada", "disabled", "ramp", "elevator", "accessible"]):
        return "Accessibility services include elevators at Gate A (North) and Gate D (West), ADA ramps near Sections 101 and 120, and dedicated wheelchair companion seating in Row WC of Sections 102, 115, 204, and 222."

    # 4. Food & Food Courts
    if any(k in clean_query for k in ["food", "eat", "menu", "restaurant", "hungry", "taco", "burger", "halal", "pizza"]):
        if "taco" in clean_query:
            return "Taco Arena is located at Section 110. They serve authentic street tacos, nachos, and hot churros."
        elif "burger" in clean_query:
            return "Burger Box is located at Section 124, serving premium flame-grilled beef burgers, vegetarian options, and side fries."
        elif "halal" in clean_query:
            return "Halal Goals is located at Section 208, featuring gyro platters, chicken over rice, shawarma, and falafel options."
        elif "pizza" in clean_query:
            return "Pizza Kick is located at Section 230, offering hot Italian style pizza slices and garlic knots."
        return "We have four main dining spots: Taco Arena (Section 110 - Mexican), Burger Box (Section 124 - American), Halal Goals (Section 208 - Halal Shawarma & Gyro), and Pizza Kick (Section 230 - Italian Pizza)."

    # 5. Parking
    if "parking" in clean_query or "car" in clean_query or "park" in clean_query:
        if "ev" in clean_query or "charger" in clean_query:
            return "EV Charging is located in Parking Zone B (North-East). It features 30 smart charging stations, and spaces must be reserved in advance via the Smart Parking dashboard."
        elif "vip" in clean_query or "media" in clean_query:
            return "VIP and Media parking is located in Zone D (West side). A valid digital VIP parking pass is required for entry."
        return "Stadium parking is split into: Zone A (North, closest to Gate A), Zone B (North-East, has EV chargers), Zone C (South, general and bus parking), and Zone D (West, VIP/Media only). We recommend Zone A or C for general ticket holders."

    # 6. Lost & Found
    if "lost" in clean_query or "found" in clean_query or "item" in clean_query or "wallet" in clean_query or "phone" in clean_query:
        return "Lost and Found is managed at the main Guest Services desk, located near Section 128, just inside Gate B (East entrance). You can report or claim items there directly."

    # 7. Exits & Emergency Exits
    if "exit" in clean_query or "emergency" in clean_query or "fire" in clean_query or "evacuate" in clean_query:
        return "In case of emergency, please proceed calmly to the nearest main gate (Gate A, B, C, or D). Follow the flashing green and neon arrow indicators on the floor. Do NOT use elevators."

    # 8. Public Transport & Trains
    if any(k in clean_query for k in ["train", "bus", "transport", "metro", "transit", "uber", "taxi", "rideshare"]):
        if "train" in clean_query or "rail" in clean_query:
            return "Meadowlands Rail Station is directly outside Gate B (East). Trains run to Secaucus Junction every 10 minutes immediately following the match."
        elif "bus" in clean_query:
            return "NJ Transit Bus Route 351 operates round-trips from NYC Port Authority direct to Parking Lot K. It is a quick and cheap option."
        elif "rideshare" in clean_query or "uber" in clean_query or "lyft" in clean_query:
            return "Rideshare (Uber/Lyft) pickup and drop-off is strictly designated at Parking Lot E. Direct walking routes connect Lot E to Gates A and B."
        return "Public transport options include the Meadowlands Rail Station outside Gate B, NJ Transit Bus Route 351 at Lot K, and rideshare services in Parking Lot E."
        
    # 9. Match Summaries
    if "match" in clean_query or "score" in clean_query or "who won" in clean_query or "summary" in clean_query:
        return "You can check the live match operations panel and the media section for live scores, active tournament rankings, and real-time match events!"

    # Default friendly answer matching keywords or general greeting
    return "I am your Stadium AI Assistant. I can help you find Gates, Restrooms, Food Stalls, Parking zones, ADA accessibility routes, Lost & Found, and public transport options. How can I assist you today?"


def generate_match_summary(match_info: dict, events: list) -> str:
    """
    Generates a human-like match summary from the match details and the logged events list.
    """
    team_a = match_info.get('team_a')
    team_b = match_info.get('team_b')
    score_a = match_info.get('score_a', 0)
    score_b = match_info.get('score_b', 0)
    
    events_str = ""
    for ev in events:
        events_str += f"- Minute {ev.minute}: {ev.type.replace('_', ' ').title()} by {ev.player_name or 'Player'} ({ev.team or ''}) - Details: {ev.details or ''}\n"

    if HAS_GEMINI:
        try:
            prompt = f"""
            Write an exciting, professional news summary (around 3-4 sentences) for a football match:
            Match: {team_a} vs {team_b}
            Final Score: {team_a} {score_a} - {score_b} {team_b}
            Key Events:
            {events_str}
            
            Follow this format: Include the final result, key goalscorers/moments, and a summary of how the match played out. Keep it realistic and engaging.
            """
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Gemini Match Summary call failed, using local generator: {e}")

    # --- LOCAL MATCH SUMMARY GENERATOR ---
    goals = [e for e in events if e.type == 'goal']
    red_cards = [e for e in events if e.type == 'red_card']
    var_reviews = [e for e in events if e.type == 'var_review']
    
    if score_a > score_b:
        result_desc = f"{team_a} defeated {team_b} by a score of {score_a}–{score_b} in a thrilling matchup."
    elif score_b > score_a:
        result_desc = f"{team_b} claimed a well-earned victory over {team_a}, finishing {score_b}–{score_a}."
    else:
        result_desc = f"The high-stakes clash between {team_a} and {team_b} ended in a hard-fought {score_a}–{score_b} draw."

    goal_desc = ""
    if goals:
        goal_scorers = [f"{g.player_name} ({g.minute}')" for g in goals if g.player_name]
        if goal_scorers:
            goal_desc = " Key goals came from " + ", ".join(goal_scorers) + "."
    
    extras = []
    if red_cards:
        extras.append("The referee issued red cards, causing tactical shifts.")
    if var_reviews:
        extras.append("VAR reviews added tension to critical decisions.")
    
    extras_desc = " " + " ".join(extras) if extras else " Both teams displayed exceptional coordination and physical endurance under intense conditions."
    
    return f"{result_desc}{goal_desc}{extras_desc} The result has significant implications for the tournament standings."


def generate_incident_report_summary(incidents: list) -> str:
    """
    Generates a command summary briefing of active or resolved emergency incidents.
    """
    if not incidents:
        return "All clear. No active safety or medical incidents reported in the stadium command log."
        
    incident_details = ""
    for idx, inc in enumerate(incidents, 1):
        incident_details += f"{idx}. Location: {inc.location} | Category: {inc.category} | Severity: {inc.severity} | Description: {inc.description} | Status: {inc.status} | Time: {inc.timestamp.strftime('%H:%M:%S')}\n"

    if HAS_GEMINI:
        try:
            prompt = f"""
            As the Stadium Command Center Intelligence Coordinator, write a structured operational summary (2-3 sentences) summarizing the following stadium incident report log:
            
            {incident_details}
            
            Synthesize the active alerts, general severity level, response status, and recommend any critical actions for security and medical dispatch.
            """
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Gemini Incident Summary call failed, using local generator: {e}")

    # --- LOCAL INCIDENT SUMMARY GENERATOR ---
    total = len(incidents)
    criticals = [i for i in incidents if i.severity.lower() == 'critical']
    active = [i for i in incidents if i.status.lower() != 'resolved']
    
    summary_text = f"Stadium Command has logged {total} active incident reports. "
    if criticals:
        summary_text += f"There are {len(criticals)} CRITICAL status alert(s) requiring immediate attention (specifically in {', '.join(set(c.location for c in criticals))}). "
    else:
        summary_text += "There are no critical red-level security alerts currently active. "
        
    if active:
        summary_text += f"Response teams have been dispatched and are currently resolving {len(active)} open incidents. Dispatch is monitoring situation levels continuously."
    else:
        summary_text += "All logged safety incidents have been successfully resolved by security and medical units."
        
    return summary_text
