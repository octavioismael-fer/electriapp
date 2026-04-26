from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "electriapp.db")


class Base(DeclarativeBase):
    pass


engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine)


def get_session():
    return SessionLocal()


def init_db():
    from electriapp.models import cliente, trabajo  # noqa
    Base.metadata.create_all(engine)
