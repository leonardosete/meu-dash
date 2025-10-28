import os
from typing import Tuple, Dict, Any
import logging

import numpy as np
import pandas as pd

from .constants import (
    ACAO_ESTABILIZADA,
    ACAO_FALHA_PERSISTENTE,
    ACAO_FLAGS_ATUACAO,
    ACAO_FLAGS_INSTABILIDADE,
    ACAO_FLAGS_OK,
    ACAO_INCONSISTENTE,
    ACAO_INSTABILIDADE_CRONICA,
    ACAO_INTERMITENTE,
    ACAO_SEMPRE_OK,
    ACAO_SUCESSO_PARCIAL,
    ACAO_STATUS_AUSENTE,
    ACAO_WEIGHTS,
    COL_CREATED_ON,
    COL_NUMBER,
    COL_PRIORITY_GROUP,
    COL_HAS_REMEDIATION_TASK,
    COL_SEVERITY,
    COL_LAST_TASK_STATUS,
    ESSENTIAL_COLS,
    GROUP_COLS,
    LIMIAR_ALERTAS_RECORRENTES,
    LOG_INVALIDOS_FILENAME,
    NO_STATUS,
    PRIORITY_GROUP_WEIGHTS,
    SEVERITY_MAP,
    SEVERITY_WEIGHTS,
    STATUS_NOT_OK,
    COL_TASKS_STATUS,
    TASK_STATUS_WEIGHTS,
    STATUS_OK,
    UNKNOWN,
)

logger = logging.getLogger(__name__)

# =============================================================================
# PROCESSAMENTO E ANÁLISE DE DADOS
# =============================================================================

def _validar_e_separar_linhas_invalidas(df: pd.DataFrame, output_dir: str) -> Tuple[pd.DataFrame, int]:
    """
    Valida a integridade dos dados de um DataFrame e separa as linhas inválidas.

    Esta função realiza múltiplas validações (integridade estrutural, formato de dados,
    datas inválidas) e move as linhas que falham em qualquer uma delas para um
    arquivo de log separado (`invalid_cols.csv`), retornando um DataFrame limpo.

    Args:
        df (pd.DataFrame): O DataFrame de entrada a ser validado.
        output_dir (str): O diretório onde o log de linhas inválidas será salvo.

    Returns:
        Tuple[pd.DataFrame, int]: Uma tupla contendo:
            - O DataFrame limpo, sem as linhas inválidas.
            - O número de linhas inválidas que foram removidas.
    """
    all_invalid_dfs = []
    invalid_indices = set()

    # VALIDAÇÃO 1: Integridade Estrutural (colunas essenciais para agrupamento)
    mask_group_cols_na = df[GROUP_COLS].isnull().any(axis=1)
    if mask_group_cols_na.any():
        df_group_cols_na = df[mask_group_cols_na].copy()
        df_group_cols_na["invalidated"] = "Linha malformada ou truncada (colunas de agrupamento essenciais ausentes)"
        all_invalid_dfs.append(df_group_cols_na)
        invalid_indices.update(df_group_cols_na.index)

    # VALIDAÇÃO 2: Formato dos Dados
    if COL_HAS_REMEDIATION_TASK in df.columns:
        df[COL_HAS_REMEDIATION_TASK] = df[COL_HAS_REMEDIATION_TASK].astype(str).str.strip()
        valid_statuses = {STATUS_OK, STATUS_NOT_OK}
        mask_formato_invalido = ~df.index.isin(invalid_indices) & (
            df[COL_HAS_REMEDIATION_TASK].notna() & ~df[COL_HAS_REMEDIATION_TASK].isin(valid_statuses)
        )
        if mask_formato_invalido.any():
            df_formato_invalido = df[mask_formato_invalido].copy()
            df_formato_invalido["invalidated"] = "Formato de has_remediation_task inesperado"
            all_invalid_dfs.append(df_formato_invalido)
            invalid_indices.update(df_formato_invalido.index)

    # VALIDAÇÃO 3: Datas Inválidas
    datetimes_temp = pd.to_datetime(df[COL_CREATED_ON], errors="coerce", format="mixed")
    mask_data_invalida = datetimes_temp.isna() & ~df.index.isin(invalid_indices)
    if mask_data_invalida.any():
        df_data_invalida = df[mask_data_invalida].copy()
        df_data_invalida["invalidated"] = "Formato de data inválido em 'sys_created_on'"
        all_invalid_dfs.append(df_data_invalida)
        invalid_indices.update(df_data_invalida.index)

    num_invalidos = len(invalid_indices)
    if all_invalid_dfs:
        df_invalidos_total = pd.concat(all_invalid_dfs, ignore_index=True)
        log_invalidos_path = os.path.join(output_dir, LOG_INVALIDOS_FILENAME)
        logger.warning(f"Detectadas {num_invalidos} linhas inválidas. Registrando em '{log_invalidos_path}'...")
        df_invalidos_total.to_csv(log_invalidos_path, index=False, encoding="utf-8-sig", sep=";")
        df = df.drop(index=list(invalid_indices)).reset_index(drop=True)

    return df, num_invalidos


