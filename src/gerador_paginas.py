import os
import re
from html import escape
import pandas as pd
from . import gerador_html
from .constants import (
    ACAO_INTERMITENTE, ACAO_FALHA_PERSISTENTE, ACAO_STATUS_AUSENTE, ACAO_INCONSISTENTE,
    COL_ASSIGNMENT_GROUP, COL_SHORT_DESCRIPTION, COL_NODE, COL_CMDB_CI,
    COL_METRIC_NAME, STATUS_OK, STATUS_NOT_OK, NO_STATUS, UNKNOWN, ACAO_FLAGS_OK, ACAO_FLAGS_INSTABILIDADE
)

# =============================================================================
# FUNÇÕES DE GERAÇÃO DE PÁGINAS HTML
# =============================================================================

def carregar_template_html(filepath: str) -> str:
    """Carrega o conteúdo de um arquivo de template HTML de forma segura."""
    print(f"📄 Carregando template de '{filepath}'...")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"O arquivo de template HTML '{filepath}' não foi encontrado.")
    except Exception as e:
        raise IOError(f"Erro inesperado ao ler o arquivo de template '{filepath}': {e}")

def gerar_resumo_executivo(summary_df: pd.DataFrame, df_atuacao: pd.DataFrame, num_logs_invalidos: int, output_path: str, plan_dir: str, details_dir: str, timestamp_str: str, trend_report_path: str = None):
    """Gera o dashboard principal em HTML com o resumo executivo da análise."""
    print("\n📊 Gerando Resumo Executivo estilo Dashboard...")
    
    total_grupos = len(summary_df)
    grupos_atuacao = len(df_atuacao)
    grupos_instabilidade = summary_df['acao_sugerida'].isin(ACAO_FLAGS_INSTABILIDADE).sum()
    taxa_sucesso = (1 - (grupos_atuacao / total_grupos)) * 100 if total_grupos > 0 else 100
    casos_ok_estaveis = total_grupos - grupos_atuacao - grupos_instabilidade
    plan_dir_base_name = os.path.basename(plan_dir)
    df_ok_filtered = summary_df[summary_df["acao_sugerida"].isin(ACAO_FLAGS_OK)]
    df_instabilidade_filtered = summary_df[summary_df["acao_sugerida"].isin(ACAO_FLAGS_INSTABILIDADE)]
    all_squads = df_atuacao[COL_ASSIGNMENT_GROUP].value_counts()
    top_squads = all_squads[all_squads > 0].nlargest(5)
    metric_counts = df_atuacao[COL_METRIC_NAME].value_counts()
    top_metrics = metric_counts[metric_counts > 0].nlargest(5)
    top_problemas_atuacao = df_atuacao.groupby(COL_SHORT_DESCRIPTION, observed=True)['alert_count'].sum().nlargest(5)
    top_problemas_remediados = df_ok_filtered.groupby(COL_SHORT_DESCRIPTION, observed=True)['alert_count'].sum().nlargest(5)
    top_problemas_geral = summary_df.groupby(COL_SHORT_DESCRIPTION, observed=True)['alert_count'].sum().nlargest(10)
    top_problemas_instabilidade = df_instabilidade_filtered.groupby(COL_SHORT_DESCRIPTION, observed=True)['alert_count'].sum().nlargest(5)
    total_alertas_remediados_ok = df_ok_filtered['alert_count'].sum()
    total_alertas_instabilidade = df_instabilidade_filtered['alert_count'].sum()
    total_alertas_problemas = df_atuacao['alert_count'].sum()
    total_alertas_geral = summary_df['alert_count'].sum()

    summary_filename = os.path.basename(output_path)
    
    title = "Dashboard - Análise de Alertas"
    
    start_date = summary_df['first_event'].min() if not summary_df.empty else None
    end_date = summary_df['last_event'].max() if not summary_df.empty else None
    date_range_text = "Período da Análise: Dados Indisponíveis"
    if start_date and end_date:
        date_range_text = f"Período da Análise: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}"
    squads_prioritarias = df_atuacao.groupby(COL_ASSIGNMENT_GROUP, observed=True).agg(
        score_acumulado=('score_ponderado_final', 'sum'),
        total_casos=('score_ponderado_final', 'size')
    ).reset_index()
    top_5_squads_agrupadas = squads_prioritarias.sort_values(by='score_acumulado', ascending=False).head(5)

    context = {
        'total_grupos': total_grupos, 'grupos_atuacao': grupos_atuacao, 'grupos_instabilidade': grupos_instabilidade,
        'taxa_sucesso': taxa_sucesso, 'casos_ok_estaveis': casos_ok_estaveis, 'top_squads': top_squads,
        'top_metrics': top_metrics, 'top_problemas_atuacao': top_problemas_atuacao,
        'top_problemas_remediados': top_problemas_remediados, 'top_problemas_geral': top_problemas_geral,
        'top_problemas_instabilidade': top_problemas_instabilidade, 'total_alertas_remediados_ok': total_alertas_remediados_ok,
        'total_alertas_instabilidade': total_alertas_instabilidade, 'total_alertas_problemas': total_alertas_problemas,
        'total_alertas_geral': total_alertas_geral, 'all_squads': all_squads,
        'top_5_squads_agrupadas': top_5_squads_agrupadas, 'num_logs_invalidos': num_logs_invalidos,
        'trend_report_path': trend_report_path, 'date_range_text': date_range_text,
        'summary_filename': summary_filename, 'plan_dir_base_name': plan_dir_base_name,
        'details_dir_base_name': os.path.basename(details_dir),
        'ai_summary': None
    }

    body_content = gerador_html.renderizar_resumo_executivo(context)
    
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    TEMPLATE_FILE = os.path.join(SCRIPT_DIR, '..', 'templates', 'template.html')
    HTML_TEMPLATE = carregar_template_html(TEMPLATE_FILE)

    footer_text = f"Relatório gerado em {timestamp_str}"
    html_content = gerador_html.renderizar_pagina_html(HTML_TEMPLATE, title, body_content, footer_text)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"✅ Resumo executivo gerado: {output_path}")

    output_dir = os.path.dirname(output_path)
    try:
        with open(os.path.join(output_dir, 'resumo_problemas.json'), 'r', encoding='utf-8') as f:
            json_content = f.read()
        html_visualizador = gerador_html.renderizar_visualizador_json(json_content)
        with open(os.path.join(output_dir, "visualizador_json.html"), 'w', encoding='utf-8') as f:
            f.write(html_visualizador)
        print(f"✅ Visualizador de JSON gerado: visualizador_json.html")
    except Exception as e:
        print(f"⚠️  Aviso: Não foi possível ler o arquivo JSON para o visualizador. Erro: {e}")

