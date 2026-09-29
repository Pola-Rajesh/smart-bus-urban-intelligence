import os
import shutil
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.services.event_service import (
    get_all_events,
    get_event_by_id,
    get_events_by_type,
    get_high_priority_events,
    get_summary,
)

from backend.services.video_service import process_uploaded_video


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

FRONTEND_DIR = PROJECT_ROOT / "frontend"

VIDEO_UPLOAD_DIR = (
    PROJECT_ROOT
    / "demo_data"
    / "uploads"
)

VIDEO_UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Smart Bus Urban Intelligence API",
    description=(
        "Database-backed backend API for "
        "Smart Bus Urban Intelligence"
    ),
    version="2.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ============================================================
# FRONTEND PAGE HELPER
# ============================================================

def frontend_file(filename: str) -> Path:

    file_path = FRONTEND_DIR / filename

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Frontend file not found: {filename}"
        )

    return file_path


# ============================================================
# FRONTEND - HOME
# ============================================================

@app.get("/", include_in_schema=False)
def frontend_home():

    return FileResponse(
        frontend_file("login.html")
    )


# ============================================================
# FRONTEND PAGES
# ============================================================

@app.get("/login.html", include_in_schema=False)
def login_page():

    return FileResponse(
        frontend_file("login.html")
    )


@app.get("/home.html", include_in_schema=False)
def home_page():

    return FileResponse(
        frontend_file("home.html")
    )


@app.get("/index.html", include_in_schema=False)
def index_page():

    return FileResponse(
        frontend_file("index.html")
    )


@app.get("/fleet.html", include_in_schema=False)
def fleet_page():

    return FileResponse(
        frontend_file("fleet.html")
    )


@app.get("/department.html", include_in_schema=False)
def department_page():

    return FileResponse(
        frontend_file("department.html")
    )


# ============================================================
# FRONTEND CSS / JS / OTHER STATIC FILES
# ============================================================

@app.get("/{filename}.css", include_in_schema=False)
def frontend_css(filename: str):

    return FileResponse(
        frontend_file(f"{filename}.css")
    )


@app.get("/{filename}.js", include_in_schema=False)
def frontend_js(filename: str):

    return FileResponse(
        frontend_file(f"{filename}.js")
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "service": "event-api",
    }


# ============================================================
# LIVE BUS FLEET
# ============================================================

@app.get("/api/fleet/buses")
def get_fleet_buses():

    return {

        "count": 5,

        "buses": [

            {
                "bus_id": "BUS-01",
                "latitude": 15.828100,
                "longitude": 78.037300,
                "status": "active",
            },

            {
                "bus_id": "BUS-02",
                "latitude": 15.830500,
                "longitude": 78.039700,
                "status": "active",
            },

            {
                "bus_id": "BUS-03",
                "latitude": 15.835000,
                "longitude": 78.042000,
                "status": "active",
            },

            {
                "bus_id": "BUS-04",
                "latitude": 15.825000,
                "longitude": 78.032000,
                "status": "active",
            },

            {
                "bus_id": "BUS-05",
                "latitude": 15.840000,
                "longitude": 78.045000,
                "status": "active",
            },

        ],
    }


# ============================================================
# DATABASE EVENT SUMMARY
# ============================================================

@app.get("/api/events/summary")
def event_summary():

    return get_summary()


# ============================================================
# HIGH PRIORITY EVENTS
# ============================================================

@app.get("/api/events/priority/high")
def high_priority_events():

    events = get_high_priority_events()

    return {
        "count": len(events),
        "events": events,
    }


# ============================================================
# ALL EVENTS
# ============================================================

@app.get("/api/events")
def all_events():

    events = get_all_events()

    return {
        "count": len(events),
        "events": events,
    }


# ============================================================
# EVENT DETAILS
# ============================================================

@app.get("/api/event/{event_id}")
def event_details(event_id: str):

    event = get_event_by_id(event_id)

    if not event:

        raise HTTPException(
            status_code=404,
            detail=f"Event not found: {event_id}",
        )

    return event


# ============================================================
# EVENTS BY TYPE
# ============================================================

@app.get("/api/events/type/{event_type}")
def events_by_type(event_type: str):

    events = get_events_by_type(event_type)

    if not events:

        raise HTTPException(
            status_code=404,
            detail=f"No events found for type: {event_type}",
        )

    return {
        "event_type": event_type,
        "count": len(events),
        "events": events,
    }


# ============================================================
# EVIDENCE IMAGE
# ============================================================

@app.get("/api/evidence/{event_id}")
def evidence_image(event_id: str):

    event = get_event_by_id(event_id)

    if not event:

        raise HTTPException(
            status_code=404,
            detail=f"Event not found: {event_id}",
        )

    image_path = event.get("evidence_image")

    if not image_path:

        raise HTTPException(
            status_code=404,
            detail="No evidence image available for this event",
        )

    if not os.path.exists(image_path):

        raise HTTPException(
            status_code=404,
            detail="Evidence image file not found",
        )

    return FileResponse(
        image_path,
        media_type="image/jpeg",
    )


# ============================================================
# VIDEO UPLOAD + PROCESSING
# ============================================================

@app.post("/api/video/upload")
async def upload_video(
    file: UploadFile = File(...)
):

    # --------------------------------------------------------
    # VALIDATE FILE
    # --------------------------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No video file provided",
        )

    # --------------------------------------------------------
    # ALLOWED VIDEO FORMATS
    # --------------------------------------------------------

    allowed_extensions = {
        ".mp4",
        ".avi",
        ".mov",
        ".mkv",
    }

    extension = Path(
        file.filename
    ).suffix.lower()

    if extension not in allowed_extensions:

        raise HTTPException(
            status_code=400,
            detail="Unsupported video format",
        )

    # --------------------------------------------------------
    # SAFE FILE NAME
    # --------------------------------------------------------

    safe_filename = Path(
        file.filename
    ).name

    video_path = (
        VIDEO_UPLOAD_DIR
        / safe_filename
    )

    # --------------------------------------------------------
    # SAVE VIDEO
    # --------------------------------------------------------

    with open(
        video_path,
        "wb",
    ) as buffer:

        shutil.copyfileobj(
            file.file,
            buffer,
        )

    print()
    print("============================================")
    print(" VIDEO UPLOAD SUCCESSFUL")
    print("============================================")
    print(f"Video: {video_path}")
    print("Starting Smart Bus AI processing...")
    print()

    # --------------------------------------------------------
    # PROCESS VIDEO
    # --------------------------------------------------------

    try:

        events = process_uploaded_video(
            video_path
        )

    except Exception as exc:

        print()
        print("VIDEO PROCESSING ERROR")
        print(exc)

        raise HTTPException(
            status_code=500,
            detail=(
                "Video processing failed: "
                f"{str(exc)}"
            ),
        )

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {

        "status": "processed",

        "filename": safe_filename,

        "video_path": str(video_path),

        "events_detected": len(events),

        "events": [

            {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "confidence": event.confidence,
                "bus_id": event.bus_id,
                "video_timestamp": event.video_timestamp,
                "latitude": event.latitude,
                "longitude": event.longitude,
                "severity": event.severity,
                "evidence_image": event.evidence_image,
                "priority": event.priority,
                "status": event.status,
                "alert_message": event.alert_message,
            }

            for event in events

        ],

        "message": (
            "Video uploaded and "
            "processed successfully"
        ),
    }