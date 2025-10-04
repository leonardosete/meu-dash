import pandas as pd
import sys
import os
import re
import json
import numpy as np
from typing import List, Tuple, Dict
from html import escape
from datetime import datetime
from .constants import (
    ACAO_ESTABILIZADA, ACAO_INTERMITENTE, ACAO_FALHA_PERSISTENTE, ACAO_STATUS_AUSENTE,
    ACAO_SEMPRE_OK, ACAO_INCONSISTENTE, ACAO_INSTABILIDADE_CRONICA, ACAO_FLAGS_ATUACAO,
    ACAO_FLAGS_OK, ACAO_FLAGS_INSTABILIDADE, SEVERITY_WEIGHTS, PRIORITY_GROUP_WEIGHTS, ACAO_WEIGHTS
)
from . import gerador_html

# =============================================================================
# CONFIGURAÇÃO E CONSTANTES
# =============================================================================

# Nomes de colunas do DataFrame
COL_CREATED_ON = "sys_created_on"
COL_NODE = "node"
COL_CMDB_CI = "cmdb_ci"
COL_SELF_HEALING_STATUS = "self_healing_status"
COL_ASSIGNMENT_GROUP = "assignment_group"
COL_SHORT_DESCRIPTION = "short_description"
COL_NUMBER = "number"
COL_SOURCE = "source"
COL_METRIC_NAME = "metric_name"
COL_CMDB_CI_SYS_CLASS_NAME = "cmdb_ci.sys_class_name"
COL_SEVERITY = "severity"
COL_PRIORITY_GROUP = "sn_priority_group"

# Colunas que definem um grupo único de alertas
GROUP_COLS: List[str] = [
    COL_ASSIGNMENT_GROUP, COL_SHORT_DESCRIPTION, COL_NODE, COL_CMDB_CI,
    COL_SOURCE, COL_METRIC_NAME, COL_CMDB_CI_SYS_CLASS_NAME,
]

# Colunas essenciais para o funcionamento do script
ESSENTIAL_COLS: List[str] = GROUP_COLS + [
    COL_CREATED_ON, COL_SELF_HEALING_STATUS, COL_NUMBER, COL_SEVERITY, COL_PRIORITY_GROUP
]

# Valores de Status de Remediação
STATUS_OK = "REM_OK"
STATUS_NOT_OK = "REM_NOT_OK"
UNKNOWN = "DESCONHECIDO"
NO_STATUS = "NO_STATUS"
LOG_INVALIDOS_FILENAME = "invalid_self_healing_status.csv"

LIMIAR_ALERTAS_RECORRENTES = 5

# Carrega o template principal de forma robusta
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

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

TEMPLATE_FILE = os.path.join(SCRIPT_DIR, '..', 'templates', 'template.html')
HTML_TEMPLATE = carregar_template_html(TEMPLATE_FILE)


# =============================================================================
# PROCESSAMENTO E ANÁLISE DE DADOS
# =============================================================================

