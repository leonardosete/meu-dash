from typing import List

# Ações Sugeridas
ACAO_ESTABILIZADA = "Remediação estabilizada (houve falha)"
ACAO_INTERMITENTE = "Analisar intermitência na remediação"
ACAO_FALHA_PERSISTENTE = "Desenvolver remediação (nenhum sucesso registrado)"
ACAO_STATUS_AUSENTE = "Verificar coleta de dados da remediação (status ausente)"
ACAO_SEMPRE_OK = "Remediação automática funcional"
ACAO_INCONSISTENTE = "Analisar causa raiz das falhas (remediação inconsistente)"
ACAO_INSTABILIDADE_CRONICA = "Revisar causa raiz (remediação recorrente)"

# Mapeamento de Ações para categorização
ACAO_FLAGS_ATUACAO = [
    ACAO_INTERMITENTE,
    ACAO_FALHA_PERSISTENTE,
    ACAO_STATUS_AUSENTE,
    ACAO_INCONSISTENTE,
]
ACAO_FLAGS_OK = [ACAO_SEMPRE_OK, ACAO_ESTABILIZADA]
ACAO_FLAGS_INSTABILIDADE = [ACAO_INSTABILIDADE_CRONICA]

# Pesos para o cálculo de Score de Criticidade
SEVERITY_WEIGHTS = {
    "Crítico": 10,
    "Alto": 8,
    "Alto / Major": 8,
    "Médio": 5,
    "Médio / Minor": 5,
    "Aviso": 3,
    "Baixo / Informativo": 2,
    "OK": 0,
    "Limpar": 0,
}
PRIORITY_GROUP_WEIGHTS = {"Urgente": 10, "Alto(a)": 8, "Moderado(a)": 5, "Baixo(a)": 2}
ACAO_WEIGHTS = {
    ACAO_FALHA_PERSISTENTE: 1.5,
    ACAO_INTERMITENTE: 1.2,
    ACAO_STATUS_AUSENTE: 1.1,
    ACAO_INCONSISTENTE: 1.1,
    ACAO_ESTABILIZADA: 1.0,
    ACAO_SEMPRE_OK: 1.0,
}
# Pesos para o cálculo do Score de Ineficiência com base nos status das tasks
TASK_STATUS_WEIGHTS = {
    "Closed Incomplete": 1.5,
    "Closed Skipped": 1.2,
    # Status que não indicam ineficiência têm peso 1.0 (não penalizam)
    "default": 1.0,
}

# Nomes de colunas do DataFrame
COL_CREATED_ON = "sys_created_on"
COL_NODE = "node"
COL_CMDB_CI = "cmdb_ci"
COL_REMEDIATION_TASKS_PRESENT = "remediation_tasks_present"
COL_ASSIGNMENT_GROUP = "assignment_group"
COL_SHORT_DESCRIPTION = "short_description"
COL_NUMBER = "number"
COL_SOURCE = "source"
COL_METRIC_NAME = "metric_name"
COL_CMDB_CI_SYS_CLASS_NAME = "cmdb_ci.sys_class_name"
COL_SEVERITY = "severity"
COL_PRIORITY_GROUP = "sn_priority_group"
COL_DURACAO = "Duração"
COL_PARENT = "parent"
COL_STATE = "state"
COL_SYS_ID = "sys_id"
COL_TYPE_DISPLAY_VALUE = "type.display_value"
COL_U_ACTION_TIME = "u_action_time"
COL_U_CLOSED_DATE = "u_closed_date"
COL_ACKNOWLEDGED = "acknowledged"
COL_CORRELATION_GROUP = "correlation_group"
COL_EVENT_COUNT = "event_count"
COL_INCIDENT = "incident"
COL_MESSAGE_KEY = "message_key"
COL_COM_REMEDIACAO = "com_remediacao"
COL_PILAR = "Pilar"
COL_TASKS_COUNT = "tasks_count"
COL_TASKS_NUMBERS = "tasks_numbers"
# Novas colunas para a Fase 3 da Refatoração (Ainda não implementadas na análise)
COL_TASKS_STATUS = "tasks_status"
COL_ALERT_FOUND = "alert_found"
COL_PROCESSING_STATUS = "processing_status"
COL_ERROR_MESSAGE = "error_message"


# Colunas que definem um grupo único de alertas
GROUP_COLS: List[str] = [
    COL_ASSIGNMENT_GROUP,
    COL_SHORT_DESCRIPTION,
    COL_NODE,
    COL_CMDB_CI,
    COL_SOURCE,
    COL_METRIC_NAME,
    COL_CMDB_CI_SYS_CLASS_NAME,
]

# Colunas essenciais para o funcionamento do script
ESSENTIAL_COLS: List[str] = GROUP_COLS + [
    COL_CREATED_ON,
    COL_REMEDIATION_TASKS_PRESENT,
    COL_NUMBER,
    COL_SEVERITY,
    COL_PRIORITY_GROUP,
    COL_DURACAO,
    COL_PARENT,
    COL_STATE,
    COL_SYS_ID,
    COL_TYPE_DISPLAY_VALUE,
    COL_U_ACTION_TIME,
    COL_U_CLOSED_DATE,
    COL_ACKNOWLEDGED,
    COL_CORRELATION_GROUP,
    COL_EVENT_COUNT,
    COL_INCIDENT,
    COL_MESSAGE_KEY,
    COL_COM_REMEDIACAO,
    COL_PILAR,
    COL_TASKS_COUNT,
    COL_TASKS_NUMBERS,
    COL_TASKS_STATUS,
    COL_ALERT_FOUND,
    COL_PROCESSING_STATUS,
    COL_ERROR_MESSAGE,
]

# Valores de Status de Remediação
STATUS_OK = "REM_OK"
STATUS_NOT_OK = "REM_NOT_OK"
UNKNOWN = "DESCONHECIDO"
NO_STATUS = "NO_STATUS"
LOG_INVALIDOS_FILENAME = "invalid_remediation_tasks_present.csv"

# Limite de histórico de relatórios a serem mantidos no banco de dados e no disco.
MAX_REPORTS_HISTORY = 60

LIMIAR_ALERTAS_RECORRENTES = 5
