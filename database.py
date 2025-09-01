from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# URL de SQLiteCloud con el driver explícito
SQLALCHEMY_DATABASE_URL = "sqlitecloud+dbapi://csxitt7rnz.g3.sqlite.cloud:8860/proyectos.db?apikey=FmUQYOjwnVPprdgQwCPsNrwKxO3fT3N7WgQP5cJla6A"

print(f"🔗 Conectando a: {SQLALCHEMY_DATABASE_URL}")

# Crear el engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
