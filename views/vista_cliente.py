import flet as ft
from electriapp.controllers.trabajo_controller import TrabajoController

BG       = "#0f172a"
SURFACE  = "#1e293b"
SURFACE2 = "#334155"
ACENTO   = "#f59e0b"
TEXTO    = "#f1f5f9"
SUBTEXTO = "#94a3b8"
OK       = "#22c55e"
ERROR    = "#ef4444"


def vista_cliente(page: ft.Page, ir_a, params: dict):
    cliente_id = params["cliente_id"]
    nombre = params["nombre"]

    trabajos = TrabajoController.obtener_por_cliente(cliente_id)
    total = sum(t.monto for t in trabajos)

    # ── Resumen header ────────────────────────────────────────────────────
    resumen = ft.Container(
        content=ft.Column(
            [
                ft.Row([
                    ft.Icon(ft.Icons.PERSON, color=ACENTO, size=28),
                    ft.Text(nombre, size=20, weight=ft.FontWeight.BOLD, color=TEXTO),
                ], spacing=10),
                ft.Divider(color=SURFACE2),
                ft.Row(
                    [
                        ft.Column([
                            ft.Text("Total acumulado", size=12, color=SUBTEXTO),
                            ft.Text(f"${total:,.0f}", size=24,
                                    weight=ft.FontWeight.BOLD, color=OK),
                        ]),
                        ft.Column([
                            ft.Text("Trabajos", size=12, color=SUBTEXTO),
                            ft.Text(str(len(trabajos)), size=24,
                                    weight=ft.FontWeight.BOLD, color=ACENTO),
                        ]),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_AROUND,
                ),
            ],
            spacing=12,
        ),
        bgcolor=SURFACE,
        border_radius=14,
        padding=16,
        margin=ft.margin.symmetric(horizontal=16, vertical=8),
    )

    # ── Lista de trabajos ─────────────────────────────────────────────────
    def card_trabajo(t):
        return ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(t.fecha.strftime("%d/%m/%Y"), size=12, color=ACENTO),
                            ft.Text(t.descripcion, size=14, color=TEXTO,
                                    overflow=ft.TextOverflow.ELLIPSIS, max_lines=2),
                        ],
                        spacing=4,
                        expand=True,
                    ),
                    ft.Text(f"${t.monto:,.0f}", size=15,
                            weight=ft.FontWeight.BOLD, color=OK),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            bgcolor=SURFACE,
            border_radius=10,
            padding=ft.padding.symmetric(horizontal=14, vertical=12),
            margin=ft.margin.symmetric(horizontal=16, vertical=3),
        )

    lista = ft.ListView(
        [card_trabajo(t) for t in trabajos],
        spacing=0,
        expand=True,
    )

    if not trabajos:
        lista = ft.Column(
            [ft.Text("Sin trabajos registrados", color=SUBTEXTO, size=14)],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
        )

    return ft.Column(
        [
            ft.Container(
                content=ft.Row(
                    [
                        ft.IconButton(ft.Icons.ARROW_BACK, icon_color=TEXTO,
                                      on_click=lambda e: ir_a("inicio", {})),
                        ft.Text("Detalle del cliente", size=18,
                                weight=ft.FontWeight.BOLD, color=TEXTO),
                    ],
                    spacing=4,
                ),
                bgcolor=SURFACE,
                padding=ft.padding.symmetric(horizontal=8, vertical=12),
            ),
            resumen,
            ft.Container(
                content=ft.Text("Historial de trabajos", size=14,
                                color=SUBTEXTO, weight=ft.FontWeight.BOLD),
                padding=ft.padding.only(left=16, top=8, bottom=4),
            ),
            lista,
        ],
        spacing=0,
        expand=True,
    )