def carregar_dados(filepath: str, output_dir: str) -> Tuple[pd.DataFrame, int]:
    """Carrega, valida e pré-processa os dados de um arquivo CSV."""
    print(f"⚙️  Carregando e preparando dados de '{filepath}'...")
    try:
        df = pd.read_csv(filepath, encoding="utf-8-sig", sep=None, engine='python')
    except FileNotFoundError:
        raise FileNotFoundError(f"O arquivo de entrada '{filepath}' não foi encontrado.")
    except Exception as e:
        raise ValueError(f"Erro ao ler ou processar o arquivo CSV '{filepath}'. Verifique o formato e a codificação. Detalhe: {e}")

    missing_cols = [col for col in ESSENTIAL_COLS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"O arquivo CSV não contém as colunas essenciais: {', '.join(missing_cols)}")

    num_invalidos = 0
    if COL_SELF_HEALING_STATUS in df.columns:
        df[COL_SELF_HEALING_STATUS] = df[COL_SELF_HEALING_STATUS].astype(str).str.strip()
        valid_statuses = {STATUS_OK, STATUS_NOT_OK}
        mask_invalidos = df[COL_SELF_HEALING_STATUS].notna() & ~df[COL_SELF_HEALING_STATUS].isin(valid_statuses)
        df_invalidos = df[mask_invalidos]
        num_invalidos = len(df_invalidos)
        if not df_invalidos.empty:
            log_invalidos_path = os.path.join(output_dir, LOG_INVALIDOS_FILENAME)
            print(f"⚠️  Detectadas {num_invalidos} linhas com status de remediação inesperado. Registrando em '{log_invalidos_path}'...")
            df_invalidos.to_csv(log_invalidos_path, index=False, encoding='utf-8-sig')

    for col in GROUP_COLS:
        df[col] = df[col].fillna(UNKNOWN).replace("", UNKNOWN)
    df[COL_CREATED_ON] = pd.to_datetime(df[COL_CREATED_ON], errors='coerce', format='mixed')
    df[COL_SELF_HEALING_STATUS] = df[COL_SELF_HEALING_STATUS].fillna(NO_STATUS)
    df['severity_score'] = df[COL_SEVERITY].map(SEVERITY_WEIGHTS).fillna(0)
    df['priority_group_score'] = df[COL_PRIORITY_GROUP].map(PRIORITY_GROUP_WEIGHTS).fillna(0)
    df['score_criticidade_final'] = df['severity_score'] + df['priority_group_score']

    for col in GROUP_COLS + [COL_SELF_HEALING_STATUS, COL_SEVERITY, COL_PRIORITY_GROUP]:
        if col in df.columns and df[col].dtype == 'object':
            df[col] = df[col].astype('category')
    print("✅ Dados carregados e preparados com sucesso.")
    return df, num_invalidos

