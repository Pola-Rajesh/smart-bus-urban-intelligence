/* ============================================================
   SMART BUS - FLEET INTELLIGENCE
   ============================================================ */


/* ============================================================
   CONFIGURATION
   ============================================================ */

const API_BASE = "http://127.0.0.1:8000";

const FLEET_ENDPOINT =
    `${API_BASE}/api/fleet/buses`;


/* ============================================================
   GLOBAL STATE
   ============================================================ */

let map = null;

let buses = [];

let markers = {};

let routes = {};

let animationFrames = {};

let selectedBusId = null;

let mapInitialized = false;


/* ============================================================
   KURNOOL DEFAULT CENTER
   ============================================================ */

const DEFAULT_CENTER = [
    15.8281,
    78.0373
];


/* ============================================================
   BUS ROUTES
   ============================================================ */

/*
    These are demonstration routes around the backend
    coordinates.

    The backend still provides the actual bus locations.

    These paths are used to visually demonstrate movement
    between telemetry updates.
*/

const ROUTES = {

    "BUS-01": [
        [15.8281, 78.0373],
        [15.8290, 78.0382],
        [15.8300, 78.0390],
        [15.8310, 78.0400],
        [15.8320, 78.0390],
        [15.8312, 78.0378],
        [15.8300, 78.0365],
        [15.8281, 78.0373]
    ],

    "BUS-02": [
        [15.8305, 78.0397],
        [15.8315, 78.0410],
        [15.8330, 78.0420],
        [15.8340, 78.0410],
        [15.8330, 78.0395],
        [15.8315, 78.0388],
        [15.8305, 78.0397]
    ],

    "BUS-03": [
        [15.8350, 78.0420],
        [15.8360, 78.0430],
        [15.8370, 78.0440],
        [15.8380, 78.0430],
        [15.8390, 78.0445],
        [15.8380, 78.0460],
        [15.8365, 78.0450],
        [15.8350, 78.0420]
    ],

    "BUS-04": [
        [15.8250, 78.0320],
        [15.8260, 78.0330],
        [15.8270, 78.0340],
        [15.8280, 78.0330],
        [15.8290, 78.0340],
        [15.8280, 78.0350],
        [15.8265, 78.0340],
        [15.8250, 78.0320]
    ],

    "BUS-05": [
        [15.8400, 78.0450],
        [15.8390, 78.0460],
        [15.8380, 78.0470],
        [15.8370, 78.0460],
        [15.8360, 78.0470],
        [15.8375, 78.0480],
        [15.8390, 78.0470],
        [15.8400, 78.0450]
    ]

};


/* ============================================================
   INITIALIZE PAGE
   ============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        initializeMap();

        setupControls();

        loadFleet();

    }
);


/* ============================================================
   INITIALIZE LEAFLET MAP
   ============================================================ */

function initializeMap() {

    const mapElement =
        document.getElementById("fleetMap");


    if (!mapElement) {

        console.error(
            "Fleet map element was not found."
        );

        return;
    }


    if (typeof L === "undefined") {

        console.error(
            "Leaflet was not loaded."
        );

        mapElement.innerHTML =
            `
            <div style="
                display:flex;
                align-items:center;
                justify-content:center;
                height:100%;
                color:#475569;
                font-family:Arial;
                background:#dcecff;
            ">
                Leaflet failed to load.
            </div>
            `;

        return;
    }


    /* --------------------------------------------------------
       CREATE MAP
    -------------------------------------------------------- */

    map = L.map(
        "fleetMap",
        {
            center: DEFAULT_CENTER,

            zoom: 14,

            zoomControl: true,

            attributionControl: true,

            preferCanvas: true
        }
    );


    /* --------------------------------------------------------
       OPENSTREETMAP TILE LAYER
    -------------------------------------------------------- */

    const tileLayer =
        L.tileLayer(
            "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            {
                maxZoom: 19,

                minZoom: 5,

                attribution:
                    '&copy; OpenStreetMap contributors',

                updateWhenIdle: false,

                keepBuffer: 4
            }
        );


    tileLayer.addTo(map);


    /* --------------------------------------------------------
       TILE ERROR HANDLING
    -------------------------------------------------------- */

    tileLayer.on(
        "tileerror",
        event => {

            console.warn(
                "Map tile failed to load:",
                event.coords
            );

        }
    );


    mapInitialized = true;


    /*
        CRITICAL FIX

        Force Leaflet to calculate the container dimensions
        after the browser has rendered the page.
    */

    setTimeout(
        () => {

            forceMapResize();

        },
        100
    );


    setTimeout(
        () => {

            forceMapResize();

        },
        500
    );


    setTimeout(
        () => {

            forceMapResize();

        },
        1200
    );


    /* --------------------------------------------------------
       WINDOW RESIZE
    -------------------------------------------------------- */

    window.addEventListener(
        "resize",
        () => {

            forceMapResize();

        }
    );


    /*
        ResizeObserver catches layout changes that normal
        window resize events do not catch.
    */

    if (
        typeof ResizeObserver !==
        "undefined"
    ) {

        const observer =
            new ResizeObserver(
                () => {

                    forceMapResize();

                }
            );


        observer.observe(
            mapElement
        );

    }

}