def gerar_planos_por_squad(df_atuacao: pd.DataFrame, output_dir: str, timestamp_str: str):
    """Gera arquivos de plano de ação HTML para cada squad com casos que precisam de atuação."""
    print("\n📋 Gerando planos de ação por squad...")
    if df_atuacao.empty:
        print("⚠️ Nenhum caso precisa de atuação. Nenhum plano de ação gerado.")
        return

    os.makedirs(output_dir, exist_ok=True)
    emoji_map = {
        ACAO_INTERMITENTE: "⚠️", ACAO_FALHA_PERSISTENTE: "❌",
        ACAO_STATUS_AUSENTE: "❓", ACAO_INCONSISTENTE: "🔍"
    }
    footer_text = f"Relatório gerado em {timestamp_str}"
    
    VALID_STATUSES_CHRONOLOGY = {STATUS_OK, STATUS_NOT_OK, NO_STATUS}
    
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    TEMPLATE_FILE = os.path.join(SCRIPT_DIR, '..', 'templates', 'template.html')
    HTML_TEMPLATE = carregar_template_html(TEMPLATE_FILE)

    for squad_name, squad_df in df_atuacao.groupby(COL_ASSIGNMENT_GROUP, observed=True):
        if squad_df.empty:
            continue

        sanitized_name = re.sub(r'[^a-zA-Z0-9_-]', '', squad_name.replace(" ", "_"))
        output_path = os.path.join(output_dir, f"plano-de-acao-{sanitized_name}.html")
        title = f"Plano de Ação: {escape(squad_name)}"
        total_alertas = squad_df['alert_count'].sum()

        body_content = '<p><a href="../todas_as_squads.html">&larr; Voltar para Planos Squads</a></p>'
        body_content += f'<h2>Visão Geral da Squad</h2><div class="grid-container">'
        body_content += f'<div class="card kpi-card"><p class="kpi-value" style="color: var(--warning-color);">{len(squad_df)}</p><p class="kpi-label">Total de Casos</p></div>'
        body_content += f'<div class="card kpi-card"><p class="kpi-value">{total_alertas}</p><p class="kpi-label">Total de Alertas Envolvidos</p></div></div>'
        top_problemas_da_squad = squad_df.groupby(COL_SHORT_DESCRIPTION, observed=True)['alert_count'].sum().nlargest(10)
        body_content += f'<div class="card" style="margin-top: 20px;"><h3>Top Problemas da Squad</h3>'
        if not top_problemas_da_squad.empty:
            body_content += '<div class="bar-chart-container">'
            min_prob_val, max_prob_val = top_problemas_da_squad.min(), top_problemas_da_squad.max()
            for problem, count in top_problemas_da_squad.items():
                bar_width = (count / max_prob_val) * 100 if max_prob_val > 0 else 0
                background_color, text_color = gerador_html.gerar_cores_para_barra(count, min_prob_val, max_prob_val)
                body_content += f'<div class="bar-item"><div class="bar-label" title="{escape(problem)}">{escape(problem)}</div><div class="bar-wrapper"><div class="bar" style="width: {bar_width}%; background-color: {background_color}; color: {text_color};">{count}</div></div></div>'
            body_content += '</div>'
        else: body_content += "<p>Nenhum problema recorrente para esta squad. ✅</p>"
        body_content += '</div>'
        body_content += f"<h2>Detalhes por Categoria de Métrica</h2>"

        row_index = 0
        metric_priority = squad_df.groupby(COL_METRIC_NAME, observed=True)['score_ponderado_final'].max().sort_values(ascending=False)
        for metric_name in metric_priority.index:
            metric_group_df = squad_df[squad_df[COL_METRIC_NAME] == metric_name]
            num_problems_in_metric = metric_group_df[COL_SHORT_DESCRIPTION].nunique()
            body_content += f'<button type="button" class="collapsible collapsible-metric"><span class="emoji">📁</span>{escape(metric_name)}<span class="instance-count">{num_problems_in_metric} {"tipos de problema" if num_problems_in_metric > 1 else "tipo de problema"}</span></button><div class="metric-content">'
            problem_priority = metric_group_df.groupby(COL_SHORT_DESCRIPTION, observed=True)['score_ponderado_final'].max().sort_values(ascending=False)
            for problem_desc in problem_priority.index:
                problem_group_df = metric_group_df[metric_group_df[COL_SHORT_DESCRIPTION] == problem_desc]
                if problem_group_df.empty:
                    continue
                acao_principal = problem_group_df['acao_sugerida'].iloc[0]
                emoji = emoji_map.get(acao_principal, '⚙️')
                num_instances = len(problem_group_df)
                total_alertas_problema = problem_group_df['alert_count'].sum()
                body_content += f'''
                <button type="button" class="collapsible collapsible-problem">
                    <span class="emoji">{emoji}</span>
                    {escape(problem_desc)}
                    <span class="instance-count">{num_instances} {"casos" if num_instances > 1 else "caso"} / {total_alertas_problema} alertas</span>
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
                '''
                problem_group_df = problem_group_df.sort_values(by="alert_count", ascending=False)
                for _, row in problem_group_df.iterrows():
                    row_index += 1
                    target_id = f"details-row-{row_index}"
                    recurso_info = f"<strong>{escape(row[COL_CMDB_CI])}</strong>"
                    if row[COL_NODE] != row[COL_CMDB_CI]: recurso_info += f"<br><small style='color:var(--text-secondary-color)'>{escape(row[COL_NODE])}</small>"
                    acao_info = f"<span class='emoji'>{emoji_map.get(row['acao_sugerida'], '⚙️')}</span> {escape(str(row['acao_sugerida']))}"
                    periodo_info = f"{row['first_event'].strftime('%d/%m %H:%M')} a<br>{row['last_event'].strftime('%d/%m %H:%M')}"
                    priority_score_html = f"<td class='priority-col' style='color: {gerador_html.gerar_cores_para_barra(row['score_ponderado_final'], 0, 20)[0]};'>{row['score_ponderado_final']:.1f}</td>"
                    body_content += f'<tr class="expandable-row" data-target="#{target_id}">{priority_score_html}<td>{recurso_info}</td><td>{acao_info}</td><td>{periodo_info}</td><td>{row["alert_count"]}</td></tr>'
                    status_emoji_map = { "REM_OK": "✅", "REM_NOT_OK": "❌", "NO_STATUS": "❓" }
                    
                    formatted_chronology = []
                    for status in row['status_chronology']:
                        if status in VALID_STATUSES_CHRONOLOGY:
                            formatted_chronology.append(f"{status_emoji_map.get(status, '⚪')} {escape(status)}")
                        else:
                            link_html = (
                                f'<a href="../qualidade_dados_remediacao.html" class="tooltip-container invalid-status-link">
                                  ⚪ {escape(status)}
                                  <div class="tooltip-content" style="width: 280px; left: 50%; margin-left: -140px;">
                                    Status inválido. Clique para ver o log de erros.
                                  </div>
                                </a>'
                            )
                            formatted_chronology.append(link_html)
                    
                    cronologia_info = f"<code>{' → '.join(formatted_chronology)}</code>"
                    alertas_info = f"<code>{escape(row['alert_numbers'])}</code>"
                    body_content += f'<tr id="{target_id}" class="details-row"><td colspan="5"><div class="details-row-content"><p><strong>Alertas Envolvidos ({row["alert_count"]}):</strong> {alertas_info}</p><p><strong>Cronologia:</strong> {cronologia_info}</p></div></td></tr>'
                body_content += '</tbody></table></div>'
            body_content += '</div>'
        html_content = gerador_html.renderizar_pagina_html(HTML_TEMPLATE, title, body_content, footer_text)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"✅ Plano de ação para a squad '{squad_name}' gerado: {output_path}")

