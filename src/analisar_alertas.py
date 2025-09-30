import pandas as pd
import argparse
import sys
import os
import re
import json
import math
import numpy as np
from typing import Set, List, Dict, Callable, Tuple
from html import escape
from datetime import datetime

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
    COL_CREATED_ON, COL_SELF_HEALING_STATUS, COL_NUMBER, COL_SEVERITY, COL_PRIORITY_GROUP
]

# Valores de Status de Remediação
STATUS_OK = "REM_OK"
STATUS_NOT_OK = "REM_NOT_OK"
UNKNOWN = "DESCONHECIDO"
NO_STATUS = "NO_STATUS"
LOG_INVALIDOS_FILENAME = "invalid_self_healing_status.csv"

# Ações Sugeridas
ACAO_ESTABILIZADA = "Remediação estabilizada (houve falha)"
ACAO_INTERMITENTE = "Analisar intermitência na remediação"
ACAO_FALHA_PERSISTENTE = "Desenvolver remediação (nenhum sucesso registrado)"
ACAO_STATUS_AUSENTE = "Verificar coleta de dados da remediação (status ausente)"
ACAO_SEMPRE_OK = "Remediação automática funcional"
ACAO_INCONSISTENTE = "Analisar causa raiz das falhas (remediação inconsistente)"
ACAO_INSTABILIDADE_CRONICA = "Revisar causa raiz (remediação recorrente)"
LIMIAR_ALERTAS_RECORRENTES = 5

# Mapeamento de Ações para categorização
ACAO_FLAGS_ATUACAO = [ACAO_INTERMITENTE, ACAO_FALHA_PERSISTENTE, ACAO_STATUS_AUSENTE, ACAO_INCONSISTENTE]
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

# Ícones SVG para o HTML
SQUAD_ICON_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="squad-icon"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>'''
DOWNLOAD_ICON_SVG = '''<svg class="download-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>'''
VIEW_ICON_SVG = '''<svg class="download-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>'''
EDIT_ICON_SVG = '''<svg class="download-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>'''
CHEVRON_SVG = '''<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="chevron"><polyline points="9 18 15 12 9 6"></polyline></svg>'''


def carregar_template_html(filepath: str) -> str:
    """Carrega o conteúdo de um arquivo de template HTML de forma segura."""
    print(f"📄 Carregando template de '{filepath}'...")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ Erro Fatal: O arquivo de template HTML '{filepath}' não foi encontrado.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro inesperado ao ler o arquivo de template '{filepath}': {e}", file=sys.stderr)
        sys.exit(1)

TEMPLATE_FILE = "templates/template.html"
HTML_TEMPLATE = carregar_template_html(TEMPLATE_FILE)

# =============================================================================
# PROCESSAMENTO E ANÁLISE DE DADOS
# =============================================================================
def carregar_dados(filepath: str) -> Tuple[pd.DataFrame, int]:
    """
    Carrega os dados de um arquivo CSV, valida, limpa, pré-processa e
    retorna a contagem de Check last columm .

    Args:
        filepath: O caminho para o arquivo CSV de entrada.

    Returns:
        Uma tupla contendo:
        - Um DataFrame do pandas pronto para análise.
        - Um inteiro com a contagem de linhas de log inválidas.
    """
    print(f"⚙️  Carregando e preparando dados de '{filepath}'...")
    try:
        df = pd.read_csv(filepath, encoding="utf-8-sig", sep=None, engine='python')
    except FileNotFoundError:
        print(f"❌ Erro Fatal: O arquivo '{filepath}' não foi encontrado.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro inesperado ao ler o arquivo '{filepath}': {e}", file=sys.stderr)
        sys.exit(1)

    # Garante a remoção de espaços em branco antes da validação
    if COL_SELF_HEALING_STATUS in df.columns:
        df[COL_SELF_HEALING_STATUS] = df[COL_SELF_HEALING_STATUS].astype(str).str.strip()

    valid_statuses = {STATUS_OK, STATUS_NOT_OK}
    mask_invalidos = df[COL_SELF_HEALING_STATUS].notna() & ~df[COL_SELF_HEALING_STATUS].isin(valid_statuses)
    df_invalidos = df[mask_invalidos]
    num_invalidos = len(df_invalidos)

    if not df_invalidos.empty:
        print(f"⚠️  Detectadas {num_invalidos} linhas com status de remediação inesperado. Registrando em '{LOG_INVALIDOS_FILENAME}'...")
        header = not os.path.exists(LOG_INVALIDOS_FILENAME)
        df_invalidos.to_csv(LOG_INVALIDOS_FILENAME, mode='a', index=False, header=header, encoding='utf-8-sig')

    missing_cols = [col for col in ESSENTIAL_COLS if col not in df.columns]
    if missing_cols:
        print(f"❌ Erro Fatal: Faltam as seguintes colunas essenciais no arquivo: {missing_cols}", file=sys.stderr)
        sys.exit(1)

    for col in GROUP_COLS:
        df[col] = df[col].fillna(UNKNOWN).replace("", UNKNOWN)

    df[COL_CREATED_ON] = pd.to_datetime(df[COL_CREATED_ON], errors='coerce', format='mixed')
    df[COL_SELF_HEALING_STATUS] = df[COL_SELF_HEALING_STATUS].fillna(NO_STATUS)

    df['severity_score'] = df[COL_SEVERITY].map(SEVERITY_WEIGHTS).fillna(0)
    df['priority_group_score'] = df[COL_PRIORITY_GROUP].map(PRIORITY_GROUP_WEIGHTS).fillna(0)
    df['score_criticidade_final'] = df['severity_score'] + df['priority_group_score']

    categorical_cols = GROUP_COLS + [COL_SELF_HEALING_STATUS, COL_SEVERITY, COL_PRIORITY_GROUP]
    for col in categorical_cols:
        if col in df.columns and df[col].dtype == 'object':
            df[col] = df[col].astype('category')

    print("✅ Dados carregados e preparados com sucesso.")
    return df, num_invalidos


