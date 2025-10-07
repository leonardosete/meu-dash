import os
from datetime import datetime
from typing import Tuple, Dict, Any
import logging

import numpy as np
import pandas as pd

from .constants import (
    ACAO_ESTABILIZADA, ACAO_FALHA_PERSISTENTE, ACAO_FLAGS_ATUACAO,
    ACAO_FLAGS_INSTABILIDADE, ACAO_FLAGS_OK, ACAO_INCONSISTENTE,
    ACAO_INSTABILIDADE_CRONICA, ACAO_INTERMITENTE, ACAO_SEMPRE_OK,
    ACAO_STATUS_AUSENTE, ACAO_WEIGHTS, COL_ASSIGNMENT_GROUP, COL_CMDB_CI,
    COL_CMDB_CI_SYS_CLASS_NAME, COL_CREATED_ON, COL_METRIC_NAME, COL_NODE,
    COL_NUMBER, COL_PRIORITY_GROUP, COL_SELF_HEALING_STATUS, COL_SEVERITY,
    COL_SHORT_DESCRIPTION, COL_SOURCE, ESSENTIAL_COLS, GROUP_COLS,
    LIMIAR_ALERTAS_RECORRENTES, LOG_INVALIDOS_FILENAME, NO_STATUS,
    PRIORITY_GROUP_WEIGHTS, SEVERITY_WEIGHTS, STATUS_NOT_OK, STATUS_OK, UNKNOWN,
)

logger = logging.getLogger(__name__)

# =============================================================================
# PROCESSAMENTO E ANÁLISE DE DADOS
# =============================================================================


def carregar_dados(filepath: str, output_dir: str) -> Tuple[pd.DataFrame, int]:
    """Carrega, valida e pré-processa os dados de um arquivo CSV."""
    logger.info(f"Carregando e preparando dados de '{filepath}'...")
    try:
        df = pd.read_csv(filepath, encoding="utf-8-sig", sep=";", engine="python")
    except FileNotFoundError:
        raise FileNotFoundError(f"O arquivo de entrada '{filepath}' não foi encontrado.")
    except Exception as e:
        raise ValueError(
            f"Erro ao ler ou processar o arquivo CSV '{filepath}'. Verifique o formato e a codificação. Detalhe: {e}"
        )

    missing_cols = [col for col in ESSENTIAL_COLS if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"O arquivo CSV não contém as colunas essenciais: {', '.join(missing_cols)}"
        )

    num_invalidos = 0
    if COL_SELF_HEALING_STATUS in df.columns:
        df[COL_SELF_HEALING_STATUS] = df[COL_SELF_HEALING_STATUS].astype(str).str.strip()
        valid_statuses = {STATUS_OK, STATUS_NOT_OK}
        mask_invalidos = df[COL_SELF_HEALING_STATUS].notna() & ~df[COL_SELF_HEALING_STATUS].isin(valid_statuses)
        df_invalidos = df[mask_invalidos]
        num_invalidos = len(df_invalidos)
        if not df_invalidos.empty:
            log_invalidos_path = os.path.join(output_dir, LOG_INVALIDOS_FILENAME)
            logger.warning(
                f"Detectadas {num_invalidos} linhas com status de remediação inesperado. Registrando em '{log_invalidos_path}'..."
            )
            df_invalidos.to_csv(log_invalidos_path, index=False, encoding="utf-8-sig")

    for col in GROUP_COLS:
        df[col] = df[col].fillna(UNKNOWN).replace("", UNKNOWN)
    df[COL_CREATED_ON] = pd.to_datetime(
        df[COL_CREATED_ON], errors="coerce", format="mixed"
    )
    df[COL_SELF_HEALING_STATUS] = df[COL_SELF_HEALING_STATUS].fillna(NO_STATUS)
    df["severity_score"] = df[COL_SEVERITY].map(SEVERITY_WEIGHTS).fillna(0)
    df["priority_group_score"] = (
        df[COL_PRIORITY_GROUP].map(PRIORITY_GROUP_WEIGHTS).fillna(0)
    )
    df["score_criticidade_final"] = df["severity_score"] + df["priority_group_score"]

    for col in GROUP_COLS + [
        COL_SELF_HEALING_STATUS,
        COL_SEVERITY,
        COL_PRIORITY_GROUP,
    ]:
        if col in df.columns and df[col].dtype == "object":
            df[col] = df[col].astype("category")
    logger.info("Dados carregados e preparados com sucesso.")
    return df, num_invalidos