def gerar_pagina_squads(all_squads: pd.Series, plan_dir: str, output_dir: str, summary_filename: str, timestamp_str: str):
    """Gera uma página HTML com o gráfico de barras para todas as squads com casos em aberto."""
    print(f"📄 Gerando página com a lista completa de squads...")
    output_path = os.path.join(output_dir, "todas_as_squads.html")
    title = "Lista Completa de Squads por Casos"
    body_content = f'<p><a href="{summary_filename}">&larr; Voltar para o Dashboard</a></p><div class="card">'
    squads_com_casos = all_squads[all_squads > 0]
    body_content += f"<h3>{title} ({len(squads_com_casos)} squads)</h3>"
    if not squads_com_casos.empty:
        body_content += '<div class="bar-chart-container">'
        min_val, max_val = squads_com_casos.min(), squads_com_casos.max()
        plan_base_dir = os.path.basename(plan_dir)
        for squad, count in squads_com_casos.items():
            bar_width = (count / max_val) * 100 if max_val > 0 else 0
            background_color, text_color = gerador_html.gerar_cores_para_barra(count, min_val, max_val)
            sanitized_name = re.sub(r'[^a-zA-Z0-9_-]', '', squad.replace(" ", "_"))
            plan_path = os.path.join(plan_base_dir, f"plano-de-acao-{sanitized_name}.html")
            body_content += f'''
            <div class="bar-item">
                <div class="bar-label"><a href="{plan_path}" title="Ver plano de ação para {escape(squad)}">{escape(squad)}</a></div>
                <div class="bar-wrapper">
                    <div class="bar" style="width: {bar_width}%; background-color: {background_color}; color: {text_color};">{count}</div>
                </div>
            </div>'''
        body_content += '</div>'
    else:
        body_content += "<p>Nenhuma squad com casos a serem listados. ✅</p>"
    body_content += '</div>'
    footer_text = f"Relatório gerado em {timestamp_str}"
    
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    TEMPLATE_FILE = os.path.join(SCRIPT_DIR, '..', 'templates', 'template.html')
    HTML_TEMPLATE = carregar_template_html(TEMPLATE_FILE)
    
    html_content = gerador_html.renderizar_pagina_html(HTML_TEMPLATE, title, body_content, footer_text)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"✅ Página de squads gerada: {output_path}")

