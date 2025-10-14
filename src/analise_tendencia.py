import pandas as pd
import os
import json
from html import escape
import logging
import re
from string import Template
from .constants import ACAO_FLAGS_ATUACAO

logger = logging.getLogger(__name__)

CASE_ID_COLS = [
    "assignment_group",
    "short_description",
    "node",
    "cmdb_ci",
    "source",
    "metric_name",
    "cmdb_ci.sys_class_name",
]


def sanitize_for_id(text):
    """Cria uma string segura para ser usada como ID HTML."""
    return re.sub(r"[^a-zA-Z0-9\-_]", "-", str(text)).lower()


def load_summary_from_json(filepath: str):
    """
    Carrega o resumo de problemas de um arquivo JSON,
    suportando o novo formato com cabeçalho e o formato antigo (apenas records).
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Verifica se o JSON tem o novo formato com 'header' e 'records'
        if isinstance(data, dict) and "records" in data:
            df = pd.DataFrame(data["records"])
        # Assume que é o formato antigo (uma lista de records)
        else:
            df = pd.DataFrame(data)

        # Converte colunas de data que podem ter sido salvas como strings
        if "first_event" in df.columns:
            df["first_event"] = pd.to_datetime(df["first_event"], errors="coerce")
        if "last_event" in df.columns:
            df["last_event"] = pd.to_datetime(df["last_event"], errors="coerce")

        logger.info(f"Resumo de problemas carregado de: {filepath}")
        return df
    except (FileNotFoundError, ValueError, TypeError) as e:
        logger.error(f"Erro ao carregar ou processar o arquivo JSON '{filepath}': {e}")
        return None


def generate_executive_summary_html(
    kpis, persistent_summary, new_cases_summary, is_direct_comparison: bool
):
    """Gera um resumo executivo com os principais insights e pontos de ação."""
    verdict_text = ""
    verdict_class = "highlight-neutral"

    # 1. O Veredito Geral - A ordem das condições é importante
    if kpis["total_p1"] == 0 and kpis["total_p2"] > 0:
        verdict_text = "⚠️ <strong>Primeira Regressão:</strong> A operação, que estava estável, registrou o surgimento de novos problemas. É um ponto de atenção crítico para evitar a degradação do serviço."
        verdict_class = "highlight-warning"
    elif kpis["total_p2"] == 0 and kpis["total_p1"] > 0:
        verdict_text = "🏆 <strong>Excelência Operacional Atingida:</strong> Todos os casos do período anterior foram resolvidos e nenhum problema novo surgiu. A operação atingiu um estado de estabilidade ideal."
        verdict_class = "highlight-success"
    elif kpis["total_p2"] > kpis["total_p1"]:
        verdict_text = "❌ <strong>Regressão:</strong> O número total de casos que exigem ação aumentou. A piora é uma combinação de problemas persistentes não resolvidos e o surgimento de novos. É crucial atacar ambas as frentes para reverter a tendência."
        verdict_class = "highlight-danger"
    elif kpis["resolved"] > 0 and (kpis["new"] / kpis["resolved"]) > 0.75:
        ponto_positivo_texto = (
            "<strong>Todos os casos</strong> do período anterior foram resolvidos."
            if kpis["improvement_rate"] == 100
            else "Alta eficácia na resolução de casos do período anterior."
        )
        verdict_text = (
            """⚠️ <strong>Alta Eficácia | Baixa Estabilidade:</strong><br>
        <span style="display: block; margin-top: 10px; font-size: 0.95em;">A análise mostra dois pontos distintos:<ul><li style="color: var(--success-color);"><strong>Ponto Positivo:</strong> """
            + ponto_positivo_texto
            + """</li><li style="color: var(--danger-color);"><strong>Ponto de Atenção:</strong> A operação continua instável, gerando <strong>"""
            + str(kpis["new"])
            + """ novos casos</strong> que precisam de atuaçao - tratar causa raiz ou criar remediação.</li></ul></span>"""
        )
        verdict_class = "highlight-warning"
    elif kpis["total_p2"] < kpis["total_p1"]:
        verdict_text = "✅ <strong>Evolução Positiva:</strong> O número total de casos diminuiu e a quantidade de novos problemas foi controlada. A operação está se tornando mais estável e eficiente."
        verdict_class = "highlight-success"
    elif kpis["total_p1"] == kpis["total_p2"] and kpis["resolved"] == 0:
        verdict_text = "⚠️ <strong>Estagnação por Inércia:</strong> O número de casos não mudou porque os problemas antigos não foram resolvidos. A ação de causa raiz é necessária."
        verdict_class = "highlight-warning"
    else:
        verdict_text = "➖ <strong>Estabilidade Neutra:</strong> O número total de casos permaneceu o mesmo, com uma troca equilibrada entre problemas resolvidos e novos."
        verdict_class = "highlight-info"

    # 2. Principal Ponto de Ação (Foco no maior problema)
    action_point = ""
    if not new_cases_summary.empty:
        top_new_squad = new_cases_summary.groupby("assignment_group").size().idxmax()
        sanitized_squad_name = re.sub(
            r"[^a-zA-Z0-9_-]", "", top_new_squad.replace(" ", "_")
        )
        squad_highlight_html = (
            f'<span style="color: var(--danger-color);">{escape(top_new_squad)}</span>'
        )
        if is_direct_comparison:
            action_point = f"<li>🔥 <strong>Ponto de Ação Principal:</strong> Squad<strong> '{squad_highlight_html}'</strong> registrou o maior número de casos sem remediação recentemente. Focar a investigação nesta equipe."
        else:
            # CORREÇÃO: Aponta para o novo caminho e nome do arquivo de plano de ação.
            action_plan_url = f"planos_de_acao/plano-de-acao-{sanitized_squad_name}.html?back=../comparativo_periodos.html"
            action_point = f'<li>🔥 <strong>Ponto de Ação Principal:</strong> Squad<strong> \'{squad_highlight_html}\'</strong> registrou o maior número de casos sem remediação recentemente. <a href="{action_plan_url}" style="font-weight: 600;">Ver Plano de Ação.</a>'
    elif not persistent_summary.empty:
        top_persistent_squad = persistent_summary.index[0]
        sanitized_squad_name = re.sub(
            r"[^a-zA-Z0-9_-]", "", top_persistent_squad.replace(" ", "_")
        )
        squad_highlight_html = f'<span style="color: var(--warning-color);">{escape(top_persistent_squad)}</span>'
        if is_direct_comparison:
            action_point = f"<li>🔥 <strong>Ponto de Ação Principal:</strong> Squad<strong> '{squad_highlight_html}'</strong> concentra o maior número de problemas persistentes. Ação de causa raiz é necessária."
        else:
            # CORREÇÃO: Aponta para o novo caminho e nome do arquivo de plano de ação.
            action_plan_url = f"planos_de_acao/plano-de-acao-{sanitized_squad_name}.html?back=../comparativo_periodos.html"
            action_point = f'<li>🔥 <strong>Ponto de Ação Principal:</strong> Squad<strong> \'{squad_highlight_html}\'</strong> concentra o maior número de problemas persistentes. <a href="{action_plan_url}" style="font-weight: 600;">Ver Plano de Ação.</a>'

    # 3. Principal Vitória (Reconhecimento)
    recognition_point = ""
    if kpis["resolved"] > 0:
        recognition_point = f"<li>✅ <strong>Principal Vitória:</strong> <strong>{kpis['resolved']} casos</strong> foram resolvidos desde o período anterior, demonstrando evolução com as remediações."

    # 4. Link para o Plano de Ação Geral
    general_action_plan_link = ""
    if not is_direct_comparison:
        # CORREÇÃO: Adiciona o parâmetro 'back' para a navegação contextual.
        action_url = "atuar.html?back=comparativo_periodos.html"
        general_action_plan_link = f'<li>📋 <strong>Plano de Ação Geral:</strong> <a href="{action_url}" style="font-weight: 600;">Ver todos os casos que necessitam de ação.</a>'

    summary_html = f"""
    <div class="card highlight {verdict_class}" style="margin-bottom: 30px;">
        <h2 style="margin-top: 0; border: none;">Diagnóstico Rápido</h2>
        <p style="font-size: 1.1em; margin-bottom: 20px;">{verdict_text}</p>
        <ul style="text-align: left; padding-left: 20px; font-size: 1.05em; line-height: 1.8;">
            {action_point}
            {recognition_point}
            {general_action_plan_link}
        </ul>
    </div>
    """
    return summary_html


def calculate_kpis_and_merged_df(df_p1_atuacao, df_p2_atuacao):
    """
    Calcula os KPIs e retorna o DataFrame mesclado com base nos dados de atuação.
    """
    valid_case_id_cols = [
        c
        for c in CASE_ID_COLS
        if c in df_p1_atuacao.columns and c in df_p2_atuacao.columns
    ]
    merged_df = pd.merge(
        df_p1_atuacao,
        df_p2_atuacao,
        on=valid_case_id_cols,
        how="outer",
        suffixes=("_p1", "_p2"),
        indicator=True,
    )

    total_p1 = len(df_p1_atuacao)
    total_p2 = len(df_p2_atuacao)
    resolved = merged_df["_merge"].eq("left_only").sum()
    new = merged_df["_merge"].eq("right_only").sum()
    persistent = merged_df["_merge"].eq("both").sum()

    alerts_total_p1 = df_p1_atuacao["alert_count"].sum()
    alerts_total_p2 = df_p2_atuacao["alert_count"].sum()
    alerts_resolved = merged_df.loc[
        merged_df["_merge"] == "left_only", "alert_count_p1"
    ].sum()
    alerts_new = merged_df.loc[
        merged_df["_merge"] == "right_only", "alert_count_p2"
    ].sum()
    alerts_persistent = merged_df.loc[
        merged_df["_merge"] == "both", "alert_count_p2"
    ].sum()
    alerts_persistent_p1 = merged_df.loc[
        merged_df["_merge"] == "both", "alert_count_p1"
    ].sum()

    improvement_rate = (resolved / total_p1 * 100) if total_p1 > 0 else 0
    regression_rate = (new / total_p2 * 100) if total_p2 > 0 else 0

    kpis = {
        "total_p1": total_p1,
        "resolved": resolved,
        "new": new,
        "total_p2": total_p2,
        "persistent": persistent,
        "alerts_total_p1": int(alerts_total_p1),
        "alerts_total_p2": int(alerts_total_p2),
        "alerts_resolved": int(alerts_resolved),
        "alerts_new": int(alerts_new),
        "alerts_persistent": int(alerts_persistent),
        "alerts_persistent_p1": int(alerts_persistent_p1),
        "improvement_rate": improvement_rate,
        "regression_rate": regression_rate,
    }

    return kpis, merged_df


def prepare_trend_dataframes(merged_df, df_p1_atuacao, df_p2_atuacao):
    """Prepara todos os DataFrames necessários para o relatório de tendência."""

    # Casos novos
    new_cases_df = merged_df[merged_df["_merge"] == "right_only"].copy()
    new_problems_summary = (
        new_cases_df.groupby("short_description", observed=True)
        .agg(
            count_p2=("alert_count_p2", "sum"), num_cases=("short_description", "size")
        )
        .reset_index()
    )
    new_problems_summary["count_p1"] = 0

    # Casos resolvidos
    resolved_cases_df = merged_df[merged_df["_merge"] == "left_only"].copy()
    resolved_problems_summary = (
        resolved_cases_df.groupby("short_description", observed=True)
        .agg(
            count_p1=("alert_count_p1", "sum"), num_cases=("short_description", "size")
        )
        .reset_index()
    )
    resolved_problems_summary["count_p2"] = 0

    # Casos persistentes (com variação)
    persistent_cases_df = merged_df[merged_df["_merge"] == "both"].copy()
    varying_problems_summary = (
        persistent_cases_df.groupby("short_description", observed=True)
        .agg(
            count_p1=("alert_count_p1", "sum"),
            count_p2=("alert_count_p2", "sum"),
            num_cases=("short_description", "size"),
        )
        .reset_index()
    )

    # Análise de squads com casos persistentes
    persistent_squads_summary = analyze_persistent_cases(merged_df)

    # Tendências de alertas por squad
    squad_trends_p1 = (
        df_p1_atuacao.groupby("assignment_group", observed=True)
        .agg(count_p1=("alert_count", "sum"))
        .reset_index()
    )
    squad_trends_p2 = (
        df_p2_atuacao.groupby("assignment_group", observed=True)
        .agg(count_p2=("alert_count", "sum"), num_cases=("assignment_group", "size"))
        .reset_index()
    )
    squad_trends_merged = pd.merge(
        squad_trends_p1, squad_trends_p2, on="assignment_group", how="outer"
    ).fillna(0)
    squad_trends_merged["num_cases"] = squad_trends_merged["num_cases"].astype(int)

    return {
        "new_cases": new_cases_df,
        "new_problems_summary": new_problems_summary,
        "resolved_cases": resolved_cases_df,
        "resolved_problems_summary": resolved_problems_summary,
        "persistent_cases": persistent_cases_df,
        "varying_problems_summary": varying_problems_summary,
        "persistent_squads_summary": persistent_squads_summary,
        "squad_trends": squad_trends_merged,
    }


def analyze_persistent_cases(merged_df):
    """Analisa apenas os casos persistentes (existiam em ambos os períodos)."""
    persistent_df = merged_df[merged_df["_merge"] == "both"].copy()
    if persistent_df.empty:
        return pd.DataFrame()

    summary = (
        persistent_df.groupby("assignment_group")
        .agg(
            num_cases=("assignment_group", "size"),
            alerts_p1=("alert_count_p1", "sum"),
            alerts_p2=("alert_count_p2", "sum"),
        )
        .fillna(0)
        .astype(int)
    )
    summary["change"] = summary["alerts_p2"] - summary["alerts_p1"]
    summary["abs_change"] = summary["change"].abs()
    return summary.sort_values(by=["num_cases", "abs_change"], ascending=[False, False])


def generate_kpis_html(kpis):
    """Gera o HTML para a seção de KPIs do panorama geral."""
    saldo_icon = ""

    if kpis["total_p2"] > kpis["total_p1"]:
        saldo_icon = (
            "<span style='font-size: 0.7em; color: var(--danger-color);'>▲</span>"
        )
    elif kpis["total_p2"] < kpis["total_p1"]:
        saldo_icon = (
            "<span style='font-size: 0.7em; color: var(--success-color);'>▼</span>"
        )

    # Calcula a variação de alertas nos casos persistentes para exibição no funil
    persistent_alerts_variation = (
        kpis["alerts_persistent"] - kpis["alerts_persistent_p1"]
    )
    variation_text = ""
    if persistent_alerts_variation != 0:
        sign = "+" if persistent_alerts_variation > 0 else ""
        color = (
            "var(--danger-color)"
            if persistent_alerts_variation > 0
            else "var(--success-color)"
        )
        variation_text = f' <span style="font-weight: 600; color: {color};">({sign}{persistent_alerts_variation})</span>'

    kpi_html = "<h2>Balanço Operacional: O Fluxo de Casos</h2>"
    kpi_html += "<div class='definition-box'><strong>Definição:</strong> Um 'Caso' é um problema único que precisa de ação. O fluxo abaixo mostra a evolução do número de casos e do volume total de alertas entre os dois períodos.</div>"

    kpi_html += f"""
    <div class="kpi-flow-container">
        <div class="kpi-flow-item"><div class="kpi-card-enhanced">
            <p class="kpi-value" style="color: var(--info-color);">{kpis["total_p1"]}</p>
            <p class="kpi-label">Casos em Aberto (Anterior)</p>
            <p class="kpi-subtitle" title="Total de problemas únicos do período anterior que não possuíam remediação bem-sucedida e exigiam ação.">{kpis["alerts_total_p1"]} alertas</p>
        </div></div>
        <div class="kpi-flow-connector icon-minus"></div>
        <div class="kpi-flow-group">
            <div class="kpi-flow-item" style="flex:auto;"><div class="kpi-card-enhanced">
                <p class="kpi-value" style="color: var(--success-color);">{kpis["resolved"]}</p>
                <p class="kpi-label">Casos Resolvidos</p>
                <p class="kpi-subtitle" title="Casos que passaram a ter remediação com sucesso (REM_OK) ou cujo volume de alertas foi zerado.">{kpis["alerts_resolved"]} alertas resolvidos</p>
            </div></div>
            <div class="kpi-flow-item" style="flex:auto;"><div class="kpi-card-enhanced">
                <p class="kpi-value" style="color: var(--persistent-color);">{kpis["persistent"]}</p>
                <p class="kpi-label">Casos Persistentes</p>
                <p class="kpi-subtitle" title="Problemas que já existiam e continuam sem remediação. O número de alertas reflete o volume do período recente, e a variação em parênteses mostra se o impacto desses problemas aumentou ou diminuiu.">{kpis["alerts_persistent"]} alertas{variation_text}</p>
            </div></div>
        </div>
        <div class="kpi-flow-connector icon-plus"></div>
        <div class="kpi-flow-item"><div class="kpi-card-enhanced">
            <p class="kpi-value" style="color: var(--warning-color);">{kpis["new"]}</p>
            <p class="kpi-label">Novos Casos</p>
            <p class="kpi-subtitle" title="Problemas que não existiam no período anterior e que surgiram no período recente já necessitando de ação.">{kpis["alerts_new"]} alertas</p>
        </div></div>
        <div class="kpi-flow-connector">=</div>
        <div class="kpi-flow-item"><div class="kpi-card-enhanced">
            <p class="kpi-value" style="color: {"var(--danger-color)" if kpis["total_p2"] > kpis["total_p1"] else "var(--success-color)"};">{saldo_icon} {kpis["total_p2"]}</p>
            <p class="kpi-label">Saldo Recente de Casos</p>
            <p class="kpi-subtitle" title="Resultado final: a soma dos Casos Persistentes com os Novos Casos. Representa o total de problemas que exigem ação neste período.">{kpis["alerts_total_p2"]} alertas</p>
        </div></div>
    </div>"""

    # Gera um insight dinâmico com base nos KPIs
    insight_text = ""
    if kpis["total_p1"] == 0 and kpis["total_p2"] > 0:
        insight_text = f"A operação estava estável e registrou <strong>{kpis['new']} novo(s) problema(s)</strong>. O foco deve ser em entender a causa dessa regressão."
    elif kpis["total_p2"] == 0:
        insight_text = "A operação atingiu um estado de <strong>zero casos</strong> que necessitam de ação. Um marco de excelência em estabilidade."
    elif kpis["resolved"] > kpis["new"]:
        insight_text = f"A equipe conseguiu resolver mais problemas do que os que surgiram (<strong>{kpis['resolved']} resolvidos</strong> vs. <strong>{kpis['new']} novos</strong>), resultando em uma melhora líquida na saúde operacional."
    else:
        insight_text = f"O número de <strong>novos problemas ({kpis['new']})</strong> foi maior ou igual ao de <strong>problemas resolvidos ({kpis['resolved']})</strong>. Isso indica que a operação está em um ciclo reativo, sem ganhos de estabilidade."

    kpi_html += f"""
    <div class="insight-box">
        💡 <strong>Análise e Insight:</strong> {insight_text}
    </div>"""

    # --- Card 1: Taxa de Resolução (Período Anterior) ---
    improvement_percent = kpis.get("improvement_rate", 0)
    resolved_count = kpis["resolved"]
    total_previous = kpis["total_p1"]

    imp_gauge_color = "var(--success-color)"
    imp_card_bg = "background-color: rgba(28, 200, 138, 0.1);"
    if improvement_percent < 75 and improvement_percent >= 50:
        imp_gauge_color = "var(--warning-color)"
        imp_card_bg = "background-color: rgba(246, 194, 62, 0.1);"
    elif improvement_percent < 50:
        imp_gauge_color = "var(--danger-color)"
        imp_card_bg = "background-color: rgba(231, 74, 59, 0.1);"

    # --- Card 2: Taxa de Novos Problemas (Período Recente) ---
    regression_percent = kpis.get("regression_rate", 0)
    new_count = kpis["new"]
    total_current = kpis["total_p2"]

    reg_gauge_color = "var(--danger-color)"
    reg_card_bg = "background-color: rgba(231, 74, 59, 0.1);"
    if regression_percent <= 25 and regression_percent > 10:
        reg_gauge_color = "var(--warning-color)"
        reg_card_bg = "background-color: rgba(246, 194, 62, 0.1);"
    elif regression_percent <= 10:
        reg_gauge_color = "var(--success-color)"
        reg_card_bg = "background-color: rgba(28, 200, 138, 0.1);"

    kpi_html += f"""
    <div class="kpi-grid-container">
        <div class="card kpi-split-layout" style="{imp_card_bg}">
            <div class="kpi-split-layout__chart">
                <div class="progress-donut" style="--p:{improvement_percent:.1f}; --c:{imp_gauge_color};">
                    <div class="progress-donut-text-content"><div class="progress-donut__value">{improvement_percent:.0f}%</div></div>
                </div>
            </div>
            <div class="kpi-split-layout__text">
                <h2>Taxa de Resolução (Período Anterior)</h2>
                <p>Dos <strong>{total_previous} casos</strong> que precisavam de ação, <strong>{resolved_count} foram resolvidos</strong>.</p>
                <small>Este KPI mede a eficácia na eliminação de problemas que já existiam.</small>
            </div>
        </div>
        <div class="card kpi-split-layout" style="{reg_card_bg}">
            <div class="kpi-split-layout__chart">
                <div class="progress-donut" style="--p:{regression_percent:.1f}; --c:{reg_gauge_color};">
                    <div class="progress-donut-text-content"><div class="progress-donut__value">{regression_percent:.0f}%</div></div>
                </div>
            </div>
            <div class="kpi-split-layout__text">
                <h2>Taxa de Novos Problemas (Período Recente)</h2>
                <p>Dos <strong>{total_current} casos</strong> atuais, <strong>{new_count} são novos</strong>, representando uma taxa de regressão.</p>
                <small>Este KPI mede a capacidade da operação de prevenir novos problemas.</small>
            </div>
        </div>
    </div>"""

    return kpi_html


def _generate_change_bar_html(change, max_abs_change):
    """Gera o HTML para uma barra de variação (positiva/negativa)."""
    change_sign = ""
    change_color = "var(--text-secondary-color)"

    if change > 0:
        bar_class = "negative"
        change_color = "var(--danger-color)"
        change_sign = "+"
    elif change < 0:
        bar_class = "positive"
        change_color = "var(--success-color)"
    else:
        bar_class = "neutral"

    bar_width = (abs(change) / max_abs_change * 100) if max_abs_change > 0 else 0

    return f"""
    <div class="change-bar-container">
        <div class="bar-wrapper"><div class="bar {bar_class}" style="width: {bar_width}%;"></div></div>
        <span class="change-value" style="color: {change_color}">{change_sign}{change:,.0f}</span>
    </div>"""


def generate_persistent_cases_table_html(summary_df, detailed_df, label_p1, label_p2):
    """Gera a tabela HTML para os casos persistentes por squad."""
    if summary_df.empty:
        return "<p>Nenhum caso persistente foi identificado. Ótimo trabalho!</p>"

    max_abs_change = summary_df["abs_change"].max() if not summary_df.empty else 1

    total_num_cases = summary_df["num_cases"].sum()
    total_alerts_p1 = summary_df["alerts_p1"].sum()
    total_alerts_p2 = summary_df["alerts_p2"].sum()
    total_change = summary_df["change"].sum()

    table_body = "<tbody>"
    chevron_svg = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" class="chevron"><polyline points="9 18 15 12 9 6"></polyline></svg>'

    for name, row in summary_df.iterrows():
        squad_id = sanitize_for_id(name)
        details_id = f"details-{squad_id}"
        num_cases, p1_count, p2_count, change = (
            row["num_cases"],
            row["alerts_p1"],
            row["alerts_p2"],
            row["change"],
        )
        bar_html = _generate_change_bar_html(change, max_abs_change)

        table_body += f"<tr class='expandable-row' data-target='{details_id}'>"
        table_body += f"<td><span style='display: flex; align-items: center; gap: 8px;'>{chevron_svg} {escape(str(name))}</span></td>"
        table_body += f"<td>{bar_html}</td><td class='center'>{p2_count}</td><td class='center'>{p1_count}</td><td class='center' style='font-weight: bold;'>{num_cases}</td></tr>"

        squad_cases_df = detailed_df[detailed_df["assignment_group"] == name]
        details_content = "<h4>Detalhes dos Casos Persistentes</h4><table class='sub-table'><thead><tr><th>Problema</th><th>Recurso Afetado</th><th>Alertas (Recente)</th><th>Alertas (Anterior)</th></tr></thead><tbody>"
        for _, case_row in squad_cases_df.iterrows():
            details_content += f"<tr><td>{escape(case_row['short_description'])}</td><td>{escape(case_row['cmdb_ci'])}</td><td>{int(case_row['alert_count_p2'])}</td><td>{int(case_row['alert_count_p1'])}</td></tr>"
        details_content += "</tbody></table>"

        table_body += f"<tr id='{details_id}' class='details-row'><td colspan='5'><div class='details-row-content'>{details_content}</div></td></tr>"
    table_body += "</tbody>"

    total_change_sign = "+" if total_change > 0 else ""
    total_change_color = (
        "var(--danger-color)"
        if total_change > 0
        else (
            "var(--success-color)"
            if total_change < 0
            else "var(--text-secondary-color)"
        )
    )

    table_footer = "<tfoot><tr><td>Total</td>"
    table_footer += f"<td><div class='change-bar-container'><span class='change-value' style='color: {total_change_color}; width: 100%; text-align: right;'>{total_change_sign}{total_change}</span></div></td>"
    table_footer += f"<td class='center'>{total_alerts_p2}</td><td class='center'>{total_alerts_p1}</td><td class='center'>{total_num_cases}</td></tr></tfoot>"

    table_header = f"<thead><tr><th style='width: 35%;'>Squad</th><th style='width: 25%;'>Variação de Alertas</th><th class='center'>Alertas ({escape(label_p2)})</th><th class='center'>Alertas ({escape(label_p1)})</th><th class='center'>Nº de Casos Persistentes</th></tr></thead>"
    return f"<table>{table_header}{table_body}{table_footer}</table>"


def generate_trend_table_html(df_merged, label_p1, label_p2):
    """Gera uma tabela de tendência genérica para diferentes categorias."""
    if df_merged.empty:
        return "<p>Nenhuma mudança registrada nesta categoria.</p>"

    df_merged["change"] = df_merged["count_p2"] - df_merged["count_p1"]
    df_merged["abs_change"] = df_merged["change"].abs()

    has_case_count = "num_cases" in df_merged.columns
    sort_columns = ["abs_change", "count_p2"]
    if has_case_count:
        sort_columns.append("num_cases")

    df_sorted = df_merged.sort_values(by=sort_columns, ascending=[False, False, False])
    max_abs_change = df_sorted["abs_change"].max() if not df_sorted.empty else 1

    total_p1, total_p2, total_change = (
        df_sorted["count_p1"].sum(),
        df_sorted["count_p2"].sum(),
        df_sorted["change"].sum(),
    )
    total_cases = df_sorted["num_cases"].sum() if has_case_count else 0

    table_header = f"<thead><tr><th>Item</th><th style='width: 35%;'>Variação de Alertas</th><th class='center'>Alertas ({escape(label_p2)})</th><th class='center'>Alertas ({escape(label_p1)})</th>"
    if has_case_count:
        case_col_name = (
            "Nº de Casos (Novos)"
            if total_p1 == 0 and total_p2 > 0
            else (
                "Nº de Casos (Resolvidos)"
                if total_p2 == 0 and total_p1 > 0
                else "Nº de Casos"
            )
        )
        table_header += f"<th class='center'>{case_col_name}</th>"
    table_header += "</tr></thead>"

    table_body = "<tbody>"
    for name, row in df_sorted.iterrows():
        p1_count, p2_count, change = row["count_p1"], row["count_p2"], row["change"]
        table_body += f"<tr><td>{escape(str(name))}</td><td>{_generate_change_bar_html(change, max_abs_change)}</td><td class='center'>{int(p2_count)}</td><td class='center'>{int(p1_count)}</td>"
        if has_case_count:
            table_body += f'<td class="center" style="font-weight: bold;">{int(row["num_cases"])}</td>'
        table_body += "</tr>"
    table_body += "</tbody>"

    total_change_sign = "+" if total_change > 0 else ""
    total_change_color = (
        "var(--danger-color)"
        if total_change > 0
        else (
            "var(--success-color)"
            if total_change < 0
            else "var(--text-secondary-color)"
        )
    )

    table_footer = "<tfoot><tr><td>Total</td>"
    table_footer += f"<td><div class='change-bar-container'><span class='change-value' style='color: {total_change_color}; width: 100%; text-align: right;'>{total_change_sign}{int(total_change)}</span></div></td>"
    table_footer += f"<td class='center'>{int(total_p2)}</td><td class='center'>{int(total_p1)}</td>"
    if has_case_count:
        table_footer += f"<td class='center'>{int(total_cases)}</td>"
    table_footer += "</tr></tfoot>"

    return f"<table>{table_header}{table_body}{table_footer}</table>"


def gerar_relatorio_tendencia(
    json_anterior: str,
    json_recente: str,
    csv_anterior_name: str,
    csv_recente_name: str,
    output_path: str,
    date_range_anterior: str = None,
    date_range_recente: str = None,
    is_direct_comparison: bool = False,
):
    """Função principal para gerar o relatório de tendência."""
    df_p1 = load_summary_from_json(json_anterior)
    df_p2 = load_summary_from_json(json_recente)

    if df_p1 is None or df_p2 is None:
        logger.error(
            "Não foi possível continuar a análise de tendência devido a erro no carregamento dos resumos JSON."
        )
        return None

    # Filtra os dados para análise de atuação (casos que precisam de ação)
    df_p1_atuacao = df_p1[df_p1["acao_sugerida"].isin(ACAO_FLAGS_ATUACAO)].copy()
    df_p2_atuacao = df_p2[df_p2["acao_sugerida"].isin(ACAO_FLAGS_ATUACAO)].copy()

    # 1. Calcula os KPIs e o DataFrame base da comparação
    kpis, merged_df = calculate_kpis_and_merged_df(df_p1_atuacao, df_p2_atuacao)

    # 2. Prepara todos os DataFrames para as tabelas e visualizações
    trend_data = prepare_trend_dataframes(merged_df, df_p1_atuacao, df_p2_atuacao)

    # 3. Monta o relatório HTML
    title = "📊 Análise de Tendência de Alertas"

    if is_direct_comparison:
        back_link = '<a href="/" class="home-button">Página Inicial</a>'
    else:
        back_link = '<a href="resumo_geral.html" class="back-to-dashboard">&larr; Voltar para o Dashboard</a>'

    periodo_anterior_text = f"<code>{escape(os.path.basename(csv_anterior_name))}</code>" + (
        f" <span style='color: var(--text-secondary-color);'>({escape(date_range_anterior)})</span>"
        if date_range_anterior
        else ""
    )
    periodo_recente_text = f"<code>{escape(os.path.basename(csv_recente_name))}</code>" + (
        f" <span style='color: var(--text-secondary-color);'>({escape(date_range_recente)})</span>"
        if date_range_recente
        else ""
    )

    body = f"""
    <div class="report-header">
        {back_link}
    </div>
    <style>
        .highlight {{ padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 5px solid; }}
        .highlight-success {{ background-color: rgba(28, 200, 138, 0.1); border-left-color: var(--success-color); }}
        .highlight-danger {{ background-color: rgba(231, 74, 59, 0.1); border-left-color: var(--danger-color); }}
        .highlight-warning {{ background-color: rgba(246, 194, 62, 0.1); border-left-color: var(--warning-color); }}
        .highlight-info {{ background-color: rgba(23, 162, 184, 0.1); border-left-color: var(--info-color); }}
        .highlight-neutral {{ background-color: rgba(108, 117, 125, 0.1); border-left-color: var(--text-secondary-color); }}
    </style>
    <h1>Análise Comparativa de Períodos</h1>
    <p class="lead" style="font-size: 1.2em; color: var(--text-secondary-color); margin-top: -15px;">Foco nos casos onde a remediação (self-healing) falhou ou não existe. </p>
    """
    body += f"<div class='definition-box' style='margin-top: 30px;'><strong>Período Anterior:</strong> {periodo_anterior_text}<br><strong>Período Recente:</strong> {periodo_recente_text}</div>"
    body += generate_executive_summary_html(
        kpis,
        trend_data["persistent_squads_summary"],
        trend_data["new_cases"],
        is_direct_comparison,
    )
    body += f"<div class='card'>{generate_kpis_html(kpis)}</div>"

    chevron_svg_collapsible = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="chevron"><polyline points="9 18 15 12 9 6"></polyline></svg>'

    body += f'<button id="foco-atuacao" type="button" class="collapsible active"><span>🔥 Foco de Atuação e Novos Riscos</span>{chevron_svg_collapsible}</button><div class="collapsible-content"><div class="tab-container"><div class="tab-links">'
    body += '<button class="tab-link active" data-target="tab-persistentes">🚨 Casos Persistentes por Squad</button><button class="tab-link" data-target="tab-novos-problemas">⚠️ Novos Problemas</button></div>'
    body += '<div id="tab-persistentes" class="tab-content active"><div class="definition-box">Casos que já precisavam de ação no período anterior e continuam precisando. <strong>Clique em uma linha da tabela para ver os detalhes.</strong></div>'
    body += (
        generate_persistent_cases_table_html(
            trend_data["persistent_squads_summary"],
            trend_data["persistent_cases"],
            "Anterior",
            "Recente",
        )
        + "</div>"
    )
    body += '<div id="tab-novos-problemas" class="tab-content"><div class="definition-box">Problemas que não precisavam de ação no período anterior, mas que surgiram no período recente já necessitando de uma.</div>'
    body += (
        generate_trend_table_html(
            trend_data["new_problems_summary"].set_index("short_description"),
            "Anterior",
            "Recente",
        )
        + "</div></div></div>"
    )

    body += f'<button type="button" class="collapsible"><span>📈 Tendências Gerais por Categoria</span>{chevron_svg_collapsible}</button><div class="collapsible-content"><div class="tab-container"><div class="tab-links">'
    body += '<button class="tab-link active" data-target="tab-variacao-squad">📈 Variação de Alertas por Squad</button><button class="tab-link" data-target="tab-variacao-problema">📊 Variação por Tipo de Problema</button></div>'
    body += '<div id="tab-variacao-squad" class="tab-content active"><div class="definition-box">Visão geral da variação no volume de alertas por squad, considerando todos os casos que necessitam de ação.</div>'
    body += (
        generate_trend_table_html(
            trend_data["squad_trends"].set_index("assignment_group"),
            "Anterior",
            "Recente",
        )
        + "</div>"
    )
    body += '<div id="tab-variacao-problema" class="tab-content"><div class="definition-box">Variação no volume de alertas para os tipos de problema que persistiram entre os dois períodos.</div>'
    body += (
        generate_trend_table_html(
            trend_data["varying_problems_summary"].set_index("short_description"),
            "Anterior",
            "Recente",
        )
        + "</div></div></div>"
    )

    body += f'<button type="button" class="collapsible"><span>✅ Vitórias</span>{chevron_svg_collapsible}</button><div class="collapsible-content"><div class="tab-container"><div class="tab-links">'
    body += '<button class="tab-link active" data-target="tab-resolvidos">✅ Problemas Resolvidos</button></div>'
    body += '<div id="tab-resolvidos" class="tab-content active"><div class="definition-box">Casos que necessitavam de ação no período anterior e que foram resolvidos, não precisando mais de atuação.</div>'
    body += (
        generate_trend_table_html(
            trend_data["resolved_problems_summary"].set_index("short_description"),
            "Anterior",
            "Recente",
        )
        + "</div></div></div>"
    )

    # CORREÇÃO: Reintroduz o script JavaScript para a funcionalidade dos botões "collapsible".
    # Este script foi removido acidentalmente e é essencial para expandir/recolher as seções.
    body += """
    <script>
        document.addEventListener("DOMContentLoaded", function() {
            function updateParentHeights(element) {
                let parentContent = element.closest('.collapsible-content');
                if (parentContent && parentContent.style.maxHeight && parentContent.style.maxHeight !== '0px') {
                    parentContent.style.maxHeight = parentContent.scrollHeight + 50 + 'px';
                    updateParentHeights(parentContent);
                }
            }

            document.querySelectorAll(".collapsible").forEach(button => {
                button.addEventListener("click", function() {
                    this.classList.toggle("active");
                    const content = this.nextElementSibling;
                    if (content.style.maxHeight && content.style.maxHeight !== '0px') {
                        content.style.maxHeight = null;
                    } else {
                        content.style.maxHeight = content.scrollHeight + 50 + "px";
                    }
                    updateParentHeights(content);
                });
            });

            setTimeout(() => {
                document.querySelectorAll('.collapsible.active').forEach(button => {
                    const content = button.nextElementSibling;
                    if (content) {
                        content.style.maxHeight = content.scrollHeight + 50 + "px";
                        updateParentHeights(content);
                    }
                });
            }, 150);

            // CORREÇÃO: Reintroduz a lógica para a funcionalidade das abas.
            document.querySelectorAll('.tab-container').forEach(container => {
                const tabLinks = container.querySelectorAll('.tab-link');
                const tabContents = container.querySelectorAll('.tab-content');
                tabLinks.forEach(link => {
                    link.addEventListener('click', (event) => {
                        const targetId = link.dataset.target;
                        if (link.classList.contains('active')) return;
                        tabLinks.forEach(l => l.classList.remove('active'));
                        tabContents.forEach(c => c.classList.remove('active'));
                        link.classList.add('active');
                        const targetContent = container.querySelector('#' + targetId);
                        if(targetContent) { targetContent.classList.add('active'); }
                        updateParentHeights(targetContent || link);
                    });
                });
            });
        });
    </script>"""

    try:
        script_dir = os.path.dirname(__file__)
        template_path = os.path.abspath(
            os.path.join(script_dir, "..", "templates", "tendencia_template.html")
        )
        with open(template_path, "r", encoding="utf-8") as f:
            template = Template(f.read())
        final_report = template.substitute(title=title, body=body)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_report)
        logger.info(f"Relatório de tendência gerado em: {output_path}")
        return kpis

    except Exception as e:
        logger.error(
            f"Ocorreu um erro inesperado ao gerar o relatório de tendência: {e}",
            exc_info=True,
        )
        return None


def main_cli():
    """Função para manter a compatibilidade com a execução via linha de comando."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Analisa a tendência entre dois resumos de problemas em JSON."
    )
    parser.add_argument(
        "json_anterior",
        help="Caminho para o arquivo de resumo JSON do período anterior.",
    )
    parser.add_argument(
        "json_recente", help="Caminho para o arquivo de resumo JSON do período recente."
    )
    parser.add_argument(
        "csv_anterior_name",
        help="Nome do arquivo CSV original do período anterior.",
    )
    parser.add_argument(
        "csv_recente_name", help="Nome do arquivo CSV original do período recente."
    )
    args = parser.parse_args()

    output_path = "resumo_tendencia.html"  # Saída padrão para CLI
    gerar_relatorio_tendencia(
        args.json_anterior,
        args.json_recente,
        args.csv_anterior_name,
        args.csv_recente_name,
        output_path,
    )


if __name__ == "__main__":
    main_cli()
