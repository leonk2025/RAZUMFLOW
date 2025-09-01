from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# URL CORRECTA para SQLiteCloud (usando sqlitecloud:// directamente)
SQLALCHEMY_DATABASE_URL = "sqlitecloud://csxitt7rnz.g3.sqlite.cloud:8860/proyectos.db?apikey=FmUQYOjwnVPprdgQwCPsNrwKxO3fT3N7WgQP5cJla6A"

print(f"🔗 Conectando a: {SQLALCHEMY_DATABASE_URL}")

# Crear el engine - SQLAlchemy detectará automáticamente el driver
engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
