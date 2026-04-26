import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from electriapp.database.connection import init_db
from electriapp._seed import sembrar
from electriapp.views.vista_inicio import vista_inicio
from electriapp.views.vista_nuevo_trabajo import vista_nuevo_trabajo
from electriapp.views.vista_cliente import vista_cliente
import flet as ft

BG = "#0f172a"

def main(page: ft.Page):
    page.title = "ElectriApp"
    page.bgcolor = BG
    page.padding = 0
    page.theme_mode = ft.ThemeMode.DARK

    contenedor = ft.Column(expand=True, spacing=0)
    page.add(contenedor)

    def ir_a(ruta: str, params: dict):
        contenedor.controls.clear()
        if ruta == "inicio":
            vista = vista_inicio(page, ir_a)
        elif ruta == "nuevo":
            vista = vista_nuevo_trabajo(page, ir_a, params)
        elif ruta == "cliente":
            vista = vista_cliente(page, ir_a, params)
        else:
            vista = vista_inicio(page, ir_a)
        contenedor.controls.append(vista)
        page.update()

    ir_a("inicio", {})

if __name__ == "__main__":
    init_db()
    sembrar()
    port = int(os.environ.get("PORT", 8080))
    ft.app(
        target=main,
        view=ft.AppView.WEB_BROWSER,
        port=port,
        host="0.0.0.0",
    )
