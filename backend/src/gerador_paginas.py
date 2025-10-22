import os
import re
from datetime import datetime
from html import escape
import logging
import pandas as pd
from . import gerador_html
from .constants import (
    ACAO_ESTABILIZADA,
    ACAO_ESTABILIZADA,
    ACAO_FALHA_PERSISTENTE,
    ACAO_FLAGS_ATUACAO,
    ACAO_FLAGS_INSTABILIDADE,
    ACAO_INSTABILIDADE_CRONICA,
    LOG_INVALIDOS_FILENAME,  # noqa: F401
    ACAO_FLAGS_OK,
    ACAO_INCONSISTENTE,
    ACAO_INTERMITENTE,
    ACAO_SEMPRE_OK,
    ACAO_STATUS_AUSENTE,
    COL_ASSIGNMENT_GROUP,
    COL_CMDB_CI,
    COL_METRIC_NAME,
    COL_NODE,
    COL_SHORT_DESCRIPTION,
    NO_STATUS,
    STATUS_NOT_OK,
    STATUS_OK,
    UNKNOWN,
)
from .analisar_alertas import (
    _save_csv,
)

logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTES DE NOMENCLATURA (python:S1192)
# =============================================================================
MAIN_TEMPLATE = "template.html"

REPORTS_DIR_SQUADS = "squads"
REPORTS_DIR_DETAILS = "detalhes"
REPORTS_DIR_PLANS = "planos_de_acao"

FILENAME_SUMMARY = "resumo_geral.html"
FILENAME_ALL_SQUADS = "todas_as_squads.html"
FILENAME_SUCCESS = "sucesso_automacao.html"
FILENAME_INSTABILITY = "instabilidade_cronica.html"
FILENAME_ACTION_PLAN = "atuar.html"
FILENAME_INVALID_LOGS_HTML = "qualidade_dados_remediacao.html"
FILENAME_JSON_VIEWER = "visualizador_json.html"
FILENAME_JSON_SUMMARY = "resumo_problemas.json"

BASE_TEMPLATE_DIR = "/app/templates"

# =============================================================================
# FUNÇÕES DE GERAÇÃO DE PÁGINAS HTML
# =============================================================================


def gerar_ecossistema_de_relatorios(
    dashboard_context: dict,
    analysis_results: dict,
    output_dir: str, # noqa: E501
    frontend_url: str = "/",
) -> str:
    """
    Orquestra a geração de todas as páginas HTML do relatório.

    Args:
        dashboard_context: Dicionário com os dados para os dashboards.
        analysis_results: Dicionário com os DataFrames da análise.
        output_dir: Diretório onde os relatórios serão salvos. # noqa: E501
        frontend_url: URL base do frontend para links de retorno.

    Returns:
        O caminho para o arquivo de resumo principal (resumo_geral.html).
    """
    logger.info("Iniciando a geração do ecossistema completo de relatórios HTML...")
    timestamp_str = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
    summary_html_path = os.path.join(output_dir, FILENAME_SUMMARY)

    # Gera o dashboard principal
    gerar_resumo_executivo(
        dashboard_context, summary_html_path, timestamp_str, frontend_url
    )

    # Prepara dados e caminhos para as páginas de detalhe
    df_atuacao = analysis_results["df_atuacao"]
    summary = analysis_results["summary"]
    details_dir = os.path.join(output_dir, REPORTS_DIR_DETAILS)
    squad_reports_dir = os.path.join(output_dir, REPORTS_DIR_SQUADS)
    summary_filename = os.path.basename(summary_html_path)
    squad_reports_base_name = os.path.basename(squad_reports_dir)

    # Gera páginas de detalhe para os principais problemas
    gerar_paginas_detalhe_problema(
        df_atuacao,
        dashboard_context["top_problemas_atuacao"].index,
        details_dir,
        summary_filename,
        "aberto_",
        squad_reports_base_name,
        timestamp_str,
    )
    gerar_paginas_detalhe_problema(
        summary[summary["acao_sugerida"].isin(ACAO_FLAGS_OK)],
        dashboard_context["top_problemas_remediados"].index,
        details_dir,
        summary_filename,
        "remediado_",
        squad_reports_base_name,
        timestamp_str,
    )
    gerar_paginas_detalhe_problema(
        summary,
        dashboard_context["top_problemas_geral"].index,
        details_dir,
        summary_filename,
        "geral_",
        squad_reports_base_name,
        timestamp_str,
    )
    gerar_paginas_detalhe_problema(
        summary[summary["acao_sugerida"].isin(ACAO_FLAGS_INSTABILIDADE)],
        dashboard_context["top_problemas_instabilidade"].index,
        details_dir,
        summary_filename,
        "instabilidade_",
        squad_reports_base_name,
        timestamp_str,
    )
    gerar_paginas_detalhe_metrica(
        df_atuacao,
        dashboard_context["top_metrics"].index,
        details_dir,
        summary_filename,
        squad_reports_base_name,
        timestamp_str,
    )

    # Gera páginas de planos de ação e visualizadores de CSV
    gerar_relatorios_por_squad(df_atuacao, squad_reports_dir, timestamp_str)
    gerar_pagina_squads(
        dashboard_context["all_squads"], squad_reports_dir, output_dir, summary_filename, timestamp_str
    )

    # REFATORAÇÃO: Centraliza a geração de relatórios de visualização de CSV.
    reports_to_generate = [
        ("remediados.csv", FILENAME_SUCCESS, "Sucesso da Automação"),
        ("remediados_frequentes.csv", FILENAME_INSTABILITY, "Instabilidade Crônica"),
    ]
    if analysis_results["num_logs_invalidos"] > 0:
        reports_to_generate.append(
            (LOG_INVALIDOS_FILENAME, FILENAME_INVALID_LOGS_HTML, "Checar Dados (Logs Inválidos)")
        )
    _gerar_relatorios_csv_viewer(reports_to_generate, output_dir, frontend_url)

    # Gera os planos de ação por squad e o plano de ação geral (atuar.html).
    gerar_paginas_atuar_por_squad(df_atuacao, output_dir, frontend_url)

    logger.info("Geração do ecossistema de relatórios HTML concluída.")
    return summary_html_path


