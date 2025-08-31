from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

#SQLALCHEMY_DATABASE_URL = "sqlite:///proyectos.db"
SQLALCHEMY_DATABASE_URL = "sqlite:////tmp/proyectos.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=false, autoflush=False, bind=engine)
Base = declarative_base()