/* ============================================================
   FORCE LEAFLET TO RECALCULATE SIZE
   ============================================================ */

function forceMapResize() {

    if (!map) {
        return;
    }


    requestAnimationFrame(
        () => {

            map.invalidateSize(
                true
            );

        }
    );

}


/* ============================================================
   SETUP BUTTONS
   ============================================================ */

function setupControls() {

    const refreshButton =
        document.getElementById(
            "refreshFleet"
        );


    if (refreshButton) {

        refreshButton.addEventListener(
            "click",
            () => {

                loadFleet();

            }
        );

    }


    const closeButton =
        document.getElementById(
            "closeDetails"
        );


    if (closeButton) {

        closeButton.addEventListener(
            "click",
            closeBusDetails
        );

    }

}


/* ============================================================
   LOAD FLEET FROM BACKEND
   ============================================================ */

async function loadFleet() {

    try {

        setGpsStatus(
            "SYNCING..."
        );


        const response =
            await fetch(
                FLEET_ENDPOINT,
                {
                    cache: "no-store"
                }
            );


        if (!response.ok) {

            throw new Error(
                `Backend returned ${response.status}`
            );

        }


        const data =
            await response.json();


        console.log(
            "Fleet API response:",
            data
        );


        buses =
            Array.isArray(data.buses)
                ? data.buses
                : [];


        updateSummary();

        renderBusList();

        renderMap();

        updateLastSync();

        setGpsStatus(
            "ONLINE"
        );


    }
    catch (error) {

        console.error(
            "Fleet loading error:",
            error
        );


        setGpsStatus(
            "OFFLINE"
        );


        const list =
            document.getElementById(
                "busList"
            );


        if (list) {

            list.innerHTML =
                `
                <div class="loading-state">

                    Unable to load fleet.

                    <br><br>

                    <span style="
                        color:#ef4444;
                        font-size:10px;
                    ">
                        ${escapeHtml(error.message)}
                    </span>

                </div>
                `;

        }

    }

}


/* ============================================================
   UPDATE SUMMARY
   ============================================================ */

function updateSummary() {

    const total =
        buses.length;


    const active =
        buses.filter(
            bus =>
                String(
                    bus.status || ""
                ).toLowerCase() ===
                "active"
        ).length;


    const fleetTotal =
        document.getElementById(
            "fleetTotal"
        );


    const activeBuses =
        document.getElementById(
            "activeBuses"
        );


    const trackedBuses =
        document.getElementById(
            "trackedBuses"
        );


    if (fleetTotal) {

        fleetTotal.textContent =
            total;

    }


    if (activeBuses) {

        activeBuses.textContent =
            active;

    }


    if (trackedBuses) {

        trackedBuses.textContent =
            buses.filter(
                bus =>
                    bus.latitude != null &&
                    bus.longitude != null
            ).length;

    }

}


/* ============================================================
   GPS STATUS
   ============================================================ */

function setGpsStatus(status) {

    const element =
        document.getElementById(
            "gpsStatus"
        );


    if (element) {

        element.textContent =
            status;

    }

}


/* ============================================================
   LAST SYNC
   ============================================================ */

function updateLastSync() {

    const element =
        document.getElementById(
            "lastUpdated"
        );


    if (!element) {
        return;
    }


    element.textContent =
        new Date().toLocaleTimeString(
            "en-IN",
            {
                hour: "2-digit",

                minute: "2-digit",

                second: "2-digit"
            }
        );

}


/* ============================================================
   RENDER BUS LIST
   ============================================================ */

function renderBusList() {

    const container =
        document.getElementById(
            "busList"
        );


    if (!container) {
        return;
    }


    container.innerHTML = "";


    if (!buses.length) {

        container.innerHTML =
            `
            <div class="loading-state">
                No buses available.
            </div>
            `;

        return;

    }


    buses.forEach(
        bus => {

            const card =
                document.createElement(
                    "div"
                );


            card.className =
                "bus-card";


            if (
                selectedBusId ===
                bus.bus_id
            ) {

                card.classList.add(
                    "selected"
                );

            }


            const status =
                String(
                    bus.status || "inactive"
                ).toLowerCase();


            const latitude =
                Number(
                    bus.latitude
                );


            const longitude =
                Number(
                    bus.longitude
                );


            card.innerHTML =
                `
                <div class="bus-card-header">

                    <span class="bus-id">

                        ${escapeHtml(
                            bus.bus_id ||
                            "UNKNOWN"
                        )}

                    </span>

                    <span class="
                        bus-status
                        ${status === "active"
                            ? "active"
                            : "inactive"}
                    ">

                        ${status.toUpperCase()}

                    </span>

                </div>


                <span class="bus-position-label">
                    GPS POSITION
                </span>


                <span class="bus-position">

                    ${formatCoordinate(
                        latitude
                    )},

                    ${formatCoordinate(
                        longitude
                    )}

                </span>
                `;


            card.addEventListener(
                "click",
                () => {

                    selectBus(
                        bus
                    );

                }
            );


            container.appendChild(
                card
            );

        }
    );

}


