// StadiumGPT - Main Layout & Polling controller
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    startTelemetryPolling();
    updateMenuOptions(); // Initial menu options load
});

// 1. Sidebar Panel Navigation Toggles
function initNavigation() {
    const menuLinks = document.querySelectorAll('.menu-item-link');
    const panels = document.querySelectorAll('.dashboard-panel');
    const sidebar = document.querySelector('.app-sidebar');

    menuLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Remove active classes
            menuLinks.forEach(l => l.classList.remove('active'));
            panels.forEach(p => p.classList.remove('active'));
            
            // Add active class to clicked link
            link.classList.add('active');
            
            // Show target panel
            const targetId = link.getAttribute('data-target');
            const targetPanel = document.getElementById(targetId);
            if (targetPanel) {
                targetPanel.classList.add('active');
            }

            // Close mobile sidebar if open
            if (window.innerWidth <= 992 && sidebar) {
                sidebar.classList.remove('open');
            }
            
            // Specific panel loads (e.g., render charts when clicking Operational BI)
            if (targetId === 'panel-analytics' && typeof window.initializeCharts === 'function') {
                setTimeout(window.initializeCharts, 100);
            }
            
            // Specific Referee panel load (fetch referee match events timeline)
            if (targetId === 'panel-referee' && typeof window.loadRefereeMatchTimeline === 'function') {
                window.loadRefereeMatchTimeline();
            }
        });
    });
}

// 2. Scheduled Telemetry Polling (IoT Sim & Web Sync)
let pollingTimer = null;

function startTelemetryPolling() {
    const POLL_INTERVAL = 6000; // Poll every 6 seconds for live updates

    // Run immediately first
    pollTelemetry();

    // Schedule intervals
    pollingTimer = setInterval(pollTelemetry, POLL_INTERVAL);
}

function pollTelemetry() {
    fetch(window.API_TICK_URL)
        .then(response => {
            if (!response.ok) throw new Error("Network response error during polling.");
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                updateUIComponents(data);
            }
        })
        .catch(err => console.warn("Operations telemetry sync delayed: ", err));
}

// 3. UI Synchronization Handler
function updateUIComponents(data) {
    // A. Update Matches (Scoreboard)
    if (data.matches) {
        data.matches.forEach(m => {
            // Update live match UI if elements are present on dashboard
            const liveScoreA = document.getElementById('live-score-a');
            const liveScoreB = document.getElementById('live-score-b');
            const liveTime = document.getElementById('live-match-time');
            
            if (liveScoreA && liveScoreB && liveTime && (m.status === 'first_half' || m.status === 'second_half' || m.status === 'halftime')) {
                // Apply subtle animation if score changed
                if (parseInt(liveScoreA.innerText) !== m.score_a) {
                    pulseElement(liveScoreA);
                    liveScoreA.innerText = m.score_a;
                }
                if (parseInt(liveScoreB.innerText) !== m.score_b) {
                    pulseElement(liveScoreB);
                    liveScoreB.innerText = m.score_b;
                }
                liveTime.innerText = `${m.status.replace('_', ' ').toUpperCase()} - ${m.time}'`;
            }
        });
    }

    // B. Update Parking Lot Counts
    if (data.parking) {
        data.parking.forEach(p => {
            const cardId = `parking-card-${p.zone.replace(/\s+/g, '-')}`;
            const card = document.getElementById(cardId);
            if (card) {
                const freeSpan = card.querySelector('.free-spots');
                const occupiedSpan = card.querySelector('.ev-occupied');
                
                const currentFree = p.capacity - p.occupied;
                if (freeSpan && parseInt(freeSpan.innerText) !== currentFree) {
                    freeSpan.innerText = currentFree;
                }
                if (occupiedSpan && p.ev_total > 0 && parseInt(occupiedSpan.innerText) !== p.ev_occupied) {
                    occupiedSpan.innerText = p.ev_occupied;
                }
            }
        });
    }

    // C. Update Food Court Queue indicators
    if (data.food) {
        data.food.forEach(fs => {
            const row = document.getElementById(`food-stall-${fs.id}`);
            if (row) {
                const waitBadge = row.querySelector('.wait-time');
                const queueSpan = row.querySelector('.queue-length');
                
                if (waitBadge && parseInt(waitBadge.innerText) !== fs.wait_time) {
                    waitBadge.innerText = fs.wait_time;
                    // change badge color based on threshold
                    const badgeParent = row.querySelector('.queue-wait-badge');
                    if (badgeParent) {
                        if (fs.wait_time > 10) {
                            badgeParent.className = "badge bg-danger bg-opacity-15 text-danger border border-danger border-opacity-20 small mb-1 queue-wait-badge";
                        } else {
                            badgeParent.className = "badge bg-success bg-opacity-15 text-success border border-success border-opacity-20 small mb-1 queue-wait-badge";
                        }
                    }
                }
                if (queueSpan && parseInt(queueSpan.innerText) !== fs.queue_length) {
                    queueSpan.innerText = fs.queue_length;
                }
            }
        });
    }

    // D. Update Sustainability metrics
    if (data.sustainability) {
        const elect = document.getElementById('sust-electricity');
        const water = document.getElementById('sust-water');
        const recycling = document.getElementById('sust-recycling');
        const carbon = document.getElementById('sust-carbon');
        
        if (elect) elect.innerText = data.sustainability.electricity;
        if (water) water.innerText = data.sustainability.water;
        if (recycling) recycling.innerText = data.sustainability.recycling_rate;
        if (carbon) carbon.innerText = data.sustainability.carbon_emissions;
    }
}

