from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

class Base(DeclarativeBase):
    pass

engine = create_engine("sqlite:///proyectos.db", echo=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


