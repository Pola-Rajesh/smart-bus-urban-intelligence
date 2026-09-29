const API_BASE = "http://127.0.0.1:8000";


// ============================================================
// GLOBAL STATE
// ============================================================

let allEvents = [];

let currentDepartment = "pothole";

let currentStatus = "all";

let currentSort = "priority";


// ============================================================
// DOM READY
// ============================================================

window.addEventListener("DOMContentLoaded", () => {

    setupDepartmentTabs();

    setupStatusFilters();

    setupControls();

    loadEvents();

});


// ============================================================
// DEPARTMENT TABS
// ============================================================

function setupDepartmentTabs() {

    document
        .querySelectorAll(".department-tab")
        .forEach(button => {

            button.addEventListener("click", () => {

                document
                    .querySelectorAll(".department-tab")
                    .forEach(tab =>
                        tab.classList.remove("active")
                    );

                button.classList.add("active");

                currentDepartment =
                    button.dataset.department;

                currentStatus = "all";

                document
                    .querySelectorAll(".status-filter")
                    .forEach(filter =>
                        filter.classList.remove("active")
                    );

                document
                    .querySelector(
                        '.status-filter[data-status="all"]'
                    )
                    ?.classList.add("active");

                renderDepartment();

            });

        });

}


// ============================================================
// STATUS FILTERS
// ============================================================

function setupStatusFilters() {

    document
        .querySelectorAll(".status-filter")
        .forEach(button => {

            button.addEventListener("click", () => {

                currentStatus =
                    button.dataset.status;

                document
                    .querySelectorAll(".status-filter")
                    .forEach(filter =>
                        filter.classList.remove("active")
                    );

                button.classList.add("active");

                renderDepartment();

            });

        });

}


// ============================================================
// CONTROLS
// ============================================================

function setupControls() {

    const refreshButton =
        document.getElementById("refreshButton");

    refreshButton.addEventListener(
        "click",
        loadEvents
    );


    const sortSelect =
        document.getElementById("sortEvents");

    sortSelect.addEventListener(
        "change",
        event => {

            currentSort =
                event.target.value;

            renderDepartment();

        }
    );

}


// ============================================================
// LOAD EVENTS
// ============================================================

async function loadEvents() {

    const container =
        document.getElementById("incidentList");

    container.innerHTML = `

        <div class="loading-state">

            <div class="loading-spinner"></div>

            Loading incidents...

        </div>

    `;


    try {

        const response =
            await fetch(
                `${API_BASE}/api/events`
            );


        if (!response.ok) {

            throw new Error(
                `Backend returned ${response.status}`
            );

        }


        const data =
            await response.json();


        allEvents =
            Array.isArray(data.events)
                ? data.events
                : [];


        updateDepartmentCounts();

        renderDepartment();

    }

    catch (error) {

        console.error(
            "Department event loading failed:",
            error
        );


        container.innerHTML = `

            <div class="empty-state">

                <div class="empty-icon">
                    ⚠️
                </div>

                <strong>
                    Unable to load incidents
                </strong>

                <p>
                    Make sure the FastAPI backend
                    is running on port 8000.
                </p>

            </div>

        `;

    }

}


// ============================================================
// DEPARTMENT FILTER
// ============================================================

function getDepartmentEvents() {

    return allEvents.filter(event => {

        const type =
            String(
                event.event_type || ""
            ).toLowerCase();


        if (
            currentDepartment === "pothole"
        ) {

            return type === "pothole";

        }


        if (
            currentDepartment === "waterlogging"
        ) {

            return (
                type === "waterlogging" ||
                type === "water_logging"
            );

        }


        return false;

    });

}


// ============================================================
// STATUS NORMALIZATION
// ============================================================

function normalizeStatus(event) {

    const raw =
        String(
            event.status || ""
        )
        .toLowerCase()
        .trim();


    if (
        raw === "resolved" ||
        raw === "closed" ||
        raw === "completed"
    ) {

        return "resolved";

    }


    if (
        raw === "in_progress" ||
        raw === "in progress" ||
        raw === "processing"
    ) {

        return "in_progress";

    }


    return "pending";

}