def adicionar_acao_sugerida(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adiciona uma coluna com ações sugeridas de forma vetorizada para melhor performance.

    Args:
        df: O DataFrame de resumo contendo a coluna 'status_chronology'.

    Returns:
        O mesmo DataFrame com a coluna 'acao_sugerida' adicionada.
    """
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
    """
    Agrupa e analisa os alertas para criar um sumário de problemas únicos.

    Args:
        df: O DataFrame completo de alertas carregado.

    Returns:
        Um DataFrame de resumo, com cada linha representando um problema único.
    """
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
    """
    Filtra os resultados em categorias, salva em arquivos CSV e retorna o dataframe de atuação.
    """
    print("\n📑 Gerando relatórios CSV...")
    alerts_atuacao = summary[summary["acao_sugerida"].isin(ACAO_FLAGS_ATUACAO)].copy()
    alerts_ok = summary[summary["acao_sugerida"].isin(ACAO_FLAGS_OK)].copy()
    alerts_instabilidade = summary[summary["acao_sugerida"].isin(ACAO_FLAGS_INSTABILIDADE)].copy()
    full_emoji_map = {
        ACAO_INTERMITENTE: "⚠️", ACAO_FALHA_PERSISTENTE: "❌", ACAO_STATUS_AUSENTE: "❓",
        ACAO_INCONSISTENTE: "🔍", ACAO_SEMPRE_OK: "✅", ACAO_ESTABILIZADA: "⚠️✅",
        ACAO_INSTABILIDADE_CRONICA: "🔁"
    }

    # --- LÓGICA DE MODIFICAÇÃO MOVIDA PARA O LOCAL CORRETO ---
    # Somente no dataframe que irá para o atuar.csv, verifica por status inválidos.
    if not alerts_atuacao.empty:
        VALID_STATUSES_FOR_CHRONOLOGY = {STATUS_OK, STATUS_NOT_OK, NO_STATUS}
        has_invalid_status_mask = alerts_atuacao['status_chronology'].apply(
            lambda chronology: any(s not in VALID_STATUSES_FOR_CHRONOLOGY for s in chronology)
        )
        if has_invalid_status_mask.any():
            alerts_atuacao.loc[has_invalid_status_mask, 'acao_sugerida'] = (
                "⚠️ Analise o status da remediação | " + alerts_atuacao.loc[has_invalid_status_mask, 'acao_sugerida']
            )
    # --- FIM DA MODIFICAÇÃO ---

    def save_csv(df, path, sort_by, ascending=False):
        if not df.empty:
            df_to_save = df.copy()
            # Esta linha agora lida corretamente tanto com os casos normais quanto os modificados.
            df_to_save['acao_sugerida'] = df_to_save['acao_sugerida'].apply(lambda x: f"{full_emoji_map.get(x, '')} {x}".strip())
            df_to_save = df_to_save.sort_values(by=sort_by, ascending=ascending)
            if 'atuar' in path:
                df_to_save['status_tratamento'] = 'Pendente'
                df_to_save['responsavel'] = ''
                df_to_save['data_previsao_solucao'] = ''
            df_to_save.to_csv(path, index=False, encoding="utf-8")
            print(f"✅ Relatório CSV gerado: {path}")

    save_csv(alerts_atuacao, output_actuation, "score_ponderado_final", False)
    save_csv(alerts_ok, output_ok, "last_event", False)
    save_csv(alerts_instabilidade, output_instability, "alert_count", False)
    return alerts_atuacao.sort_values(by="score_ponderado_final", ascending=False)

def export_summary_to_json(summary: pd.DataFrame, output_path: str):
    """Salva o dataframe de resumo em formato JSON."""
    print(f"\n💾 Exportando resumo para JSON...")
    summary_json = summary.copy()
    for col in ['first_event', 'last_event']:
        if col in summary_json.columns:
            summary_json[col] = summary_json[col].astype(str)
    summary_json.to_json(output_path, orient='records', indent=4, date_format='iso')
    print(f"✅ Resumo salvo em: {output_path}")

# =============================================================================
# GERAÇÃO DE PÁGINAS HTML
# =============================================================================

def gerar_cores_para_barra(valor: float, valor_min: float, valor_max: float) -> tuple[str, str]:
    """Gera uma tupla com (cor de fundo, cor de texto) para a barra do gráfico."""
    if valor_max == valor_min:
        return "hsl(0, 90%, 55%)", "white"
    fracao = (valor - valor_min) / (valor_max - valor_min) if valor_max > valor_min else 0
    hue = 60 - (fracao * 60)
    background_color = f"hsl({hue:.0f}, 90%, 55%)"
    text_color = "var(--text-color-dark)" if hue > 35 else "white"
    return background_color, text_color

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
                background_color, text_color = gerar_cores_para_barra(count, min_prob_val, max_prob_val)
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
                    priority_score_html = f"<td class='priority-col' style='color: {gerar_cores_para_barra(row['score_ponderado_final'], 0, 20)[0]};'>{row['score_ponderado_final']:.1f}</td>"
                    body_content += f'<tr class="expandable-row" data-target="#{target_id}">{priority_score_html}<td>{recurso_info}</td><td>{acao_info}</td><td>{periodo_info}</td><td>{row["alert_count"]}</td></tr>'
                    status_emoji_map = { "REM_OK": "✅", "REM_NOT_OK": "❌", "NO_STATUS": "❓" }
                    
                    formatted_chronology = []
                    for status in row['status_chronology']:
                        if status in VALID_STATUSES_CHRONOLOGY:
                            formatted_chronology.append(f"{status_emoji_map.get(status, '⚪')} {escape(status)}")
                        else:
                            link_html = (
                                f'<a href="../visualizador_logs_invalidos.html" class="tooltip-container invalid-status-link">'
                                f'  ⚪ {escape(status)}'
                                f'  <div class="tooltip-content" style="width: 280px; left: 50%; margin-left: -140px;">'
                                f'    Status inválido. Clique para ver o log de erros.'
                                f'  </div>'
                                f'</a>'
                            )
                            formatted_chronology.append(link_html)
                    
                    cronologia_info = f"<code>{' → '.join(formatted_chronology)}</code>"
                    alertas_info = f"<code>{escape(row['alert_numbers'])}</code>"
                    body_content += f'<tr id="{target_id}" class="details-row"><td colspan="5"><div class="details-row-content"><p><strong>Alertas Envolvidos ({row["alert_count"]}):</strong> {alertas_info}</p><p><strong>Cronologia:</strong> {cronologia_info}</p></div></td></tr>'
                body_content += '</tbody></table></div>'
            body_content += '</div>'
        html_content = HTML_TEMPLATE.format(title=title, body=body_content, footer_timestamp=footer_text)
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
            background_color, text_color = gerar_cores_para_barra(count, min_val, max_val)
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
    html_content = HTML_TEMPLATE.format(title=title, body=body_content, footer_timestamp=footer_text)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"✅ Página de squads gerada: {output_path}")


def gerar_paginas_detalhe_problema(df_source: pd.DataFrame, problem_list: pd.Index, output_dir: str, summary_filename: str, file_prefix: str, plan_dir_name: str, timestamp_str: str):
    """Gera páginas de detalhe para uma lista de problemas específicos."""
    if problem_list.empty:
        return
    os.makedirs(output_dir, exist_ok=True)
    emoji_map = {
        ACAO_INTERMITENTE: "⚠️", ACAO_FALHA_PERSISTENTE: "❌", ACAO_STATUS_AUSENTE: "❓",
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
        html_content = HTML_TEMPLATE.format(title=title, body=body_content, footer_timestamp=footer_text)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    print(f"✅ {len(problem_list)} páginas de detalhe do contexto '{file_prefix}' geradas.")


def gerar_paginas_detalhe_metrica(df_atuacao_source: pd.DataFrame, metric_list: pd.Index, output_dir: str, summary_filename: str, plan_dir_name: str, timestamp_str: str):
    """Gera páginas de detalhe para categorias de métricas com casos em aberto."""
    if metric_list.empty:
        return
    os.makedirs(output_dir, exist_ok=True)
    emoji_map = {
        ACAO_INTERMITENTE: "⚠️", ACAO_FALHA_PERSISTENTE: "❌", ACAO_STATUS_AUSENTE: "❓", ACAO_INCONSISTENTE: "🔍"
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
        html_content = HTML_TEMPLATE.format(title=title, body=body_content, footer_timestamp=footer_text)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    print(f"✅ {len(metric_list)} páginas de detalhe de métricas geradas.")

def gerar_resumo_executivo(summary_df: pd.DataFrame, df_atuacao: pd.DataFrame, num_logs_invalidos: int, output_path: str, plan_dir: str, details_dir: str, actuation_csv_path: str, ok_csv_path: str, json_path: str, timestamp_str: str, trend_report_path: str = None):
    """Gera o dashboard principal em HTML com o resumo executivo da análise."""
    print("\n📊 Gerando Resumo Executivo estilo Dashboard...")
    
    total_grupos = len(summary_df)
    grupos_atuacao = len(df_atuacao)
    grupos_instabilidade = summary_df['acao_sugerida'].isin(ACAO_FLAGS_INSTABILIDADE).sum()
    taxa_sucesso = (1 - (grupos_atuacao / total_grupos)) * 100 if total_grupos > 0 else 100
    casos_ok_estaveis = total_grupos - grupos_atuacao - grupos_instabilidade
    summary_filename = os.path.basename(output_path)
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

    gerar_paginas_detalhe_problema(df_atuacao, top_problemas_atuacao.index, details_dir, summary_filename, 'aberto_', plan_dir_base_name, timestamp_str)
    gerar_paginas_detalhe_problema(df_ok_filtered, top_problemas_remediados.index, details_dir, summary_filename, 'remediado_', plan_dir_base_name, timestamp_str)
    gerar_paginas_detalhe_problema(summary_df, top_problemas_geral.index, details_dir, summary_filename, 'geral_', plan_dir_base_name, timestamp_str)
    gerar_paginas_detalhe_problema(df_instabilidade_filtered, top_problemas_instabilidade.index, details_dir, summary_filename, 'instabilidade_', plan_dir_base_name, timestamp_str)
    gerar_paginas_detalhe_metrica(df_atuacao, top_metrics.index, details_dir, summary_filename, plan_dir_base_name, timestamp_str)

    title = "Dashboard - Análise de Alertas"
    
    # Adicionando o período da análise
    start_date = summary_df['first_event'].min() if not summary_df.empty else None
    end_date = summary_df['last_event'].max() if not summary_df.empty else None
    date_range_text = "Período da Análise: Dados Indisponíveis"
    if start_date and end_date:
        start_date_formatted = start_date.strftime('%d/%m/%Y')
        end_date_formatted = end_date.strftime('%d/%m/%Y')
        date_range_text = f"Período da Análise: {start_date_formatted} a {end_date_formatted}"
    
    list_card_styles = '''
    <style>
        .volume-card-item { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid var(--border-color); }
        .volume-card-item:last-child { border-bottom: none; }
        .volume-card-label { font-size: 1em; color: var(--text-secondary-color); }
        .volume-card-value { font-size: 1.5em; font-weight: bold; }
        .priority-list-item-new { display: flex; align-items: center; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid var(--border-color); transition: background-color 0.2s ease; }
        .priority-list-item-new:hover { background-color: #33365a; border-radius: 4px; }
        .squad-info-new { display: flex; align-items: center; gap: 10px; }
        .squad-name-new { font-weight: 500; }
        .priority-score-new { font-weight: bold; background-color: #e74a3b; padding: 5px 10px; border-radius: 4px; color: var(--text-color-dark); }
        .squad-icon { color: var(--text-secondary-color); width: 22px; height: 22px; }
    </style>
    '''
    body_content = list_card_styles
    body_content += f'<p style="font-size: 1.1em; color: var(--text-secondary-color); margin-top: -15px;">{date_range_text}</p>'
    body_content += f'''
                <div style="margin-bottom: 25px;">
                    <button type="button" class="collapsible collapsible-main-header">{CHEVRON_SVG}Conceitos</button>
                    <div class="content" style="display: none; padding: 0; border: none; background: none;">
                        <div class="card" style="margin-top: 10px; padding: 20px;">

                            <button type="button" class="collapsible active">{CHEVRON_SVG}<strong>Casos vs. Alertas</strong></button>
                            <div class="content" style="display: block; padding-left: 28px;">
                                <div style="padding: 15px 0 15px 15px; border-left: 2px solid var(--accent-color); color: var(--text-secondary-color);">
                                    Para focar no que é mais importante, os gráficos distinguem entre <strong>Alertas</strong> e <strong>Casos</strong>.
                                    <br><br>
                                    Um <strong>Alerta</strong> é uma notificação individual — pense nele como o &#34;ruído&#34; que você recebe.
                                    <br><br>
                                    Um <strong>Caso</strong> é a causa raiz de um problema. Ele agrupa todos os alertas do mesmo tipo em um único recurso.
                                    <br><br>
                                    <strong>Exemplo:</strong> Um servidor com pouco espaço em disco pode gerar 100 <strong>Alertas</strong> de &#34;disco cheio&#34;. No entanto, como todos esses alertas são sobre o mesmo problema, eles são agrupados em apenas <strong>1 Caso</strong>. Se esse servidor também apresentar um problema de CPU, isso será um <strong>2º Caso</strong>, porque exige uma ação diferente.
                                </div>
                            </div>

                            <button type="button" class="collapsible" style="margin-top: 15px;">{CHEVRON_SVG}<strong>Como a Prioridade dos Casos é Definida?</strong></button>
                            <div class="content" style="display: none; padding-left: 28px;">
                                 <div style="padding: 15px 0 15px 15px; border-left: 2px solid var(--danger-color); color: var(--text-secondary-color);">
                                    A pontuação de prioridade não é um valor arbitrário. Ela é calculada pela fórmula: <br>
                                    <code>Score = (Pilar 1: Risco) * (Pilar 2: Ineficiência) * (Pilar 3: Impacto)</code>
                                    <br><br>
                                    <h4 style="color: var(--text-color); margin-top: 15px; margin-bottom: 5px;">Pilar 1: Score de Risco</h4>
                                    Mede a gravidade base do problema. É a soma dos pesos da Severidade e Prioridade do alerta, valores extraídos diretamente das colunas <strong>severity</strong> e <strong>sn_priority_group</strong> do arquivo de dados.
                                    <table class="sub-table">
                                        <thead>
                                            <tr>
                                                <th>Severidade</th>
                                                <th>Peso</th>
                                                <th>Prioridade</th>
                                                <th>Peso</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <tr>
                                                <td>Crítico</td>
                                                <td style="color: var(--danger-color); font-weight: 500;">10</td>
                                                <td>Urgente</td>
                                                <td style="color: var(--danger-color); font-weight: 500;">10</td>
                                            </tr>
                                            <tr>
                                                <td>Alto / Major</td>
                                                <td style="color: var(--warning-color); font-weight: 500;">8</td>
                                                <td>Alto(a)</td>
                                                <td style="color: var(--warning-color); font-weight: 500;">8</td>
                                            </tr>
                                            <tr>
                                                <td>Médio / Minor</td>
                                                <td style="color: var(--accent-color); font-weight: 500;">5</td>
                                                <td>Moderado(a)</td>
                                                <td style="color: var(--accent-color); font-weight: 500;">5</td>
                                            </tr>
                                            <tr>
                                                <td>Aviso / Baixo</td>
                                                <td>2-3</td>
                                                <td>Baixo(a)</td>
                                                <td>2</td>
                                            </tr>
                                        </tbody>
                                    </table>
                                    <h4 style="color: var(--text-color); margin-top: 15px; margin-bottom: 5px;">Pilar 2: Multiplicador de Ineficiência</h4>
                                    Penaliza casos onde a automação falhou. Quanto pior a falha, maior o multiplicador.
                                    <table class="sub-table"><thead><tr><th>Resultado da Automação</th><th>Multiplicador</th></tr></thead><tbody><tr><td>Falha Persistente (nunca funcionou)</td><td style="color: var(--danger-color);">x 1.5</td></tr><tr><td>Intermitente (falha às vezes)</td><td style="color: var(--warning-color);">x 1.2</td></tr><tr><td>Status Ausente / Inconsistente</td><td style="color: var(--warning-color);">x 1.1</td></tr><tr><td>Funcionou no final (Estabilizada / Sempre OK)</td><td>x 1.0</td></tr></tbody></table>
                                    <h4 style="color: var(--text-color); margin-top: 15px; margin-bottom: 5px;">Pilar 3: Multiplicador de Impacto</h4>
                                    <div style="padding-bottom: 10px; color: var(--text-secondary-color);">
                                    Penaliza o "ruído" operacional gerado pelo volume de alertas de um mesmo caso. O cálculo utiliza a fórmula matemática <code>1 + ln(N)</code>, onde <code>ln</code> é o <strong>logaritmo natural</strong> e <code>N</code> é o número de alertas. Essa abordagem garante que o impacto do ruído seja significativo no início, mas cresça de forma controlada para volumes muito altos.
                                    </div>  
                                    <table class="sub-table"><thead><tr><th>Nº de Alertas no Caso</th><th>Multiplicador Aprox.</th></tr></thead><tbody><tr><td>1 alerta</td><td>x 1.0</td></tr><tr><td>10 alertas</td><td style="color: var(--accent-color); font-weight: 500;">x 3.3</td></tr><tr><td>50 alertas</td><td style="color: var(--warning-color); font-weight: 500;">x 4.9</td></tr><tr><td>100 alertas</td><td style="color: var(--danger-color); font-weight: 500;">x 5.6</td></tr></tbody></table>
                                    <h4 style="color: var(--text-color); margin-top: 20px; margin-bottom: 5px; border-top: 1px solid var(--border-color); padding-top: 15px;">Exemplo Prático Completo</h4>
                                    Um alerta de <strong>CPU Saturated</strong> com <strong>Severidade Crítica (<span style="color: var(--danger-color); font-weight: 500;">10</span>)</strong> e <strong>Prioridade Urgente (<span style="color: var(--danger-color); font-weight: 500;">10</span>)</strong>, cuja remediação teve <strong>Falha Persistente</strong> e que gerou <strong>50 alertas</strong>.
                                    <ul>
                                        <li><strong>Score de Risco:</strong> 10 + 10 = <strong style="color: var(--danger-color);">20</strong></li>
                                        <li><strong>Multiplicador de Ineficiência:</strong> <strong style="color: var(--danger-color);">1.5</strong></li>
                                        <li><strong>Multiplicador de Impacto:</strong> 1 + log(50) ≈ <strong style="color: var(--warning-color);">4.9</strong></li>
                                    </ul>
                                    <strong>Score Final = 20 * 1.5 * 4.9 = <span style="font-size: 1.1em; color: var(--danger-color); font-weight: bold;">147</span></strong>
                                </div>
                            </div>

                            <button type="button" class="collapsible" style="margin-top: 15px;">{CHEVRON_SVG}<strong>Como a Remediação é Contabilizada?</strong></button>
                            <div class="content" style="display: none; padding-left: 28px;">
                                <div style="padding: 15px 0 15px 15px; border-left: 2px solid var(--accent-color); color: var(--text-secondary-color);">
                                    <p>A análise da remediação se baseia em uma etapa de preparação dos dados. Nesse passo anterior, cada alerta é verificado para identificar se existe uma "Tarefa de Correção" (<strong>REM00XXXXX</strong>) associada a ele. É a presença desse registro que confirma que uma automação foi <strong>executada</strong>.</p>
                                    <p style="margin-top: 10px;">Para definir o <strong>resultado</strong>, o processo então analisa o status dessa tarefa. O texto exato encontrado nesse campo determina o desfecho: <strong>"REM_OK"</strong> é contabilizado como <strong>sucesso</strong>, enquanto <strong>"REM_NOT_OK"</strong> é contabilizado como <strong>falha</strong>. A detecção de um desses dois "eventos" no alerta é o que classifica o status da remediação.</p>
                                    
                                    <div style="background-color: #fffbe6; border-left: 5px solid #ffe58f; padding: 15px 20px; margin-top: 15px; color: #665424;">
                                        <strong>Ponto de Atenção:</strong> Este método confirma a <em>execução</em> de uma automação, mas não garante, por si só, que a remediação foi de fato <em>efetiva</em> para solucionar a causa raiz do problema. Uma investigação futura é necessária para aprofundar essa análise. O próximo passo será um trabalho em conjunto com o time de Automação para entender o significado detalhado dos status dentro de uma tarefa REM00XXXXX e como extrair essa informação para o relatório.
                                    </div>
                                </div>
                            </div>

                            <button type="button" class="collapsible" style="margin-top: 15px;">{CHEVRON_SVG}<strong>Como Interpretar o quadro de Remediações?</strong></button>
                            <div class="content" style="display: none; padding-left: 28px;">
                                <div style="padding: 15px 0 15px 15px; border-left: 2px solid var(--warning-color); color: var(--text-secondary-color);">
                                    Um número alto neste quadro é bom (a automação está funcionando), mas também é um sinal de alerta. Ele indica <strong>instabilidade crônica</strong>: um problema que ocorre e é remediado com muita frequência. Esses são candidatos ideais para uma análise de causa raiz mais profunda, visando a solução definitiva.
                                </div>
                            </div>

                            <button type="button" class="collapsible" style="margin-top: 15px;">{CHEVRON_SVG}<strong>O que significa o valor "DESCONHECIDO"?</strong></button>
                            <div class="content" style="display: none; padding-left: 28px;">
                                <div style="padding: 15px 0 15px 15px; border-left: 2px solid var(--text-secondary-color); color: var(--text-secondary-color);">
                                    Quando o valor "DESCONHECIDO" aparece em campos como Squad, Métrica ou Recurso, significa que a informação estava <strong>ausente no arquivo de dados original</strong>. Isso geralmente aponta para uma oportunidade de melhorar a qualidade e o enriquecimento dos dados na origem (o sistema de monitoramento), garantindo que todo alerta seja corretamente categorizado.
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                '''
    # Define os estilos do banner uma vez para ser usado por ambos os avisos
    notification_banner_styles = '''
    <style>
    .notification-banner {
        display: flex;
        align-items: center;
        gap: 15px;
        padding: 15px 20px;
        border-radius: 8px;
        margin: 25px 0;
        color: var(--text-color);
    }
    .notification-banner.warning {
        background-color: rgba(231, 74, 59, 0.1);
        border: 1px solid var(--danger-color);
    }
    .notification-banner.trend {
        background-color: rgba(78, 115, 223, 0.1);
        border: 1px solid var(--accent-color);
    }
    .notification-banner .icon { font-size: 1.5em; }
    .notification-banner .text { flex-grow: 1; }
    .notification-banner .details-link {
        font-weight: bold;
        white-space: nowrap;
    }
    .notification-banner.warning .details-link {
        color: var(--danger-color);
    }
    .notification-banner.trend .details-link {
        color: var(--accent-color);
    }
    </style>
    '''

    # Injeta os estilos apenas se um dos banners for ser exibido
    if num_logs_invalidos > 0 or trend_report_path:
        body_content += notification_banner_styles
    
    # Gera o banner de Qualidade de Dados (lógica existente)
    if num_logs_invalidos > 0:
        body_content += f'''
        <div class="notification-banner warning">
            <span class="icon">📜</span>
            <div class="text">
                <strong>Aviso de Qualidade de Dados:</strong> Foram encontrados <strong>{num_logs_invalidos} alertas</strong> com status de remediação inválido.
            </div>
            <a href="visualizador_logs_invalidos.html" class="details-link">Detalhes &rarr;</a>
        </div>
        '''

    # Gera o banner de Relatório de Tendência (nova lógica e posição)
    if trend_report_path:
        body_content += f'''
        <div class="notification-banner trend">
            <span class="icon">📈</span>
            <div class="text">
                <strong>Análise Comparativa Disponível:</strong> Compare os resultados atuais com o período anterior para identificar novas tendências, regressões e melhorias.
            </div>
            <a href="{os.path.basename(trend_report_path)}" class="details-link">Relatório de Tendência &rarr;</a>
        </div>
        '''
    
    body_content += f'<button type="button" class="collapsible-row active">{CHEVRON_SVG}VISÃO GERAL</button>'
    body_content += '<div class="content" style="display: block; padding-top: 20px;">'
    
    body_content += f'<div class="grid-container" style="grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));">'
    
    gauge_color_class = "var(--success-color)"
    automation_card_class = "card-neon-green"
    if taxa_sucesso < 50:
        gauge_color_class = "var(--danger-color)"
        automation_card_class = "card-neon-red"
    elif taxa_sucesso < 70:
        gauge_color_class = "var(--warning-color)"
        automation_card_class = "card-neon-warning"
    
    view_icon_html = f'<a href="editor_atuacao.html" class="download-link" title="Abrir editor para atuar.csv">{VIEW_ICON_SVG}</a>' if grupos_atuacao > 0 else f'<span class="download-link" title="Nenhum arquivo de atuação gerado." style="cursor: not-allowed;">{VIEW_ICON_SVG.replace("<svg", "<svg style=\'opacity: 0.4;\'")}</span>'
    card_class = 'card-fire-shake' if grupos_atuacao > 0 else 'card-neon card-neon-blue'
    tooltip_text = 'Casos que precisam de revisão: Remediação Pendente.' if grupos_atuacao > 0 else 'Tudo certo! Nenhum caso precisa de intervenção manual.'
    status_icon_html = f'''<div class="tooltip-container" style="position: absolute; top: 15px; left: 15px;"><span class="{'flashing-icon' if grupos_atuacao > 0 else ''}" style="font-size: 1.5em;">{'🚨' if grupos_atuacao > 0 else '✅'}</span><div class="tooltip-content" style="width: 240px; left: 0; margin-left: 0;">{escape(tooltip_text)}</div></div>'''
    kpi_color_style = 'color: var(--danger-color);' if grupos_atuacao > 0 else 'color: var(--accent-color);'
    body_content += f'''
    <div class="card kpi-card {card_class}">
        {status_icon_html}
        <p class="kpi-value" style="{kpi_color_style}">{grupos_atuacao}</p>
        <p class="kpi-label">Casos sem Remediação | Foco de Atuação</p>
        {view_icon_html}
    </div>
    '''

    instabilidade_view_icon_html = f'<a href="instabilidade_cronica.html" class="download-link" title="Visualizar detalhes dos casos de instabilidade">{VIEW_ICON_SVG}</a>' if grupos_instabilidade > 0 else f'<span class="download-link" title="Nenhum caso de instabilidade crônica detectado." style="cursor: not-allowed;">{VIEW_ICON_SVG.replace("<svg", "<svg style=\'opacity: 0.4;\'")}</span>'
    instabilidade_card_class = 'card-neon card-neon-warning' if grupos_instabilidade > 0 else 'card-neon card-neon-blue'
    instabilidade_kpi_color = 'color: var(--warning-color);' if grupos_instabilidade > 0 else 'color: var(--accent-color);'
    tooltip_instabilidade_text = "Casos que são remediados, mas ocorrem com alta frequência. Oportunidades para análise de causa raiz." if grupos_instabilidade > 0 else "Nenhum ponto de alta recorrência crônica detectado."
    instabilidade_status_icon_html = f'''<div class="tooltip-container" style="position: absolute; top: 15px; left: 15px;"><span class="{'flashing-icon' if grupos_instabilidade > 0 else ''}" style="font-size: 1.5em;">{'⚠️' if grupos_instabilidade > 0 else '✅'}</span><div class="tooltip-content" style="width: 280px; left: 0; margin-left: 0;">{escape(tooltip_instabilidade_text)}</div></div>'''
    
    body_content += f'''
    <div class="card kpi-card {instabilidade_card_class}">
        {instabilidade_status_icon_html}
        <p class="kpi-value" style="{instabilidade_kpi_color}">{grupos_instabilidade}</p>
        <p class="kpi-label">Casos Remediados com Frequência</p>
        {instabilidade_view_icon_html}
    </div>
    '''
    
    casos_sucesso = total_grupos - grupos_atuacao
    tooltip_gauge = f"Percentual e contagem de Casos resolvidos automaticamente: {casos_sucesso} de {total_grupos} problemas tiveram a remediação executada com sucesso."
    sucesso_page_name = "sucesso_automacao.html"
    sucesso_view_icon_html = f'<a href="{sucesso_page_name}" class="download-link" title="Visualizar detalhes dos casos resolvidos">{VIEW_ICON_SVG}</a>' if casos_sucesso > 0 else f'<span class="download-link" title="Nenhum caso resolvido automaticamente." style="cursor: not-allowed;">{VIEW_ICON_SVG.replace("<svg", "<svg style=\'opacity: 0.4;\'")}</span>'
    body_content += f'''
    <div class="card kpi-card card-neon {automation_card_class}">
        <div class="tooltip-container" style="position: absolute; top: 15px; left: 15px;"><span style="font-size: 1.5em;">🤖</span><div class="tooltip-content" style="width: 280px; left: 0; margin-left: 0;">{escape(tooltip_gauge)}</div></div>
        <p class="kpi-value" style="color: {gauge_color_class}; font-size: 4em; margin: 0;">{taxa_sucesso:.1f}%</p>
        <p class="kpi-label" style="margin-top: 0px; margin-bottom: 10px;">Sucesso da Automação</p>
        <p style="font-size: 1.2em; color: var(--text-secondary-color); margin: 0;">{casos_sucesso} <span style="font-size: 0.8em;">de</span> {total_grupos} <span style="font-size: 0.8em;">Casos</span></p>
        {sucesso_view_icon_html}
    </div>
    '''

    tooltip_volume_casos = "Distribuição do total de casos únicos analisados no período."
    body_content += f'''
    <div class="card">
        <h3><span class="card-title">Volume de Casos</span><div class="tooltip-container"><span class="info-icon">i</span><div class="tooltip-content">{escape(tooltip_volume_casos)}</div></div></h3>
        <div class="volume-card-item"><span class="volume-card-label">Total de Casos</span><span class="volume-card-value">{total_grupos}</span></div>
        <div class="volume-card-item"><span class="volume-card-label">Remediados (Estável)</span><span class="volume-card-value" style="color: var(--success-color);">{casos_ok_estaveis}</span></div>
        <div class="volume-card-item"><span class="volume-card-label">Remediados (Frequente)</span><span class="volume-card-value" style="color: var(--warning-color);">{grupos_instabilidade}</span></div>
        <div class="volume-card-item"><span class="volume-card-label">Sem Remediação</span><span class="volume-card-value" style="color: var(--danger-color);">{grupos_atuacao}</span></div>
    </div>
    '''

    tooltip_volume = "Distribuição do total de alertas únicos analisados no período."
    sem_remediacao_color_style = 'color: var(--danger-color);' if total_alertas_problemas > 0 else 'color: var(--text-secondary-color);'
    remediados_color_style = 'color: var(--success-color);'
    body_content += f'''
    <div class="card">
        <h3><span class="card-title">Volume de Alertas</span><div class="tooltip-container"><span class="info-icon">i</span><div class="tooltip-content">{escape(tooltip_volume)}</div></div></h3>
        <div class="volume-card-item"><span class="volume-card-label">Total de Alertas</span><span class="volume-card-value">{total_alertas_geral}</span></div>
        <div class="volume-card-item"><span class="volume-card-label">Remediados (Estável)</span><span class="volume-card-value" style="{remediados_color_style}">{total_alertas_remediados_ok}</span></div>
        <div class="volume-card-item"><span class="volume-card-label">Remediados (Frequente)</span><span class="volume-card-value" style="color: var(--warning-color);">{total_alertas_instabilidade}</span></div>
        <div class="volume-card-item"><span class="volume-card-label">Sem Remediação</span><span class="volume-card-value" style="{sem_remediacao_color_style}">{total_alertas_problemas}</span></div>
        <a href="visualizador_json.html" target="_blank" class="download-link" title="Visualizar JSON com todos os Casos">{VIEW_ICON_SVG}</a>
    </div>
    '''

    tooltip_top5 = "As 5 squads com maior carga de criticidade, classificadas pela soma da prioridade de todos os seus casos em aberto."
    
    squads_prioritarias = df_atuacao.groupby(COL_ASSIGNMENT_GROUP, observed=True).agg(
        score_acumulado=('score_ponderado_final', 'sum'),
        total_casos=('score_ponderado_final', 'size')
    ).reset_index()
    top_5_squads_agrupadas = squads_prioritarias.sort_values(by='score_acumulado', ascending=False).head(5)

    body_content += f'''
    <div class="card" style="padding-bottom: 15px;">
        <h3><span class="card-title">Top 5 Squads Prioritárias</span><div class="tooltip-container"><span class="info-icon">i</span><div class="tooltip-content" style="width: 280px; margin-left: -140px;">{escape(tooltip_top5)}</div></div></h3>
        <div style="flex-grow: 1; display: flex; flex-direction: column;">
    '''
    if not top_5_squads_agrupadas.empty:
        max_score = top_5_squads_agrupadas['score_acumulado'].max() if not top_5_squads_agrupadas.empty else 20
        min_score = 0
        for _, row in top_5_squads_agrupadas.iterrows():
            score_color, _ = gerar_cores_para_barra(row['score_acumulado'], min_score, max_score * 1.1)
            squad_name = escape(row[COL_ASSIGNMENT_GROUP])
            total_casos_txt = f"({row['total_casos']} {'casos' if row['total_casos'] > 1 else 'caso'})"
            sanitized_squad_name = re.sub(r'[^a-zA-Z0-9_-]', '', squad_name.replace(" ", "_"))
            plan_path = f"{plan_dir_base_name}/plano-de-acao-{sanitized_squad_name}.html"
            
            body_content += f'''
            <a href="{plan_path}" class="priority-list-item-new" title="Ver plano de ação para {squad_name}">
                <div class="squad-info-new">
                    {SQUAD_ICON_SVG}
                    <span class="squad-name-new">{squad_name} <small style="color:var(--text-secondary-color)">{total_casos_txt}</small></span>
                </div>
                <span class="priority-score-new" style="background-color: {score_color};">{row['score_acumulado']:.1f}</span>
            </a>
            '''
    else:
        body_content += "<p>Nenhum caso prioritário precisa de atuação. ✅</p>"
    body_content += '</div></div>'
    body_content += '</div></div>'

    body_content += f'<button type="button" class="collapsible-row active">{CHEVRON_SVG}TOP 5 - SEM REMEDIAÇÃO</button>'
    body_content += '<div class="content" style="display: none; padding-top: 20px;"><div class="grid-container" style="grid-template-columns: 1fr 1fr; align-items: stretch; gap: 20px;">'
    tooltip_squads = "Squads com maior número de Casos sem remediação."
    body_content += f'<div class="card"><h3><span class="card-title">TOP 5 SQUADS</span><div class="tooltip-container"><span class="info-icon">i</span><div class="tooltip-content">{escape(tooltip_squads)}</div></div></h3>'
    if not top_squads.empty:
        body_content += '<div class="bar-chart-container">'
        min_squad_val, max_squad_val = top_squads.min(), top_squads.max()
        for squad, count in top_squads.items():
            bar_width = (count / max_squad_val) * 100
            background_color, text_color = gerar_cores_para_barra(count, min_squad_val, max_squad_val)
            sanitized_name = re.sub(r'[^a-zA-Z0-9_-]', '', squad.replace(" ", "_"))
            plan_path = os.path.join(plan_dir_base_name, f"plano-de-acao-{sanitized_name}.html")
            body_content += f'<div class="bar-item"><div class="bar-label"><a href="{plan_path}" title="{escape(squad)}">{escape(squad)}</a></div><div class="bar-wrapper"><div class="bar" style="width: {bar_width}%; background-color: {background_color}; color: {text_color};">{count}</div></div></div>'
        body_content += '</div>'
    else:
        body_content += "<p>Nenhuma squad com casos que precisam de atuação. ✅</p>"
    squads_com_casos_count = len(all_squads[all_squads > 0])
    if squads_com_casos_count > len(top_squads):
        body_content += f'<div class="footer-link"><a href="todas_as_squads.html">Ver todas as squads ({squads_com_casos_count}) &rarr;</a></div>'
    body_content += '</div>'

    tooltip_abertos = "Tipos de problemas que mais geraram alertas sem remediação."
    body_content += f'<div class="card"><h3><span class="card-title">TOP 5 ALERTAS</span><div class="tooltip-container"><span class="info-icon">i</span><div class="tooltip-content">{escape(tooltip_abertos)}</div></div></h3>'
    if not top_problemas_atuacao.empty:
        body_content += '<div class="bar-chart-container">'
        min_val, max_val = top_problemas_atuacao.min(), top_problemas_atuacao.max()
        details_base_dir = os.path.basename(details_dir)
        for problem, count in top_problemas_atuacao.items():
            bar_width = (count / max_val) * 100
            background_color, text_color = gerar_cores_para_barra(count, min_val, max_val)
            sanitized_name = re.sub(r'[^a-zA-Z0-9_-]', '', problem[:50].replace(" ", "_"))
            details_path = os.path.join(details_base_dir, f"detalhe_aberto_{sanitized_name}.html")
            body_content += f'<div class="bar-item"><div class="bar-label"><a href="{details_path}" title="Ver detalhes">{escape(problem)}</a></div><div class="bar-wrapper"><div class="bar" style="width: {bar_width}%; background-color: {background_color}; color: {text_color};">{count}</div></div></div>'
        body_content += '</div>'
    else: body_content += "<p>Nenhum caso em aberto. ✅</p>"
    body_content += '</div></div>'
    
    tooltip_metricas = "Categorias de métricas com maior número de Casos sem remediação."
    body_content += f'<div class="card full-width"><h3><span class="card-title">TOP 5 CATEGORIAS</span><div class="tooltip-container"><span class="info-icon">i</span><div class="tooltip-content">{escape(tooltip_metricas)}</div></div></h3>'
    if not top_metrics.empty:
        body_content += '<div class="bar-chart-container">'
        min_metric_val, max_metric_val = top_metrics.min(), top_metrics.max()
        details_base_dir = os.path.basename(details_dir)
        for metric, count in top_metrics.items():
            bar_width = (count / max_metric_val) * 100
            background_color, text_color = gerar_cores_para_barra(count, min_metric_val, max_metric_val)
            sanitized_name = re.sub(r'[^a-zA-Z0-9_-]', '', metric.replace(" ", "_"))
            details_path = os.path.join(details_base_dir, f"detalhe_metrica_{sanitized_name}.html")
            label_html = f'<a href="{details_path}" title="Ver detalhes">{escape(metric)}</a>'
            body_content += f'<div class="bar-item"><div class="bar-label">{label_html}</div><div class="bar-wrapper"><div class="bar" style="width: {bar_width}%; background-color: {background_color}; color: {text_color};">{count}</div></div></div>'
        body_content += '</div>'
    else: body_content += "<p>Nenhuma categoria com casos em aberto. ✅</p>"
    body_content += '</div></div>'

    body_content += f'<button type="button" class="collapsible-row active">{CHEVRON_SVG}TENDÊNCIAS E OPORTUNIDADES</button>'
    body_content += '<div class="content" style="display: none; padding-top: 20px;"><div class="grid-container" style="grid-template-columns: 1fr; gap: 20px;">'
    
    tooltip_instabilidade_chart = "Problemas que mais geram alertas recorrentes, mesmo com a remediação funcionando. Indicam instabilidade crônica."
    body_content += f'<div class="card"><h3><span class="card-title">TOP 5 PONTOS DE ATENÇÃO</span><div class="tooltip-container"><span class="flashing-icon">🚨</span><div class="tooltip-content" style="width: 300px;">{escape(tooltip_instabilidade_chart)}</div></div></h3>'
    if not top_problemas_instabilidade.empty:
        body_content += '<div class="bar-chart-container">'
        min_val, max_val = top_problemas_instabilidade.min(), top_problemas_instabilidade.max()
        details_base_dir = os.path.basename(details_dir)
        for problem, count in top_problemas_instabilidade.items():
            bar_width = (count / max_val) * 100
            background_color, text_color = "hsl(45, 90%, 55%)", "var(--text-color-dark)"
            sanitized_name = re.sub(r'[^a-zA-Z0-9_-]', '', problem[:50].replace(" ", "_"))
            details_path = os.path.join(details_base_dir, f"detalhe_instabilidade_{sanitized_name}.html")
            body_content += f'<div class="bar-item"><div class="bar-label"><a href="{details_path}" title="Ver detalhes">{escape(problem)}</a></div><div class="bar-wrapper"><div class="bar" style="width: {bar_width}%; background-color: {background_color}; color: {text_color};">{count}</div></div></div>'
        body_content += '</div>'
    else: body_content += "<p>Nenhum ponto de alta recorrência crônica detectado. ✅</p>"
    body_content += '</div>'
    
    mensagem_tooltip = "Problemas com menor frequência de remediação, mas que também podem indicar instabilidade e são candidatos a uma análise de causa raiz definitiva."
    body_content += f'<div class="card"><h3><span class="card-title">TOP 5 REMEDIAÇÕES EXECUTADAS</span><div class="tooltip-container"><span class="flashing-icon">⚠️</span><div class="tooltip-content">{escape(mensagem_tooltip)}</div></div></h3>'
    if not top_problemas_remediados.empty:
        body_content += '<div class="bar-chart-container">'
        min_val, max_val = top_problemas_remediados.min(), top_problemas_remediados.max()
        details_base_dir = os.path.basename(details_dir)
        for problem, count in top_problemas_remediados.items():
            bar_width = (count / max_val) * 100
            background_color, text_color = f"hsl(155, 60%, 45%)", "white"
            sanitized_name = re.sub(r'[^a-zA-Z0-9_-]', '', problem[:50].replace(" ", "_"))
            details_path = os.path.join(details_base_dir, f"detalhe_remediado_{sanitized_name}.html")
            body_content += f'<div class="bar-item"><div class="bar-label"><a href="{details_path}" title="Ver detalhes">{escape(problem)}</a></div><div class="bar-wrapper"><div class="bar" style="width: {bar_width}%; background-color: {background_color}; color: {text_color};">{count}</div></div></div>'
        body_content += '</div>'
    else: body_content += "<p><strong>⚠️ Nenhum problema remediado automaticamente.</strong></p>"
    body_content += '</div></div></div>'

    body_content += f'<button type="button" class="collapsible-row active">{CHEVRON_SVG}TOP 10 - ALERTAS (GERAL)</button>'
    body_content += '<div class="content" style="display: none; padding-top: 20px;">'
    tooltip_recorrentes = "Os 10 tipos de problemas que mais ocorreram (volume total de alertas), independente da automação."
    body_content += f'<div class="card"><h3><span class="card-title">TOP 10 ALERTAS</span><div class="tooltip-container"><span class="info-icon">i</span><div class="tooltip-content">{escape(tooltip_recorrentes)}</div></div></h3>'
    if not top_problemas_geral.empty:
        body_content += '<div class="bar-chart-container">'
        min_prob_val, max_prob_val = top_problemas_geral.min(), top_problemas_geral.max()
        details_base_dir = os.path.basename(details_dir)
        for problem, count in top_problemas_geral.items():
            bar_width = (count / max_prob_val) * 100
            background_color, text_color = gerar_cores_para_barra(count, min_prob_val, max_prob_val)
            sanitized_name = re.sub(r'[^a-zA-Z0-9_-]', '', problem[:50].replace(" ", "_"))
            details_path = os.path.join(details_base_dir, f"detalhe_geral_{sanitized_name}.html")
            body_content += f'<div class="bar-item"><div class="bar-label"><a href="{details_path}" title="Ver detalhes">{escape(problem)}</a></div><div class="bar-wrapper"><div class="bar" style="width: {bar_width}%; background-color: {background_color}; color: {text_color};">{count}</div></div></div>'
        body_content += '</div>'
    else: body_content += "<p>Nenhum problema recorrente. ✅</p>"
    body_content += '</div></div>'

    footer_text = f"Relatório gerado em {timestamp_str}"
    html_content = HTML_TEMPLATE.format(title=title, body=body_content, footer_timestamp=footer_text)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"✅ Resumo executivo gerado: {output_path}")

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            gerar_visualizador_json(os.path.dirname(output_path), f.read())
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
    csv_payload = csv_content.replace('`', '\\`')
    try:
        with open(template_path, 'r', encoding='utf-8') as f_template, open(output_path, 'w', encoding='utf-8') as f_out:
            for line in f_template:
                if '__CSV_DATA_PLACEHOLDER__' in line and 'const csvDataPayload' in line:
                    indent = line[:len(line) - len(line.lstrip())]
                    f_out.write(f"{indent}const csvDataPayload = `{csv_payload}`;\n")
                else:
                    f_out.write(line.replace('remediados.csv', os.path.basename(ok_csv_path)))
    except FileNotFoundError:
        print(f"❌ Erro: Template '{template_path}' não encontrado.", file=sys.stderr)
        return
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
    csv_payload = csv_content.replace('`', '\\`')
    try:
        with open(template_path, 'r', encoding='utf-8') as f_template, open(output_path, 'w', encoding='utf-8') as f_out:
            for line in f_template:
                if '__CSV_DATA_PLACEHOLDER__' in line and 'const csvDataPayload' in line:
                    indent = line[:len(line) - len(line.lstrip())]
                    f_out.write(f"{indent}const csvDataPayload = `{csv_payload}`;\n")
                else:
                    line = line.replace('Sucesso da Automação - remediados.csv', 'Instabilidade Crônica - remediados_frequentes.csv')
                    line = line.replace('remediados.csv', os.path.basename(instability_csv_path))
                    f_out.write(line)
    except FileNotFoundError:
        print(f"❌ Erro: Template '{template_path}' não encontrado.", file=sys.stderr)
        return
    print(f"✅ Página de visualização de instabilidade gerada: {output_path}")

def gerar_pagina_logs_invalidos(output_dir: str, log_csv_path: str, template_path: str):
    """Gera uma página HTML para visualização dos Check last columm ."""
    print(f"📄 Gerando página de visualização para '{os.path.basename(log_csv_path)}'...")
    output_path = os.path.join(output_dir, "visualizador_logs_invalidos.html")
    try:
        with open(log_csv_path, 'r', encoding='utf-8') as f:
            csv_content = f.read().lstrip()
    except FileNotFoundError:
        csv_content = ""
        print(f"⚠️ Aviso: Arquivo '{log_csv_path}' não encontrado. Gerando página vazia.")
    
    csv_payload = csv_content.replace('`', '\\`')
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f_template, open(output_path, 'w', encoding='utf-8') as f_out:
            for line in f_template:
                if '__CSV_DATA_PLACEHOLDER__' in line and 'const csvDataPayload' in line:
                    indent = line[:len(line) - len(line.lstrip())]
                    f_out.write(f"{indent}const csvDataPayload = `{csv_payload}`;\n")
                else:
                    line = line.replace('Sucesso da Automação - remediados.csv', f'Check last columm  - {log_csv_path}')
                    line = line.replace('remediados.csv', log_csv_path)
                    f_out.write(line)
    except FileNotFoundError:
        print(f"❌ Erro: Template '{template_path}' não encontrado.", file=sys.stderr)
        return
    print(f"✅ Página de visualização de logs inválidos gerada: {output_path}")


def gerar_visualizador_json(output_dir: str, json_data_str: str):
    """
    Cria um arquivo HTML estático para visualizar o JSON de forma formatada.
    """
    file_path = os.path.join(output_dir, "visualizador_json.html")
    
    # Conteúdo do visualizador de JSON
    HTML_VISUALIZADOR_JSON = f'''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Visualizador de Problemas (JSON)</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/json.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css">
    <style>
        :root {{
            --bg-color: #1a1c2f;
            --card-color: #2c2f48;
            --text-color: #f0f0f0;
            --border-color: #404466;
            --accent-color: #4e73df;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: auto;
        }}
        h1 {{
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 10px;
            font-weight: 500;
        }}
        a {{
            color: var(--accent-color);
            text-decoration: none;
            font-weight: 500;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        #json-container {{
            background-color: var(--card-color);
            border-radius: 8px;
            padding: 20px;
            border: 1px solid var(--border-color);
            white-space: pre-wrap; 
            word-break: break-all;
        }}
        .hljs {{
            background: transparent !important;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Resumo de Casos (JSON)</h1>
        <p><a href="resumo_geral.html">&larr; Voltar para o Dashboard</a></p>
        <div id="json-container">
            <pre><code id="json-content" class="language-json"></code></pre>
        </div>
    </div>

    <script>
        // Os dados do JSON são injetados aqui pelo script Python
        const jsonData = {json_data_str};
        
        try {{
            const formattedJson = JSON.stringify(jsonData, null, 2);
            const codeElement = document.getElementById('json-content');
            codeElement.textContent = formattedJson;
            hljs.highlightElement(codeElement);
        }} catch (error) {{
            console.error("Erro ao formatar o JSON embutido:", error);
            document.getElementById('json-content').textContent = "Erro ao renderizar o JSON. Verifique o console para mais detalhes.";
        }}
    </script>
</body>
</html>
'''
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(HTML_VISUALIZADOR_JSON)
        print(f"✅ Visualizador de JSON gerado: {file_path}")
    except Exception as e:
        print(f"❌ Erro ao gerar o visualizador de JSON: {e}", file=sys.stderr)

# =============================================================================
# EXECUÇÃO PRINCIPAL
# =============================================================================

def main():
    """
    Ponto de entrada principal do script.
    Analisa os argumentos da linha de comando e orquestra o fluxo de análise e geração de relatórios.
    """
    parser = argparse.ArgumentParser(description="Analisa um arquivo CSV de alertas para identificar grupos que necessitam de atuação.")
    parser.add_argument("input_file", help="Caminho para o arquivo CSV de entrada.")
    
    parser.add_argument("--output-summary", default="resumo_geral.html", help="Caminho para o resumo executivo HTML.")
    parser.add_argument("--output-actuation", help="Caminho para o CSV de atuação geral.")
    parser.add_argument("--output-ok", help="Caminho para o CSV de alertas OK ou estabilizados.")
    parser.add_argument("--output-instability", help="Caminho para o CSV de casos de instabilidade.")
    parser.add_argument("--plan-dir", help="Diretório para os planos de ação por squad.")
    parser.add_argument("--details-dir", help="Diretório para as páginas de detalhe dos problemas.")
    parser.add_argument("--output-json", required=True, help="Caminho para o resumo em JSON.")
    parser.add_argument("--resumo-only", action='store_true', help="Se especificado, gera apenas o arquivo de resumo JSON.")
    parser.add_argument("--trend-report-path", help="Caminho opcional para um relatório de tendência.")
    
    args = parser.parse_args()

    if not args.resumo_only:
        required_for_full_run = [
            args.output_actuation,
            args.output_ok,
            args.output_instability,
            args.plan_dir,
            args.details_dir
        ]
        if not all(required_for_full_run):
            parser.error(
                "para o modo de análise completa, os argumentos --output-actuation, --output-ok, "
                "--output-instability, --plan-dir e --details-dir são obrigatórios."
            )

    timestamp_str = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")

    df, num_logs_invalidos = carregar_dados(args.input_file)
    summary = analisar_grupos(df)
    export_summary_to_json(summary.copy(), args.output_json)

    if not args.resumo_only:
        output_dir = os.path.dirname(args.output_summary) or '.'
        summary_filename = os.path.basename(args.output_summary)
        
        df_atuacao = gerar_relatorios_csv(summary, args.output_actuation, args.output_ok, args.output_instability)
        
        gerar_resumo_executivo(
            summary, df_atuacao, num_logs_invalidos, args.output_summary, args.plan_dir,
            args.details_dir, args.output_actuation, args.output_ok,
            args.output_json, timestamp_str, args.trend_report_path
        )
        
        gerar_planos_por_squad(df_atuacao, args.plan_dir, timestamp_str)
        all_squads = df_atuacao[COL_ASSIGNMENT_GROUP].value_counts()
        gerar_pagina_squads(all_squads, args.plan_dir, output_dir, summary_filename, timestamp_str)
        
        sucesso_template_file = "templates/sucesso_template.html"
        gerar_pagina_sucesso(output_dir, args.output_ok, sucesso_template_file)
        gerar_pagina_instabilidade(output_dir, args.output_instability, sucesso_template_file)
        
        if num_logs_invalidos > 0:
            gerar_pagina_logs_invalidos(output_dir, LOG_INVALIDOS_FILENAME, sucesso_template_file)


if __name__ == "__main__":
    main()