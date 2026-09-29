const API_URL = "http://127.0.0.1:8000";

let map;
let markersLayer;


/* =========================================================
   MAP INITIALIZATION
========================================================= */

function initializeMap() {

    map = L.map("map").setView(
        [15.8283, 78.0375],
        16
    );

    L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
            attribution: "&copy; OpenStreetMap contributors"
        }
    ).addTo(map);

    markersLayer = L.layerGroup().addTo(map);
}


/* =========================================================
   EVENT ICONS
========================================================= */

function getEventIcon(type) {

    switch (type) {

        case "pothole":
            return "🕳️";

        case "waterlogging":
            return "💧";

        case "traffic":
            return "🚦";

        default:
            return "📍";
    }
}


/* =========================================================
   LOAD EVENTS FROM FASTAPI
========================================================= */

async function loadEvents() {

    try {

        const response =
            await fetch(`${API_URL}/api/events`);

        if (!response.ok) {

            throw new Error(
                `Backend returned HTTP ${response.status}`
            );
        }

        const data =
            await response.json();

        const events =
            data.events || [];

        updateSummary(events);

        updateAlerts(events);

        updateTable(events);

        updateMap(events);

        document.getElementById(
            "lastUpdated"
        ).textContent =
            "Updated: " +
            new Date().toLocaleTimeString();

    }

    catch (error) {

        console.error(
            "Backend connection error:",
            error
        );

        document.getElementById(
            "alerts"
        ).innerHTML = `

            <div class="loading">

                ❌ Unable to connect to backend.

                <br><br>

                Make sure FastAPI is running on:

                <br>

                <b>${API_URL}</b>

            </div>
        `;
    }
}


/* =========================================================
   SUMMARY CARDS
========================================================= */

function updateSummary(events) {

    const potholes =
        events.filter(
            e => e.event_type === "pothole"
        ).length;

    const waterlogging =
        events.filter(
            e => e.event_type === "waterlogging"
        ).length;

    const traffic =
        events.filter(
            e => e.event_type === "traffic"
        ).length;

    const high =
        events.filter(
            e => e.priority === 3
        ).length;


    document.getElementById(
        "totalEvents"
    ).textContent = events.length;


    document.getElementById(
        "highEvents"
    ).textContent = high;


    document.getElementById(
        "potholeEvents"
    ).textContent = potholes;


    document.getElementById(
        "waterEvents"
    ).textContent = waterlogging;


    document.getElementById(
        "trafficEvents"
    ).textContent = traffic;
}


/* =========================================================
   HIGH PRIORITY ALERTS
========================================================= */

function updateAlerts(events) {

    const alerts =
        events.filter(
            e => e.priority === 3
        );

    const container =
        document.getElementById("alerts");


    if (alerts.length === 0) {

        container.innerHTML = `
            <div class="loading">
                No high-priority events.
            </div>
        `;

        return;
    }


    container.innerHTML =
        alerts.map(event => {

            return `

                <div class="alert-card">

                    <h3>
                        ${getEventIcon(event.event_type)}
                        ${event.alert_message}
                    </h3>

                    <p>
                        <b>Event:</b>
                        ${event.event_id}
                    </p>

                    <p>
                        <b>Confidence:</b>

                        <span class="confidence">
                            ${(event.confidence * 100).toFixed(1)}%
                        </span>
                    </p>

                    <p>
                        <b>Severity:</b>
                        ${event.severity}
                    </p>

                    <p>
                        <b>Bus:</b>
                        ${event.bus_id}
                    </p>

                    <p>
                        <b>GPS:</b>
                        ${event.latitude.toFixed(6)},
                        ${event.longitude.toFixed(6)}
                    </p>

                    <p>
                        <b>Video Time:</b>
                        ${event.video_timestamp.toFixed(2)}s
                    </p>

                </div>

            `;

        }).join("");
}


/* =========================================================
   EVENT TABLE
========================================================= */

function updateTable(events) {

    const tbody =
        document.getElementById(
            "eventTable"
        );


    /*
        Sort according to the actual
        video timestamp.
    */

    const sorted =
        [...events].sort(
            (a, b) =>
                a.video_timestamp -
                b.video_timestamp
        );


    tbody.innerHTML =
        sorted.map(event => {

            const type =
                event.event_type;

            const severity =
                event.severity;


            return `

                <tr>

                    <td>
                        <b>${event.event_id}</b>
                    </td>

                    <td>

                        <span class="
                            badge
                            badge-${type}
                        ">

                            ${getEventIcon(type)}
                            ${type}

                        </span>

                    </td>

                    <td>
                        ${(event.confidence * 100).toFixed(1)}%
                    </td>

                    <td>

                        <span class="
                            badge
                            badge-${severity.toLowerCase()}
                        ">

                            ${severity}

                        </span>

                    </td>

                    <td>
                        ${event.bus_id}
                    </td>

                    <td>

                        ${event.latitude.toFixed(6)},
                        ${event.longitude.toFixed(6)}

                    </td>

                    <td>

                        ${event.video_timestamp.toFixed(2)}s

                    </td>

                </tr>

            `;

        }).join("");
}


/* =========================================================
   MAP MARKERS
========================================================= */

function updateMap(events) {

    markersLayer.clearLayers();


    if (events.length === 0) {
        return;
    }


    const coordinates = [];


    events.forEach(event => {

        const lat =
            event.latitude;

        const lon =
            event.longitude;


        coordinates.push(
            [lat, lon]
        );


        const marker =
            L.marker([lat, lon]);


        marker.bindPopup(`

            <div style="min-width:240px">

                <h3>

                    ${getEventIcon(event.event_type)}

                    ${event.event_type.toUpperCase()}

                </h3>

                <hr>

                <b>Event:</b>
                ${event.event_id}

                <br><br>

                <b>Alert:</b>
                ${event.alert_message}

                <br><br>

                <b>Confidence:</b>
                ${(event.confidence * 100).toFixed(1)}%

                <br>

                <b>Severity:</b>
                ${event.severity}

                <br>

                <b>Priority:</b>
                ${event.priority}

                <br>

                <b>Bus:</b>
                ${event.bus_id}

                <br>

                <b>Video Time:</b>
                ${event.video_timestamp.toFixed(2)}s

                <br><br>

                <b>GPS:</b>

                <br>

                ${lat.toFixed(6)},
                ${lon.toFixed(6)}

            </div>

        `);


        marker.addTo(
            markersLayer
        );

    });


    /*
        Automatically zoom
        to detected events.
    */

    if (coordinates.length > 0) {

        map.fitBounds(
            coordinates,
            {
                padding: [40, 40]
            }
        );
    }
}


/* =========================================================
   START DASHBOARD
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        initializeMap();

        loadEvents();

    }
);