// ============================================================
// SORT
// ============================================================

function sortEvents(events) {

    return events.sort((a, b) => {

        const statusA =
            normalizeStatus(a);

        const statusB =
            normalizeStatus(b);


        if (currentSort === "priority") {

            const priority = {

                pending: 1,

                in_progress: 2,

                resolved: 3

            };

            if (
                priority[statusA] !==
                priority[statusB]
            ) {

                return (
                    priority[statusA] -
                    priority[statusB]
                );

            }

            return (
                getDate(b) -
                getDate(a)
            );

        }


        if (currentSort === "newest") {

            return (
                getDate(b) -
                getDate(a)
            );

        }


        if (currentSort === "oldest") {

            return (
                getDate(a) -
                getDate(b)
            );

        }


        if (currentSort === "confidence") {

            return (
                getConfidence(b) -
                getConfidence(a)
            );

        }


        return 0;

    });

}


// ============================================================
// RENDER DEPARTMENT
// ============================================================

function renderDepartment() {

    const departmentEvents =
        getDepartmentEvents();


    updateSummary(
        departmentEvents
    );


    let filtered =
        departmentEvents.filter(event => {

            if (
                currentStatus === "all"
            ) {

                return true;

            }

            return (
                normalizeStatus(event) ===
                currentStatus
            );

        });


    filtered =
        sortEvents(filtered);


    const container =
        document.getElementById(
            "incidentList"
        );


    document.getElementById(
        "incidentCountLabel"
    ).textContent =
        `${filtered.length} incident${filtered.length === 1 ? "" : "s"}`;


    if (!filtered.length) {

        container.innerHTML = `

            <div class="empty-state">

                <div class="empty-icon">
                    ✓
                </div>

                <strong>
                    No incidents found
                </strong>

                <p>
                    There are no ${currentStatus === "all" ? "" : currentStatus.replace("_", " ")}
                    ${currentDepartment} incidents in this queue.
                </p>

            </div>

        `;

        return;

    }


    container.innerHTML = "";


    filtered.forEach(event => {

        container.appendChild(
            createIncidentCard(event)
        );

    });

}


// ============================================================
// CREATE INCIDENT CARD
// ============================================================

function createIncidentCard(event) {

    const card =
        document.createElement("div");


    const status =
        normalizeStatus(event);


    card.className =
        `incident-card ${status.replace("_", "-")}`;


    const eventType =
        event.event_type ||
        currentDepartment;


    const icon =
        eventType === "pothole"
            ? "🕳️"
            : "🌊";


    const confidence =
        (
            getConfidence(event) * 100
        ).toFixed(1);


    const latitude =
        event.latitude ??
        "-";


    const longitude =
        event.longitude ??
        "-";


    const videoTime =
        event.video_timestamp ??
        "-";


    card.innerHTML = `

        <div class="incident-top">

            <div class="incident-title">

                <div class="incident-icon">
                    ${icon}
                </div>

                <div>

                    <strong>
                        ${capitalize(eventType)}
                    </strong>

                    <div class="incident-id">
                        ${event.event_id || "Unknown Event"}
                    </div>

                </div>

            </div>


            <span class="status-badge status-${status}">

                ${formatStatus(status)}

            </span>

        </div>


        <div class="incident-info">

            <div class="info-item">

                <span>DETECTED</span>

                <strong>
                    ${formatDate(event.detected_at)}
                </strong>

            </div>


            <div class="info-item">

                <span>CONFIDENCE</span>

                <strong>
                    ${confidence}%
                </strong>

            </div>


            <div class="info-item">

                <span>LOCATION</span>

                <strong>
                    ${latitude}, ${longitude}
                </strong>

            </div>


            <div class="info-item">

                <span>VIDEO TIME</span>

                <strong>
                    ${videoTime}s
                </strong>

            </div>

        </div>


        <div class="incident-actions">

            ${
                status === "pending"
                ? `
                    <button
                        class="action-button action-progress"
                        onclick="updateIncidentStatus('${event.event_id}', 'in_progress')">

                        Start Work

                    </button>
                `
                : ""
            }


            ${
                status !== "resolved"
                ? `
                    <button
                        class="action-button action-resolve"
                        onclick="updateIncidentStatus('${event.event_id}', 'resolved')">

                        ✓ Mark Resolved

                    </button>
                `
                : ""
            }

        </div>

    `;


    return card;

}

