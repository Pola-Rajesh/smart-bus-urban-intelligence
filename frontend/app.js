const API_BASE = "http://127.0.0.1:8000";


// ============================================================
// GLOBAL EVENT STATE
// ============================================================

let allEvents = [];

let currentFilter = "all";

let currentSort = "newest";


// ============================================================
// LOAD SUMMARY
// ============================================================

async function loadSummary() {

    try {

        const response = await fetch(
            `${API_BASE}/api/events/summary`
        );

        if (!response.ok) {
            throw new Error("Failed to load summary");
        }

        const data = await response.json();

        document.getElementById(
            "totalEvents"
        ).textContent = data.total_events ?? 0;

        document.getElementById(
            "potholes"
        ).textContent = data.potholes ?? 0;

        document.getElementById(
            "waterlogging"
        ).textContent = data.waterlogging ?? 0;

        document.getElementById(
            "traffic"
        ).textContent = data.traffic ?? 0;

    }

    catch (error) {

        console.error(
            "Failed to load summary:",
            error
        );

    }
}


// ============================================================
// LOAD EVENTS FROM BACKEND
// ============================================================

async function loadEvents() {

    const container =
        document.getElementById(
            "eventsContainer"
        );

    try {

        const response = await fetch(
            `${API_BASE}/api/events`
        );

        if (!response.ok) {
            throw new Error(
                `Backend returned ${response.status}`
            );
        }

        const data = await response.json();

        allEvents = Array.isArray(data.events)
            ? data.events
            : [];

        renderEvents();

    }

    catch (error) {

        console.error(
            "Failed to load events:",
            error
        );

        container.innerHTML =
            `<p class="empty-message">
                Failed to load events.
                <br>
                Make sure the FastAPI backend is running.
             </p>`;
    }
}


// ============================================================
// SAFE DATE PARSER
// ============================================================

function getEventDate(event) {

    if (!event || !event.detected_at) {
        return 0;
    }

    const date =
        new Date(event.detected_at);

    const time =
        date.getTime();

    if (Number.isNaN(time)) {
        return 0;
    }

    return time;
}


// ============================================================
// EVENT ID NUMBER
// ============================================================

function getEventIdNumber(event) {

    if (!event || !event.event_id) {
        return 0;
    }

    const match =
        String(event.event_id).match(
            /(\d+)$/
        );

    if (!match) {
        return 0;
    }

    return Number(match[1]);
}


// ============================================================
// RENDER EVENTS
// ============================================================

function renderEvents() {

    const container =
        document.getElementById(
            "eventsContainer"
        );

    container.innerHTML = "";


    // ========================================================
    // FILTER
    // ========================================================

    let filteredEvents =
        allEvents.filter(
            event => {

                if (
                    currentFilter === "all"
                ) {

                    return true;

                }

                return (
                    event.event_type ===
                    currentFilter
                );

            }
        );


    // ========================================================
    // SORT
    // ========================================================

    filteredEvents.sort(
        (a, b) => {

            switch (currentSort) {


                // ------------------------------------------------
                // NEWEST FIRST
                // ------------------------------------------------

                case "newest": {

                    const timeA =
                        getEventDate(a);

                    const timeB =
                        getEventDate(b);

                    if (timeB !== timeA) {
                        return timeB - timeA;
                    }

                    return (
                        getEventIdNumber(b) -
                        getEventIdNumber(a)
                    );
                }


                // ------------------------------------------------
                // OLDEST FIRST
                // ------------------------------------------------

                case "oldest": {

                    const timeA =
                        getEventDate(a);

                    const timeB =
                        getEventDate(b);

                    if (timeA !== timeB) {
                        return timeA - timeB;
                    }

                    return (
                        getEventIdNumber(a) -
                        getEventIdNumber(b)
                    );
                }


                // ------------------------------------------------
                // HIGHEST CONFIDENCE
                // ------------------------------------------------

                case "confidence-high": {

                    const confidenceA =
                        Number(a.confidence) || 0;

                    const confidenceB =
                        Number(b.confidence) || 0;

                    if (
                        confidenceB !==
                        confidenceA
                    ) {

                        return (
                            confidenceB -
                            confidenceA
                        );

                    }

                    return (
                        getEventDate(b) -
                        getEventDate(a)
                    );
                }


                // ------------------------------------------------
                // LOWEST CONFIDENCE
                // ------------------------------------------------

                case "confidence-low": {

                    const confidenceA =
                        Number(a.confidence) || 0;

                    const confidenceB =
                        Number(b.confidence) || 0;

                    if (
                        confidenceA !==
                        confidenceB
                    ) {

                        return (
                            confidenceA -
                            confidenceB
                        );

                    }

                    return (
                        getEventDate(b) -
                        getEventDate(a)
                    );
                }


                default:

                    return 0;
            }

        }
    );


    // ========================================================
    // NO EVENTS
    // ========================================================

    if (!filteredEvents.length) {

        container.innerHTML =
            `<p class="empty-message">
                No events found for this filter.
             </p>`;

        return;
    }


    // ========================================================
    // DISPLAY EVENTS
    // ========================================================

    filteredEvents.forEach(
        event => {

            const card =
                document.createElement(
                    "div"
                );

            card.className =
                "event-card";


            // ------------------------------------------------
            // SEVERITY
            // ------------------------------------------------

            const severity =
                (
                    event.severity ||
                    "LOW"
                ).toLowerCase();


            // ------------------------------------------------
            // CONFIDENCE
            // ------------------------------------------------

            const confidence =
                (
                    (Number(event.confidence) || 0)
                    * 100
                ).toFixed(1);


            // ------------------------------------------------
            // EVENT TYPE
            // ------------------------------------------------

            const eventType =
                event.event_type ||
                "unknown";


            // ------------------------------------------------
            // STATUS
            // ------------------------------------------------

            const status =
                event.status ||
                "UNKNOWN";


            // ------------------------------------------------
            // GPS
            // ------------------------------------------------

            const latitude =
                event.latitude ??
                "-";

            const longitude =
                event.longitude ??
                "-";


            // ------------------------------------------------
            // VIDEO TIME
            // ------------------------------------------------

            const videoTime =
                event.video_timestamp ??
                "-";


            // ------------------------------------------------
            // CARD
            // ------------------------------------------------

            card.innerHTML = `

                <div class="event-title">

                    <span class="event-type">

                        ${getEventIcon(eventType)}

                        ${eventType}

                    </span>

                    <span class="${severity}">

                        ${event.severity || "LOW"}

                    </span>

                </div>


                <div class="event-info">

                    <strong>
                        ${event.event_id || "-"}
                    </strong>

                    <br>

                    Detected:
                    ${formatDateTime(
                        event.detected_at
                    )}

                    <br>

                    Confidence:
                    ${confidence}%

                    <br>

                    Video Time:
                    ${videoTime}s

                    <br>

                    GPS:
                    ${latitude},
                    ${longitude}

                    <br>

                    Status:
                    ${status}

                </div>

            `;


            // ------------------------------------------------
            // EVIDENCE CLICK
            // ------------------------------------------------

            card.onclick =
                () => showEvidence(event);


            container.appendChild(
                card
            );

        }
    );
}


