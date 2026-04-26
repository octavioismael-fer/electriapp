from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from electriapp.database.connection import Base


class Trabajo(Base):
    __tablename__ = "trabajos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    descripcion = Column(String(500), nullable=False)
    monto = Column(Float, nullable=False, default=0.0)
    fecha = Column(DateTime, nullable=False, default=datetime.now)
    created_at = Column(DateTime, default=datetime.now)

    cliente = relationship("Cliente", back_populates="trabajos")

    def __repr__(self):
        return f"<Trabajo {self.descripcion[:30]} ${self.monto}>"