def carregar_dados(filepath: str, output_dir: str) -> Tuple[pd.DataFrame, int]:
    """
    Carrega, valida e pré-processa os dados de um arquivo CSV.

    Esta função orquestra o processo de ingestão de dados. Ela lê um arquivo CSV,
    valida se o schema (colunas obrigatórias) está correto, chama a função de
    validação de linhas e realiza um pré-processamento final nos dados limpos.

    Args:
        filepath (str): O caminho para o arquivo CSV a ser carregado.
        output_dir (str): O diretório de saída para logs de validação.

    Returns:
        Tuple[pd.DataFrame, int]: Uma tupla contendo:
            - O DataFrame pré-processado e pronto para análise.
            - O número de linhas inválidas que foram detectadas e removidas.

    Raises:
        ValueError: Se o arquivo CSV não contiver todas as colunas essenciais.
    """
    logger.info(f"Carregando e preparando dados de '{filepath}'...")
    try:
        # MELHORIA: Usa sep=None para que o 'engine' do Python detecte
        # automaticamente o separador (seja ';' ou ',').
        # Isso torna a ingestão de dados mais robusta.
        df = pd.read_csv(filepath, encoding="utf-8-sig", sep=None, engine="python")
    except FileNotFoundError:
        raise FileNotFoundError(
            f"O arquivo de entrada '{filepath}' não foi encontrado."
        )
    except Exception as e:
        raise ValueError(
            f"Erro ao ler ou processar o arquivo CSV '{filepath}'. Verifique o formato e a codificação. Detalhe: {e}"
        ) from e

    # Garante que linhas completamente vazias (comuns em CSVs malformados) sejam removidas.
    df.dropna(how="all", inplace=True)

    # VALIDAÇÃO ESTRITA: Garante que todas as colunas definidas como essenciais
    # estejam presentes no arquivo de entrada. Se alguma faltar, o processo falha.
    missing_cols = [col for col in ESSENTIAL_COLS if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Layout do arquivo incompatível. As seguintes colunas obrigatórias não foram encontradas: {', '.join(missing_cols)}. Consulte a documentação para mais detalhes."
        )

    # Delega a lógica de validação para a função auxiliar.
    df, num_invalidos = _validar_e_separar_linhas_invalidas(df, output_dir)

    # O pré-processamento final só ocorre no DataFrame limpo.
    df[COL_CREATED_ON] = pd.to_datetime(df[COL_CREATED_ON], errors="coerce", format="mixed")
    for col in GROUP_COLS:
        df[col] = df[col].fillna(UNKNOWN).replace("", UNKNOWN)
    # Garante que a coluna exista antes de tentar preencher NaNs
    if COL_HAS_REMEDIATION_TASK in df.columns:
        df[COL_HAS_REMEDIATION_TASK] = df[COL_HAS_REMEDIATION_TASK].fillna(NO_STATUS)

    logger.info("Dados carregados e preparados com sucesso.")
    return df, num_invalidos


