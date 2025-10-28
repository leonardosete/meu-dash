"""
Módulo para construir os dicionários de contexto para a renderização de templates HTML.
"""

import os
from typing import Dict, Any
import logging
import pandas as pd

from .constants import (
    ACAO_SUCESSO_PARCIAL,
    ACAO_FLAGS_INSTABILIDADE,
    ACAO_FLAGS_OK,
    COL_ASSIGNMENT_GROUP,
    COL_METRIC_NAME,
    COL_SHORT_DESCRIPTION,
)

logger = logging.getLogger(__name__)


def build_dashboard_context(
    summary_df: pd.DataFrame,
    df_atuacao: pd.DataFrame,
    num_logs_invalidos: int,
    output_dir: str,
    plan_dir: str,
    details_dir: str,
    trend_report_path: str = None,
) -> Dict[str, Any]:
    """
    Constrói o dicionário de contexto para o dashboard principal.

    Args:
        summary_df: DataFrame com o resumo geral da análise.
        df_atuacao: DataFrame com os Casos que necessitam de atuação.
        num_logs_invalidos: Número de logs com status de remediação inválido.
        output_dir: Diretório de saída dos relatórios.
        plan_dir: Diretório dos planos de ação.
        details_dir: Diretório das páginas de detalhe.
        trend_report_path: Caminho para o relatório de tendência (opcional).

    Returns:
        Um dicionário com todos os dados necessários para renderizar o template do dashboard.
    """
    logger.info("Construindo contexto para o dashboard...")

    total_grupos = len(summary_df)
    grupos_atuacao = len(df_atuacao)
    grupos_instabilidade = summary_df["acao_sugerida"].isin(ACAO_FLAGS_INSTABILIDADE).sum()
    grupos_sucesso_parcial = summary_df["acao_sugerida"].eq(ACAO_SUCESSO_PARCIAL).sum()

    casos_ok_estaveis = (
        total_grupos - grupos_atuacao - grupos_instabilidade - grupos_sucesso_parcial
    )

    # CORREÇÃO: A taxa de sucesso deve ser baseada apenas nos casos que são 100% OK e estáveis.
    taxa_sucesso = (
        (casos_ok_estaveis / total_grupos) * 100 if total_grupos > 0 else 0
    )
    df_ok_filtered = summary_df[summary_df["acao_sugerida"].isin(ACAO_FLAGS_OK)]
    df_instabilidade_filtered = summary_df[
        summary_df["acao_sugerida"].isin(ACAO_FLAGS_INSTABILIDADE)
    ]
    df_sucesso_parcial_filtered = summary_df[
        summary_df["acao_sugerida"] == ACAO_SUCESSO_PARCIAL
    ]

    all_squads = df_atuacao[COL_ASSIGNMENT_GROUP].value_counts()
    top_squads = all_squads[all_squads > 0].nlargest(5)

    metric_counts = df_atuacao[COL_METRIC_NAME].value_counts()
    top_metrics = metric_counts[metric_counts > 0].nlargest(5)

    top_problemas_atuacao = (
        df_atuacao.groupby(COL_SHORT_DESCRIPTION, observed=True)["alert_count"]
        .sum()
        .nlargest(5)
    )
    top_problemas_remediados = (
        df_ok_filtered.groupby(COL_SHORT_DESCRIPTION, observed=True)["alert_count"]
        .sum()
        .nlargest(5)
    )
    top_problemas_geral = (
        summary_df.groupby(COL_SHORT_DESCRIPTION, observed=True)["alert_count"]
        .sum()
        .nlargest(10)
    )
    top_problemas_instabilidade = (
        df_instabilidade_filtered.groupby(COL_SHORT_DESCRIPTION, observed=True)[
            "alert_count"
        ]
        .sum()
        .nlargest(5)
    )

    total_alertas_remediados_ok = df_ok_filtered["alert_count"].sum()
    total_alertas_instabilidade = df_instabilidade_filtered["alert_count"].sum()
    total_alertas_problemas = df_atuacao["alert_count"].sum()
    total_alertas_sucesso_parcial = df_sucesso_parcial_filtered["alert_count"].sum()
    total_alertas_geral = summary_df["alert_count"].sum()

    start_date = summary_df["first_event"].min() if not summary_df.empty else None
    end_date = summary_df["last_event"].max() if not summary_df.empty else None
    date_range_text = "Período da Análise: Dados Indisponíveis"
    if start_date and end_date:
        date_range_text = f"Período da Análise: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}"

    squads_prioritarias = (
        df_atuacao.groupby(COL_ASSIGNMENT_GROUP, observed=True)
        .agg(
            score_acumulado=("score_ponderado_final", "sum"),
            total_casos=("score_ponderado_final", "size"),
        )
        .reset_index()
    )
    top_5_squads_agrupadas = squads_prioritarias.sort_values(
        by="score_acumulado", ascending=False
    ).head(5)

    context = {
        "total_grupos": total_grupos,
        "grupos_atuacao": grupos_atuacao,
        "grupos_instabilidade": grupos_instabilidade,
        "grupos_sucesso_parcial": grupos_sucesso_parcial,
        "taxa_sucesso": taxa_sucesso,
        "casos_ok_estaveis": casos_ok_estaveis,
        "top_squads": top_squads,
        "top_metrics": top_metrics,
        "top_problemas_atuacao": top_problemas_atuacao,
        "top_problemas_remediados": top_problemas_remediados,
        "top_problemas_geral": top_problemas_geral,
        "top_problemas_instabilidade": top_problemas_instabilidade,
        "total_alertas_remediados_ok": total_alertas_remediados_ok,
        "total_alertas_instabilidade": total_alertas_instabilidade,
        "total_alertas_problemas": total_alertas_problemas,
        "total_alertas_sucesso_parcial": total_alertas_sucesso_parcial,
        "total_alertas_geral": total_alertas_geral,
        "all_squads": all_squads,
        "top_5_squads_agrupadas": top_5_squads_agrupadas,
        "num_logs_invalidos": num_logs_invalidos,
        "trend_report_path": trend_report_path,
        "date_range_text": date_range_text,
        "summary_filename": os.path.basename(
            os.path.join(output_dir, "resumo_geral.html")
        ),
        "plan_dir_base_name": os.path.basename(plan_dir),
        "details_dir_base_name": os.path.basename(details_dir),
        "ai_summary": None,  # Placeholder for future AI summary feature
    }
    logger.info("Contexto para o dashboard construído com sucesso.")
    return context