def carregar_template_html(filepath: str) -> str:
    """Carrega o conteúdo de um arquivo de template HTML de forma segura."""
    logger.info(f"Carregando template de '{filepath}'...")
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(
            f"O arquivo de template HTML '{filepath}' não foi encontrado."
        )
    except Exception as e:
        raise IOError(f"Erro inesperado ao ler o arquivo de template '{filepath}': {e}")


def gerar_resumo_executivo(
    context: dict, output_path: str, timestamp_str: str, frontend_url: str = "/"
):  # type: ignore
    """Gera o dashboard principal em HTML com base em um contexto de dados pré-construído."""
    logger.info("Gerando Resumo Executivo estilo Dashboard...")

    title = "Dashboard - Análise de Alertas"

    # Renderiza o corpo do HTML usando o contexto fornecido
    body_content = gerador_html.renderizar_resumo_executivo(context, frontend_url)

    # Carrega o template principal
    # CORREÇÃO: Usa um caminho absoluto para o template, garantindo que funcione no contêiner.
    HTML_TEMPLATE = carregar_template_html(os.path.join(BASE_TEMPLATE_DIR, MAIN_TEMPLATE))

    # Renderiza a página final e a salva
    footer_text = f"Relatório gerado em {timestamp_str}"
    html_content = gerador_html.renderizar_template_string(
        template_string=HTML_TEMPLATE,
        title=title,
        body_content=body_content,
        footer_text=footer_text,
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    logger.info(f"Resumo executivo gerado: {output_path}")

    output_dir = os.path.dirname(output_path)
    try:
        with open(
            os.path.join(output_dir, FILENAME_JSON_SUMMARY), "r", encoding="utf-8"
        ) as f:
            json_content = f.read()
        html_visualizador = gerador_html.renderizar_visualizador_json(json_content)
        with open(
            os.path.join(output_dir, FILENAME_JSON_VIEWER), "w", encoding="utf-8"
        ) as f:
            f.write(html_visualizador)
        logger.info("Visualizador de JSON gerado: visualizador_json.html")
    except Exception as e:
        logger.warning(
            f"Não foi possível ler o arquivo JSON para o visualizador. Erro: {e}"
        )


def gerar_relatorios_por_squad(  # type: ignore
    df_atuacao: pd.DataFrame, output_dir: str, timestamp_str: str
):
    """Gera arquivos de relatório detalhado para cada squad com Casos que precisam de atuação."""
    logger.info("Gerando relatórios detalhados por squad...")
    if df_atuacao.empty:
        logger.info("Nenhum caso precisa de atuação. Nenhum relatório de squad gerado.")
        return

    os.makedirs(output_dir, exist_ok=True)
    emoji_map = {
        ACAO_INTERMITENTE: "⚠️",
        ACAO_FALHA_PERSISTENTE: "❌",
        ACAO_STATUS_AUSENTE: "❓",
        ACAO_INCONSISTENTE: "🔍",
    }
    footer_text = f"Relatório gerado em {timestamp_str}"

    # CORREÇÃO: Usa um caminho absoluto para o template, garantindo que funcione no contêiner.
    HTML_TEMPLATE = carregar_template_html(os.path.join(BASE_TEMPLATE_DIR, MAIN_TEMPLATE))

    for squad_name, squad_df in df_atuacao.groupby(COL_ASSIGNMENT_GROUP, observed=True):
        if squad_df.empty:
            continue

        # CORREÇÃO: Restaurado o nome e caminho originais para os relatórios de squad.
        # Esta função gera os relatórios detalhados (squad-*.html), não os planos de ação.
        sanitized_name = re.sub(r"[^a-zA-Z0-9_-]", "", squad_name.replace(" ", "_"))
        # Garante que o diretório de squads exista.
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"squad-{sanitized_name}.html")
        title = f"Relatório da Squad: {escape(squad_name)}"
        total_alertas = squad_df["alert_count"].sum()

        body_content = '<p><a href="../todas_as_squads.html">&larr; Voltar para Lista de Squads</a></p>'
        body_content += f'<h2>Visão Geral da Squad - {escape(squad_name)}</h2><div class="grid-container">'
        body_content += f'<div class="card kpi-card"><p class="kpi-value" style="color: var(--warning-color);">{len(squad_df)}</p><p class="kpi-label">Total de Casos</p></div>'
        body_content += f'<div class="card kpi-card"><p class="kpi-value">{total_alertas}</p><p class="kpi-label">Total de Alertas Envolvidos</p></div></div>'
        top_problemas_da_squad = (
            squad_df.groupby(COL_SHORT_DESCRIPTION, observed=True)["alert_count"]
            .sum()
            .nlargest(10)
        )
        body_content += '<div class="card" style="margin-top: 20px;"><h3>Top Problemas da Squad</h3>'
        if not top_problemas_da_squad.empty:
            body_content += '<div class="bar-chart-container">'
            min_prob_val, max_prob_val = (
                top_problemas_da_squad.min(),
                top_problemas_da_squad.max(),
            )
            for problem, count in top_problemas_da_squad.items():
                bar_width = (count / max_prob_val) * 100 if max_prob_val > 0 else 0
                background_color, text_color = gerador_html.gerar_cores_para_barra(
                    count, min_prob_val, max_prob_val
                )
                body_content += f'<div class="bar-item"><div class="bar-label" title="{escape(problem)}">{escape(problem)}</div><div class="bar-wrapper"><div class="bar" style="width: {bar_width}%; background-color: {background_color}; color: {text_color};">{count}</div></div></div>'
            body_content += "</div>"
        else:
            body_content += "<p>Nenhum problema recorrente para esta squad. ✅</p>"
        body_content += "</div>"
        body_content += "<h2>Detalhes por Categoria de Métrica</h2>"

        row_index = 0
        metric_priority = (
            squad_df.groupby(COL_METRIC_NAME, observed=True)["score_ponderado_final"]
            .max()
            .sort_values(ascending=False)
        )
        for metric_name in metric_priority.index:
            metric_group_df = squad_df[squad_df[COL_METRIC_NAME] == metric_name]
            num_problems_in_metric = metric_group_df[COL_SHORT_DESCRIPTION].nunique()
            body_content += f'<button type="button" class="collapsible collapsible-metric"><span class="emoji">📁</span>{escape(metric_name)}<span class="instance-count">{num_problems_in_metric} {"tipos de problema" if num_problems_in_metric > 1 else "tipo de problema"}</span></button><div class="metric-content">'
            problem_priority = (
                metric_group_df.groupby(COL_SHORT_DESCRIPTION, observed=True)[
                    "score_ponderado_final"
                ]
                .max()
                .sort_values(ascending=False)
            )
            for problem_desc in problem_priority.index:
                problem_group_df = metric_group_df[
                    metric_group_df[COL_SHORT_DESCRIPTION] == problem_desc
                ]
                if problem_group_df.empty:
                    continue
                acao_principal = problem_group_df["acao_sugerida"].iloc[0]
                emoji = emoji_map.get(acao_principal, "⚙️")
                num_instances = len(problem_group_df)
                total_alertas_problema = problem_group_df["alert_count"].sum()
                body_content += f"""
                <button type="button" class="collapsible collapsible-problem">
                    <span class="emoji">{emoji}</span>
                    {escape(problem_desc)}
                    <span class="instance-count">{num_instances} {"Casos" if num_instances > 1 else "caso"} / {total_alertas_problema} alertas</span>
                </button>
                <div class="content">
                    <table>
                        <thead>
                            <tr>
                                <th class="priority-col">Prioridade</th>
                                <th>Recurso (CI) / Nó</th>
                                <th>Ação Sugerida</th>
                                <th>Período</th>
                                <th>Alertas</th>
                            </tr>
                        </thead>
                        <tbody>
                """
                problem_group_df = problem_group_df.sort_values(
                    by="alert_count", ascending=False
                )
                for _, row in problem_group_df.iterrows():
                    row_index += 1
                    target_id = f"details-row-{row_index}"
                    recurso_info = f"<strong>{escape(row[COL_CMDB_CI])}</strong>"
                    if row[COL_NODE] != row[COL_CMDB_CI]:
                        recurso_info += f"<br><small style='color:var(--text-secondary-color)'>{escape(row[COL_NODE])}</small>"
                    acao_info = f"<span class='emoji'>{emoji_map.get(row['acao_sugerida'], '⚙️')}</span> {escape(str(row['acao_sugerida']))}"
                    periodo_info = f"{row['first_event'].strftime('%d/%m %H:%M')} a<br>{row['last_event'].strftime('%d/%m %H:%M')}"
                    priority_score_html = f"<td class='priority-col' style='color: {gerador_html.gerar_cores_para_barra(row['score_ponderado_final'], 0, 20)[0]};'>{row['score_ponderado_final']:.1f}</td>"
                    body_content += f'<tr class="expandable-row" data-target="#{target_id}">{priority_score_html}<td>{recurso_info}</td><td>{acao_info}</td><td>{periodo_info}</td><td>{row["alert_count"]}</td></tr>'
                    status_emoji_map = {
                        "REM_OK": "✅",
                        "REM_NOT_OK": "❌",
                        "NO_STATUS": "❓",
                    }
                    # NOVO: Mapa de emojis para os status de tasks
                    task_status_emoji_map = {
                        "Closed": "✅",
                        "Closed Incomplete": "❌",
                        "Closed Skipped": "⏭️",
                        "Canceled": "🚫",
                        "Open": "⏳",
                        "No Task Found": "❓",
                    }
                    formatted_chronology = []
                    for status in row["status_chronology"]:
                        # A validação de dados agora ocorre na carga, então aqui apenas formatamos.
                        emoji = task_status_emoji_map.get(status, "⚪")
                        formatted_chronology.append(f"{emoji} {escape(str(status))}")

                    cronologia_info = f"<code>{' → '.join(formatted_chronology)}</code>"
                    alertas_info = f"<code>{escape(row['alert_numbers'])}</code>"
                    body_content += f'<tr id="{target_id}" class="details-row"><td colspan="5"><div class="details-row-content"><p><strong>Alertas Envolvidos ({row["alert_count"]}):</strong> {alertas_info}</p><p><strong>Cronologia:</strong> {cronologia_info}</p></div></td></tr>'
                body_content += "</tbody></table></div>" # Fim da tabela de um problema
            body_content += "</div>" # Fim do metric-content
        html_content = gerador_html.renderizar_template_string(
            template_string=HTML_TEMPLATE, title=title, body_content=body_content, footer_text=footer_text
        )
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        logger.info(f"Relatório para a squad '{squad_name}' gerado: {output_path}")


