"""Agenda de Tarefas — interface feita com Flet."""
import os
from datetime import date

import flet as ft

from banco import BancoTarefas

PASTA = os.path.dirname(os.path.abspath(__file__))
FILTROS = ['todas', 'pendentes', 'concluidas']


class AgendaTarefas:
    def __init__(self, page: ft.Page):
        self.page = page
        self.banco = BancoTarefas(os.path.join(PASTA, 'tarefas.db'))
        self.filtro = 'todas'
        self.prazo = None

        page.title = 'Agenda de Tarefas'
        page.theme_mode = ft.ThemeMode.LIGHT
        page.bgcolor = ft.Colors.WHITE
        page.window.width = 420
        page.window.height = 620
        page.window.resizable = False
        page.padding = 20
        # calendário e textos do sistema em português
        page.locale_configuration = ft.LocaleConfiguration(
            supported_locales=[ft.Locale('pt', 'BR')],
            current_locale=ft.Locale('pt', 'BR'),
        )

        self.campo_tarefa = ft.TextField(
            hint_text='Digite uma tarefa e aperte Enter',
            expand=True,
            on_submit=self.adicionar,
        )
        self.texto_prazo = ft.Text(size=12, color=ft.Colors.BLUE_GREY_700)
        self.botao_limpar_prazo = ft.IconButton(
            icon=ft.Icons.CLOSE, icon_size=16, tooltip='Remover prazo',
            visible=False, on_click=self.limpar_prazo,
        )
        self.contador = ft.Text(size=13, color=ft.Colors.BLUE_GREY_600)
        self.lista = ft.ListView(expand=True, spacing=2)

        page.add(
            ft.Text('📋 Agenda de Tarefas', size=24, weight=ft.FontWeight.BOLD),
            self.contador,
            ft.Row([
                self.campo_tarefa,
                ft.IconButton(icon=ft.Icons.CALENDAR_MONTH, tooltip='Definir prazo', on_click=self.abrir_calendario),
                ft.FloatingActionButton(icon=ft.Icons.ADD, mini=True, on_click=self.adicionar),
            ]),
            ft.Row([self.texto_prazo, self.botao_limpar_prazo], spacing=0),
            ft.Tabs(
                length=3,
                selected_index=0,
                on_change=self.trocar_filtro,
                content=ft.TabBar(tabs=[
                    ft.Tab(label='Todas'),
                    ft.Tab(label='Pendentes'),
                    ft.Tab(label='Concluídas'),
                ]),
            ),
            self.lista,
            ft.Row(
                [ft.TextButton('Limpar concluídas', icon=ft.Icons.CLEANING_SERVICES, on_click=self.limpar_concluidas)],
                alignment=ft.MainAxisAlignment.END,
            ),
        )
        self.atualizar_lista()

    # ---------- ações ----------
    def adicionar(self, e):
        nome = self.campo_tarefa.value.strip()
        if not nome:
            return
        self.banco.adicionar(nome, self.prazo)
        self.campo_tarefa.value = ''
        self.limpar_prazo(None)
        self.atualizar_lista()

    def marcar(self, id_tarefa, concluida):
        self.banco.marcar(id_tarefa, concluida)
        self.atualizar_lista()

    def remover(self, id_tarefa):
        self.banco.remover(id_tarefa)
        self.atualizar_lista()

    def limpar_concluidas(self, e):
        self.banco.limpar_concluidas()
        self.atualizar_lista()

    def trocar_filtro(self, e):
        self.filtro = FILTROS[e.control.selected_index]
        self.atualizar_lista()

    # ---------- prazo ----------
    def abrir_calendario(self, e):
        self.page.show_dialog(ft.DatePicker(
            first_date=date.today(),
            value=self.prazo or date.today(),
            on_change=self.escolher_prazo,
        ))

    def escolher_prazo(self, e):
        self.prazo = e.control.value.date() if hasattr(e.control.value, 'date') else e.control.value
        self.texto_prazo.value = f'Prazo: {self.prazo:%d/%m/%Y}'
        self.botao_limpar_prazo.visible = True
        self.page.update()

    def limpar_prazo(self, e):
        self.prazo = None
        self.texto_prazo.value = ''
        self.botao_limpar_prazo.visible = False
        self.page.update()

    # ---------- tela ----------
    def linha_tarefa(self, tarefa):
        if tarefa.prazo is None:
            info_prazo = ft.Container()
        else:
            info_prazo = ft.Text(
                ('⚠ ' if tarefa.atrasada else '') + f'{tarefa.prazo:%d/%m}',
                size=12,
                color=ft.Colors.RED_600 if tarefa.atrasada else ft.Colors.BLUE_GREY_500,
            )
        return ft.Row(
            [
                ft.Checkbox(
                    label=tarefa.nome,
                    value=tarefa.concluida,
                    expand=True,
                    on_change=lambda e, id_=tarefa.id: self.marcar(id_, e.control.value),
                ),
                info_prazo,
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    icon_color=ft.Colors.RED_400,
                    tooltip='Excluir',
                    on_click=lambda e, id_=tarefa.id: self.remover(id_),
                ),
            ],
        )

    def atualizar_lista(self):
        tarefas = self.banco.listar(self.filtro)
        self.lista.controls = [self.linha_tarefa(t) for t in tarefas]
        if not tarefas:
            self.lista.controls = [ft.Text('Nenhuma tarefa por aqui 🎉', color=ft.Colors.BLUE_GREY_400)]

        concluidas, total = self.banco.contar()
        self.contador.value = f'{concluidas} de {total} concluídas' if total else 'Comece adicionando uma tarefa'
        self.page.update()


if __name__ == '__main__':
    ft.run(AgendaTarefas, assets_dir='assets')
