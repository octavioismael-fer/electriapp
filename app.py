from flask import Flask, render_template, request, redirect, url_for, jsonify

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import sessionmaker, DeclarativeBase, relationship, joinedload
from datetime import datetime
import os

app = Flask(__name__)

class Base(DeclarativeBase):
    pass

class Cliente(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(150), unique=True, nullable=False)
    telefono = Column(String(30), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    trabajos = relationship("Trabajo", back_populates="cliente", cascade="all, delete-orphan")

class Trabajo(Base):
    __tablename__ = "trabajos"
    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    descripcion = Column(String(500), nullable=False)
    monto = Column(Float, nullable=False, default=0.0)
    fecha = Column(DateTime, nullable=False, default=datetime.now)
    pagado = Column(Boolean, nullable=False, default=False)   # ← NUEVO
    cliente = relationship("Cliente", back_populates="trabajos")

MESES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
         "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

def get_session():
    engine = create_engine(os.environ["DATABASE_URL"])
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

def buscar_o_crear_cliente(session, nombre):
    nombre = nombre.strip().title()
    cliente = session.query(Cliente).filter(Cliente.nombre.ilike(nombre)).first()
    if not cliente:
        cliente = Cliente(nombre=nombre)
        session.add(cliente)
        session.flush()
    return cliente

@app.route("/")
def index():
    ahora = datetime.now()
    mes = int(request.args.get("mes", ahora.month))
    anio = int(request.args.get("anio", ahora.year))
    filtro = request.args.get("filtro", "todos")  # ← NUEVO: todos / pagados / deben

    session = get_session()
    inicio = datetime(anio, mes, 1)
    fin = datetime(anio, mes+1, 1) if mes < 12 else datetime(anio+1, 1, 1)

    query = (session.query(Trabajo)
             .options(joinedload(Trabajo.cliente))
             .filter(Trabajo.fecha >= inicio, Trabajo.fecha < fin)
             .order_by(Trabajo.fecha.desc()))

    # ← NUEVO: aplicar filtro de pago
    if filtro == "pagados":
        query = query.filter(Trabajo.pagado == True)
    elif filtro == "deben":
        query = query.filter(Trabajo.pagado == False)

    trabajos = query.all()
    total = sum(t.monto for t in trabajos)

    # Para el resumen usamos siempre todos (sin filtro)
    todos = (session.query(Trabajo)
             .options(joinedload(Trabajo.cliente))
             .filter(Trabajo.fecha >= inicio, Trabajo.fecha < fin)
             .all())
    resumen = {}
    for t in todos:
        cid = t.cliente_id
        if cid not in resumen:
            resumen[cid] = {"nombre": t.cliente.nombre, "total": 0, "cantidad": 0, "id": cid}
        resumen[cid]["total"] += t.monto
        resumen[cid]["cantidad"] += 1

    mes_ant = 12 if mes == 1 else mes - 1
    anio_ant = anio - 1 if mes == 1 else anio
    mes_sig = 1 if mes == 12 else mes + 1
    anio_sig = anio + 1 if mes == 12 else anio

    session.close()
    return render_template("index.html",
                           trabajos=trabajos, total=total, resumen=list(resumen.values()),
                           mes=mes, anio=anio, nombre_mes=MESES[mes-1],
                           mes_ant=mes_ant, anio_ant=anio_ant,
                           mes_sig=mes_sig, anio_sig=anio_sig,
                           filtro=filtro)  # ← NUEVO

@app.route("/nuevo", methods=["GET", "POST"])
def nuevo():
    session = get_session()
    if request.method == "POST":
        nombre_cliente = request.form["cliente"].strip().title()
        descripcion = request.form["descripcion"].strip()
        monto = float(request.form["monto"] or 0)
        fecha = datetime.strptime(request.form["fecha"], "%Y-%m-%d")
        pagado = request.form.get("pagado") == "1"   # ← NUEVO

        try:
            cliente = buscar_o_crear_cliente(session, nombre_cliente)
            trabajo = Trabajo(cliente_id=cliente.id, descripcion=descripcion,
                              monto=monto, fecha=fecha, pagado=pagado)   # ← NUEVO
            session.add(trabajo)
            session.commit()
        except Exception:
            session.rollback()
            cliente = session.query(Cliente).filter(
                Cliente.nombre.ilike(nombre_cliente)).first()
            if cliente:
                trabajo = Trabajo(cliente_id=cliente.id, descripcion=descripcion,
                                  monto=monto, fecha=fecha, pagado=pagado)   # ← NUEVO
                session.add(trabajo)
                session.commit()
        finally:
            session.close()
        return redirect(url_for("index", mes=fecha.month, anio=fecha.year))

    clientes = [c.nombre for c in session.query(Cliente).order_by(Cliente.nombre).all()]
    session.close()
    return render_template("nuevo.html", clientes=clientes, hoy=datetime.now().strftime("%Y-%m-%d"))

@app.route("/cliente/<int:cliente_id>")
def cliente(cliente_id):
    session = get_session()
    c = session.query(Cliente).filter(Cliente.id == cliente_id).first()
    trabajos = (session.query(Trabajo)
                .options(joinedload(Trabajo.cliente))
                .filter(Trabajo.cliente_id == cliente_id)
                .order_by(Trabajo.fecha.desc()).all())
    total = sum(t.monto for t in trabajos)
    cobrado = sum(t.monto for t in trabajos if t.pagado)      # ← NUEVO
    pendiente = sum(t.monto for t in trabajos if not t.pagado) # ← NUEVO
    session.close()
    return render_template("cliente.html", cliente=c, trabajos=trabajos,
                           total=total, cobrado=cobrado, pendiente=pendiente)  # ← NUEVO

@app.route("/eliminar/<int:trabajo_id>", methods=["POST"])
def eliminar(trabajo_id):
    session = get_session()
    t = session.query(Trabajo).filter(Trabajo.id == trabajo_id).first()
    mes, anio = t.fecha.month, t.fecha.year
    session.delete(t)
    session.commit()
    session.close()
    return redirect(url_for("index", mes=mes, anio=anio))

# ← NUEVO: ruta para alternar estado de pago sin recargar página
@app.route("/toggle-pago/<int:trabajo_id>", methods=["POST"])
def toggle_pago(trabajo_id):
    session = get_session()
    t = session.query(Trabajo).filter(Trabajo.id == trabajo_id).first()
    if t:
        t.pagado = not t.pagado
        session.commit()
        result = {"pagado": t.pagado}
    else:
        result = {"error": "not found"}
    session.close()
    return jsonify(result)

@app.route("/api/clientes")
def api_clientes():
    session = get_session()
    q = request.args.get("q", "")
    clientes = session.query(Cliente).filter(
        Cliente.nombre.ilike(f"%{q}%")).limit(5).all()
    session.close()
    return jsonify([c.nombre for c in clientes])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
