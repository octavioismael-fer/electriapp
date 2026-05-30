from flask import Flask, render_template, request, redirect, url_for, jsonify

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import sessionmaker, DeclarativeBase, relationship, joinedload
from datetime import datetime, timedelta, timezone

# Argentina no observa DST, siempre UTC-3
ARGENTINA_TZ = timezone(timedelta(hours=-3))

def ahora_local():
    """Hora actual en Argentina como datetime naive (compatible con tarea_datetime en DB)."""
    return datetime.now(ARGENTINA_TZ).replace(tzinfo=None)
import os
import json

from pywebpush import webpush, WebPushException

app = Flask(__name__)

@app.context_processor
def inject_vapid():
    return {"vapid_public_key": os.environ.get("VAPID_PUBLIC_KEY", "")}

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
    pagado = Column(Boolean, nullable=False, default=False)
    es_tarea = Column(Boolean, nullable=False, default=False)
    tarea_datetime = Column(DateTime, nullable=True)
    tarea_hecha = Column(Boolean, nullable=False, default=False)
    cliente = relationship("Cliente", back_populates="trabajos")

class PushSubscription(Base):
    __tablename__ = "push_subscriptions"
    id = Column(Integer, primary_key=True)
    endpoint = Column(String(500), unique=True, nullable=False)
    p256dh = Column(String(200), nullable=False)
    auth = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

class NotificacionEnviada(Base):
    __tablename__ = "notificaciones_enviadas"
    id = Column(Integer, primary_key=True)
    trabajo_id = Column(Integer, ForeignKey("trabajos.id", ondelete="CASCADE"), nullable=False)
    tipo = Column(String(20), nullable=False)  # "aviso" o "ahora"
    enviada_at = Column(DateTime, default=datetime.now)

def _enviar_push_a_todos(session, titulo, cuerpo):
    subs = session.query(PushSubscription).all()
    private_key = os.environ.get("VAPID_PRIVATE_KEY", "")
    email = os.environ.get("VAPID_EMAIL", "admin@electriapp.com")
    muertos = []
    for sub in subs:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth}
                },
                data=json.dumps({"titulo": titulo, "cuerpo": cuerpo}),
                vapid_private_key=private_key,
                vapid_claims={"sub": f"mailto:{email}"}
            )
        except WebPushException as ex:
            if ex.response and ex.response.status_code in (404, 410):
                muertos.append(sub.id)
    for sid in muertos:
        session.query(PushSubscription).filter(PushSubscription.id == sid).delete()
    if muertos:
        session.commit()

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
    filtro = request.args.get("filtro", "todos")

    session = get_session()
    inicio = datetime(anio, mes, 1)
    fin = datetime(anio, mes+1, 1) if mes < 12 else datetime(anio+1, 1, 1)

    query = (session.query(Trabajo)
             .options(joinedload(Trabajo.cliente))
             .filter(Trabajo.fecha >= inicio, Trabajo.fecha < fin)
             .order_by(Trabajo.fecha.desc()))

    if filtro == "pagados":
        query = query.filter(Trabajo.pagado == True)
    elif filtro == "deben":
        query = query.filter(Trabajo.pagado == False)

    trabajos = query.all()
    total = sum(t.monto for t in trabajos)

    resumen = {}
    for t in trabajos:
        cid = t.cliente_id
        if cid not in resumen:
            resumen[cid] = {"nombre": t.cliente.nombre, "total": 0, "cantidad": 0, "id": cid}
        resumen[cid]["total"] += t.monto
        resumen[cid]["cantidad"] += 1

    tareas_pendientes = (session.query(Trabajo)
                         .options(joinedload(Trabajo.cliente))
                         .filter(Trabajo.es_tarea == True,
                                 Trabajo.tarea_hecha == False,
                                 Trabajo.tarea_datetime != None)
                         .order_by(Trabajo.tarea_datetime.asc())
                         .all())

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
                           filtro=filtro,
                           tareas_pendientes=tareas_pendientes)

