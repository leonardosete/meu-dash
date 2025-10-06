import pandas as pd
import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.analisar_alertas import analisar_grupos, adicionar_acao_sugerida
from src.constants import STATUS_OK, STATUS_NOT_OK, NO_STATUS, ACAO_ESTABILIZADA, ACAO_INTERMITENTE, ACAO_FALHA_PERSISTENTE, ACAO_SEMPRE_OK, ACAO_STATUS_AUSENTE

@pytest.fixture
def sample_dataframe():
    """Cria um DataFrame de exemplo para os testes."""
    data = {
        'cmdb_ci': ['server1', 'server1', 'server2', 'server2', 'server3', 'server4', 'server4'],
        'metric_name': ['cpu', 'cpu', 'memory', 'memory', 'disk', 'cpu', 'cpu'],
        'assignment_group': ['group_a', 'group_a', 'group_b', 'group_b', 'group_a', 'group_c', 'group_c'],
        'short_description': ['high cpu', 'high cpu', 'low memory', 'low memory', 'disk full', 'high cpu', 'high cpu'],
        'sys_created_on': pd.to_datetime(['2023-01-01 10:00', '2023-01-01 11:00', '2023-01-02 12:00', '2023-01-02 13:00', '2023-01-03 14:00', '2023-01-04 15:00', '2023-01-04 16:00']),
        'number': ['INC1', 'INC2', 'INC3', 'INC4', 'INC5', 'INC6', 'INC7'],
        'self_healing_status': [STATUS_OK, STATUS_NOT_OK, STATUS_OK, STATUS_OK, NO_STATUS, STATUS_NOT_OK, STATUS_NOT_OK],
        'severity': [3, 3, 2, 2, 4, 3, 3],
        'priority_group': ['high', 'high', 'medium', 'medium', 'high', 'low', 'low']
    }
    df = pd.DataFrame(data)
    df['severity_score'] = df['severity'].replace({4: 4, 3: 3, 2: 2, 1: 1, 0: 0})
    df['priority_group_score'] = df['priority_group'].replace({'high': 3, 'medium': 2, 'low': 1})
    df['score_criticidade_final'] = df['severity_score'] + df['priority_group_score']
    return df

def test_analisar_grupos(sample_dataframe):
    """Testa se a função analisar_grupos agrupa corretamente os alertas."""
    summary = analisar_grupos(sample_dataframe)
    assert len(summary) == 4  # Espera 4 grupos únicos
    assert 'status_chronology' in summary.columns

    # Testa a cronologia de um grupo específico
    server1_group = summary[summary['cmdb_ci'] == 'server1']
    assert server1_group['status_chronology'].iloc[0] == [STATUS_OK, STATUS_NOT_OK]

def test_adicionar_acao_sugerida():
    """Testa a lógica da função adicionar_acao_sugerida."""
    data = {
        'status_chronology': [
            [STATUS_OK, STATUS_NOT_OK, STATUS_OK],  # Estabilizada
            [STATUS_NOT_OK, STATUS_OK, STATUS_NOT_OK],  # Intermitente
            [STATUS_NOT_OK, STATUS_NOT_OK],  # Falha Persistente
            [STATUS_OK, STATUS_OK],  # Sempre OK
            [NO_STATUS, NO_STATUS],  # Status Ausente
            [], # Vazio, deve ser status ausente
        ],
        'alert_count': [3, 3, 2, 2, 2, 0]
    }
    df = pd.DataFrame(data)
    df = adicionar_acao_sugerida(df)

    assert df['acao_sugerida'].tolist() == [
        ACAO_ESTABILIZADA,
        ACAO_INTERMITENTE,
        ACAO_FALHA_PERSISTENTE,
        ACAO_SEMPRE_OK,
        ACAO_STATUS_AUSENTE,
        ACAO_STATUS_AUSENTE
    ]
