from datetime import date, timedelta

import pytest

from banco import BancoTarefas


@pytest.fixture
def banco(tmp_path):
    return BancoTarefas(tmp_path / 'teste.db')


def test_adicionar_e_listar(banco):
    banco.adicionar('Estudar Python')
    tarefas = banco.listar()
    assert len(tarefas) == 1
    assert tarefas[0].nome == 'Estudar Python'
    assert tarefas[0].concluida is False


def test_nome_vazio_nao_e_aceito(banco):
    with pytest.raises(ValueError):
        banco.adicionar('   ')


def test_tarefas_com_mesmo_nome_sao_independentes(banco):
    primeira = banco.adicionar('Comprar pão')
    banco.adicionar('Comprar pão')
    banco.marcar(primeira, True)
    assert [t.concluida for t in banco.listar()] == [False, True]


def test_filtros(banco):
    a = banco.adicionar('A')
    banco.adicionar('B')
    banco.marcar(a, True)
    assert [t.nome for t in banco.listar('pendentes')] == ['B']
    assert [t.nome for t in banco.listar('concluidas')] == ['A']
    with pytest.raises(ValueError):
        banco.listar('qualquer')


def test_ordem_por_prazo(banco):
    hoje = date.today()
    banco.adicionar('Sem prazo')
    banco.adicionar('Depois', hoje + timedelta(days=5))
    banco.adicionar('Antes', hoje + timedelta(days=1))
    assert [t.nome for t in banco.listar()] == ['Antes', 'Depois', 'Sem prazo']


def test_atrasada(banco):
    ontem = date.today() - timedelta(days=1)
    id_ = banco.adicionar('Pagar conta', ontem)
    assert banco.listar()[0].atrasada
    banco.marcar(id_, True)
    assert not banco.listar()[0].atrasada


def test_remover_e_limpar_concluidas(banco):
    a = banco.adicionar('A')
    b = banco.adicionar('B')
    banco.adicionar('C')
    banco.remover(a)
    banco.marcar(b, True)
    assert banco.limpar_concluidas() == 1
    assert [t.nome for t in banco.listar()] == ['C']


def test_contar(banco):
    assert banco.contar() == (0, 0)
    a = banco.adicionar('A')
    banco.adicionar('B')
    banco.marcar(a, True)
    assert banco.contar() == (1, 2)


def test_dados_persistem_entre_sessoes(tmp_path):
    caminho = tmp_path / 'persistente.db'
    BancoTarefas(caminho).adicionar('Continuar amanhã')
    assert BancoTarefas(caminho).listar()[0].nome == 'Continuar amanhã'