@app.route("/nuevo", methods=["GET", "POST"])
def nuevo():
    session = get_session()
    if request.method == "POST":
        nombre_cliente = request.form["cliente"].strip().title()
        descripcion = request.form["descripcion"].strip()
        monto = float(request.form["monto"] or 0)
        fecha = datetime.strptime(request.form["fecha"], "%Y-%m-%d")
        pagado = request.form.get("pagado") == "1"

        es_tarea = request.form.get("es_tarea") == "1"
        tarea_datetime = None
        if es_tarea:
            tarea_fecha_str = request.form.get("tarea_fecha", "")
            tarea_hora_str = request.form.get("tarea_hora", "")
            if tarea_fecha_str and tarea_hora_str:
                tarea_datetime = datetime.strptime(
                    f"{tarea_fecha_str} {tarea_hora_str}", "%Y-%m-%d %H:%M"
                )

        try:
            cliente = buscar_o_crear_cliente(session, nombre_cliente)
            trabajo = Trabajo(
                cliente_id=cliente.id,
                descripcion=descripcion,
                monto=monto,
                fecha=fecha,
                pagado=pagado,
                es_tarea=es_tarea,
                tarea_datetime=tarea_datetime
            )
            session.add(trabajo)
            session.commit()
        except Exception:
            session.rollback()
            cliente = session.query(Cliente).filter(
                Cliente.nombre.ilike(nombre_cliente)).first()
            if cliente:
                trabajo = Trabajo(
                    cliente_id=cliente.id,
                    descripcion=descripcion,
                    monto=monto,
                    fecha=fecha,
                    pagado=pagado,
                    es_tarea=es_tarea,
                    tarea_datetime=tarea_datetime
                )
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
    cobrado = sum(t.monto for t in trabajos if t.pagado)
    pendiente = sum(t.monto for t in trabajos if not t.pagado)
    session.close()
    return render_template("cliente.html", cliente=c, trabajos=trabajos,
                           total=total, cobrado=cobrado, pendiente=pendiente)

@app.route("/eliminar/<int:trabajo_id>", methods=["POST"])
def eliminar(trabajo_id):
    session = get_session()
    t = session.query(Trabajo).filter(Trabajo.id == trabajo_id).first()
    mes, anio = t.fecha.month, t.fecha.year
    session.delete(t)
    session.commit()
    session.close()
    return redirect(url_for("index", mes=mes, anio=anio))

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

@app.route("/tarea-hecha/<int:trabajo_id>", methods=["POST"])
def tarea_hecha(trabajo_id):
    session = get_session()
    t = session.query(Trabajo).filter(Trabajo.id == trabajo_id).first()
    if t:
        t.tarea_hecha = True
        session.commit()
        result = {"ok": True}
    else:
        result = {"error": "not found"}
    session.close()
    return jsonify(result)

@app.route("/api/tareas-pendientes")
def api_tareas_pendientes():
    session = get_session()
    tareas = (session.query(Trabajo)
              .options(joinedload(Trabajo.cliente))
              .filter(Trabajo.es_tarea == True,
                      Trabajo.tarea_hecha == False,
                      Trabajo.tarea_datetime != None)
              .all())
    result = []
    for t in tareas:
        result.append({
            "id": t.id,
            "cliente": t.cliente.nombre,
            "descripcion": t.descripcion,
            "tarea_datetime": t.tarea_datetime.isoformat() if t.tarea_datetime else None
        })
    session.close()
    return jsonify(result)

@app.route("/sw.js")
def service_worker():
    from flask import send_from_directory
    response = send_from_directory('static', 'sw.js')
    response.headers['Service-Worker-Allowed'] = '/'
    response.headers['Cache-Control'] = 'no-cache'
    return response

@app.route("/debug")
def debug():
    return render_template("debug.html")

@app.route("/api/clientes")
def api_clientes():
    session = get_session()
    q = request.args.get("q", "")
    clientes = session.query(Cliente).filter(
        Cliente.nombre.ilike(f"%{q}%")).limit(5).all()
    session.close()
    return jsonify([c.nombre for c in clientes])

