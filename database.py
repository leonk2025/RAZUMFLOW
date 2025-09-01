from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# URL para Turso (LibSQL)
SQLALCHEMY_DATABASE_URL = os.getenv("TURSO_URL", "libsql://proyectos-leonk2025.aws-eu-west-1.turso.io")

print(f"🔗 Conectando a: {SQLALCHEMY_DATABASE_URL}")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