/* ============================================================
   RENDER MAP
   ============================================================ */

function renderMap() {

    if (!map) {
        return;
    }


    /* --------------------------------------------------------
       REMOVE OLD ROUTES
    -------------------------------------------------------- */

    Object.values(
        routes
    ).forEach(
        route => {

            if (route) {

                map.removeLayer(
                    route
                );

            }

        }
    );


    routes = {};


    /* --------------------------------------------------------
       UPDATE / CREATE MARKERS
    -------------------------------------------------------- */

    const bounds =
        [];


    buses.forEach(
        bus => {

            const lat =
                Number(
                    bus.latitude
                );


            const lng =
                Number(
                    bus.longitude
                );


            if (
                !Number.isFinite(lat) ||
                !Number.isFinite(lng)
            ) {

                return;

            }


            bounds.push(
                [
                    lat,
                    lng
                ]
            );


            drawBusRoute(
                bus
            );


            createOrUpdateMarker(
                bus
            );

        }
    );


    /* --------------------------------------------------------
       FIT MAP TO BUSES
    -------------------------------------------------------- */

    if (bounds.length) {

        const leafletBounds =
            L.latLngBounds(
                bounds
            );


        map.fitBounds(
            leafletBounds,
            {
                padding: [
                    60,
                    60
                ],

                maxZoom: 15,

                animate: true,

                duration: 0.8
            }
        );

    }
    else {

        map.setView(
            DEFAULT_CENTER,
            14
        );

    }


    /*
        IMPORTANT:
        invalidate AFTER fitBounds.
    */

    setTimeout(
        () => {

            forceMapResize();

        },
        100
    );


    startBusAnimations();

}


/* ============================================================
   CREATE / UPDATE BUS MARKER
   ============================================================ */

function createOrUpdateMarker(
    bus
) {

    const lat =
        Number(
            bus.latitude
        );


    const lng =
        Number(
            bus.longitude
        );


    if (
        !Number.isFinite(lat) ||
        !Number.isFinite(lng)
    ) {

        return;

    }


    const busId =
        bus.bus_id;


    /* --------------------------------------------------------
       CREATE ICON
    -------------------------------------------------------- */

    const icon =
        L.divIcon(
            {
                className:
                    "",

                html:
                    `
                    <div
                        class="bus-marker"
                        title="${escapeHtml(
                            busId
                        )}"
                    >
                        🚌
                    </div>
                    `,

                iconSize: [
                    36,
                    36
                ],

                iconAnchor: [
                    18,
                    18
                ]
            }
        );


    /* --------------------------------------------------------
       EXISTING MARKER
    -------------------------------------------------------- */

    if (
        markers[busId]
    ) {

        markers[busId]
            .setLatLng(
                [
                    lat,
                    lng
                ]
            );

        return;

    }


    /* --------------------------------------------------------
       CREATE MARKER
    -------------------------------------------------------- */

    const marker =
        L.marker(
            [
                lat,
                lng
            ],
            {
                icon: icon,

                zIndexOffset: 1000
            }
        );


    marker.addTo(
        map
    );


    marker.bindPopup(
        createPopupContent(
            bus
        )
    );


    marker.on(
        "click",
        () => {

            selectBus(
                bus
            );

        }
    );


    markers[busId] =
        marker;

}


/* ============================================================
   DRAW ROUTE
   ============================================================ */

function drawBusRoute(
    bus
) {

    const route =
        ROUTES[
            bus.bus_id
        ];


    if (
        !route ||
        route.length < 2
    ) {

        return;

    }


    const polyline =
        L.polyline(
            route,
            {
                className:
                    "bus-route",

                color:
                    "#168cff",

                weight:
                    4,

                opacity:
                    0.5,

                dashArray:
                    "10 8"
            }
        );


    polyline.addTo(
        map
    );


    routes[
        bus.bus_id
    ] =
        polyline;

}


/* ============================================================
   POPUP
   ============================================================ */

