import flet as ft
from datetime import datetime
from electriapp.controllers.trabajo_controller import TrabajoController
from electriapp.controllers.cliente_controller import ClienteController

MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
         "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

# Paleta de colores
BG       = "#0f172a"
SURFACE  = "#1e293b"
SURFACE2 = "#334155"
ACENTO   = "#f59e0b"
TEXTO    = "#f1f5f9"
SUBTEXTO = "#94a3b8"
OK       = "#22c55e"
ERROR    = "#ef4444"


def vista_inicio(page: ft.Page, ir_a):
    ahora = datetime.now()
    mes_actual = [ahora.month]
    anio_actual = [ahora.year]

    # ── Header ────────────────────────────────────────────────────────────
    def cambiar_mes(delta):
        m = mes_actual[0] + delta
        a = anio_actual[0]
        if m > 12:
            m, a = 1, a + 1
        elif m < 1:
            m, a = 12, a - 1
        mes_actual[0] = m
        anio_actual[0] = a
        refrescar()

    lbl_mes = ft.Text("", size=20, weight=ft.FontWeight.BOLD, color=TEXTO)
    lbl_total = ft.Text("", size=14, color=SUBTEXTO)

    header = ft.Row(
        [
            ft.IconButton(ft.Icons.CHEVRON_LEFT, icon_color=ACENTO,
                          on_click=lambda e: cambiar_mes(-1)),
            ft.Column([lbl_mes, lbl_total], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                      spacing=2, expand=True),
            ft.IconButton(ft.Icons.CHEVRON_RIGHT, icon_color=ACENTO,
                          on_click=lambda e: cambiar_mes(1)),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    # ── Lista de trabajos ─────────────────────────────────────────────────
    lista = ft.ListView(spacing=8, padding=ft.padding.symmetric(horizontal=16), expand=True)

    def card_trabajo(t: dict):
        def on_eliminar(e, tid=t["id"]):
            def confirmar(e):
                TrabajoController.eliminar(tid)
                dlg.open = False
                page.update()
                refrescar()

            def cancelar(e):
                dlg.open = False
                page.update()

            dlg = ft.AlertDialog(
                title=ft.Text("¿Eliminar trabajo?"),
                content=ft.Text("Esta acción no se puede deshacer."),
                actions=[
                    ft.TextButton("Cancelar", on_click=cancelar),
                    ft.TextButton("Eliminar", on_click=confirmar,
                                  style=ft.ButtonStyle(color=ERROR)),
                ],
            )
            page.overlay.append(dlg)
            dlg.open = True
            page.update()

        fecha_str = t["fecha"].strftime("%d/%m")

        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        content=ft.Text(fecha_str, size=13, color=ACENTO,
                                        weight=ft.FontWeight.BOLD),
                        width=42,
                    ),
                    ft.Column(
                        [
                            ft.Text(t["cliente"], size=14, weight=ft.FontWeight.BOLD,
                                    color=TEXTO, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Text(t["descripcion"], size=12, color=SUBTEXTO,
                                    overflow=ft.TextOverflow.ELLIPSIS, max_lines=2),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.Column(
                        [
                            ft.Text(f"${t['monto']:,.0f}", size=15,
                                    weight=ft.FontWeight.BOLD, color=OK),
                            ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=ERROR,
                                          icon_size=18, on_click=on_eliminar,
                                          tooltip="Eliminar"),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.END,
                        spacing=0,
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.START,
                spacing=12,
            ),
            bgcolor=SURFACE,
            border_radius=12,
            padding=ft.padding.symmetric(horizontal=14, vertical=12),
            on_click=lambda e, cid=t["cliente_id"], cnombre=t["cliente"]:
                ir_a("cliente", {"cliente_id": cid, "nombre": cnombre}),
            ink=True,
        )

    # ── Resumen por cliente ───────────────────────────────────────────────
    resumen_col = ft.Column(spacing=6, visible=False)

    def card_cliente_resumen(r: dict):
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.PERSON_OUTLINE, color=ACENTO, size=20),
                    ft.Column(
                        [
                            ft.Text(r["cliente"], size=14, weight=ft.FontWeight.BOLD,
                                    color=TEXTO),
                            ft.Text(f"{r['trabajos']} trabajo{'s' if r['trabajos'] != 1 else ''}",
                                    size=12, color=SUBTEXTO),
                        ],
                        spacing=2, expand=True,
                    ),
                    ft.Text(f"${r['total']:,.0f}", size=15, weight=ft.FontWeight.BOLD,
                            color=OK),
                ],
                spacing=12,
            ),
            bgcolor=SURFACE,
            border_radius=12,
            padding=ft.padding.symmetric(horizontal=14, vertical=12),
            on_click=lambda e, cid=r["cliente_id"], cnombre=r["cliente"]:
                ir_a("cliente", {"cliente_id": cid, "nombre": cnombre}),
            ink=True,
        )

    # ── Toggle vista ──────────────────────────────────────────────────────
    vista_actual = ["lista"]  # "lista" o "resumen"

    def toggle_vista(e):
        if vista_actual[0] == "lista":
            vista_actual[0] = "resumen"
            lista.visible = False
            resumen_col.visible = True
            btn_toggle.icon = ft.Icons.LIST
            btn_toggle.tooltip = "Ver lista"
        else:
            vista_actual[0] = "lista"
            lista.visible = True
            resumen_col.visible = False
            btn_toggle.icon = ft.Icons.BAR_CHART
            btn_toggle.tooltip = "Ver resumen por cliente"
        page.update()

    btn_toggle = ft.IconButton(ft.Icons.BAR_CHART, icon_color=ACENTO,
                               tooltip="Ver resumen por cliente",
                               on_click=toggle_vista)

    # ── Estado vacío ──────────────────────────────────────────────────────
    empty_state = ft.Column(
        [
            ft.Icon(ft.Icons.ELECTRICAL_SERVICES, size=64, color=SURFACE2),
            ft.Text("Sin trabajos este mes", size=16, color=SUBTEXTO),
            ft.Text("Tocá + para agregar el primero", size=13, color=SURFACE2),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
        visible=False,
        expand=True,
    )

    def refrescar():
        m, a = mes_actual[0], anio_actual[0]
        lbl_mes.value = f"{MESES[m - 1]} {a}"
        trabajos = TrabajoController.obtener_por_mes(a, m)
        total = sum(t["monto"] for t in trabajos)
        lbl_total.value = f"Total: ${total:,.0f}  •  {len(trabajos)} trabajos"

        lista.controls.clear()
        for t in trabajos:
            lista.controls.append(card_trabajo(t))

        resumen = TrabajoController.resumen_por_cliente_mes(a, m)
        resumen_col.controls.clear()
        for r in resumen:
            resumen_col.controls.append(card_cliente_resumen(r))

        sin_trabajos = len(trabajos) == 0
        lista.visible = not sin_trabajos and vista_actual[0] == "lista"
        resumen_col.visible = not sin_trabajos and vista_actual[0] == "resumen"
        empty_state.visible = sin_trabajos

        page.update()

    refrescar()

    return ft.Column(
        [
            # AppBar manual
            ft.Container(
                content=ft.Row(
                    [
                        ft.Row([
                            ft.Icon(ft.Icons.BOLT, color=ACENTO, size=26),
                            ft.Text("ElectriApp", size=20, weight=ft.FontWeight.BOLD,
                                    color=ACENTO),
                        ], spacing=6),
                        btn_toggle,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                bgcolor=SURFACE,
                padding=ft.padding.symmetric(horizontal=16, vertical=12),
            ),

            ft.Container(content=header,
                         padding=ft.padding.symmetric(horizontal=16, vertical=12)),

            ft.Divider(height=1, color=SURFACE2),

            ft.Stack([lista, resumen_col, empty_state], expand=True),

            # FAB zona
            ft.Container(
                content=ft.FloatingActionButton(
                    icon=ft.Icons.ADD,
                    bgcolor=ACENTO,
                    foreground_color=BG,
                    on_click=lambda e: ir_a("nuevo", {"refrescar": refrescar}),
                ),
                alignment=ft.alignment.bottom_right,
                padding=ft.padding.only(right=20, bottom=20),
            ),
        ],
        spacing=0,
        expand=True,
    )