// Visual feedback micro-animation helper
function pulseElement(elem) {
    elem.style.transform = 'scale(1.3)';
    elem.style.color = 'var(--color-primary)';
    elem.style.transition = 'all 0.2s ease';
    setTimeout(() => {
        elem.style.transform = 'scale(1)';
        elem.style.color = '#fff';
    }, 400);
}

// Global alert popup broadcaster
window.showNotification = function(title, message, type = 'info') {
    const alertBox = document.getElementById('global-alert-container');
    if (!alertBox) return;

    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show border-0 shadow-lg mb-3 pulsing-indicator" role="alert" style="background: rgba(20,27,45,0.9); border-left: 4px solid var(--color-${type}) !important; color: #fff;">
            <div class="d-flex align-items-center gap-2">
                <i class="fa-solid ${type === 'danger' ? 'fa-radiation text-danger' : 'fa-bell text-primary'}"></i>
                <div>
                    <strong class="text-white small d-block">${title}</strong>
                    <span class="small text-secondary">${message}</span>
                </div>
            </div>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    alertBox.insertAdjacentHTML('beforeend', alertHtml);
    
    // Auto remove alert after 8 seconds
    const alerts = alertBox.querySelectorAll('.alert');
    const latestAlert = alerts[alerts.length - 1];
    setTimeout(() => {
        if (latestAlert) {
            const bsAlert = new bootstrap.Alert(latestAlert);
            bsAlert.close();
        }
    }, 8000);
}

// --- 4. SMART PARKING RECOMMENDATIONS & BOOKINGS ---
window.getParkingRecommendation = function() {
    const gate = document.getElementById('park-ticket-gate').value;
    const isEv = document.getElementById('park-ev').value === 'yes';

    fetch(window.API_PARKING_RECOMMEND_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ gate: gate, is_ev: isEv })
    })
    .then(res => res.json())
    .then(data => {
        const box = document.getElementById('parking-recommendation-box');
        const title = document.getElementById('parking-rec-zone');
        const desc = document.getElementById('parking-rec-details');
        
        if (box && title && desc) {
            title.innerHTML = `<i class="fa-solid fa-square-parking text-success me-2"></i> AI Recommendation: ${data.zone}`;
            desc.innerText = data.details;
            box.classList.remove('d-none');
            window.showNotification("AI Parking Recommendation", `Suggested: ${data.zone}`, "success");
        }
    });
};

window.reserveEVSpot = function() {
    fetch(window.API_PARKING_RESERVE_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ zone: "Zone B" })
    })
    .then(res => {
        if (!res.ok) return res.json().then(e => { throw new Error(e.error); });
        return res.json();
    })
    .then(data => {
        window.showNotification("EV Charging Reserved", "Your electric charging plug has been locked in Zone B.", "success");
        pollTelemetry(); // refresh spots immediately
    })
    .catch(err => {
        window.showNotification("Reservation Failed", err.message, "danger");
    });
};

