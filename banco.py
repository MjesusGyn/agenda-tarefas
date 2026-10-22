"""Camada de dados da Agenda de Tarefas (SQLite)."""
import sqlite3
from dataclasses import dataclass
from datetime import date

FILTROS = ('todas', 'pendentes', 'concluidas')


@dataclass
class Tarefa:
    id: int
    nome: str
    concluida: bool
    prazo: date | None

    @property
    def atrasada(self):
        return not self.concluida and self.prazo is not None and self.prazo < date.today()


class BancoTarefas:
    def __init__(self, caminho='tarefas.db'):
        self.caminho = caminho
        self._executar('''
            CREATE TABLE IF NOT EXISTS tarefas (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                nome      TEXT    NOT NULL,
                concluida INTEGER NOT NULL DEFAULT 0,
                prazo     TEXT
            )
        ''')

    def _executar(self, sql, parametros=()):
        with sqlite3.connect(self.caminho) as conexao:
            cursor = conexao.execute(sql, parametros)
            return cursor.fetchall(), cursor.lastrowid, cursor.rowcount

    def adicionar(self, nome, prazo=None):
        nome = nome.strip()
        if not nome:
            raise ValueError('O nome da tarefa não pode ser vazio.')
        _, novo_id, _ = self._executar(
            'INSERT INTO tarefas (nome, prazo) VALUES (?, ?)',
            (nome, prazo.isoformat() if prazo else None),
        )
        return novo_id

    def listar(self, filtro='todas'):
        if filtro not in FILTROS:
            raise ValueError(f'Filtro inválido: {filtro}')
        condicao = {'todas': '', 'pendentes': 'WHERE concluida = 0', 'concluidas': 'WHERE concluida = 1'}[filtro]
        # pendentes primeiro; dentro delas, as com prazo mais próximo
        linhas, _, _ = self._executar(f'''
            SELECT id, nome, concluida, prazo FROM tarefas {condicao}
            ORDER BY concluida, prazo IS NULL, prazo, id
        ''')
        return [
            Tarefa(id_, nome, bool(concluida), date.fromisoformat(prazo) if prazo else None)
            for id_, nome, concluida, prazo in linhas
        ]

    def marcar(self, id_tarefa, concluida):
        self._executar('UPDATE tarefas SET concluida = ? WHERE id = ?', (int(concluida), id_tarefa))

    def remover(self, id_tarefa):
        self._executar('DELETE FROM tarefas WHERE id = ?', (id_tarefa,))

    def limpar_concluidas(self):
        _, _, removidas = self._executar('DELETE FROM tarefas WHERE concluida = 1')
        return removidas

    def contar(self):
        """Retorna (concluídas, total)."""
        linhas, _, _ = self._executar('SELECT COALESCE(SUM(concluida), 0), COUNT(*) FROM tarefas')
        return linhas[0]