@app.route("/debug/cron-check")
def debug_cron_check():
    session = get_session()
    try:
        ahora = ahora_local()
        tareas = (session.query(Trabajo)
                  .options(joinedload(Trabajo.cliente))
                  .filter(Trabajo.es_tarea == True,
                          Trabajo.tarea_hecha == False,
                          Trabajo.tarea_datetime != None)
                  .all())
        subs = session.query(PushSubscription).count()
        resultado = []
        for t in tareas:
            minutos = (t.tarea_datetime - ahora).total_seconds() / 60
            resultado.append({
                "id": t.id,
                "cliente": t.cliente.nombre,
                "tarea_datetime": t.tarea_datetime.isoformat(),
                "minutos_restantes": round(minutos, 1),
                "en_ventana_aviso": 13 <= minutos <= 17,
                "en_ventana_ahora": -1 <= minutos <= 1,
            })
    finally:
        session.close()
    return jsonify({
        "ahora_servidor": ahora.isoformat(),
        "suscripciones_en_db": subs,
        "tareas_pendientes": resultado,
    })

@app.route("/debug/push-status")
def debug_push_status():
    import traceback
    session = get_session()
    try:
        sub_count = session.query(PushSubscription).count()
    except Exception:
        return jsonify({"error": traceback.format_exc()}), 200
    finally:
        session.close()
    return jsonify({
        "suscripciones_en_db": sub_count,
        "vapid_public_key": bool(os.environ.get("VAPID_PUBLIC_KEY")),
        "vapid_private_key": bool(os.environ.get("VAPID_PRIVATE_KEY")),
        "vapid_email": os.environ.get("VAPID_EMAIL", "NO SETEADO"),
    })

@app.route("/api/subscribe", methods=["POST"])
def api_subscribe():
    data = request.json
    if not data or "endpoint" not in data:
        return jsonify({"error": "invalid"}), 400
    try:
        endpoint = data["endpoint"]
        p256dh = data["keys"]["p256dh"]
        auth = data["keys"]["auth"]
    except (KeyError, TypeError):
        return jsonify({"error": "invalid payload"}), 400

    session = get_session()
    try:
        sub = session.query(PushSubscription).filter(
            PushSubscription.endpoint == endpoint
        ).first()
        if not sub:
            sub = PushSubscription(endpoint=endpoint, p256dh=p256dh, auth=auth)
            session.add(sub)
            session.commit()
    finally:
        session.close()
    return jsonify({"ok": True})

@app.route("/api/enviar-notificaciones", methods=["GET", "POST"])
def api_enviar_notificaciones():
    import traceback
    session = get_session()
    try:
        ahora = ahora_local()
        enviadas = 0
        errores = []

        # Limpia registros viejos (más de 2 días)
        session.query(NotificacionEnviada).filter(
            NotificacionEnviada.enviada_at < datetime.now() - timedelta(days=2)
        ).delete()

        tareas = (session.query(Trabajo)
                  .options(joinedload(Trabajo.cliente))
                  .filter(Trabajo.es_tarea == True,
                          Trabajo.tarea_hecha == False,
                          Trabajo.tarea_datetime != None)
                  .all())

        for t in tareas:
            dt = t.tarea_datetime
            minutos = (dt - ahora).total_seconds() / 60

            # Aviso ~15 minutos antes
            if 13 <= minutos <= 17:
                ya = session.query(NotificacionEnviada).filter(
                    NotificacionEnviada.trabajo_id == t.id,
                    NotificacionEnviada.tipo == "aviso"
                ).first()
                if not ya:
                    try:
                        _enviar_push_a_todos(session, f"⚡ En ~15 min — {t.cliente.nombre}", t.descripcion)
                        session.add(NotificacionEnviada(trabajo_id=t.id, tipo="aviso"))
                        enviadas += 1
                    except Exception as e:
                        errores.append({"tarea": t.id, "tipo": "aviso", "error": traceback.format_exc()})

            # Notificación en el momento
            if -1 <= minutos <= 1:
                ya = session.query(NotificacionEnviada).filter(
                    NotificacionEnviada.trabajo_id == t.id,
                    NotificacionEnviada.tipo == "ahora"
                ).first()
                if not ya:
                    try:
                        _enviar_push_a_todos(session, f"🔧 ¡Ahora! — {t.cliente.nombre}", t.descripcion)
                        session.add(NotificacionEnviada(trabajo_id=t.id, tipo="ahora"))
                        enviadas += 1
                    except Exception as e:
                        errores.append({"tarea": t.id, "tipo": "ahora", "error": traceback.format_exc()})

        session.commit()
    except Exception as e:
        session.rollback()
        return jsonify({"ok": False, "error": traceback.format_exc()}), 200
    finally:
        session.close()
    return jsonify({"ok": True, "enviadas": enviadas, "errores": errores})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
