from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# We use SQLite for the initial MVP scaffolding to avoid requiring a running Postgres instance.
# SQLAlchemy abstracts this so it can be trivially swapped to PostgreSQL later via the connection string.
SQLALCHEMY_DATABASE_URL = "sqlite:///./diagnostic_engine.db"
# If using PostgreSQL:
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost/dbname"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