// ============================================================
// EVENT FILTER
// ============================================================

function filterEvents(type) {

    currentFilter = type;


    // --------------------------------------------------------
    // REMOVE ACTIVE STATE
    // --------------------------------------------------------

    document
        .querySelectorAll(
            ".filter-button"
        )
        .forEach(
            button => {

                button.classList.remove(
                    "active"
                );

            }
        );


    // --------------------------------------------------------
    // SET ACTIVE BUTTON
    // --------------------------------------------------------

    const buttons =
        document.querySelectorAll(
            ".filter-button"
        );


    buttons.forEach(
        button => {

            const text =
                button.textContent
                    .trim()
                    .toLowerCase();


            if (

                (type === "all" &&
                 text === "all") ||

                (type === "pothole" &&
                 text === "potholes") ||

                (type === "traffic" &&
                 text === "traffic") ||

                (type === "waterlogging" &&
                 text === "waterlogging")

            ) {

                button.classList.add(
                    "active"
                );

            }

        }
    );


    renderEvents();
}


// ============================================================
// EVENT SORT
// ============================================================

function sortEvents(sortType) {

    currentSort =
        sortType || "newest";

    renderEvents();
}


// ============================================================
// FORMAT DATE / TIME
// ============================================================

function formatDateTime(value) {

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

        return value;

    }


    return date.toLocaleString(
        "en-IN",
        {
            year: "numeric",
            month: "short",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit"
        }
    );
}


// ============================================================
// EVENT ICON
// ============================================================

function getEventIcon(type) {

    const icons = {

        pothole:
            "🚧",

        waterlogging:
            "💧",

        traffic:
            "🚗",

        hit_and_run:
            "🚨"

    };


    return (
        icons[type] ||
        "⚠️"
    );
}


// ============================================================
// SHOW EVIDENCE
// ============================================================

function showEvidence(event) {

    const container =
        document.getElementById(
            "evidenceContainer"
        );


    if (!event) {

        container.innerHTML =
            `<p class="empty-message">
                No event selected.
             </p>`;

        return;
    }


    if (!event.evidence_image) {

        container.innerHTML =
            `<p class="empty-message">
                No evidence available.
             </p>`;

        return;
    }


    const confidence =
        (
            (Number(event.confidence) || 0)
            * 100
        ).toFixed(1);


    container.innerHTML = `

        <div>

            <img
                class="evidence-image"
                src="${API_BASE}/api/evidence/${event.event_id}"
                alt="Detection evidence"
            >


            <div
                class="event-info"
                style="margin-top:15px"
            >

                <strong>
                    ${event.alert_message || "Urban incident detected"}
                </strong>

                <br>

                Event ID:
                ${event.event_id || "-"}

                <br>

                Detected:
                ${formatDateTime(
                    event.detected_at
                )}

                <br>

                Confidence:
                ${confidence}%

                <br>

                Location:
                ${event.latitude ?? "-"},
                ${event.longitude ?? "-"}

                <br>

                Status:
                ${event.status || "UNKNOWN"}

            </div>

        </div>

    `;
}