// ============================================================
// UPDATE INCIDENT STATUS
// FRONTEND-ONLY PROTOTYPE VERSION
// ============================================================

function updateIncidentStatus(eventId, newStatus) {

    if (!eventId) {
        return;
    }

    // ----------------------------------------------------------
    // FIND THE INCIDENT
    // ----------------------------------------------------------

    const event = allEvents.find(
        item => String(item.event_id) === String(eventId)
    );

    if (!event) {

        console.error(
            "Incident not found:",
            eventId
        );

        return;
    }


    // ----------------------------------------------------------
    // UPDATE STATUS LOCALLY
    // ----------------------------------------------------------

    event.status = newStatus;


    // ----------------------------------------------------------
    // ADD RESOLUTION TIME
    // ----------------------------------------------------------

    if (newStatus === "resolved") {

        event.resolved_at =
            new Date().toISOString();

    }


    // ----------------------------------------------------------
    // RE-RENDER DEPARTMENT
    // ----------------------------------------------------------

    renderDepartment();


    // ----------------------------------------------------------
    // SHOW SUCCESS MESSAGE
    // ----------------------------------------------------------

    alert(
        `Incident ${eventId} has been marked as ${formatStatus(newStatus)}.`
    );

}

// ============================================================
// SUMMARY
// ============================================================

function updateSummary(events) {

    let pending = 0;

    let progress = 0;

    let resolved = 0;


    events.forEach(event => {

        const status =
            normalizeStatus(event);


        if (status === "pending") {

            pending++;

        }

        else if (
            status === "in_progress"
        ) {

            progress++;

        }

        else if (
            status === "resolved"
        ) {

            resolved++;

        }

    });


    document.getElementById(
        "pendingCount"
    ).textContent = pending;


    document.getElementById(
        "progressCount"
    ).textContent = progress;


    document.getElementById(
        "resolvedCount"
    ).textContent = resolved;


    document.getElementById(
        "totalCount"
    ).textContent =
        events.length;

}


// ============================================================
// DEPARTMENT COUNTS
// ============================================================

function updateDepartmentCounts() {

    const potholes =
        allEvents.filter(
            event =>
                String(
                    event.event_type || ""
                ).toLowerCase() ===
                "pothole"
        ).length;


    const waterlogging =
        allEvents.filter(
            event => {

                const type =
                    String(
                        event.event_type || ""
                    ).toLowerCase();

                return (
                    type === "waterlogging" ||
                    type === "water_logging"
                );

            }
        ).length;


    document.getElementById(
        "potholeTabCount"
    ).textContent =
        potholes;


    document.getElementById(
        "waterTabCount"
    ).textContent =
        waterlogging;

}


// ============================================================
// HELPERS
// ============================================================

function getConfidence(event) {

    const value =
        Number(
            event.confidence
        );


    if (
        Number.isNaN(value)
    ) {

        return 0;

    }


    return value;

}


function getDate(event) {

    if (!event.detected_at) {

        return 0;

    }


    const date =
        new Date(
            event.detected_at
        );


    return Number.isNaN(
        date.getTime()
    )
        ? 0
        : date.getTime();

}


function formatDate(value) {

    if (!value) {

        return "Unknown";

    }


    const date =
        new Date(value);


    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return String(value);

    }


    return date.toLocaleString(
        "en-IN",
        {
            day: "2-digit",
            month: "short",
            hour: "2-digit",
            minute: "2-digit"
        }
    );

}


function formatStatus(status) {

    if (
        status === "in_progress"
    ) {

        return "IN PROGRESS";

    }


    if (
        status === "resolved"
    ) {

        return "RESOLVED";

    }


    return "PENDING";

}


function capitalize(value) {

    if (!value) {

        return "";

    }


    return (
        value.charAt(0).toUpperCase() +
        value.slice(1)
    );

}


// ============================================================
// AUTO REFRESH
// ============================================================

setInterval(
    loadEvents,
    15000
);