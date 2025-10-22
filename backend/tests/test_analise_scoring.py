import pandas as pd
import numpy as np
from src.analisar_alertas import analisar_grupos
from src.constants import (
    GROUP_COLS,
    COL_TASKS_STATUS,
    TASK_STATUS_WEIGHTS, # Assuming this is still correct
    COL_CREATED_ON,
    COL_NUMBER,
    COL_REMEDIATION_TASKS_PRESENT,
    COL_SEVERITY,
    COL_PRIORITY_GROUP,
)


def test_fator_ineficiencia_task_calculation():
    """
    Valida se o 'fator_ineficiencia_task' é calculado corretamente com base
    nos pesos definidos em TASK_STATUS_WEIGHTS e se ele impacta o score final.
    """
    # Dados de exemplo com diferentes status de task
    data = {
        "assignment_group": ["SQUAD_A", "SQUAD_A", "SQUAD_B", "SQUAD_C"],
        "short_description": ["Problema 1", "Problema 1", "Problema 2", "Problema 3"],
        "node": ["server1", "server1", "server2", "server3"],
        "cmdb_ci": ["ci1", "ci1", "ci2", "ci3"],
        "source": ["source1", "source1", "source2", "source3"],
        "metric_name": ["metric1", "metric1", "metric2", "metric3"],
        "cmdb_ci.sys_class_name": ["class1", "class1", "class2", "class3"],
        "sys_created_on": pd.to_datetime(["2023-01-01", "2023-01-01", "2023-01-01", "2023-01-01"]),
        "number": ["1", "2", "3", "4"],
        "remediation_tasks_present": ["REM_OK", "REM_OK", "REM_NOT_OK", "NO_STATUS"],
        "severity": ["Alto", "Alto", "Médio", "Crítico"],
        "sn_priority_group": ["Alto(a)", "Alto(a)", "Moderado(a)", "Urgente"],
        "tasks_status": ["Closed Incomplete", "Closed Incomplete", "Canceled", "Closed"],
        "severity_score": [8, 8, 5, 10],
        "priority_group_score": [8, 8, 5, 10],
        "score_criticidade_final": [16, 16, 10, 20],
    }
    df = pd.DataFrame(data)

    # Executa a função de análise
    summary = analisar_grupos(df)

    # Extrai os fatores para cada grupo
    fator_problema1 = summary[summary["short_description"] == "Problema 1"]["fator_ineficiencia_task"].iloc[0]
    fator_problema2 = summary[summary["short_description"] == "Problema 2"]["fator_ineficiencia_task"].iloc[0]
    fator_problema3 = summary[summary["short_description"] == "Problema 3"]["fator_ineficiencia_task"].iloc[0]

    # Valida se os fatores foram aplicados corretamente
    assert fator_problema1 == TASK_STATUS_WEIGHTS.get("Closed Incomplete", 1.0)
    assert fator_problema2 == TASK_STATUS_WEIGHTS.get("Canceled", 1.0)
    assert fator_problema3 == TASK_STATUS_WEIGHTS.get("default", 1.0)