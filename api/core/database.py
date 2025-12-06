from sqlmodel import create_engine, SQLModel, Session
from api.core.config import settings

# Create the database engine
engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))


def create_db_and_tables() -> None:
    """Create all database tables."""
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
