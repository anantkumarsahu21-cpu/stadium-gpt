// StadiumGPT - Indoor Navigation Map Controls

// 1. Coordinates Mapping for SVG Path Rendering
const COORDINATES = {
    // Gates
    "gate-A": { x: 300, y: 110, label: "Gate A (North Entrance)" },
    "gate-B": { x: 510, y: 300, label: "Gate B (East Transport Hub)" },
    "gate-C": { x: 300, y: 490, label: "Gate C (South Food Plaza)" },
    "gate-D": { x: 90, y: 300, label: "Gate D (West VIP Entrance)" },

    // Seating Sections
    "sec-101": { x: 300, y: 200, label: "Seat Sector 101 (North Stands)" },
    "sec-102": { x: 390, y: 300, label: "Seat Sector 102 (East Stands)" },
    "sec-103": { x: 300, y: 400, label: "Seat Sector 103 (South Stands)" },
    "sec-104": { x: 210, y: 300, label: "Seat Sector 104 (West Stands)" },

    // Facilities
    "facility-restroom-102": { x: 430, y: 220, label: "Restroom - Section 102 (ADA)" },
    "facility-restroom-204": { x: 170, y: 380, label: "Restroom - Section 204" },
    "facility-food-110": { x: 330, y: 460, label: "Taco Arena - Section 110" },
    "facility-food-124": { x: 270, y: 460, label: "Burger Box - Section 124" },
    "facility-medical-A": { x: 270, y: 140, label: "Medical Command - Gate A" },
    "facility-medical-D": { x: 130, y: 270, label: "Medical Command - Gate D" }
};

let lastSelectedMapObject = null;

// 2. Select Handlers for Map elements
window.selectSection = function(id, status, occupancy) {
    revealInspector(
        `Seat Sector ${id}`,
        `${status} (${occupancy}% occupied)`,
        `This section serves Level 1 general admission tickets. Safe evacuation routes lead directly to Gate A or B. Smart crowd predictions suggest steady egress post-match.`,
        `sec-${id}`
    );
    highlightSVGElement(`sec-${id}`);
};

window.selectGate = function(name, sub, parking) {
    revealInspector(
        name,
        sub,
        `Main security checkpoint. Egress routes connect to ${parking}. Direct elevator facilities serve ADA ticket holders at North Gate checkpoint.`,
        `gate-${name.charAt(name.length - 1)}`.toLowerCase() // matches SVG element IDs
    );
    highlightSVGElement(`gate-${name.charAt(name.length - 1)}`);
};

window.selectFacility = function(type, location, notes) {
    const keyMap = {
        "Section 102": "facility-restroom-102",
        "Section 204": "facility-restroom-204",
        "Section 110 (Taco Arena)": "facility-food-110",
        "Section 124 (Burger Box)": "facility-food-124",
        "Gate A / Sec 101": "facility-medical-A",
        "Gate D / Sec 104": "facility-medical-D"
    };

    revealInspector(
        `${type} - ${location}`,
        "Active Facility",
        `Details: ${notes}. Operating at optimal parameters. Wheelchair ramps and elevator linkages connect directly to the main concourse level.`,
        keyMap[location]
    );
    highlightSVGElement(keyMap[location]);
};

function revealInspector(title, subtitle, desc, keyId) {
    const card = document.getElementById('map-selection-card');
    const content = document.getElementById('inspector-content');
    
    if (!card || !content) return;
    
    document.getElementById('inspect-title').innerText = title;
    
    const subtitleBadge = document.getElementById('inspect-subtitle');
    subtitleBadge.innerText = subtitle;
    
    // adjust subtitle colors depending on occupancy/danger
    if (subtitle.includes('High') || subtitle.includes('Critical')) {
        subtitleBadge.className = "badge bg-danger";
    } else if (subtitle.includes('Medium')) {
        subtitleBadge.className = "badge bg-warning text-dark";
    } else {
        subtitleBadge.className = "badge bg-success";
    }

    document.getElementById('inspect-description').innerText = desc;
    
    content.classList.remove('d-none');
    lastSelectedMapObject = keyId;
}

// Highlight clicked SVG item
function highlightSVGElement(id) {
    // clear active styling
    const shapes = document.querySelectorAll('.stadium-section, .stadium-gate, .stadium-restroom, .stadium-food, .stadium-medical');
    shapes.forEach(s => {
        s.style.strokeWidth = s.classList.contains('stadium-section') ? '2' : '1';
        s.style.stroke = s.classList.contains('stadium-section') ? 'var(--border-card)' : '#000';
    });

    const activeEl = document.getElementById(id);
    if (activeEl) {
        activeEl.style.stroke = "#ffaa00";
        activeEl.style.strokeWidth = "4";
    }
}

// Target Route Plot handler
window.routeToSelected = function() {
    if (!lastSelectedMapObject) return;
    
    const destSelector = document.getElementById('nav-dest');
    if (destSelector) {
        // Set values and run
        destSelector.value = lastSelectedMapObject;
        calculatePath();
        
        // Show notification
        window.showNotification("Path Plotted", `Route has been highlighted to ${COORDINATES[lastSelectedMapObject].label}`, "primary");
    }
};

// 3. Vector Pathfinding Calculator
window.calculatePath = function() {
    const sourceVal = document.getElementById('nav-source').value;
    const destVal = document.getElementById('nav-dest').value;
    const accessibleChecked = document.getElementById('nav-accessible').checked;
    
    const src = COORDINATES[sourceVal];
    const dst = COORDINATES[destVal];
    
    if (!src || !dst) return;
    
    // Calculate intermediate waypoints for elegant visual curves around center pitch
    // If path crosses the center pitch, route around the perimeter
    const pathLine = document.getElementById('nav-routing-line');
    if (!pathLine) return;
    
    let pathD = `M ${src.x} ${src.y}`;
    
    // Waypoint math: detour around center (300, 300) if crossing pitch
    const needsDetour = (src.x < 300 && dst.x > 300) || (src.x > 300 && dst.x < 300) || 
                        (src.y < 300 && dst.y > 300) || (src.y > 300 && dst.y < 300);
                        
    if (needsDetour) {
        // Route through upper or lower perimeter ring
        const midY = (src.y + dst.y) / 2 > 300 ? 430 : 170;
        const midX = (src.x + dst.x) / 2 > 300 ? 420 : 180;
        pathD += ` Q ${midX} ${midY}, ${dst.x} ${dst.y}`;
    } else {
        pathD += ` L ${dst.x} ${dst.y}`;
    }
    
    pathLine.setAttribute('d', pathD);
    pathLine.style.display = 'block';
    
    // Render text output directions
    const instructionBox = document.getElementById('nav-result-card');
    const textDest = document.getElementById('nav-instructions-text');
    
    if (instructionBox && textDest) {
        let text = `Depart from ${src.label}. Walk along the inner concourse route towards Section ${destVal.includes('sec-') ? destVal.substring(4) : 'facilities'}. `;
        if (accessibleChecked) {
            text += `ADA Priority: Follow green tactile pavement arrows and use the elevators located at Gate A or Gate D. Avoid steps at Ramps 101.`;
        } else {
            text += `Standard route: Proceed via Ramps 101 or escalators to level 2. Total distance approx. 120m.`;
        }
        
        textDest.innerText = text;
        instructionBox.classList.remove('d-none');
    }
};
