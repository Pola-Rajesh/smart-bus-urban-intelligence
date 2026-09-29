import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


# --------------------------------------------------
# PROJECT DATABASE PATH
# --------------------------------------------------

DATABASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATABASE_PATH = os.path.join(
    DATABASE_DIR,
    "smart_bus.db"
)

DATABASE_URL = "sqlite:///" + DATABASE_PATH


# --------------------------------------------------
# DATABASE ENGINE
# --------------------------------------------------

engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False
    }
)


# --------------------------------------------------
# SESSION
# --------------------------------------------------

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# --------------------------------------------------
# BASE MODEL
# --------------------------------------------------

Base = declarative_base()


# --------------------------------------------------
# DATABASE SESSION HELPER
# --------------------------------------------------

def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()