function createPopupContent(
    bus
) {

    return `
        <div style="
            min-width:170px;
            font-family:Arial,sans-serif;
        ">

            <strong style="
                font-size:14px;
                color:#0f172a;
            ">
                ${escapeHtml(
                    bus.bus_id ||
                    "Bus"
                )}
            </strong>

            <hr style="
                border:none;
                border-top:1px solid #e2e8f0;
                margin:7px 0;
            ">

            <div style="
                font-size:11px;
                line-height:1.7;
                color:#475569;
            ">

                <b>Status:</b>
                ${escapeHtml(
                    bus.status ||
                    "UNKNOWN"
                )}

                <br>

                <b>Latitude:</b>
                ${formatCoordinate(
                    Number(
                        bus.latitude
                    )
                )}

                <br>

                <b>Longitude:</b>
                ${formatCoordinate(
                    Number(
                        bus.longitude
                    )
                )}

            </div>

        </div>
    `;

}


/* ============================================================
   SELECT BUS
   ============================================================ */

function selectBus(
    bus
) {

    selectedBusId =
        bus.bus_id;


    /* --------------------------------------------------------
       UPDATE DETAILS
    -------------------------------------------------------- */

    const details =
        document.getElementById(
            "busDetails"
        );


    if (details) {

        details.classList.remove(
            "hidden"
        );

    }


    setText(
        "selectedBusId",
        bus.bus_id || "---"
    );


    setText(
        "selectedStatus",
        String(
            bus.status ||
            "UNKNOWN"
        ).toUpperCase()
    );


    setText(
        "selectedLatitude",
        formatCoordinate(
            Number(
                bus.latitude
            )
        )
    );


    setText(
        "selectedLongitude",
        formatCoordinate(
            Number(
                bus.longitude
            )
        )
    );


    /* --------------------------------------------------------
       UPDATE LIST
    -------------------------------------------------------- */

    renderBusList();


    /* --------------------------------------------------------
       FOCUS MAP
    -------------------------------------------------------- */

    const marker =
        markers[
            bus.bus_id
        ];


    if (marker) {

        map.flyTo(
            marker.getLatLng(),
            16,
            {
                duration:
                    0.8
            }
        );


        marker.openPopup();

    }

}


/* ============================================================
   CLOSE BUS DETAILS
   ============================================================ */

function closeBusDetails() {

    selectedBusId =
        null;


    const details =
        document.getElementById(
            "busDetails"
        );


    if (details) {

        details.classList.add(
            "hidden"
        );

    }


    renderBusList();

}


/* ============================================================
   BUS ANIMATION
   ============================================================ */

function startBusAnimations() {

    buses.forEach(
        bus => {

            const route =
                ROUTES[
                    bus.bus_id
                ];


            if (
                !route ||
                route.length < 2
            ) {

                return;

            }


            animateBus(
                bus.bus_id,
                route
            );

        }
    );

}


/* ============================================================
   ANIMATE INDIVIDUAL BUS
   ============================================================ */

function animateBus(
    busId,
    route
) {

    if (
        animationFrames[
            busId
        ]
    ) {

        cancelAnimationFrame(
            animationFrames[
                busId
            ]
        );

    }


    const marker =
        markers[
            busId
        ];


    if (!marker) {
        return;
    }


    let segment =
        0;


    let progress =
        0;


    const speed =
        0.0008;


    function animate() {

        if (!markers[busId]) {
            return;
        }


        const start =
            route[
                segment
            ];


        const end =
            route[
                (segment + 1) %
                route.length
            ];


        progress +=
            speed;


        if (
            progress >= 1
        ) {

            progress =
                0;


            segment =
                (segment + 1) %
                route.length;

        }


        const lat =
            start[0] +
            (
                end[0] -
                start[0]
            ) *
            progress;


        const lng =
            start[1] +
            (
                end[1] -
                start[1]
            ) *
            progress;


        marker.setLatLng(
            [
                lat,
                lng
            ]
        );


        animationFrames[
            busId
        ] =
            requestAnimationFrame(
                animate
            );

    }


    animate();

}


/* ============================================================
   PERIODIC BACKEND SYNC
   ============================================================ */

setInterval(
    () => {

        loadFleet();

    },
    15000
);


/* ============================================================
   HELPERS
   ============================================================ */

function setText(
    id,
    value
) {

    const element =
        document.getElementById(
            id
        );


    if (element) {

        element.textContent =
            value;

    }

}


function formatCoordinate(
    value
) {

    if (
        !Number.isFinite(
            value
        )
    ) {

        return "--";

    }


    return value.toFixed(
        6
    );

}


function escapeHtml(
    value
) {

    return String(
        value ?? ""
    )
        .replace(
            /&/g,
            "&amp;"
        )
        .replace(
            /</g,
            "&lt;"
        )
        .replace(
            />/g,
            "&gt;"
        )
        .replace(
            /"/g,
            "&quot;"
        )
        .replace(
            /'/g,
            "&#039;"
        );

}