def adicionar_acao_sugerida(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona a coluna 'acao_sugerida' com base na cronologia dos status."""
    last_status = df["status_chronology"].str[-1].fillna(NO_STATUS)
    has_ok = df["status_chronology"].apply(lambda c: STATUS_OK in c)
    has_only_no_status = df["status_chronology"].apply(
        lambda c: not c or all(s == NO_STATUS for s in c)
    )
    has_multiple_unique_statuses = df["status_chronology"].apply(
        lambda c: len(set(c)) > 1
    )

    conditions = [
        has_only_no_status,
        (last_status == STATUS_OK)
        & (df["alert_count"] >= LIMIAR_ALERTAS_RECORRENTES),
        (last_status == STATUS_OK) & has_multiple_unique_statuses,
        (last_status == STATUS_OK),
        (last_status != STATUS_OK) & has_ok,
        (last_status != STATUS_OK),
    ]
    choices = [
        ACAO_STATUS_AUSENTE,
        ACAO_INSTABILIDADE_CRONICA,
        ACAO_ESTABILIZADA,
        ACAO_SEMPRE_OK,
        ACAO_INTERMITENTE,
        ACAO_FALHA_PERSISTENTE,
    ]
    df["acao_sugerida"] = np.select(conditions, choices, default=UNKNOWN)
    return df

def analisar_grupos(df: pd.DataFrame) -> pd.DataFrame:
    """Agrupa e analisa os alertas para criar um sumário de problemas únicos."""
    logger.info("Analisando e agrupando alertas...")
    aggregations = {
        COL_CREATED_ON: ["min", "max"],
        COL_NUMBER: ["nunique", lambda x: ", ".join(sorted(x.unique()))],
        COL_SELF_HEALING_STATUS: lambda x: ", ".join(sorted(x.unique())),
        "score_criticidade_final": "max",
    }
    summary = (
        df.groupby(GROUP_COLS, observed=True, dropna=False)
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
        "score_criticidade_agregado",
    ]
    if not df.empty:
        sorted_df = df.sort_values(by=GROUP_COLS + [COL_CREATED_ON])
        chronology = (
            sorted_df.groupby(GROUP_COLS, observed=True, dropna=False)[
                COL_SELF_HEALING_STATUS
            ]
            .apply(list)
            .reset_index(name="status_chronology")
        )
        summary = pd.merge(summary, chronology, on=GROUP_COLS, how="left")
    else:
        summary["status_chronology"] = [[] for _ in range(len(summary))]

    summary = adicionar_acao_sugerida(summary)
    summary["fator_peso_remediacao"] = (
        summary["acao_sugerida"].map(ACAO_WEIGHTS).fillna(1.0)
    )
    summary["fator_volume"] = 1 + np.log(summary["alert_count"].clip(1))
    summary["score_ponderado_final"] = (
        summary["score_criticidade_agregado"]
        * summary["fator_peso_remediacao"]
        * summary["fator_volume"]
    )
    logger.info(f"Total de grupos únicos analisados: {summary.shape[0]}")
    return summary

# =============================================================================
# GERAÇÃO DE RELATÓRIOS (CSV E JSON)
# =============================================================================

def gerar_relatorios_csv(summary: pd.DataFrame, output_actuation: str, output_ok: str, output_instability: str) -> pd.DataFrame:
    """Filtra os resultados, salva em CSV e retorna o dataframe de atuação."""
    logger.info("Gerando relatórios CSV...")
    alerts_atuacao = summary[summary["acao_sugerida"].isin(ACAO_FLAGS_ATUACAO)].copy()
    alerts_ok = summary[summary["acao_sugerida"].isin(ACAO_FLAGS_OK)].copy()
    alerts_instabilidade = summary[summary["acao_sugerida"].isin(ACAO_FLAGS_INSTABILIDADE)].copy()
    full_emoji_map = {
        ACAO_INTERMITENTE: "⚠️",
        ACAO_FALHA_PERSISTENTE: "❌",
        ACAO_STATUS_AUSENTE: "❓",
        ACAO_INCONSISTENTE: "🔍",
        ACAO_SEMPRE_OK: "✅",
        ACAO_ESTABILIZADA: "⚠️✅",
        ACAO_INSTABILIDADE_CRONICA: "🔁",
    }

    if not alerts_atuacao.empty:
        VALID_STATUSES_FOR_CHRONOLOGY = {STATUS_OK, STATUS_NOT_OK, NO_STATUS}
        has_invalid_status_mask = alerts_atuacao["status_chronology"].apply(
            lambda chronology: any(s not in VALID_STATUSES_FOR_CHRONOLOGY for s in chronology)
        )
        if has_invalid_status_mask.any():
            alerts_atuacao.loc[has_invalid_status_mask, "acao_sugerida"] = "⚠️🔍 Analise o status da remediação 🔍⚠️ | " + alerts_atuacao.loc[has_invalid_status_mask, "acao_sugerida"]

    def save_csv(df, path, sort_by, ascending=False):
        if not df.empty:
            df_to_save = df.copy()
            df_to_save['acao_sugerida'] = df_to_save['acao_sugerida'].apply(lambda x: f"{full_emoji_map.get(x, '')} {x}".strip())
            df_to_save = df_to_save.sort_values(by=sort_by, ascending=ascending)
            if 'atuar' in path:
                df_to_save['status_tratamento'] = 'Pendente'
                df_to_save['responsavel'] = ''
                df_to_save['data_previsao_solucao'] = ''
            df_to_save.to_csv(path, index=False, encoding="utf-8-sig")
            logger.info(f"Relatório CSV gerado: {path}")

    save_csv(alerts_atuacao, output_actuation, "score_ponderado_final", False)
    save_csv(alerts_ok, output_ok, "last_event", False)
    save_csv(alerts_instabilidade, output_instability, "alert_count", False)
    return alerts_atuacao.sort_values(by="score_ponderado_final", ascending=False)

def export_summary_to_json(summary: pd.DataFrame, output_path: str):
    """Salva o dataframe de resumo em formato JSON."""
    logger.info("Exportando resumo para JSON...")
    summary_json = summary.copy()
    for col in ["first_event", "last_event"]:
        if col in summary_json.columns:
            summary_json[col] = summary_json[col].astype(str)
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
    output_instability_csv = os.path.join(
        output_dir, "remediados_frequentes.csv"
    )
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