import flet as ft
import os
from electriapp.database.connection import init_db
from electriapp.views.vista_inicio import vista_inicio
from electriapp.views.vista_nuevo_trabajo import vista_nuevo_trabajo
from electriapp.views.vista_cliente import vista_cliente

BG = "#0f172a"


def main(page: ft.Page):
    page.title = "ElectriApp"
    page.bgcolor = BG
    page.padding = 0
    page.theme_mode = ft.ThemeMode.DARK
    page.fonts = {}

    # Tamaño mobile
    page.window.width = 390
    page.window.height = 844

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

    # Ruta inicial
    ir_a("inicio", {})


def run():
    init_db()
    port = int(os.environ.get("PORT", 8080))
    ft.app(
        target=main,
        view=ft.AppView.WEB_BROWSER,
        port=port,
        host="0.0.0.0",
    )


if __name__ == "__main__":
    run()
