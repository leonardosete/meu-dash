import pandas as pd
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.analisar_alertas import analisar_grupos, adicionar_acao_sugerida
from src.constants import (
    COL_TASKS_STATUS,
    PRIORITY_GROUP_WEIGHTS,
    SEVERITY_WEIGHTS,
    STATUS_OK,
    STATUS_NOT_OK,
    NO_STATUS,
    ACAO_ESTABILIZADA,
    ACAO_INTERMITENTE,
    ACAO_FALHA_PERSISTENTE,
    ACAO_SEMPRE_OK,
    ACAO_INSTABILIDADE_CRONICA,
    ACAO_STATUS_AUSENTE,
)


@pytest.fixture
def sample_dataframe():
    """Cria um DataFrame de exemplo para os testes."""
    data = {
        "cmdb_ci": [
            "server1",
            "server1",
            "server2",
            "server2",
            "server3",
            "server4",
            "server4",
            "server5",
        ],
        "metric_name": ["cpu", "cpu", "memory", "memory", "disk", "cpu", "cpu", "network"],
        "assignment_group": [
            "group_a",
            "group_a",
            "group_b",
            "group_b",
            "group_a",
            "group_c",
            "group_c",
            "group_d",
        ],
        "short_description": [
            "high cpu",
            "high cpu",
            "low memory",
            "low memory",
            "disk full",
            "high cpu",
            "high cpu",
            "network issue",
        ],
        "sys_created_on": pd.to_datetime(
            [
                "2023-01-01 10:00",
                "2023-01-01 11:00",
                "2023-01-02 12:00",
                "2023-01-02 13:00",
                "2023-01-03 14:00",
                "2023-01-04 15:00",
                "2023-01-04 16:00",
                "2023-01-05 10:00",
            ]
        ),
        "number": ["INC1", "INC2", "INC3", "INC4", "INC5", "INC6", "INC7", "INC8"],
        "remediation_tasks_present": [
            STATUS_OK,
            STATUS_NOT_OK,
            STATUS_OK,
            STATUS_OK,
            NO_STATUS,
            STATUS_NOT_OK,
            STATUS_NOT_OK,
            STATUS_NOT_OK,
        ],
        "severity": ["Alto", "Alto", "Médio", "Médio", "Crítico", "Alto", "Alto", "Crítico"],
        "sn_priority_group": ["Alto(a)", "Alto(a)", "Moderado(a)", "Moderado(a)", "Alto(a)", "Baixo(a)", "Baixo(a)", "Alto(a)"],
        "node": ["node1", "node1", "node2", "node2", "node3", "node4", "node4", "node5"],
        "source": [
            "source1",
            "source1",
            "source2",
            "source2",
            "source3",
            "source4",
            "source4",
            "source5",
        ],
        "cmdb_ci.sys_class_name": [
            "class1",
            "class1",
            "class2",
            "class2",
            "class3",
            "class4",
            "class4",
            "class5",
        ],
        # Adiciona a coluna 'tasks_status' com valores de exemplo para o teste
        COL_TASKS_STATUS: [
            "Closed",
            "Closed",
            "Closed Incomplete",
            "Closed Incomplete",
            "Canceled",
            "Open",
            "Open",
            "Closed Skipped",
        ],
    }
    df = pd.DataFrame(data)
    df["severity_score"] = df["severity"].map(SEVERITY_WEIGHTS).fillna(0)
    df["priority_group_score"] = (
        df["sn_priority_group"].map(PRIORITY_GROUP_WEIGHTS).fillna(0)
    )
    df["score_criticidade_final"] = df["severity_score"] + df["priority_group_score"]
    return df


def test_analisar_grupos(sample_dataframe):
    """Testa se a função analisar_grupos agrupa corretamente os alertas."""
    summary = analisar_grupos(sample_dataframe)
    assert len(summary) == 5  # Espera 5 grupos únicos após a adição de mais dados de teste
    assert "status_chronology" in summary.columns

    # Testa a cronologia de um grupo específico
    server1_group = summary[summary["cmdb_ci"] == "server1"]
    # A cronologia agora é baseada em 'tasks_status'
    assert server1_group["status_chronology"].iloc[0] == ["Closed", "Closed"]


def test_adicionar_acao_sugerida():
    """Testa a lógica da função adicionar_acao_sugerida."""
    data = {
        "status_chronology": [
            ["Closed Incomplete", "Closed Complete"],  # Estabilizada (Falhou, depois sucesso)
            ["Closed Complete", "Closed Incomplete"],  # Intermitente (último é falha)
            ["Closed Incomplete", "Closed Incomplete"],  # Falha Persistente
            ["Closed Complete", "Closed Complete"],  # Sempre OK
            [NO_STATUS, NO_STATUS],  # Status Ausente
            [],  # Vazio, deve ser status ausente
            ["Closed Complete", "Closed Complete", "Closed Complete", "Closed Complete", "Closed Complete", "Closed Complete"], # Instabilidade Crônica
            ["No Task Found"], # Falha Persistente (No Task Found)
        ],
        "alert_count": [2, 2, 2, 2, 2, 0, 6, 1],
        # Adiciona a coluna 'tasks_status' que agora é necessária pela função
        COL_TASKS_STATUS: ["Closed Complete", "Closed Incomplete", "Closed Incomplete", "Closed Complete", NO_STATUS, NO_STATUS, "Closed Complete", "No Task Found"]
    }
    df = pd.DataFrame(data)
    df = adicionar_acao_sugerida(df)

    assert df["acao_sugerida"].tolist() == [
        ACAO_ESTABILIZADA,
        ACAO_INTERMITENTE,
        ACAO_FALHA_PERSISTENTE,
        ACAO_SEMPRE_OK,
        ACAO_STATUS_AUSENTE,
        ACAO_STATUS_AUSENTE,
        ACAO_INSTABILIDADE_CRONICA,
        ACAO_FALHA_PERSISTENTE,
    ]
