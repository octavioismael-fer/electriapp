"""Datos de demo para probar la app."""
from electriapp.database.connection import get_session
from electriapp.models.cliente import Cliente
from electriapp.models.trabajo import Trabajo
from datetime import datetime, timedelta


def sembrar():
    session = get_session()
    try:
        if session.query(Cliente).count() > 0:
            return

        ahora = datetime.now()
        clientes_data = [
            "García Roberto",
            "Martínez Ana",
            "López Juan",
            "Fernández María",
        ]
        clientes = []
        for nombre in clientes_data:
            c = Cliente(nombre=nombre)
            session.add(c)
            clientes.append(c)
        session.flush()

        trabajos_data = [
            (0, "Instalación de tomacorriente triple", 4500, -2),
            (0, "Cambio de llaves de luz", 2000, -5),
            (1, "Revisión y reparación de tablero eléctrico", 12000, -1),
            (1, "Instalación punto de luz exterior", 6500, -8),
            (2, "Cambio de disyuntores", 8000, -3),
            (3, "Instalación aire acondicionado split", 15000, -6),
            (3, "Puesta a tierra", 9500, -10),
        ]
        for idx, desc, monto, dias in trabajos_data:
            t = Trabajo(
                cliente_id=clientes[idx].id,
                descripcion=desc,
                monto=monto,
                fecha=ahora + timedelta(days=dias),
            )
            session.add(t)

        session.commit()
        print("✅ Datos de demo cargados.")
    except Exception as e:
        session.rollback()
        print(f"⚠️ Error: {e}")
    finally:
        session.close()
