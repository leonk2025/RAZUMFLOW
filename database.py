from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# URL DIRECTA de SQLiteCloud (para testing)
SQLALCHEMY_DATABASE_URL = "sqlitecloud://csxitt7rnz.g3.sqlite.cloud:8860/proyectos.db?apikey=FmUQYOjwnVPprdgQwCPsNrwKxO3fT3N7WgQP5cJla6A"

# Debug para confirmar que usa SQLiteCloud
print(f"🔗 Conectando a: {SQLALCHEMY_DATABASE_URL}")
print("✅ Usando SQLiteCloud directamente")

# Crear el engine para SQLiteCloud (sin connect_args para SQLite local)
engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
