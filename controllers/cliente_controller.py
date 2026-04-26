from electriapp.models.cliente import Cliente
from electriapp.database.connection import get_session


class ClienteController:

    @staticmethod
    def obtener_todos() -> list[Cliente]:
        session = get_session()
        try:
            return session.query(Cliente).order_by(Cliente.nombre).all()
        finally:
            session.close()

    @staticmethod
    def obtener_nombres() -> list[str]:
        session = get_session()
        try:
            clientes = session.query(Cliente.nombre).order_by(Cliente.nombre).all()
            return [c.nombre for c in clientes]
        finally:
            session.close()

    @staticmethod
    def buscar_o_crear(nombre: str) -> Cliente:
        """Devuelve el cliente existente o lo crea si no existe."""
        nombre = nombre.strip().title()
        session = get_session()
        try:
            cliente = session.query(Cliente).filter(
                Cliente.nombre.ilike(nombre)
            ).first()
            if not cliente:
                cliente = Cliente(nombre=nombre)
                session.add(cliente)
                session.commit()
                session.refresh(cliente)
            return cliente
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
    def obtener_por_id(cliente_id: int) -> Cliente | None:
        session = get_session()
        try:
            return session.query(Cliente).filter(Cliente.id == cliente_id).first()
        finally:
            session.close()

    @staticmethod
    def eliminar(cliente_id: int):
        session = get_session()
        try:
            cliente = session.query(Cliente).filter(Cliente.id == cliente_id).first()
            if cliente:
                session.delete(cliente)
                session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