def gerar_pagina_sucesso(output_dir: str, ok_csv_path: str, template_path: str):
    """Gera uma página HTML para visualização dos casos resolvidos com sucesso."""
    print(f"📄 Gerando página de visualização para '{os.path.basename(ok_csv_path)}'...")
    output_path = os.path.join(output_dir, "sucesso_automacao.html")
    try:
        with open(ok_csv_path, 'r', encoding='utf-8') as f:
            csv_content = f.read().lstrip()
    except FileNotFoundError:
        csv_content = ""
        print(f"⚠️ Aviso: Arquivo '{ok_csv_path}' não encontrado. Gerando página vazia.")
    try:
        with open(template_path, 'r', encoding='utf-8') as f_template:
            template_content = f_template.read()
        final_html = gerador_html.renderizar_pagina_csv_viewer(template_content, csv_content, "Sucesso da Automação", os.path.basename(ok_csv_path))
        with open(output_path, 'w', encoding='utf-8') as f_out:
            f_out.write(final_html)
    except FileNotFoundError:
        raise FileNotFoundError(f"Template '{template_path}' não encontrado.")
    print(f"✅ Página de visualização de sucesso gerada: {output_path}")

def gerar_pagina_instabilidade(output_dir: str, instability_csv_path: str, template_path: str):
    """Gera uma página HTML para visualização dos casos de instabilidade crônica."""
    print(f"📄 Gerando página de visualização para '{os.path.basename(instability_csv_path)}'...")
    output_path = os.path.join(output_dir, "instabilidade_cronica.html")
    try:
        with open(instability_csv_path, 'r', encoding='utf-8') as f:
            csv_content = f.read().lstrip()
    except FileNotFoundError:
        csv_content = ""
        print(f"⚠️ Aviso: Arquivo '{instability_csv_path}' não encontrado. Gerando página vazia.")
    try:
        with open(template_path, 'r', encoding='utf-8') as f_template:
            template_content = f_template.read()
        final_html = gerador_html.renderizar_pagina_csv_viewer(template_content, csv_content, "Instabilidade Crônica", os.path.basename(instability_csv_path))
        with open(output_path, 'w', encoding='utf-8') as f_out:
            f_out.write(final_html)
    except FileNotFoundError:
        raise FileNotFoundError(f"Template '{template_path}' não encontrado.")
    print(f"✅ Página de visualização de instabilidade gerada: {output_path}")