def gerar_pagina_squads(  # type: ignore
    all_squads: pd.Series,
    squad_reports_dir: str,
    output_dir: str,
    summary_filename: str, # noqa: E501
    timestamp_str: str,
):
    """Gera uma página HTML com o gráfico de barras para todas as squads com Casos em aberto."""
    logger.info("Gerando página com a lista completa de squads...")
    output_path = os.path.join(output_dir, FILENAME_ALL_SQUADS)
    title = "Lista Completa de Squads por Casos"
    body_content = f'<p><a href="{summary_filename}">&larr; Voltar para o Dashboard</a></p><div class="card">'
    squads_com_casos = all_squads[all_squads > 0]
    body_content += f"<h3>{title} ({len(squads_com_casos)} squads)</h3>"
    if not squads_com_casos.empty:
        body_content += '<div class="bar-chart-container">'
        min_val, max_val = squads_com_casos.min(), squads_com_casos.max()
        squad_reports_base_dir = os.path.basename(squad_reports_dir)
        for squad, count in squads_com_casos.items():
            bar_width = (count / max_val) * 100 if max_val > 0 else 0
            background_color, text_color = gerador_html.gerar_cores_para_barra(
                count, min_val, max_val
            )
            sanitized_name = re.sub(r"[^a-zA-Z0-9_-]", "", squad.replace(" ", "_"))
            report_path = os.path.join(
                squad_reports_base_dir, f"squad-{sanitized_name}.html"
            )
            body_content += f"""
            <div class="bar-item">
                <div class="bar-label"><a href="{report_path}" title="Ver relatório para {escape(squad)}">{escape(squad)}</a></div>
                <div class="bar-wrapper">
                    <div class="bar" style="width: {bar_width}%; background-color: {background_color}; color: {text_color};">{count}</div>
                </div>
            </div>"""
        body_content += "</div>"
    else:
        body_content += "<p>Nenhuma squad com Casos a serem listados. ✅</p>"
    body_content += "</div>"
    footer_text = f"Relatório gerado em {timestamp_str}"

    # CORREÇÃO: Usa um caminho absoluto para o template, garantindo que funcione no contêiner.
    HTML_TEMPLATE = carregar_template_html(os.path.join(BASE_TEMPLATE_DIR, MAIN_TEMPLATE))

    html_content = gerador_html.renderizar_template_string(
        template_string=HTML_TEMPLATE, title=title, body_content=body_content, footer_text=footer_text
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    logger.info(f"Página de squads gerada: {output_path}")


def gerar_paginas_detalhe_problema(  # type: ignore
    df_source: pd.DataFrame,
    problem_list: pd.Index,
    output_dir: str,
    summary_filename: str,
    file_prefix: str,
    squad_reports_dir_name: str,
    timestamp_str: str,
):
    """Gera páginas de detalhe para uma lista de problemas específicos."""
    if problem_list.empty:
        return
    os.makedirs(output_dir, exist_ok=True)
    emoji_map = {
        ACAO_INTERMITENTE: "⚠️",
        ACAO_FALHA_PERSISTENTE: "❌",
        ACAO_STATUS_AUSENTE: "❓",
        ACAO_INCONSISTENTE: "🔍",
        ACAO_SEMPRE_OK: "✅",
        ACAO_ESTABILIZADA: "✅",
        "🔁": "🔁",
    }

    # CORREÇÃO: Usa um caminho absoluto para o template, garantindo que funcione no contêiner.
    HTML_TEMPLATE = carregar_template_html(os.path.join(BASE_TEMPLATE_DIR, MAIN_TEMPLATE))
    footer_text = f"Relatório gerado em {timestamp_str}"

    logger.info(f"Gerando páginas de detalhe para o contexto: '{file_prefix}'...")
    for problem_desc in problem_list:
        sanitized_name = re.sub(
            r"[^a-zA-Z0-9_-]", "", problem_desc[:50].replace(" ", "_")
        )
        output_path = os.path.join(
            output_dir, f"detalhe_{file_prefix}{sanitized_name}.html"
        )
        problem_df = df_source[
            df_source[COL_SHORT_DESCRIPTION] == problem_desc
        ].sort_values(by="alert_count", ascending=False)
        if problem_df.empty:
            continue
        total_alerts = problem_df["alert_count"].sum()
        total_instances = len(problem_df)
        title = f"Resumo do Problema: {escape(problem_desc)}"
        body_content = f'<p><a href="../{summary_filename}">&larr; Voltar para o Dashboard</a></p><h2>{escape(problem_desc)}</h2><p>Total de alertas: <strong>{total_alerts}</strong> | Casos distintos: <strong>{total_instances}</strong></p>'
        body_content += "<table><thead><tr><th>Recurso (CI) / Nó</th><th>Ação Sugerida</th><th>Período</th><th>Total de Alertas</th><th>Squad</th></tr></thead><tbody>"
        for _, row in problem_df.iterrows():
            recurso_info = f"<strong>{escape(row[COL_CMDB_CI])}</strong>"
            if row[COL_NODE] != row[COL_CMDB_CI]:
                recurso_info += f"<br><small style='color:var(--text-secondary-color)'>{escape(row[COL_NODE])}</small>"
            acao_sugerida = row.get("acao_sugerida", UNKNOWN)
            acao_info = f"<span class='emoji'>{emoji_map.get(acao_sugerida, '⚙️')}</span> {escape(str(acao_sugerida))}"
            periodo_info = f"{row['first_event'].strftime('%d/%m %H:%M')} a<br>{row['last_event'].strftime('%d/%m %H:%M')}"
            squad_name = row[COL_ASSIGNMENT_GROUP]
            if acao_sugerida in ACAO_FLAGS_ATUACAO:
                sanitized_squad_name = re.sub(
                    r"[^a-zA-Z0-9_-]", "", squad_name.replace(" ", "_")
                )
                report_path = (
                    f"../{squad_reports_dir_name}/squad-{sanitized_squad_name}.html"
                )
                squad_info = f'<a href="{report_path}">{escape(squad_name)}</a>'
            else:
                squad_info = escape(squad_name)
            body_content += f"<tr><td>{recurso_info}</td><td>{acao_info}</td><td>{periodo_info}</td><td>{row['alert_count']}</td><td>{squad_info}</td></tr>"
        body_content += "</tbody></table>" # Fim da tabela
        html_content = gerador_html.renderizar_template_string(
            template_string=HTML_TEMPLATE, title=title, body_content=body_content, footer_text=footer_text
        )
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
    logger.info(
        f"{len(problem_list)} páginas de detalhe do contexto '{file_prefix}' geradas."
    )


def gerar_paginas_detalhe_metrica(  # type: ignore
    df_atuacao_source: pd.DataFrame,
    metric_list: pd.Index,
    output_dir: str,
    summary_filename: str,
    squad_reports_dir_name: str,
    timestamp_str: str,
):
    """Gera páginas de detalhe para categorias de métricas com Casos em aberto."""
    if metric_list.empty:
        return
    os.makedirs(output_dir, exist_ok=True)
    emoji_map = {
        ACAO_INTERMITENTE: "⚠️",
        ACAO_FALHA_PERSISTENTE: "❌",
        ACAO_STATUS_AUSENTE: "❓",
        ACAO_INCONSISTENTE: "🔍",
    }

    # CORREÇÃO: Usa um caminho absoluto para o template, garantindo que funcione no contêiner.
    HTML_TEMPLATE = carregar_template_html(os.path.join(BASE_TEMPLATE_DIR, MAIN_TEMPLATE))
    footer_text = f"Relatório gerado em {timestamp_str}"

    logger.info("Gerando páginas de detalhe para Métricas em Aberto...")
    for metric_name in metric_list:
        sanitized_name = re.sub(r"[^a-zA-Z0-9_-]", "", metric_name.replace(" ", "_"))
        output_path = os.path.join(output_dir, f"detalhe_metrica_{sanitized_name}.html")
        metric_df = df_atuacao_source[
            df_atuacao_source[COL_METRIC_NAME] == metric_name
        ].sort_values(by="last_event", ascending=False)
        if metric_df.empty:
            continue
        total_instances = len(metric_df)
        title = f"Detalhe da Métrica em Aberto: {escape(metric_name)}"
        body_content = f'<p><a href="../{summary_filename}">&larr; Voltar para o Dashboard</a></p><h2>{escape(metric_name)}</h2><p>Total de Casos em aberto: <strong>{total_instances}</strong></p>'
        body_content += "<table><thead><tr><th>Recurso (CI) / Nó</th><th>Ação Sugerida</th><th>Período</th><th>Problema</th><th>Squad</th></tr></thead><tbody>"
        for _, row in metric_df.iterrows():
            recurso_info = f"<strong>{escape(row[COL_CMDB_CI])}</strong>"
            if row[COL_NODE] != row[COL_CMDB_CI]:
                recurso_info += f"<br><small style='color:var(--text-secondary-color)'>{escape(row[COL_NODE])}</small>"
            acao_sugerida = row.get("acao_sugerida", UNKNOWN)
            acao_info = f"<span class='emoji'>{emoji_map.get(acao_sugerida, '⚙️')}</span> {escape(str(acao_sugerida))}"
            periodo_info = f"{row['first_event'].strftime('%d/%m %H:%M')} a<br>{row['last_event'].strftime('%d/%m %H:%M')}"
            squad_name = row[COL_ASSIGNMENT_GROUP]
            sanitized_squad_name = re.sub(
                r"[^a-zA-Z0-9_-]", "", squad_name.replace(" ", "_")
            )
            report_path = (
                f"../{squad_reports_dir_name}/squad-{sanitized_squad_name}.html"
            )
            squad_info = f'<a href="{report_path}">{escape(squad_name)}</a>'
            problema_info = escape(row[COL_SHORT_DESCRIPTION])
            body_content += f"<tr><td>{recurso_info}</td><td>{acao_info}</td><td>{periodo_info}</td><td>{problema_info}</td><td>{squad_info}</td></tr>" # Fim da linha
        body_content += "</tbody></table>" # Fim da tabela
        html_content = gerador_html.renderizar_template_string(
            template_string=HTML_TEMPLATE, title=title, body_content=body_content, footer_text=footer_text
        )
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
    logger.info(f"{len(metric_list)} páginas de detalhe de métricas geradas.")


def gerar_pagina_visualizacao_csv(
    output_dir: str,
    csv_filename: str,
    output_html_filename: str,
    page_title: str,
    frontend_url: str,
):
    """Gera uma página HTML genérica para visualização de um arquivo CSV."""
    csv_path = os.path.join(output_dir, csv_filename)
    output_html_path = os.path.join(output_dir, output_html_filename)
    # CORREÇÃO: Usa o template genérico e correto para visualizadores de CSV.
    viewer_template_path = os.path.join(BASE_TEMPLATE_DIR, "csv_viewer_template.html")

    logger.info(f"Gerando página de visualização para '{csv_filename}'...")

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            csv_content = f.read().lstrip()
    except FileNotFoundError:
        csv_content = ""
        logger.warning(f"Arquivo '{csv_path}' não encontrado. Gerando página vazia.")

    try:
        # Carrega o template do visualizador (que contém o placeholder para o CSV)
        template_str = carregar_template_html(viewer_template_path)

        # CORREÇÃO: Usa o renderizador Jinja2 em vez de .format() para evitar o KeyError.
        # Isso trata o CSS e os placeholders de forma segura.
        html_content = gerador_html.renderizar_template_string(
            template_string=template_str,
            page_title=page_title,
            csv_filename=csv_filename,
            back_link_url=frontend_url,
            csv_data_payload=csv_content.replace("`", "\\`"),  # Escapa para o JS
        )
        with open(output_html_path, "w", encoding="utf-8") as f_out:
            f_out.write(html_content)

    except FileNotFoundError:
        raise FileNotFoundError(
            f"Template '{viewer_template_path}' não encontrado."
        )
    logger.info(f"Página de visualização '{output_html_filename}' gerada: {output_html_path}")


def _gerar_relatorios_csv_viewer(reports_config: list, output_dir: str, frontend_url: str):
    """
    Função auxiliar para gerar múltiplos relatórios de visualização de CSV.

    Args:
        reports_config (list): Uma lista de tuplas, onde cada tupla contém
                               (csv_filename, output_html_filename, page_title).
        output_dir (str): O diretório de saída para os relatórios.
        frontend_url (str): A URL base do frontend para links de retorno.
    """
    for csv_filename, output_html_filename, page_title in reports_config:
        gerar_pagina_visualizacao_csv(
            output_dir=output_dir,
            csv_filename=csv_filename,
            output_html_filename=output_html_filename,
            page_title=page_title,
            frontend_url=frontend_url,
        )


def gerar_paginas_atuar_por_squad(
    df_atuacao: pd.DataFrame, output_dir: str, frontend_url: str
):
    """Gera arquivos de atuação (CSV e HTML) filtrados para cada squad."""
    if df_atuacao.empty:
        return

    logger.info("Gerando páginas de atuação filtradas por squad...")
    viewer_template_path = os.path.join(BASE_TEMPLATE_DIR, "csv_viewer_template.html")

    template_content = carregar_template_html(viewer_template_path)
    # NOVO: Mapa de emojis para prefixar a ação sugerida no CSV.
    full_emoji_map = {
        ACAO_INTERMITENTE: "⚠️",
        ACAO_FALHA_PERSISTENTE: "❌",
        ACAO_STATUS_AUSENTE: "❓",
        ACAO_INCONSISTENTE: "🔍",
        ACAO_SEMPRE_OK: "✅",
        ACAO_ESTABILIZADA: "⚠️✅",
        ACAO_INSTABILIDADE_CRONICA: "🔁",
    }

    for squad_name, squad_df in df_atuacao.groupby(COL_ASSIGNMENT_GROUP, observed=True):
        if squad_df.empty:
            continue

        sanitized_name = re.sub(r"[^a-zA-Z0-9_-]", "", squad_name.replace(" ", "_"))
        # CORREÇÃO: Define o diretório e o nome do arquivo corretamente.
        planos_dir = os.path.join(output_dir, REPORTS_DIR_PLANS)
        os.makedirs(planos_dir, exist_ok=True)
        csv_filename = f"plano-de-acao-{sanitized_name}.csv"
        html_filename = f"plano-de-acao-{sanitized_name}.html"
        csv_path = os.path.join(planos_dir, csv_filename)
        html_path = os.path.join(planos_dir, html_filename)

        df_to_save = squad_df.copy()
        # REUTILIZAÇÃO: Usa a função _save_csv para garantir a consistência
        # na formatação e seleção de colunas.
        _save_csv(
            df_to_save, csv_path, "score_ponderado_final", full_emoji_map, False
        )

        # 2. Gera o HTML correspondente
        # CORREÇÃO: Lê o conteúdo do CSV recém-criado para injetar no HTML.
        with open(csv_path, "r", encoding="utf-8") as f:
            csv_content = f.read().lstrip()

        # CORREÇÃO: Usa o renderizador Jinja2 em vez de .format() para evitar o KeyError. # noqa: E501
        final_html = gerador_html.renderizar_template_string(
            template_string=template_content,
            page_title=f"Plano de Ação: {squad_name}",
            csv_filename=csv_filename,
            back_link_url="../resumo_geral.html",  # CORREÇÃO: Usa um caminho relativo para voltar ao dashboard do relatório.
            # Escapa para o JS
            csv_data_payload=csv_content.replace("`", "\\`"),
        )

        with open(html_path, "w", encoding="utf-8") as f_out:
            f_out.write(final_html)

    # Adicional: Gera o arquivo atuar.html geral, se houver dados.
    geral_atuar_csv_path = os.path.join(output_dir, "atuar.csv")
    csv_content = ""  # Garante que a variável seja reiniciada
    if os.path.exists(geral_atuar_csv_path):
        with open(geral_atuar_csv_path, "r", encoding="utf-8") as f:
            csv_content = f.read().lstrip()

        if len(csv_content.splitlines()) > 1:
            atuar_html_path = os.path.join(output_dir, FILENAME_ACTION_PLAN)
            # CORREÇÃO: Usa o renderizador Jinja2 em vez de .format() para evitar o KeyError. # noqa: E501
            final_html = gerador_html.renderizar_template_string(
                template_string=template_content,
                page_title="Plano de Ação Geral",
                csv_filename="atuar.csv",
                back_link_url=frontend_url,  # CORREÇÃO: Aponta para a raiz da SPA
                # Escapa para o JS
                csv_data_payload=csv_content.replace("`", "\\`"),
            )

            with open(atuar_html_path, "w", encoding="utf-8") as f_out:
                f_out.write(final_html)

    logger.info("Páginas de atuação (geral e por squad) geradas com sucesso.")
