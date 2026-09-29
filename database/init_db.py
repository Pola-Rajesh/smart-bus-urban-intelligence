from database import engine, Base

# Import models so SQLAlchemy knows which tables to create
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

sys.path.insert(
    0,
    os.path.join(PROJECT_ROOT, "backend", "models")
)

from event_model import Event


print("============================================")
print(" SMART BUS DATABASE INITIALIZATION")
print("============================================")

print()
print("Creating database tables...")

Base.metadata.create_all(bind=engine)

print()
print("Database initialization complete.")
print("Database file:")
print(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "smart_bus.db"
        )
    )
)

print()
print("Tables created:")
print("- events")

print("============================================")