def adicionar_acao_sugerida(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adiciona a coluna 'acao_sugerida' com base na cronologia dos status das tarefas.

    Esta função implementa a árvore de decisão principal da aplicação. Ela analisa
    o histórico de status de remediação de cada "Caso" e atribui uma ação
    sugerida com base em um conjunto de regras de negócio priorizadas (ex:
    instabilidade crônica, falha persistente, sucesso, etc.).

    Args:
        df (pd.DataFrame): O DataFrame de resumo dos "Casos", que deve conter
            as colunas 'last_tasks_status', 'status_chronology' e 'alert_count'.

    Returns:
        pd.DataFrame: O DataFrame de entrada com a coluna 'acao_sugerida' adicionada.
    """
    # Define quais status de task são considerados um "sucesso"
    SUCCESS_STATUSES = {"Closed"}

    # GARANTIA DE RETROCOMPATIBILIDADE: Se a coluna de status de task não existir,
    # retorna uma ação padrão para evitar erros.
    if COL_LAST_TASK_STATUS not in df.columns:
        df["acao_sugerida"] = ACAO_STATUS_AUSENTE
        return df
        
    # Extrai informações da cronologia de tasks e do status final (o primeiro da lista, que corresponde ao alerta mais recente)
    SUCCESS_STATUSES = {"Closed"}
    # CORREÇÃO: Usa o 'last_tasks_status' (o mais recente) como base para a lógica.
    last_status = df[COL_LAST_TASK_STATUS].fillna(NO_STATUS)
    has_success = df["status_chronology"].apply(
        lambda c: bool(c) and any(s in SUCCESS_STATUSES for s in c)
    )
    has_only_no_status = df["status_chronology"].apply(
        lambda c: not c or all(s == NO_STATUS for s in c)
    )

    # CORREÇÃO: A lógica foi reestruturada para maior clareza e para tratar os casos de borda corretamente.
    conditions = [
        # PRIORIDADE 0: Se o status for nulo ou a cronologia vazia, é um problema de coleta de dados.
        # Regra de Negócio: Dados de remediação ausentes. Ação é investigar a coleta.
        (last_status == NO_STATUS) | has_only_no_status,
        # PRIORIDADE 1: Se a tarefa não foi encontrada, é uma falha de remediação.
        # Regra de Negócio: A automação nem sequer foi acionada. Ação é desenvolver/corrigir o gatilho.
        last_status == "No Task Found",
        # PRIORIDADE 2: Casos crônicos, mesmo que sejam "sucesso", devem ser tratados como instabilidade.
        # Regra de Negócio: O problema se repete >5 vezes, mesmo com automação. A causa raiz é outra.
        (df["alert_count"] >= LIMIAR_ALERTAS_RECORRENTES) & last_status.isin(SUCCESS_STATUSES),
        # PRIORIDADE 3: Casos de sucesso parcial (incluindo "Canceled").
        # Regra de Negócio: A automação rodou mas não resolveu completamente. Ação é revisar o script.
        last_status.isin(["Closed Skipped", "Canceled"]), # Casos de sucesso parcial não crônicos.
        # PRIORIDADE 4: A automação rodou, falhou, mas depois teve sucesso. Indica estabilização.
        (last_status.isin(SUCCESS_STATUSES)) & has_success & df['status_chronology'].apply(lambda x: len({s for s in x if pd.notna(s) and s != NO_STATUS}) > 1),
        # PRIORIDADE 5: A automação sempre teve sucesso.
        (last_status.isin(SUCCESS_STATUSES)) & has_success,
        # PRIORIDADE 6: A automação teve sucesso no passado, mas a última execução falhou. Indica intermitência.
        (~last_status.isin(SUCCESS_STATUSES)) & has_success,
        # PRIORIDADE 7: A automação nunca teve sucesso. Falha persistente.
        ~has_success,
    ]
    choices = [
        ACAO_STATUS_AUSENTE,
        ACAO_FALHA_PERSISTENTE, # Trata "No Task Found" como falha persistente
        ACAO_INSTABILIDADE_CRONICA,
        ACAO_SUCESSO_PARCIAL,
        ACAO_ESTABILIZADA,
        ACAO_SEMPRE_OK,
        ACAO_INTERMITENTE,
        ACAO_FALHA_PERSISTENTE,
    ]
    df["acao_sugerida"] = np.select(conditions, choices, default=UNKNOWN)

    return df


def _calcular_fatores_de_ponderacao(summary: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula e adiciona as colunas de fatores de ponderação ao sumário.

    Esta função calcula os três multiplicadores que compõem o score ponderado:
    1.  **fator_peso_remediacao**: Penaliza casos que exigem mais esforço (ex: desenvolver automação).
    2.  **fator_ineficiencia_task**: Penaliza casos onde a automação falhou.
    3.  **fator_volume**: Penaliza casos que ocorrem com mais frequência.

    Args:
        summary (pd.DataFrame): O DataFrame de resumo dos "Casos".

    Returns:
        pd.DataFrame: O DataFrame de resumo com as colunas de fatores adicionadas.
    """
    # Fator 1: Peso da Ação de Remediação
    summary["fator_peso_remediacao"] = (
        summary["acao_sugerida"].map(ACAO_WEIGHTS).fillna(1.0)
    )

    # Fator 2: Ineficiência da Task de Automação
    if "status_chronology" not in summary.columns:
        summary["fator_ineficiencia_task"] = 1.0
        logger.warning("Coluna 'status_chronology' não encontrada. Fator de ineficiência de tasks não será aplicado.")
    else:
        default_weight = TASK_STATUS_WEIGHTS.get("default", 1.0)
        def get_max_inefficiency_factor(chronology):
            if not chronology:
                return default_weight
            # Encontra o peso máximo (pior caso) na cronologia
            return max(TASK_STATUS_WEIGHTS.get(status, default_weight) for status in chronology)
        summary["fator_ineficiencia_task"] = summary["status_chronology"].apply(get_max_inefficiency_factor)

    # Fator 3: Volume de Alertas
    summary["fator_volume"] = 1 + np.log(summary["alert_count"].clip(1))

    return summary


def analisar_grupos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Função central que agrupa alertas em "Casos" e calcula o score ponderado.

    Esta função recebe um DataFrame de alertas individuais, executa a lógica de
    cálculo de risco base, agrupa os alertas em "Casos" únicos, agrega as
    informações relevantes (como contagem e cronologia) e, por fim, calcula o
    `score_ponderado_final` para cada caso.

    Args:
        df (pd.DataFrame): O DataFrame de alertas pré-processado pela função
            `carregar_dados`.

    Returns:
        pd.DataFrame: Um DataFrame de resumo onde cada linha representa um "Caso" único,
        enriquecido com todos os scores e fatores.
    """
    logger.info("Analisando e agrupando alertas...")

    # Normaliza a coluna de severidade (lowercase, sem acentos) para a busca no mapa.
    severity_normalized = df[COL_SEVERITY].str.lower().str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')
    # Mapeia a versão normalizada para a chave padrão e depois para o peso.
    severity_standardized = severity_normalized.map(SEVERITY_MAP)
    df["severity_score"] = severity_standardized.map(SEVERITY_WEIGHTS).fillna(0)

    df["priority_group_score"] = (
        df[COL_PRIORITY_GROUP].map(PRIORITY_GROUP_WEIGHTS).fillna(0)
    )
    df["score_criticidade_final"] = df["severity_score"] + df["priority_group_score"]

    aggregations = {
        COL_CREATED_ON: ["min", "max"],
        COL_NUMBER: ["nunique", lambda x: ", ".join(sorted(x.unique()))],
        # CORREÇÃO: A coluna 'statuses' agora é apenas um artefato legado. A cronologia real virá de 'tasks_status'.
        COL_HAS_REMEDIATION_TASK: lambda x: ", ".join(sorted(x.dropna().astype(str).unique())),
        "score_criticidade_final": "max",  # Pega o maior score de risco do grupo
        COL_TASKS_STATUS: "first", # Pega o status da task do alerta mais recente
    }
    # GARANTIA DE ORDEM: Ordena o DataFrame pela data de criação ANTES do groupby.
    # Isso garante que a agregação 'first' para 'tasks_status' pegue o status do alerta mais recente.
    df_sorted_for_agg = df.sort_values(by=COL_CREATED_ON, ascending=False)

    summary = (
        df_sorted_for_agg.groupby(GROUP_COLS, observed=True, dropna=False)
        .agg(aggregations)
        .reset_index()
    )
    summary.columns = [
        *GROUP_COLS,
        "first_event",
        "last_event",
        "alert_count",
        "alert_numbers",
        "statuses",
        "score_criticidade_agregado",  # Nome da coluna após a agregação
        "last_tasks_status",  # Renomeado para clareza
    ]
    if not df.empty:
        sorted_df = df.sort_values(by=GROUP_COLS + [COL_CREATED_ON])
        chronology = (
            sorted_df.groupby(GROUP_COLS, observed=True, dropna=False)[COL_TASKS_STATUS]
            .apply(list)
            .reset_index(name="status_chronology")
        )
        summary = pd.merge(
            summary, chronology, on=GROUP_COLS, how="left", validate="one_to_one"
        )
    else:
        summary["status_chronology"] = [[] for _ in range(len(summary))]

    summary = adicionar_acao_sugerida(summary)

    summary = _calcular_fatores_de_ponderacao(summary)

    summary["score_ponderado_final"] = (
        summary["score_criticidade_agregado"]
        * summary["fator_peso_remediacao"]
        * summary["fator_volume"]
        * summary["fator_ineficiencia_task"]
    )
    logger.info(f"Total de grupos únicos analisados: {summary.shape[0]}")
    return summary


# =============================================================================
# GERAÇÃO DE RELATÓRIOS (CSV E JSON)
# =============================================================================

# Define o conjunto de colunas essenciais e a ordem para os relatórios finais.
# Isso garante consistência e remove "ruído" dos relatórios.
colunas_essenciais_relatorio = [
    "score_ponderado_final",
    "acao_sugerida",
    "assignment_group",
    "short_description",
    "cmdb_ci",
    "node",
    "metric_name",
    "first_event",
    "last_event",
    "alert_count",
    "alert_numbers",
    # Colunas opcionais que fornecem contexto adicional
    "status_chronology",
    "last_tasks_status",
    # Colunas específicas do plano de ação
    "status_tratamento",
    "responsavel",
    "data_previsao_solucao",
]


# Mapa de emojis centralizado para garantir consistência em todos os relatórios.
FULL_EMOJI_MAP = {
    ACAO_INTERMITENTE: "⚠️",
    ACAO_FALHA_PERSISTENTE: "❌",
    ACAO_STATUS_AUSENTE: "❓",
    ACAO_INCONSISTENTE: "🔍",
    ACAO_SEMPRE_OK: "✅",
    ACAO_ESTABILIZADA: "⚠️✅",
    ACAO_SUCESSO_PARCIAL: "🧐",
    ACAO_INSTABILIDADE_CRONICA: "🔁",
}

def _save_csv(df, path, sort_by, full_emoji_map, ascending=False):
    """Função auxiliar para salvar DataFrames em CSV com formatação padronizada."""
    if not df.empty:
        # Garante que colunas de metadados internos não vazem para os relatórios.
        colunas_a_remover = ["processing_status", "error_message"]
        df = df.drop(
            columns=[col for col in colunas_a_remover if col in df.columns]
        )
        df_to_save = df.copy()
        df_to_save["acao_sugerida"] = df_to_save["acao_sugerida"].apply(
            lambda x: f"{full_emoji_map.get(x, '')} {x}".strip()
        )
        # Garante que as datas sejam formatadas no padrão brasileiro para os relatórios.
        for col in ["first_event", "last_event"]:
            if col in df_to_save.columns:
                # Converte para datetime se não for, e então formata.
                df_to_save[col] = pd.to_datetime(df_to_save[col]).dt.strftime('%d/%m/%Y %H:%M:%S')

        if "score_ponderado_final" in df_to_save.columns:
            df_to_save["score_ponderado_final"] = df_to_save["score_ponderado_final"].round(1)
        df_to_save = df_to_save.sort_values(by=sort_by, ascending=ascending)
        if "atuar" in path or "plano-de-acao" in path:
            df_to_save["status_tratamento"] = "Pendente"
            df_to_save["responsavel"] = ""
            df_to_save["data_previsao_solucao"] = ""
        colunas_presentes = [col for col in colunas_essenciais_relatorio if col in df_to_save.columns]
        df_final = df_to_save[colunas_presentes]
        df_final.to_csv(path, index=False, encoding="utf-8-sig", sep=";")
        logger.info(f"Relatório CSV gerado: {path}")

def gerar_relatorios_csv(
    summary: pd.DataFrame,
    output_actuation: str,
    output_ok: str,
    output_instability: str,
) -> pd.DataFrame:
    """Filtra os resultados, salva em CSV e retorna o dataframe de atuação."""
    logger.info("Gerando relatórios CSV...")
    alerts_atuacao = summary[summary["acao_sugerida"].isin(ACAO_FLAGS_ATUACAO)].copy()
    alerts_ok = summary[summary["acao_sugerida"].isin(ACAO_FLAGS_OK)].copy()
    alerts_instabilidade = summary[
        summary["acao_sugerida"].isin(ACAO_FLAGS_INSTABILIDADE)
    ].copy()

    _save_csv(alerts_atuacao, output_actuation, "score_ponderado_final", FULL_EMOJI_MAP, False)
    _save_csv(alerts_ok, output_ok, "last_event", FULL_EMOJI_MAP, False)
    _save_csv(alerts_instabilidade, output_instability, "alert_count", FULL_EMOJI_MAP, False)
    return alerts_atuacao.sort_values(by="score_ponderado_final", ascending=False)


def export_summary_to_json(summary: pd.DataFrame, output_path: str):
    """Salva o dataframe de resumo em formato JSON."""
    logger.info("Exportando resumo para JSON...")
    # Garante que colunas de metadados internos não vazem para o JSON.
    colunas_a_remover = ["processing_status", "error_message"]
    summary = summary.drop(
        columns=[col for col in colunas_a_remover if col in summary.columns]
    )
    summary_json = summary.copy()
    for col in ["first_event", "last_event"]:
        if col in summary_json.columns:
            summary_json[col] = pd.to_datetime(summary_json[col]).dt.strftime('%d/%m/%Y %H:%M:%S')
    summary_json.to_json(output_path, orient="records", indent=4, date_format="iso")
    logger.info(f"Resumo salvo em: {output_path}")


# =============================================================================
# EXECUÇÃO PRINCIPAL
# =============================================================================


def analisar_arquivo_csv(
    input_file: str, output_dir: str, light_analysis: bool = False
) -> Dict[str, Any]:
    """
    Função principal que orquestra a análise de um arquivo CSV.
    Retorna um dicionário com os resultados da análise e metadados.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Define caminhos
    output_actuation_csv = os.path.join(output_dir, "atuar.csv")
    output_ok_csv = os.path.join(output_dir, "remediados.csv")
    output_instability_csv = os.path.join(output_dir, "remediados_frequentes.csv")
    output_json = os.path.join(output_dir, "resumo_problemas.json")

    # 1. Análise de Dados
    df, num_logs_invalidos = carregar_dados(input_file, output_dir)
    summary = analisar_grupos(df)
    export_summary_to_json(summary.copy(), output_json)

    df_atuacao = summary[summary["acao_sugerida"].isin(ACAO_FLAGS_ATUACAO)].copy()

    if light_analysis:
        logger.info("Análise leve concluída. Apenas o resumo JSON foi gerado.")
        return {
            "summary": summary,
            "df_atuacao": df_atuacao,
            "num_logs_invalidos": num_logs_invalidos,
            "json_path": output_json,
        }

    # 2. Geração de Relatórios CSV
    df_atuacao = gerar_relatorios_csv(
        summary, output_actuation_csv, output_ok_csv, output_instability_csv
    )

    logger.info(f"Análise de dados finalizada. Artefatos gerados em: {output_dir}")

    return {
        "summary": summary,
        "df_atuacao": df_atuacao,
        "num_logs_invalidos": num_logs_invalidos,
        "json_path": output_json,
    }
