import sqlite3
from pathlib import Path


# ============================================================
# DATABASE PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATABASE_PATH = (
    PROJECT_ROOT
    / "database"
    / "smart_bus.db"
)


print("============================================")
print(" SMART BUS SESSION DATABASE MIGRATION")
print("============================================")
print()

print(f"Database: {DATABASE_PATH}")
print()


# ============================================================
# CONNECT
# ============================================================

connection = sqlite3.connect(
    DATABASE_PATH
)

cursor = connection.cursor()


try:

    # ========================================================
    # CREATE PROCESSING SESSIONS TABLE
    # ========================================================

    print("Creating processing_sessions table...")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processing_sessions (

            id INTEGER PRIMARY KEY,

            session_id TEXT NOT NULL UNIQUE,

            video_filename TEXT NOT NULL,

            uploaded_at TEXT,

            completed_at TEXT,

            status TEXT,

            total_events INTEGER DEFAULT 0
        )
    """)

    print("Processing sessions table ready.")


    # ========================================================
    # CHECK EVENTS TABLE
    # ========================================================

    cursor.execute(
        "PRAGMA table_info(events)"
    )

    columns = [
        row[1]
        for row in cursor.fetchall()
    ]


    # ========================================================
    # ADD SESSION ID TO EVENTS
    # ========================================================

    if "session_id" not in columns:

        print("Adding session_id to events table...")

        cursor.execute("""
            ALTER TABLE events
            ADD COLUMN session_id TEXT
        """)

        print("session_id column added.")

    else:

        print("session_id column already exists.")


    # ========================================================
    # CREATE INDEX
    # ========================================================

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        ix_events_session_id
        ON events(session_id)
    """)


    # ========================================================
    # COMMIT
    # ========================================================

    connection.commit()


    print()
    print("============================================")
    print(" MIGRATION SUCCESSFUL")
    print("============================================")
    print()
    print("Existing events were NOT deleted.")
    print("Existing event data was NOT modified.")
    print("Processing sessions table is ready.")
    print("events.session_id is ready.")
    print()


except Exception as error:

    connection.rollback()

    print()
    print("============================================")
    print(" MIGRATION FAILED")
    print("============================================")
    print(error)

    raise


finally:

    connection.close()
