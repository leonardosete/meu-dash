import pandas as pd
import numpy as np
import pytest
from src.analisar_alertas import analisar_grupos
from src.constants import (
    TASK_STATUS_WEIGHTS,
    ACAO_WEIGHTS,
    ACAO_SUCESSO_PARCIAL,
    ACAO_SEMPRE_OK,
    ACAO_INTERMITENTE,
    ACAO_FALHA_PERSISTENTE,
    ACAO_STATUS_AUSENTE,
)


# Helper para calcular o score esperado, evitando repetição e cálculos manuais.
def calcular_score_esperado(
    score_base, peso_acao, alert_count, fator_ineficiencia_task
):
    """
    Calcula o score ponderado final esperado com base nos fatores.
    """
    fator_volume = 1 + np.log(alert_count)
    return score_base * peso_acao * fator_volume * fator_ineficiencia_task


@pytest.fixture
def sample_data():
    """Fixture com dados de teste abrangendo múltiplos cenários."""
    return {
        "assignment_group": ["SQUAD_A", "SQUAD_A", "SQUAD_B", "SQUAD_C", "SQUAD_D", "SQUAD_E"],
        "short_description": ["P1", "P1", "P2", "P3", "P4", "P5"],
        "node": ["s1", "s1", "s2", "s3", "s4", "s5"],
        "cmdb_ci": ["ci1", "ci1", "ci2", "ci3", "ci4", "ci5"],
        "source": ["src1", "src1", "src2", "src3", "src4", "src5"],
        "metric_name": ["m1", "m1", "m2", "m3", "m4", "m5"],
        "cmdb_ci.sys_class_name": ["c1", "c1", "c2", "c3", "c4", "c5"],
        "sys_created_on": pd.to_datetime([
            "2023-01-01 10:00", "2023-01-01 11:00",  # P1
            "2023-01-02",  # P2
            "2023-01-03",  # P3
            "2023-01-04",  # P4
            "2023-01-05",  # P5
        ], format="mixed"),
        "number": ["1", "2", "3", "4", "5", "6"],
        # P1 e P2 agora formam um grupo intermitente. P1 falhou, P2 teve sucesso parcial.
        "has_remediation_task": ["REM_NOT_OK", "REM_OK", "REM_OK", "NO_STATUS", "REM_OK", "REM_OK"],
        "severity": ["Alto", "Alto", "Medio", "Crítico", "Baixo", "Medio"],
        "sn_priority_group": ["Alto(a)", "Alto(a)", "Moderado(a)", "Urgente", "Baixo(a)", "Moderado(a)"],
        # Cenários de tasks_status:
        # P1: Grupo com histórico de falha (Closed Incomplete) e sucesso (Closed).
        # P2: Grupo com histórico de falha (Closed Incomplete) e sucesso parcial (Canceled).
        # P3: Sucesso limpo.
        # P4: Status nulo/vazio (deve usar default).
        # P5: Sucesso parcial (Closed Skipped).
        "tasks_status": ["Closed", "Closed Incomplete", "Canceled", "Closed", None, "Closed Skipped"],
        "severity_score": [8, 8, 5, 10, 2, 5],
        "priority_group_score": [8, 8, 5, 10, 2, 5],
        "score_criticidade_final": [16, 16, 10, 20, 4, 10],
    }


@pytest.mark.parametrize(
    "problem_id, expected_factor",
    [
        ("P1", TASK_STATUS_WEIGHTS.get("Closed Incomplete")),  # Pior caso na cronologia
        ("P2", TASK_STATUS_WEIGHTS.get("Canceled")),          # O status do último alerta é Canceled
        ("P3", TASK_STATUS_WEIGHTS.get("default")),           # Sucesso limpo
        ("P4", TASK_STATUS_WEIGHTS.get("default")),           # Status nulo
        ("P5", TASK_STATUS_WEIGHTS.get("Closed Skipped")),    # Sucesso parcial
    ],
)
def test_fator_ineficiencia_task(sample_data, problem_id, expected_factor):
    """Valida se o 'fator_ineficiencia_task' é calculado corretamente para diferentes cenários."""
    df = pd.DataFrame(sample_data)
    summary = analisar_grupos(df)
    result = summary[summary["short_description"] == problem_id].iloc[0]
    assert result["fator_ineficiencia_task"] == expected_factor


@pytest.mark.parametrize(
    "problem_id, expected_acao",
    [
        ("P1", ACAO_INTERMITENTE),       # Falhou e depois sucesso
        # Cenário P2 é um único alerta com status "Canceled" e sem histórico de falha.
        # A ação correta é Sucesso Parcial.
        ("P2", ACAO_SUCESSO_PARCIAL),
        ("P3", ACAO_SEMPRE_OK),          # Sempre sucesso
        ("P4", ACAO_STATUS_AUSENTE),     # Status nulo
        ("P5", ACAO_SUCESSO_PARCIAL),    # Sucesso parcial (skipped)
    ],
)
def test_acao_sugerida(sample_data, problem_id, expected_acao):
    """Valida se a 'acao_sugerida' é definida corretamente."""
    df = pd.DataFrame(sample_data)
    summary = analisar_grupos(df)
    result = summary[summary["short_description"] == problem_id].iloc[0]
    assert result["acao_sugerida"] == expected_acao


@pytest.mark.parametrize(
    "problem_id, score_base, alert_count",
    [
        ("P1", 16, 2),
        ("P2", 10, 1),
        ("P3", 20, 1),
        ("P4", 4, 1),
        ("P5", 10, 1),
    ],
)
def test_score_ponderado_final(sample_data, problem_id, score_base, alert_count):
    """Valida o cálculo completo do 'score_ponderado_final'."""
    df = pd.DataFrame(sample_data)
    summary = analisar_grupos(df)
    result = summary[summary["short_description"] == problem_id].iloc[0]

    # Obtém os fatores calculados pela função
    acao_sugerida = result["acao_sugerida"]
    fator_ineficiencia = result["fator_ineficiencia_task"]
    peso_acao = ACAO_WEIGHTS.get(acao_sugerida, 1.0)

    # Calcula o score esperado usando o helper
    score_esperado = calcular_score_esperado(
        score_base, peso_acao, alert_count, fator_ineficiencia
    )

    # Compara o resultado real com o esperado
    assert round(result["score_ponderado_final"], 2) == round(score_esperado, 2)