def adicionar_acao_sugerida(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona a coluna 'acao_sugerida' com base na cronologia dos status."""
    last_status = df['status_chronology'].str[-1].fillna(NO_STATUS)
    has_ok = df['status_chronology'].apply(lambda c: STATUS_OK in c)
    has_only_no_status = df['status_chronology'].apply(lambda c: not c or all(s == NO_STATUS for s in c))
    has_multiple_unique_statuses = df['status_chronology'].apply(lambda c: len(set(c)) > 1)

    conditions = [
        has_only_no_status,
        (last_status == STATUS_OK) & (df['alert_count'] >= LIMIAR_ALERTAS_RECORRENTES),
        (last_status == STATUS_OK) & has_multiple_unique_statuses,
        (last_status == STATUS_OK),
        (last_status != STATUS_OK) & has_ok,
        (last_status != STATUS_OK)
    ]
    choices = [
        ACAO_STATUS_AUSENTE, ACAO_INSTABILIDADE_CRONICA, ACAO_ESTABILIZADA,
        ACAO_SEMPRE_OK, ACAO_INTERMITENTE, ACAO_FALHA_PERSISTENTE
    ]
    df['acao_sugerida'] = np.select(conditions, choices, default=UNKNOWN)
    return df

def analisar_grupos(df: pd.DataFrame) -> pd.DataFrame:
    """Agrupa e analisa os alertas para criar um sumário de problemas únicos."""
    print("\n⏳ Analisando e agrupando alertas...")
    aggregations = {
        COL_CREATED_ON: ['min', 'max'],
        COL_NUMBER: ['nunique', lambda x: ', '.join(sorted(x.unique()))],
        COL_SELF_HEALING_STATUS: lambda x: ', '.join(sorted(x.unique())),
        'score_criticidade_final': 'max'
    }
    summary = df.groupby(GROUP_COLS, observed=True, dropna=False).agg(aggregations).reset_index()
    summary.columns = [
        *GROUP_COLS, 'first_event', 'last_event', 'alert_count',
        'alert_numbers', 'statuses', 'score_criticidade_agregado'
    ]
    if not df.empty:
        sorted_df = df.sort_values(by=GROUP_COLS + [COL_CREATED_ON])
        chronology = sorted_df.groupby(GROUP_COLS, observed=True, dropna=False)[COL_SELF_HEALING_STATUS].apply(list).reset_index(name='status_chronology')
        summary = pd.merge(summary, chronology, on=GROUP_COLS, how='left')
    else:
        summary['status_chronology'] = [[] for _ in range(len(summary))]

    summary = adicionar_acao_sugerida(summary)
    summary['fator_peso_remediacao'] = summary['acao_sugerida'].map(ACAO_WEIGHTS).fillna(1.0)
    summary['fator_volume'] = 1 + np.log(summary['alert_count'].clip(1))
    summary['score_ponderado_final'] = (
        summary['score_criticidade_agregado'] * summary['fator_peso_remediacao'] * summary['fator_volume']
    )
    print(f"📊 Total de grupos únicos analisados: {summary.shape[0]}")
    return summary

# =============================================================================
# GERAÇÃO DE RELATÓRIOS (CSV E JSON)
# =============================================================================

def gerar_relatorios_csv(summary: pd.DataFrame, output_actuation: str, output_ok: str, output_instability: str) -> pd.DataFrame:
    """Filtra os resultados, salva em CSV e retorna o dataframe de atuação."""
    print("\n📑 Gerando relatórios CSV...")
    alerts_atuacao = summary[summary["acao_sugerida"].isin(ACAO_FLAGS_ATUACAO)].copy()
    alerts_ok = summary[summary["acao_sugerida"].isin(ACAO_FLAGS_OK)].copy()
    alerts_instabilidade = summary[summary["acao_sugerida"].isin(ACAO_FLAGS_INSTABILIDADE)].copy()
    full_emoji_map = {
        acao_INTERMITENTE: "⚠️", ACAO_FALHA_PERSISTENTE: "❌", ACAO_STATUS_AUSENTE: "❓",
        acao_INCONSISTENTE: "🔍", ACAO_SEMPRE_OK: "✅", ACAO_ESTABILIZADA: "⚠️✅",
        acao_INSTABILIDADE_CRONICA: "🔁"
    }

    if not alerts_atuacao.empty:
        VALID_STATUSES_FOR_CHRONOLOGY = {STATUS_OK, STATUS_NOT_OK, NO_STATUS}
        has_invalid_status_mask = alerts_atuacao['status_chronology'].apply(
            lambda chronology: any(s not in VALID_STATUSES_FOR_CHRONOLOGY for s in chronology)
        )
        if has_invalid_status_mask.any():
            alerts_atuacao.loc[has_invalid_status_mask, 'acao_sugerida'] = (
                "⚠️🔍 Analise o status da remediação 🔍⚠️ | " + alerts_atuacao.loc[has_invalid_status_mask, 'acao_sugerida']
            )

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
            print(f"✅ Relatório CSV gerado: {path}")

    save_csv(alerts_atuacao, output_actuation, "score_ponderado_final", False)
    save_csv(alerts_ok, output_ok, "last_event", False)
    save_csv(alerts_instabilidade, output_instability, "alert_count", False)
    return alerts_atuacao.sort_values(by="score_ponderado_final", ascending=False)

def export_summary_to_json(summary: pd.DataFrame, header: Dict, output_path: str):
    """Salva o dataframe de resumo e o cabeçalho em formato JSON."""
    print(f"\n💾 Exportando resumo para JSON...")
    
    # Converte o DataFrame para uma lista de dicionários
    records = summary.to_dict(orient='records')
    
    # Cria a estrutura final do JSON
    json_data = {
        "header": header,
        "records": records
    }
    
    # Salva o arquivo JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=4, default=str) # Usa default=str para lidar com tipos de data/numpy
        
    print(f"✅ Resumo salvo em: {output_path}")

# =============================================================================
# GERAÇÃO DE PÁGINAS HTML (Lógica de negócio inalterada)
# =============================================================================
# Todas as funções `gerar_...` permanecem aqui, exatamente como no seu original.
# Elas são a lógica de negócio para a apresentação e não devem ser removidas.
# ... (COPIE TODAS AS FUNÇÕES `gerar_planos_por_squad`, `gerar_pagina_squads`,
# `gerar_paginas_detalhe_problema`, `gerar_resumo_executivo`, etc., aqui) ...
# Omitido por brevidade, mas devem estar presentes no arquivo final.
def gerar_planos_por_squad(df_atuacao: pd.DataFrame, output_dir: str, timestamp_str: str):
    """Gera arquivos de plano de ação HTML para cada squad com casos que precisam de atuação."""
    print("\n📋 Gerando planos de ação por squad...")
    if df_atuacao.empty:
        print("⚠️ Nenhum caso precisa de atuação. Nenhum plano de ação gerado.")
        return

    os.makedirs(output_dir, exist_ok=True)
    emoji_map = {
        acao_INTERMITENTE: "⚠️", ACAO_FALHA_PERSISTENTE: "❌",
        ACAO_STATUS_AUSENTE: "❓", ACAO_INCONSISTENTE: "🔍"
    }
    footer_text = f"Relatório gerado em {timestamp_str}"
    
    VALID_STATUSES_CHRONOLOGY = {STATUS_OK, STATUS_NOT_OK, NO_STATUS}

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
                                f'''<a href="../qualidade_dados_remediacao.html" class="tooltip-container invalid-status-link">
                                  ⚪ {escape(status)}
                                  <div class="tooltip-content" style="width: 280px; left: 50%; margin-left: -140px;">
                                    Status inválido. Clique para ver o log de erros.
                                  </div>
                                </a>'''
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
    html_content = gerador_html.renderizar_pagina_html(HTML_TEMPLATE, title, body_content, footer_text)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"✅ Página de squads gerada: {output_path}")

def gerar_paginas_detalhe_problema(df_source: pd.DataFrame, problem_list: pd.Index, output_dir: str, summary_filename: str, file_prefix: str, plan_dir_name: str, timestamp_str: str):
    """Gera páginas de detalhe para uma lista de problemas específicos."""
    if problem_list.empty:
        return
    os.makedirs(output_dir, exist_ok=True)
    emoji_map = {
        acao_INTERMITENTE: "⚠️", ACAO_FALHA_PERSISTENTE: "❌", ACAO_STATUS_AUSENTE: "❓",
        ACAO_INCONSISTENTE: "🔍", ACAO_SEMPRE_OK: "✅", ACAO_ESTABILIZADA: "✅",
        ACAO_INSTABILIDADE_CRONICA: "🔁"
    }
    footer_text = f"Relatório gerado em {timestamp_str}"
    print(f"\n📄 Gerando páginas de detalhe para o contexto: '{file_prefix}'...")
    for problem_desc in problem_list:
        sanitized_name = re.sub(r'[^a-zA-Z0-9_-]', '', problem_desc[:50].replace(" ", "_"))
        output_path = os.path.join(output_dir, f"detalhe_{file_prefix}{sanitized_name}.html")
        problem_df = df_source[df_source[COL_SHORT_DESCRIPTION] == problem_desc].sort_values(by="alert_count", ascending=False)
        if problem_df.empty:
            continue
        total_alerts = problem_df['alert_count'].sum()
        total_instances = len(problem_df)
        title = f"Resumo do Problema: {escape(problem_desc)}"
        body_content = f'<p><a href="../{summary_filename}">&larr; Voltar para o Dashboard</a></p><h2>{escape(problem_desc)}</h2><p>Total de alertas: <strong>{total_alerts}</strong> | Casos distintos: <strong>{total_instances}</strong></p>'
        body_content += '<table><thead><tr><th>Recurso (CI) / Nó</th><th>Ação Sugerida</th><th>Período</th><th>Total de Alertas</th><th>Squad</th></tr></thead><tbody>'
        for _, row in problem_df.iterrows():
            recurso_info = f"<strong>{escape(row[COL_CMDB_CI])}</strong>"
            if row[COL_NODE] != row[COL_CMDB_CI]: recurso_info += f"<br><small style='color:var(--text-secondary-color)'>{escape(row[COL_NODE])}</small>"
            acao_sugerida = row.get('acao_sugerida', UNKNOWN)
            acao_info = f"<span class='emoji'>{emoji_map.get(acao_sugerida, '⚙️')}</span> {escape(str(acao_sugerida))}"
            periodo_info = f"{row['first_event'].strftime('%d/%m %H:%M')} a<br>{row['last_event'].strftime('%d/%m %H:%M')}"
            squad_name = row[COL_ASSIGNMENT_GROUP]
            if acao_sugerida in ACAO_FLAGS_ATUACAO:
                sanitized_squad_name = re.sub(r'[^a-zA-Z0-9_-]', '', squad_name.replace(" ", "_"))
                plan_path = f"../{plan_dir_name}/plano-de-acao-{sanitized_squad_name}.html"
                squad_info = f'<a href="{plan_path}">{escape(squad_name)}</a>'
            else:
                squad_info = escape(squad_name)
            body_content += f'<tr><td>{recurso_info}</td><td>{acao_info}</td><td>{periodo_info}</td><td>{row["alert_count"]}</td><td>{squad_info}</td></tr>'
        body_content += '</tbody></table>'
        html_content = gerador_html.renderizar_pagina_html(HTML_TEMPLATE, title, body_content, footer_text)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    print(f"✅ {len(problem_list)} páginas de detalhe do contexto '{file_prefix}' geradas.")

def gerar_paginas_detalhe_metrica(df_atuacao_source: pd.DataFrame, metric_list: pd.Index, output_dir: str, summary_filename: str, plan_dir_name: str, timestamp_str: str):
    """Gera páginas de detalhe para categorias de métricas com casos em aberto."""
    if metric_list.empty:
        return
    os.makedirs(output_dir, exist_ok=True)
    emoji_map = {
        acao_INTERMITENTE: "⚠️", ACAO_FALHA_PERSISTENTE: "❌", ACAO_STATUS_AUSENTE: "❓", ACAO_INCONSISTENTE: "🔍"
    }
    footer_text = f"Relatório gerado em {timestamp_str}"
    print(f"\n📄 Gerando páginas de detalhe para Métricas em Aberto...")
    for metric_name in metric_list:
        sanitized_name = re.sub(r'[^a-zA-Z0-9_-]', '', metric_name.replace(" ", "_"))
        output_path = os.path.join(output_dir, f"detalhe_metrica_{sanitized_name}.html")
        metric_df = df_atuacao_source[df_atuacao_source[COL_METRIC_NAME] == metric_name].sort_values(by="last_event", ascending=False)
        if metric_df.empty:
            continue
        total_instances = len(metric_df)
        title = f"Detalhe da Métrica em Aberto: {escape(metric_name)}"
        body_content = f'<p><a href="../{summary_filename}">&larr; Voltar para o Dashboard</a></p><h2>{escape(metric_name)}</h2><p>Total de Casos em aberto: <strong>{total_instances}</strong></p>'
        body_content += '<table><thead><tr><th>Recurso (CI) / Nó</th><th>Ação Sugerida</th><th>Período</th><th>Problema</th><th>Squad</th></tr></thead><tbody>'
        for _, row in metric_df.iterrows():
            recurso_info = f"<strong>{escape(row[COL_CMDB_CI])}</strong>"
            if row[COL_NODE] != row[COL_CMDB_CI]: recurso_info += f"<br><small style='color:var(--text-secondary-color)'>{escape(row[COL_NODE])}</small>"
            acao_sugerida = row.get('acao_sugerida', UNKNOWN)
            acao_info = f"<span class='emoji'>{emoji_map.get(acao_sugerida, '⚙️')}</span> {escape(str(acao_sugerida))}"
            periodo_info = f"{row['first_event'].strftime('%d/%m %H:%M')} a<br>{row['last_event'].strftime('%d/%m %H:%M')}"
            squad_name = row[COL_ASSIGNMENT_GROUP]
            sanitized_squad_name = re.sub(r'[^a-zA-Z0-9_-]', '', squad_name.replace(" ", "_"))
            plan_path = f"../{plan_dir_name}/plano-de-acao-{sanitized_squad_name}.html"
            squad_info = f'<a href="{plan_path}">{escape(squad_name)}</a>'
            problema_info = escape(row[COL_SHORT_DESCRIPTION])
            body_content += f'<tr><td>{recurso_info}</td><td>{acao_info}</td><td>{periodo_info}</td><td>{problema_info}</td><td>{squad_info}</td></tr>'
        body_content += '</tbody></table>'
        html_content = gerador_html.renderizar_pagina_html(HTML_TEMPLATE, title, body_content, footer_text)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    print(f"✅ {len(metric_list)} páginas de detalhe de métricas geradas.")

def gerar_resumo_executivo(summary_df: pd.DataFrame, df_atuacao: pd.DataFrame, num_logs_invalidos: int, output_path: str, plan_dir: str, details_dir: str, timestamp_str: str, trend_report_path: str = None, ai_summary: str = None):
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
    gerar_paginas_detalhe_problema(df_atuacao, top_problemas_atuacao.index, details_dir, summary_filename, 'aberto_', plan_dir_base_name, timestamp_str)
    gerar_paginas_detalhe_problema(df_ok_filtered, top_problemas_remediados.index, details_dir, summary_filename, 'remediado_', plan_dir_base_name, timestamp_str)
    gerar_paginas_detalhe_problema(summary_df, top_problemas_geral.index, details_dir, summary_filename, 'geral_', plan_dir_base_name, timestamp_str)
    gerar_paginas_detalhe_problema(df_instabilidade_filtered, top_problemas_instabilidade.index, details_dir, summary_filename, 'instabilidade_', plan_dir_base_name, timestamp_str)
    gerar_paginas_detalhe_metrica(df_atuacao, top_metrics.index, details_dir, summary_filename, plan_dir_base_name, timestamp_str)


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
        'ai_summary': ai_summary
    }

    body_content = gerador_html.renderizar_resumo_executivo(context)
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
        print(f"⚠️  Aviso: Não foi possível ler o arquivo JSON para o visualizador. Erro: {e}", file=sys.stderr)

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
        csv_payload = csv_content.replace('\\', r'\\').replace('`', r'`')
        placeholder = "___CSV_DATA_PAYLOAD_EDITOR___"
        template_com_placeholder = template_content.replace('const csvDataPayload = `__CSV_DATA_PLACEHOLDER__`', f'const csvDataPayload = `{placeholder}`')
        final_html = template_com_placeholder.replace(placeholder, csv_payload)
        with open(output_path, 'w', encoding='utf-8') as f_out:
            f_out.write(final_html)
    except FileNotFoundError:
        raise FileNotFoundError(f"Template '{template_path}' não encontrado.")
    print(f"✅ Página de edição gerada: {output_path}")

# =============================================================================
# NOVA EXECUÇÃO PRINCIPAL (WEB-FOCUSED)
# =============================================================================

def analisar_arquivo_csv(input_file: str, output_dir: str, light_analysis: bool = False, trend_report_path: str = None, ai_summary: str = None) -> Dict[str, str]:
    """
    Função principal, otimizada para uso web, que orquestra a análise de um arquivo CSV.
    """
    timestamp_str = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
    os.makedirs(output_dir, exist_ok=True)

    # Define caminhos
    output_summary_html = os.path.join(output_dir, "resumo_geral.html")
    output_actuation_csv = os.path.join(output_dir, "atuar.csv")
    output_ok_csv = os.path.join(output_dir, "remediados.csv")
    output_instability_csv = os.path.join(output_dir, "remediados_frequentes.csv")
    plan_dir = os.path.join(output_dir, "planos_de_acao")
    details_dir = os.path.join(output_dir, "detalhes")
    output_json = os.path.join(output_dir, "resumo_problemas.json")

    df, num_logs_invalidos = carregar_dados(input_file, output_dir)
    summary = analisar_grupos(df)

    # Calcula os dados do cabeçalho para o dashboard
    if not summary.empty:
        header_data = {
            "total_alertas": int(summary['alert_count'].sum()),
            "risco_medio": summary['score_criticidade_agregado'].mean(),
            "ineficiencia_media": summary['fator_peso_remediacao'].mean(),
            "impacto_medio": summary['fator_volume'].mean(),
        }
    else:
        header_data = {
            "total_alertas": 0,
            "risco_medio": 0,
            "ineficiencia_media": 0,
            "impacto_medio": 0,
        }

    export_summary_to_json(summary.copy(), header_data, output_json)

    if light_analysis:
        print("💡 Análise leve concluída. Apenas o resumo JSON foi gerado.")
        return {'html_path': None, 'json_path': output_json}

    df_atuacao = gerar_relatorios_csv(summary, output_actuation_csv, output_ok_csv, output_instability_csv)
    
    gerar_resumo_executivo(summary, df_atuacao, num_logs_invalidos, output_summary_html, plan_dir, details_dir, timestamp_str, trend_report_path, ai_summary)
    
    gerar_planos_por_squad(df_atuacao, plan_dir, timestamp_str)
    all_squads = df_atuacao[COL_ASSIGNMENT_GROUP].value_counts()
    gerar_pagina_squads(all_squads, plan_dir, output_dir, os.path.basename(output_summary_html), timestamp_str)
    
    base_template_dir = os.path.join(SCRIPT_DIR, '..', 'templates')
    sucesso_template_file = os.path.join(base_template_dir, 'sucesso_template.html')
    editor_template_file = os.path.join(base_template_dir, 'editor_template.html')

    gerar_pagina_sucesso(output_dir, output_ok_csv, sucesso_template_file)
    gerar_pagina_instabilidade(output_dir, output_instability_csv, sucesso_template_file)
    gerar_pagina_editor_atuacao(output_dir, output_actuation_csv, editor_template_file)
    
    if num_logs_invalidos > 0:
        log_invalidos_path = os.path.join(output_dir, LOG_INVALIDOS_FILENAME)
        gerar_pagina_logs_invalidos(output_dir, log_invalidos_path, sucesso_template_file)

    print(f"✅ Análise completa finalizada. Relatório principal em: {output_summary_html}")
    return {'html_path': output_summary_html, 'json_path': output_json}

def atualizar_resumo_com_ia(summary_html_path: str, ai_summary: str):
    """Atualiza o arquivo de resumo HTML com o sumário gerado pela IA."""
    print(f"🔄 Atualizando o resumo com a análise da IA...")
    try:
        with open(summary_html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Formata o resumo da IA para HTML
        ai_summary_html = f'''
        <div class="notification-banner trend" style="margin-top: 25px; border-left: 5px solid var(--accent-color); background: linear-gradient(145deg, rgba(78, 115, 223, 0.1), rgba(78, 115, 223, 0.05));">
            <span class="icon" style="font-size: 1.8em; align-self: flex-start;">🤖</span>
            <div class="text">
                <h3 style="margin-top: 0; margin-bottom: 10px; color: var(--accent-color);">Resumo Executivo (IA)</h3>
                <p style="margin: 0; font-size: 1.05em; line-height: 1.6;">{ai_summary}</p>
            </div>
        </div>
        '''
        
        # Substitui o placeholder pelo conteúdo da IA
        content = content.replace("<!-- AI_SUMMARY_PLACEHOLDER -->", ai_summary_html)
        
        with open(summary_html_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Resumo atualizado com sucesso em: {summary_html_path}")
        
    except FileNotFoundError:
        print(f"❌ Erro: O arquivo de resumo '{summary_html_path}' não foi encontrado para atualização.")
    except Exception as e:
        print(f"❌ Erro ao atualizar o resumo com a análise da IA: {e}")