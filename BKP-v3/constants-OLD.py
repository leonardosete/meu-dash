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
    ACAO_INCONSISTENTE
]
ACAO_FLAGS_OK = [ACAO_SEMPRE_OK, ACAO_ESTABILIZADA]
ACAO_FLAGS_INSTABILIDADE = [ACAO_INSTABILIDADE_CRONICA]

# Pesos para o cálculo de Score de Criticidade
SEVERITY_WEIGHTS = {
    'Crítico': 10, 'Alto': 8, 'Alto / Major': 8, 'Médio': 5,
    'Médio / Minor': 5, 'Aviso': 3, 'Baixo / Informativo': 2,
    'OK': 0, 'Limpar': 0,
}
PRIORITY_GROUP_WEIGHTS = {
    'Urgente': 10, 'Alto(a)': 8, 'Moderado(a)': 5, 'Baixo(a)': 2
}
ACAO_WEIGHTS = {
    ACAO_FALHA_PERSISTENTE: 1.5, ACAO_INTERMITENTE: 1.2,
    ACAO_STATUS_AUSENTE: 1.1, ACAO_INCONSISTENTE: 1.1,
    ACAO_ESTABILIZADA: 1.0, ACAO_SEMPRE_OK: 1.0
}