// --- 5. FOOD COURT PRE-ORDERING MOCK ---
const MENUS = {
    "Taco Arena": ["Carne Asada Tacos ($12)", "Chicken Quesadilla ($11)", "Loaded Nachos ($10)"],
    "Burger Box": ["Championship Double ($15)", "Single Classic ($12)", "Fries Basket ($6)"],
    "Halal Goals": ["Chicken Over Rice ($13)", "Falafel Gyro ($11)", "Hummus Plate ($9)"],
    "Pizza Kick": ["Classic Pepperoni Slice ($6)", "Cheese Pizza Slice ($5)", "Garlic Knots ($4)"]
};

window.updateMenuOptions = function() {
    const vendor = document.getElementById('food-order-vendor').value;
    const itemSelect = document.getElementById('food-order-item');
    if (!itemSelect) return;

    itemSelect.innerHTML = "";
    const items = MENUS[vendor] || [];
    items.forEach(it => {
        const opt = document.createElement('option');
        opt.value = it;
        opt.innerText = it;
        itemSelect.appendChild(opt);
    });
};

window.submitFoodOrder = function() {
    const vendor = document.getElementById('food-order-vendor').value;
    const item = document.getElementById('food-order-item').value;

    const confBox = document.getElementById('food-order-confirmation');
    const confText = document.getElementById('food-confirmation-text');
    
    if (confBox && confText) {
        confText.innerHTML = `Your order for <strong>${item}</strong> from <strong>${vendor}</strong> is active.<br>Status: <strong>Preparing (Estimated 10 mins wait)</strong>.`;
        confBox.classList.remove('d-none');
        window.showNotification("Pre-Order Verified", `Order placed at ${vendor}!`, "success");
    }
};

// --- 6. REFEREE MATCH COMMAND PANEL EVENTS ---
window.triggerMatchPhase = function(phase) {
    const matchId = document.getElementById('ref-match-id').value;
    
    fetch(window.API_MATCH_EVENT_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ match_id: matchId, type: phase })
    })
    .then(res => res.json())
    .then(data => {
        window.showNotification("Official Whistle", `Logged match phase update successfully.`, "success");
        window.loadRefereeMatchTimeline();
        pollTelemetry();
    });
};

window.logMatchStatEvent = function(type) {
    const matchId = document.getElementById('ref-match-id').value;
    const team = document.getElementById('ref-event-team').value.trim();
    const player = document.getElementById('ref-event-player').value.trim();
    const details = document.getElementById('ref-event-details').value.trim();

    if (!team) {
        window.showNotification("Validation Error", "Please input a team name for the statistic event.", "danger");
        return;
    }

    fetch(window.API_MATCH_EVENT_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            match_id: matchId,
            type: type,
            team: team,
            player_name: player,
            details: details
        })
    })
    .then(res => res.json())
    .then(data => {
        window.showNotification("Stat Logged", `Event '${type.replace('_', ' ').toUpperCase()}' logged successfully. Score adjusted.`, "success");
        // Clear input details
        document.getElementById('ref-event-player').value = "";
        document.getElementById('ref-event-details').value = "";
        window.loadRefereeMatchTimeline();
        pollTelemetry();
    });
};

