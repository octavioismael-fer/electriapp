import flet as ft
from datetime import datetime
from electriapp.controllers.trabajo_controller import TrabajoController
from electriapp.controllers.cliente_controller import ClienteController

BG       = "#0f172a"
SURFACE  = "#1e293b"
SURFACE2 = "#334155"
ACENTO   = "#f59e0b"
TEXTO    = "#f1f5f9"
SUBTEXTO = "#94a3b8"
OK       = "#22c55e"
ERROR    = "#ef4444"

MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
         "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]


def vista_nuevo_trabajo(page: ft.Page, ir_a, params: dict):
    refrescar_inicio = params.get("refrescar", lambda: None)
    hoy = datetime.now()
    fecha_sel = [hoy]
    error_msg = ft.Text("", color=ERROR, size=13, visible=False)

    # ── Campo cliente con sugerencias ─────────────────────────────────────
    nombres_clientes = ClienteController.obtener_nombres()
    sugerencias_visibles = ft.Column(spacing=4, visible=False)

    campo_cliente = ft.TextField(
        label="Cliente",
        hint_text="Nombre del cliente",
        border_color=SURFACE2,
        focused_border_color=ACENTO,
        label_style=ft.TextStyle(color=SUBTEXTO),
        color=TEXTO,
        bgcolor=SURFACE,
        border_radius=10,
        prefix_icon=ft.Icons.PERSON_OUTLINE,
    )

    def on_cliente_change(e):
        texto = campo_cliente.value.strip().lower()
        sugerencias_visibles.controls.clear()
        if texto and len(texto) >= 2:
            matches = [n for n in nombres_clientes if texto in n.lower()][:4]
            if matches:
                for nombre in matches:
                    sugerencias_visibles.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.PERSON, size=16, color=ACENTO),
                                ft.Text(nombre, color=TEXTO, size=14),
                            ], spacing=8),
                            bgcolor=SURFACE2,
                            border_radius=8,
                            padding=ft.padding.symmetric(horizontal=14, vertical=10),
                            on_click=lambda e, n=nombre: seleccionar_cliente(n),
                            ink=True,
                        )
                    )
                sugerencias_visibles.visible = True
            else:
                sugerencias_visibles.visible = False
        else:
            sugerencias_visibles.visible = False
        page.update()

    def seleccionar_cliente(nombre):
        campo_cliente.value = nombre
        sugerencias_visibles.visible = False
        page.update()

    campo_cliente.on_change = on_cliente_change

    # ── Descripción ───────────────────────────────────────────────────────
    campo_descripcion = ft.TextField(
        label="Descripción del trabajo",
        hint_text="Ej: Instalación de toma corriente, reparación tablero...",
        border_color=SURFACE2,
        focused_border_color=ACENTO,
        label_style=ft.TextStyle(color=SUBTEXTO),
        color=TEXTO,
        bgcolor=SURFACE,
        border_radius=10,
        multiline=True,
        min_lines=3,
        max_lines=5,
        prefix_icon=ft.Icons.BUILD_OUTLINED,
    )

    # ── Monto ─────────────────────────────────────────────────────────────
    campo_monto = ft.TextField(
        label="Monto ($)",
        hint_text="0",
        border_color=SURFACE2,
        focused_border_color=ACENTO,
        label_style=ft.TextStyle(color=SUBTEXTO),
        color=TEXTO,
        bgcolor=SURFACE,
        border_radius=10,
        keyboard_type=ft.KeyboardType.NUMBER,
        prefix_icon=ft.Icons.ATTACH_MONEY,
    )

    # ── Fecha ─────────────────────────────────────────────────────────────
    lbl_fecha = ft.Text(hoy.strftime("%d / %m / %Y"), size=16, color=TEXTO,
                        weight=ft.FontWeight.BOLD)

    def cambiar_dia(delta):
        from datetime import timedelta
        fecha_sel[0] = fecha_sel[0] + timedelta(days=delta)
        lbl_fecha.value = fecha_sel[0].strftime("%d / %m / %Y")
        page.update()

    selector_fecha = ft.Container(
        content=ft.Column([
            ft.Text("Fecha del trabajo", size=13, color=SUBTEXTO),
            ft.Row(
                [
                    ft.IconButton(ft.Icons.CHEVRON_LEFT, icon_color=ACENTO,
                                  on_click=lambda e: cambiar_dia(-1)),
                    ft.Container(content=lbl_fecha, expand=True,
                                 alignment=ft.alignment.center),
                    ft.IconButton(ft.Icons.CHEVRON_RIGHT, icon_color=ACENTO,
                                  on_click=lambda e: cambiar_dia(1)),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
        ], spacing=4),
        bgcolor=SURFACE,
        border_radius=10,
        padding=ft.padding.symmetric(horizontal=14, vertical=10),
    )

    # ── Guardar ───────────────────────────────────────────────────────────
    def guardar(e):
        cliente_nombre = campo_cliente.value.strip()
        descripcion = campo_descripcion.value.strip()
        monto_str = campo_monto.value.strip().replace(",", ".").replace("$", "")

        # Validaciones
        if not cliente_nombre:
            error_msg.value = "El nombre del cliente es obligatorio"
            error_msg.visible = True
            page.update()
            return
        if not descripcion:
            error_msg.value = "La descripción es obligatoria"
            error_msg.visible = True
            page.update()
            return
        try:
            monto = float(monto_str) if monto_str else 0.0
            if monto < 0:
                raise ValueError
        except ValueError:
            error_msg.value = "El monto debe ser un número válido"
            error_msg.visible = True
            page.update()
            return

        error_msg.visible = False

        # Guardar
        cliente = ClienteController.buscar_o_crear(cliente_nombre)
        TrabajoController.crear(
            cliente_id=cliente.id,
            descripcion=descripcion,
            monto=monto,
            fecha=fecha_sel[0],
        )

        # Snackbar de éxito
        page.snack_bar = ft.SnackBar(
            content=ft.Row([
                ft.Icon(ft.Icons.CHECK_CIRCLE, color=OK),
                ft.Text("  Trabajo guardado", color=TEXTO),
            ]),
            bgcolor=SURFACE2,
            duration=2000,
        )
        page.snack_bar.open = True
        refrescar_inicio()
        ir_a("inicio", {})

    btn_guardar = ft.ElevatedButton(
        text="Guardar trabajo",
        icon=ft.Icons.SAVE_OUTLINED,
        bgcolor=ACENTO,
        color=BG,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=ft.padding.symmetric(vertical=16),
        ),
        expand=True,
        on_click=guardar,
    )

    return ft.Column(
        [
            # AppBar
            ft.Container(
                content=ft.Row(
                    [
                        ft.IconButton(ft.Icons.ARROW_BACK, icon_color=TEXTO,
                                      on_click=lambda e: ir_a("inicio", {})),
                        ft.Text("Nuevo trabajo", size=18, weight=ft.FontWeight.BOLD,
                                color=TEXTO),
                    ],
                    spacing=4,
                ),
                bgcolor=SURFACE,
                padding=ft.padding.symmetric(horizontal=8, vertical=12),
            ),

            # Formulario
            ft.ListView(
                [
                    ft.Container(height=8),
                    campo_cliente,
                    sugerencias_visibles,
                    campo_descripcion,
                    campo_monto,
                    selector_fecha,
                    error_msg,
                    ft.Container(height=8),
                    ft.Row([btn_guardar]),
                    ft.Container(height=20),
                ],
                spacing=12,
                padding=ft.padding.symmetric(horizontal=16),
                expand=True,
            ),
        ],
        spacing=0,
        expand=True,
    )