// ============================================================
// HIGH PRIORITY EVENTS
// ============================================================

async function loadHighPriority() {

    const container =
        document.getElementById(
            "highPriorityContainer"
        );


    try {

        const response =
            await fetch(
                `${API_BASE}/api/events/priority/high`
            );


        if (!response.ok) {

            throw new Error(
                `Backend returned ${response.status}`
            );

        }


        const data =
            await response.json();


        container.innerHTML = "";


        if (
            !data.events ||
            !data.events.length
        ) {

            container.innerHTML =
                `<p class="empty-message">
                    No high priority alerts.
                 </p>`;

            return;
        }


        // ----------------------------------------------------
        // SORT HIGH PRIORITY ALERTS
        // NEWEST FIRST
        // ----------------------------------------------------

        const alerts =
            [...data.events].sort(
                (a, b) => {

                    const timeA =
                        getEventDate(a);

                    const timeB =
                        getEventDate(b);

                    if (timeB !== timeA) {

                        return (
                            timeB -
                            timeA
                        );

                    }

                    return (
                        getEventIdNumber(b) -
                        getEventIdNumber(a)
                    );

                }
            );


        alerts.forEach(
            event => {

                const alert =
                    document.createElement(
                        "div"
                    );


                alert.className =
                    "event-card";


                const confidence =
                    (
                        (Number(event.confidence) || 0)
                        * 100
                    ).toFixed(1);


                alert.innerHTML = `

                    <div class="event-title">

                        <span class="event-type">

                            🚨

                            ${event.event_type || "Incident"}

                        </span>

                        <span class="high">

                            HIGH

                        </span>

                    </div>


                    <div class="event-info">

                        ${event.alert_message || "High priority event"}

                        <br>

                        <strong>
                            ${event.event_id || "-"}
                        </strong>

                        <br>

                        Detected:
                        ${formatDateTime(
                            event.detected_at
                        )}

                        <br>

                        Confidence:
                        ${confidence}%

                        <br>

                        GPS:
                        ${event.latitude ?? "-"},
                        ${event.longitude ?? "-"}

                    </div>

                `;


                alert.onclick =
                    () => showEvidence(event);


                container.appendChild(
                    alert
                );

            }
        );

    }

    catch (error) {

        console.error(
            "Failed to load alerts:",
            error
        );

        container.innerHTML =
            `<p class="empty-message">
                Failed to load high priority alerts.
             </p>`;

    }
}


// ============================================================
// PROCESS VIDEO
// ============================================================

async function processVideo() {

    const input =
        document.getElementById(
            "videoInput"
        );


    const status =
        document.getElementById(
            "processingStatus"
        );


    const button =
        document.getElementById(
            "processButton"
        );


    if (!input.files.length) {

        status.textContent =
            "Please select a video first.";

        return;
    }


    const file =
        input.files[0];


    const formData =
        new FormData();


    formData.append(
        "file",
        file
    );


    button.disabled = true;


    status.textContent =
        "Uploading and processing video...";


    try {

        const response =
            await fetch(
                `${API_BASE}/api/video/upload`,
                {
                    method: "POST",
                    body: formData
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Video processing failed"
            );

        }


        status.textContent =
            `Processing complete. ` +
            `${data.events_detected || 0} events detected.`;


        // ----------------------------------------------------
        // REFRESH DASHBOARD
        // ----------------------------------------------------

        await loadSummary();

        await loadEvents();

        await loadHighPriority();


        // ----------------------------------------------------
        // RESET EVENT VIEW
        // ----------------------------------------------------

        currentFilter =
            "all";

        currentSort =
            "newest";


        const sortSelect =
            document.getElementById(
                "eventSort"
            );


        if (sortSelect) {

            sortSelect.value =
                "newest";

        }


        // ----------------------------------------------------
        // RESET ACTIVE FILTER BUTTON
        // ----------------------------------------------------

        document
            .querySelectorAll(
                ".filter-button"
            )
            .forEach(
                button => {

                    button.classList.remove(
                        "active"
                    );

                    if (
                        button.textContent
                            .trim()
                            .toLowerCase() ===
                        "all"
                    ) {

                        button.classList.add(
                            "active"
                        );

                    }

                }
            );


        renderEvents();

    }

    catch (error) {

        console.error(
            "Video processing error:",
            error
        );


        status.textContent =
            `Error: ${error.message}`;

    }

    finally {

        button.disabled =
            false;

    }
}


// ============================================================
// INITIAL LOAD
// ============================================================

window.addEventListener(
    "DOMContentLoaded",
    () => {

        loadSummary();

        loadEvents();

        loadHighPriority();

    }
);