def gerar_pagina_logs_invalidos(output_dir: str, log_csv_path: str, template_path: str):
    """Gera uma página HTML para visualização dos logs com status inválido."""
    print(f"📄 Gerando página de visualização para '{os.path.basename(log_csv_path)}'...")
    output_path = os.path.join(output_dir, "qualidade_dados_remediacao.html")
    try:
        with open(log_csv_path, 'r', encoding='utf-8') as f:
            csv_content = f.read().lstrip()
    except FileNotFoundError:
        csv_content = ""
        print(f"⚠️ Aviso: Arquivo '{log_csv_path}' não encontrado. Gerando página vazia.")
    try:
        with open(template_path, 'r', encoding='utf-8') as f_template:
            template_content = f_template.read()
        final_html = gerador_html.renderizar_pagina_csv_viewer(template_content, csv_content, "Qualidade de Dados", os.path.basename(log_csv_path))
        with open(output_path, 'w', encoding='utf-8') as f_out:
            f_out.write(final_html)
    except FileNotFoundError:
        raise FileNotFoundError(f"Template '{template_path}' não encontrado.")
    print(f"✅ Página de visualização de logs inválidos gerada: {output_path}")

def gerar_pagina_editor_atuacao(output_dir: str, actuation_csv_path: str, template_path: str):
    """Gera uma página HTML para edição do arquivo de atuação."""
    print(f"📄 Gerando página de edição para '{os.path.basename(actuation_csv_path)}'...")
    output_path = os.path.join(output_dir, "editor_atuacao.html")
    try:
        with open(actuation_csv_path, 'r', encoding='utf-8') as f:
            csv_content = f.read().lstrip()
    except FileNotFoundError:
        csv_content = ""
        print(f"⚠️ Aviso: Arquivo '{actuation_csv_path}' não encontrado. Gerando página de edição vazia.")
    try:
        with open(template_path, 'r', encoding='utf-8') as f_template:
            template_content = f_template.read()
        csv_payload = csv_content.replace('\\', r'\\\\').replace('`', r'`')
        placeholder = "___CSV_DATA_PAYLOAD_EDITOR___")
        template_com_placeholder = template_content.replace('const csvDataPayload = `__CSV_DATA_PLACEHOLDER__`', f'const csvDataPayload = `{placeholder}`')
        final_html = template_com_placeholder.replace(placeholder, csv_payload)
        with open(output_path, 'w', encoding='utf-8') as f_out:
            f_out.write(final_html)
    except FileNotFoundError:
        raise FileNotFoundError(f"Template '{template_path}' não encontrado.")
    print(f"✅ Página de edição gerada: {output_path}")
