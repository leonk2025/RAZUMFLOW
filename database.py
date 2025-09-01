from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Configuración para SQLiteCloud (usa variable de entorno para seguridad)
#SQLALCHEMY_DATABASE_URL = os.getenv("SQLITECLOUD_URL", "sqlite:///proyectos.db")
SQLALCHEMY_DATABASE_URL = os.getenv("SQLITECLOUD_URL","sqlitecloud://csxitt7rnz.g3.sqlite.cloud:8860/proyectos.db?apikey=FmUQYOjwnVPprdgQwCPsNrwKxO3fT3N7WgQP5cJla6A")

# Crear el engine - se adapta automáticamente según la URL
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite://" in SQLALCHEMY_DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
