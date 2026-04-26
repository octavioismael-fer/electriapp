from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from electriapp.database.connection import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(150), unique=True, nullable=False)
    telefono = Column(String(30), nullable=True)
    email = Column(String(150), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    trabajos = relationship("Trabajo", back_populates="cliente", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Cliente {self.nombre}>"
