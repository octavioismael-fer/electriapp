from flask import Flask, render_template, request, redirect, url_for, jsonify
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, DeclarativeBase, relationship
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import os

app = Flask(__name__)

# ── Base de datos ─────────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "electriapp.db")
engine = create_engine(f"sqlite:///{DB_PATH}")
Session = sessionmaker(bind=engine)

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
    cliente = relationship("Cliente", back_populates="trabajos")

Base.metadata.create_all(engine)

# ── Helpers ───────────────────────────────────────────────────────────────
MESES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
         "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

def get_session():
    return Session()

# ── Rutas ─────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    ahora = datetime.now()
    mes = int(request.args.get("mes", ahora.month))
    anio = int(request.args.get("anio", ahora.year))

    session = get_session()
    inicio = datetime(anio, mes, 1)
    fin = datetime(anio, mes+1, 1) if mes < 12 else datetime(anio+1, 1, 1)

    trabajos = (session.query(Trabajo)
                .filter(Trabajo.fecha >= inicio, Trabajo.fecha < fin)
                .order_by(Trabajo.fecha.desc()).all())

    total = sum(t.monto for t in trabajos)

    # Resumen por cliente
    resumen = {}
    for t in trabajos:
        cid = t.cliente_id
        if cid not in resumen:
            resumen[cid] = {"nombre": t.cliente.nombre, "total": 0, "cantidad": 0, "id": cid}
        resumen[cid]["total"] += t.monto
        resumen[cid]["cantidad"] += 1

    # Navegacion de mes
    if mes == 1:
        mes_ant, anio_ant = 12, anio - 1
    else:
        mes_ant, anio_ant = mes - 1, anio
    if mes == 12:
        mes_sig, anio_sig = 1, anio + 1
    else:
        mes_sig, anio_sig = mes + 1, anio

    session.close()
    return render_template("index.html",
        trabajos=trabajos, total=total, resumen=list(resumen.values()),
        mes=mes, anio=anio, nombre_mes=MESES[mes-1],
        mes_ant=mes_ant, anio_ant=anio_ant,
        mes_sig=mes_sig, anio_sig=anio_sig)


@app.route("/nuevo", methods=["GET", "POST"])
def nuevo():
    session = get_session()
    if request.method == "POST":
        nombre_cliente = request.form["cliente"].strip().title()
        descripcion = request.form["descripcion"].strip()
        monto = float(request.form["monto"] or 0)
        fecha_str = request.form["fecha"]
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d")

        cliente = session.query(Cliente).filter(
            Cliente.nombre.ilike(nombre_cliente)).first()
        if not cliente:
            cliente = Cliente(nombre=nombre_cliente)
            session.add(cliente)
            session.flush()

        trabajo = Trabajo(cliente_id=cliente.id, descripcion=descripcion,
                          monto=monto, fecha=fecha)
        session.add(trabajo)
        session.commit()
        session.close()
        return redirect(url_for("index", mes=fecha.month, anio=fecha.year))

    clientes = [c.nombre for c in session.query(Cliente).order_by(Cliente.nombre).all()]
    session.close()
    hoy = datetime.now().strftime("%Y-%m-%d")
    return render_template("nuevo.html", clientes=clientes, hoy=hoy)


@app.route("/cliente/<int:cliente_id>")
def cliente(cliente_id):
    session = get_session()
    c = session.query(Cliente).filter(Cliente.id == cliente_id).first()
    trabajos = (session.query(Trabajo)
                .filter(Trabajo.cliente_id == cliente_id)
                .order_by(Trabajo.fecha.desc()).all())
    total = sum(t.monto for t in trabajos)
    session.close()
    return render_template("cliente.html", cliente=c, trabajos=trabajos, total=total)


@app.route("/eliminar/<int:trabajo_id>", methods=["POST"])
def eliminar(trabajo_id):
    session = get_session()
    t = session.query(Trabajo).filter(Trabajo.id == trabajo_id).first()
    mes = t.fecha.month
    anio = t.fecha.year
    session.delete(t)
    session.commit()
    session.close()
    return redirect(url_for("index", mes=mes, anio=anio))


@app.route("/api/clientes")
def api_clientes():
    session = get_session()
    q = request.args.get("q", "").lower()
    clientes = session.query(Cliente).filter(
        Cliente.nombre.ilike(f"%{q}%")).limit(5).all()
    session.close()
    return jsonify([c.nombre for c in clientes])


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
