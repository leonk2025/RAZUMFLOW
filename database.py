from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# URL para Turso (formato correcto)
TURSO_DATABASE_URL = os.getenv("TURSO_URL", "libsql://proyectos-leonk2025.aws-eu-west-1.turso.io")
TURSO_AUTH_TOKEN = os.getenv("TURSO_TOKEN", "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3NTY3MzczNTMsImlkIjoiNzM5ZWViY2QtZGQ0NS00ZjM0LTkxZmQtOGE1NjBiNTYxZjk2IiwicmlkIjoiYjJmOWQwZmItZjZiYi00MWNmLWE4MWUtZmFiOTg0OWNhNDRmIn0.WqPiIBT9cl5Q1kYX7pAStHfivto_tbvYKPdWsB33QzoboyZYgj72mwa0jKqzkT62TJ4dKjOciCEyRt0UhB7qAw")

# Connection string completo
SQLALCHEMY_DATABASE_URL = f"{TURSO_DATABASE_URL}?authToken={TURSO_AUTH_TOKEN}"

print(f"🔗 Conectando a Turso: {TURSO_DATABASE_URL}")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
