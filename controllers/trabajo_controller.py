from electriapp.models.trabajo import Trabajo
from electriapp.models.cliente import Cliente
from electriapp.database.connection import get_session
from datetime import datetime


class TrabajoController:

    @staticmethod
    def crear(cliente_id: int, descripcion: str, monto: float, fecha: datetime) -> Trabajo:
        session = get_session()
        try:
            trabajo = Trabajo(
                cliente_id=cliente_id,
                descripcion=descripcion.strip(),
                monto=monto,
                fecha=fecha,
            )
            session.add(trabajo)
            session.commit()
            session.refresh(trabajo)
            return trabajo
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
    def obtener_por_mes(anio: int, mes: int) -> list[dict]:
        """Retorna todos los trabajos de un mes con datos del cliente."""
        session = get_session()
        try:
            inicio = datetime(anio, mes, 1)
            fin = datetime(anio, mes + 1, 1) if mes < 12 else datetime(anio + 1, 1, 1)

            trabajos = (
                session.query(Trabajo)
                .filter(Trabajo.fecha >= inicio, Trabajo.fecha < fin)
                .order_by(Trabajo.fecha.desc())
                .all()
            )
            resultado = []
            for t in trabajos:
                cliente = session.query(Cliente).filter(Cliente.id == t.cliente_id).first()
                resultado.append({
                    "id": t.id,
                    "cliente": cliente.nombre if cliente else "—",
                    "cliente_id": t.cliente_id,
                    "descripcion": t.descripcion,
                    "monto": t.monto,
                    "fecha": t.fecha,
                })
            return resultado
        finally:
            session.close()

    @staticmethod
    def obtener_por_cliente(cliente_id: int) -> list[Trabajo]:
        session = get_session()
        try:
            return (
                session.query(Trabajo)
                .filter(Trabajo.cliente_id == cliente_id)
                .order_by(Trabajo.fecha.desc())
                .all()
            )
        finally:
            session.close()

    @staticmethod
    def total_por_mes(anio: int, mes: int) -> float:
        trabajos = TrabajoController.obtener_por_mes(anio, mes)
        return sum(t["monto"] for t in trabajos)

    @staticmethod
    def total_por_cliente(cliente_id: int) -> float:
        trabajos = TrabajoController.obtener_por_cliente(cliente_id)
        return sum(t.monto for t in trabajos)

    @staticmethod
    def resumen_por_cliente_mes(anio: int, mes: int) -> list[dict]:
        """Agrupa los trabajos del mes por cliente."""
        trabajos = TrabajoController.obtener_por_mes(anio, mes)
        clientes = {}
        for t in trabajos:
            cid = t["cliente_id"]
            if cid not in clientes:
                clientes[cid] = {"cliente": t["cliente"], "cliente_id": cid,
                                  "trabajos": 0, "total": 0.0}
            clientes[cid]["trabajos"] += 1
            clientes[cid]["total"] += t["monto"]
        return sorted(clientes.values(), key=lambda x: x["total"], reverse=True)

    @staticmethod
    def eliminar(trabajo_id: int):
        session = get_session()
        try:
            t = session.query(Trabajo).filter(Trabajo.id == trabajo_id).first()
            if t:
                session.delete(t)
                session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
    def actualizar(trabajo_id: int, descripcion: str, monto: float, fecha: datetime):
        session = get_session()
        try:
            t = session.query(Trabajo).filter(Trabajo.id == trabajo_id).first()
            if not t:
                raise ValueError("Trabajo no encontrado")
            t.descripcion = descripcion.strip()
            t.monto = monto
            t.fecha = fecha
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
