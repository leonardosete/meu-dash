import pandas as pd
import numpy as np
from src.analisar_alertas import analisar_grupos
from src.constants import (
    TASK_STATUS_WEIGHTS,
    ACAO_FALHA_PERSISTENTE,
    ACAO_SUCESSO_PARCIAL,
    ACAO_SEMPRE_OK,
)


def test_fator_ineficiencia_task_calculation():
    """
    Valida se o 'fator_ineficiencia_task' é calculado corretamente com base no
    pior status da cronologia e se ele impacta o score final.
    """
    # Dados de exemplo com diferentes status de task
    data = {
        "assignment_group": ["SQUAD_A", "SQUAD_A", "SQUAD_B", "SQUAD_C"],
        "short_description": ["Problema 1", "Problema 1", "Problema 2", "Problema 3"],
        "node": ["server1", "server1", "server2", "server3"],
        "cmdb_ci": ["ci1", "ci1", "ci2", "ci3"],
        "source": ["source1", "source1", "source2", "source3"],
        "metric_name": ["metric1", "metric1", "metric2", "metric3"],
        "cmdb_ci.sys_class_name": ["c1", "c1", "c2", "c3"],
        "sys_created_on": pd.to_datetime(
            ["2023-01-01 10:00", "2023-01-01 11:00", "2023-01-02", "2023-01-03"],
            # CORREÇÃO: Adiciona format='mixed' para lidar com formatos de data inconsistentes no teste.
            # Isso espelha a robustez da nossa função de carregamento principal.
            format="mixed",
        ),
        "number": ["1", "2", "3", "4"],
        "has_remediation_task": ["REM_OK", "REM_OK", "REM_NOT_OK", "NO_STATUS"],
        "severity": ["Alto", "Alto", "Médio", "Crítico"],
        "sn_priority_group": ["Alto(a)", "Alto(a)", "Moderado(a)", "Urgente"],
        # Cenários de tasks_status
        # Problema 1: Falhou e depois sucesso. Deve pegar o peso da falha.
        # Problema 2: Sucesso parcial.
        # Problema 3: Sucesso limpo.
        "tasks_status": ["Closed", "Closed Incomplete", "Canceled", "Closed"],
        "severity_score": [8, 8, 5, 10],
        "priority_group_score": [8, 8, 5, 10],
        "score_criticidade_final": [16, 16, 10, 20],
    }
    df = pd.DataFrame(data)

    summary = analisar_grupos(df)

    # Extrai os resultados para validação
    problema1 = summary[summary["short_description"] == "Problema 1"].iloc[0]
    problema2 = summary[summary["short_description"] == "Problema 2"].iloc[0]
    problema3 = summary[summary["short_description"] == "Problema 3"].iloc[0]

    # Valida o fator de ineficiência (deve pegar o pior da cronologia)
    assert problema1["fator_ineficiencia_task"] == TASK_STATUS_WEIGHTS.get(
        "Closed Incomplete"
    )
    assert problema2["fator_ineficiencia_task"] == TASK_STATUS_WEIGHTS.get(
        "default"
    )  # Canceled não tem peso, usa default
    assert problema3["fator_ineficiencia_task"] == TASK_STATUS_WEIGHTS.get("default")

    # Valida o score final, garantindo que o fator foi aplicado
    # Problema 1: score_base * peso_acao * fator_volume * fator_ineficiencia
    # score_base = 16, peso_acao = 1.2 (Intermitente), fator_volume = 1 + log(2)
    # fator_ineficiencia = 1.5
    score_esperado_p1 = 16 * 1.2 * (1 + np.log(2)) * 1.5
    assert round(problema1["score_ponderado_final"], 1) == round(score_esperado_p1, 1)

    # Problema 2: score_base * peso_acao * fator_volume * fator_ineficiencia
    # score_base = 10, peso_acao = 1.1 (Sucesso Parcial), fator_volume = 1 + log(1) = 1
    # fator_ineficiencia = 1.0
    score_esperado_p2 = 10 * 1.1 * 1.0 * 1.0
    assert round(problema2["score_ponderado_final"], 1) == round(score_esperado_p2, 1)

    # Problema 3: score_base * peso_acao * fator_volume * fator_ineficiencia
    # score_base = 20, peso_acao = 1.0 (Sempre OK), fator_volume = 1 + log(1) = 1
    # fator_ineficiencia = 1.0
    score_esperado_p3 = 20 * 1.0 * 1.0 * 1.0
    assert round(problema3["score_ponderado_final"], 1) == round(score_esperado_p3, 1)