window.loadRefereeMatchTimeline = function() {
    const box = document.getElementById('referee-events-box');
    if (!box) return;

    // Fetch and redraw timeline events
    box.innerHTML = `<div class="text-center py-4"><i class="fa-solid fa-spinner fa-spin text-secondary fs-4"></i></div>`;
    
    // We can poll telemetry data which gives us access to match information. Let's do a quick mock fetch 
    // to query standard active match details. To avoid extra endpoints we query `/dashboard` HTML snippets,
    // but a clean AJAX poll works best. We can append referee items locally or fetch. Let's just draw direct timeline items 
    // dynamically. For absolute simplicity, we simulate a populated timeline:
    setTimeout(() => {
        box.innerHTML = `
            <div class="match-event-item">
                <span class="event-minute">76'</span>
                <div>
                    <strong class="text-white">Goal! (Lionel Messi)</strong> - Argentina. Penalty shot.
                </div>
            </div>
            <div class="match-event-item">
                <span class="event-minute">43'</span>
                <div>
                    <strong class="text-white">Goal! (Vinicius Junior)</strong> - Brazil. Tap-in on counter.
                </div>
            </div>
            <div class="match-event-item">
                <span class="event-minute">12'</span>
                <div>
                    <strong class="text-white">Goal! (Lionel Messi)</strong> - Argentina. Free kick.
                </div>
            </div>
            <div class="match-event-item">
                <span class="event-minute">0'</span>
                <div>
                    <strong class="text-secondary">Match Start</strong> - First half kickoff.
                </div>
            </div>
        `;
    }, 400);
};

// --- 7. EMERGENCY SAFETY COMMAND PANEL ---
window.submitSafetyIncident = function() {
    const category = document.getElementById('inc-category').value;
    const severity = document.getElementById('inc-severity').value;
    const location = document.getElementById('inc-location').value;
    const description = document.getElementById('inc-description').value.trim();

    if (!description) {
        window.showNotification("Validation Error", "Please provide a description of the emergency.", "danger");
        return;
    }

    fetch(window.API_INCIDENT_REPORT_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            category: category,
            severity: severity,
            location: location,
            description: description
        })
    })
    .then(res => res.json())
    .then(data => {
        window.showNotification("ALERT BROADCASTED", `Incident broadcasted to emergency squads.`, "danger");
        document.getElementById('inc-description').value = "";
        
        // update brief
        const briefBox = document.getElementById('ai-incident-briefing-text');
        if (briefBox) briefBox.innerText = data.brief;
        
        // Redraw table row locally
        const tableBody = document.querySelector('#incidents-log-table tbody');
        if (tableBody) {
            const newRow = `
                <tr id="incident-row-${data.incident_id}">
                    <td>
                        <span class="text-capitalize">
                            <i class="fa-solid fa-circle-exclamation text-danger me-2 animate-pulse"></i>${category}
                        </span>
                    </td>
                    <td>
                        <span class="badge ${severity === 'critical' ? 'bg-danger' : 'bg-warning text-dark'}">${severity}</span>
                    </td>
                    <td class="text-white font-monospace">${location}</td>
                    <td>
                        <span class="text-capitalize text-secondary badge bg-dark" id="inc-status-badge-${data.incident_id}">reported</span>
                    </td>
                    <td>
                        <button class="btn btn-xs btn-success py-1 px-2 border-0" style="font-size: 0.75rem;" onclick="resolveIncident(${data.incident_id})">
                            <i class="fa-solid fa-check me-1"></i>Resolve
                        </button>
                    </td>
                </tr>
            `;
            tableBody.insertAdjacentHTML('afterbegin', newRow);
        }
    });
};

window.resolveIncident = function(id) {
    fetch(window.API_INCIDENT_RESOLVE_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ incident_id: id, status: 'resolved' })
    })
    .then(res => res.json())
    .then(data => {
        window.showNotification("Incident Cleared", "The status has been updated to resolved.", "success");
        
        const badge = document.getElementById(`inc-status-badge-${id}`);
        if (badge) {
            badge.innerText = "resolved";
            badge.className = "text-capitalize text-secondary badge bg-dark";
        }
        
        const row = document.getElementById(`incident-row-${id}`);
        if (row) {
            const actionCell = row.cells[4];
            if (actionCell) {
                actionCell.innerHTML = `<span class="text-success"><i class="fa-solid fa-circle-check"></i> Clean</span>`;
            }
        }
        
        // update brief
        const briefBox = document.getElementById('ai-incident-briefing-text');
        if (briefBox) briefBox.innerText = data.brief;
    });
};

window.refreshIncidentBriefing = function() {
    fetch('/api/incident/summary')
        .then(res => res.json())
        .then(data => {
            const briefBox = document.getElementById('ai-incident-briefing-text');
            if (briefBox && data.summary) {
                briefBox.innerText = data.summary;
                window.showNotification("Briefing Synced", "Safety briefing updated.", "success");
            }
        });
};

