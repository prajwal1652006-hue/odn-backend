from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

DATABASE_URL = settings.DATABASE_URL

if DATABASE_URL.startswith("postgres://"):
	DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://") and not (
	"+psycopg" in DATABASE_URL or "+psycopg2" in DATABASE_URL
):
	DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_engine(
	DATABASE_URL,
	pool_pre_ping=True,
	pool_size=10,
	max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
	"""Dependency for obtaining database sessions per API request."""
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()
