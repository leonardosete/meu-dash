import pandas as pd
import sys
import os
import argparse
from html import escape
import re
from string import Template

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>$title</title>
    <style>
        :root {
            --bg-color: #1a1c2f;
            --card-color: #2c2f48;
            --text-color: #f0f0f0;
            --text-secondary-color: #a0a0b0;
            --border-color: #404466;
            --success-color: #1cc88a;
            --warning-color: #f6c23e;
            --danger-color: #e74a3b;
            --info-color: #4e73df;
            --persistent-color: #D89F3B;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: var(--text-color);
            background-color: var(--bg-color);
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: auto;
        }
        h1, h2, h3 {
            color: var(--text-color);
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 10px;
            font-weight: 500;
        }
        h1 { font-size: 2em; margin-bottom: 20px; }
        h2 { font-size: 1.5em; margin-top: 40px; border: none; }
        h3 {
            font-size: 1.2em;
            margin-top: 20px;
            margin-bottom: 15px;
            border-bottom: none;
            color: var(--text-secondary-color);
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .card {
            background: var(--card-color);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            margin-bottom: 25px;
        }
        
        .kpi-flow-container {
            display: flex;
            flex-wrap: nowrap;
            align-items: center;
            justify-content: space-between;
            gap: 15px;
            margin-bottom: 25px;
            overflow-x: auto;
            padding-bottom: 10px;
        }
        .kpi-flow-item { flex: 1; min-width: 160px; text-align: center; }
        .kpi-flow-connector { font-size: 2.5em; color: var(--border-color); font-weight: bold; flex: 0; text-align: center; }
        .kpi-flow-group {
            display: flex; flex-direction: column; gap: 15px;
            border-left: 2px dashed var(--border-color); border-right: 2px dashed var(--border-color);
            padding: 0 20px; margin: 0 10px;
        }
        .kpi-card-enhanced {
            background: var(--card-color); border: 1px solid var(--border-color);
            border-radius: 8px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); text-align: center;
        }
        .kpi-card-enhanced .kpi-value { font-size: 2.8em; margin: 0; line-height: 1.1; font-weight: 700; }
        .kpi-card-enhanced .kpi-label { font-size: 0.9em; font-weight: 500; margin: 5px 0 8px 0; color: var(--text-color); }
        .kpi-card-enhanced .kpi-subtitle {
            font-size: 0.8em; color: var(--text-secondary-color); margin: 0;
            background-color: var(--bg-color); padding: 3px 8px; border-radius: 4px; display: inline-block;
            cursor: help;
        }
        .icon-minus::before { content: "−"; color: var(--danger-color); }
        .icon-plus::before { content: "+"; color: var(--success-color); }

        .definition-box, .insight-box {
            padding: 15px 20px; margin: 15px 0 25px 0; border-radius: 0 8px 8px 0;
            color: var(--text-secondary-color); line-height: 1.7;
        }
        .definition-box { background-color: rgba(78, 115, 223, 0.1); border-left: 4px solid var(--info-color); }
        .insight-box { background-color: rgba(246, 194, 62, 0.1); border-left: 4px solid var(--warning-color); }
        
        table { 
            width: 100%; border-collapse: collapse; margin-top: 20px; 
            box-shadow: 0 2px 8px rgba(0,0,0,0.2); border-radius: 8px; overflow: hidden;
        }
        th, td { 
            padding: 12px 15px; text-align: left; 
            border-bottom: 1px solid var(--border-color); vertical-align: middle;
        }
        th { background-color: #262940; font-weight: bold; }
        tbody tr:nth-child(even) { background-color: #33365a; }
        tr:not(.details-row):hover { background-color: #3c4062; }
        tbody tr:last-child td { border-bottom: none; }
        tfoot tr { background-color: #262940; font-weight: bold; border-top: 2px solid var(--info-color); }
        .center { text-align: center; }
        
        .change-bar-container { display: flex; align-items: center; gap: 10px; }
        .bar-wrapper { flex-grow: 1; background-color: var(--border-color); border-radius: 4px; height: 12px; }
        .bar { height: 100%; border-radius: 4px; }
        .bar.positive { background-color: var(--success-color); }
        .bar.negative { background-color: var(--danger-color); }
        .change-value { font-weight: bold; min-width: 45px; text-align: right; }

        .kpi-split-layout { display: flex; flex-wrap: wrap; align-items: center; gap: 40px; padding: 20px 30px; }
        .kpi-split-layout__text { flex: 1; min-width: 280px; }
        .kpi-split-layout__text h2 { border: none; margin-top: 0; margin-bottom: 15px; font-size: 1.4em; }
        .kpi-split-layout__text p { color: var(--text-secondary-color); margin-bottom: 15px; line-height: 1.7; font-size: 0.95em;}
        .kpi-split-layout__text small { color: var(--text-secondary-color); opacity: 0.7; }
        .kpi-split-layout__chart { flex-shrink: 0; margin: 0 auto; }

        .progress-donut {
            --p: 0; --c: var(--info-color); --b: 18px; --w: 160px;
            width: var(--w); aspect-ratio: 1; position: relative; display: grid;
            place-content: center; margin: 5px; border-radius: 50%;
            background: conic-gradient(var(--c) calc(var(--p) * 1%), var(--border-color) 0);
        }
        .progress-donut::before { content: ""; position: absolute; inset: var(--b); background: var(--card-color); border-radius: 50%; }
        .progress-donut-text-content { position: relative; text-align: center; }
        .progress-donut__value { font-size: 1.9em; font-weight: 700; line-height: 1; color: var(--c); }

        a { color: var(--info-color); text-decoration: none; font-weight: 500; }
        a:hover { text-decoration: underline; }
        
        .collapsible {
            background-color: var(--card-color); color: var(--text-color); cursor: pointer; padding: 18px; width: 100%;
            border: 1px solid var(--border-color); border-radius: 8px; text-align: left; outline: none; font-size: 1.3em;
            font-weight: 500; transition: background-color 0.3s ease; display: flex; align-items: center; justify-content: space-between;
        }
        .collapsible:hover { background-color: #33365a; }
        .collapsible.active { border-bottom-left-radius: 0; border-bottom-right-radius: 0; }
        .collapsible .chevron { transition: transform 0.3s ease; margin-left: 15px; }
        .collapsible.active .chevron { transform: rotate(90deg); }
        .collapsible-content {
            padding: 0 25px; background-color: var(--card-color); border: 1px solid var(--border-color); border-top: none;
            border-bottom-left-radius: 8px; border-bottom-right-radius: 8px; overflow: hidden; max-height: 0;
            transition: max-height 0.3s ease-out, padding 0.3s ease-out; margin-bottom: 20px;
        }
        
        .tab-container {
            padding-top: 5px;
        }
        .tab-links {
            display: flex;
            border-bottom: 2px solid var(--border-color);
            margin-bottom: 25px;
        }
        .tab-link {
            padding: 12px 20px;
            cursor: pointer;
            background: none;
            border: none;
            color: var(--text-secondary-color);
            font-size: 1.05em;
            font-weight: 500;
            transition: color 0.3s, border-bottom 0.3s;
            border-bottom: 3px solid transparent;
            margin-bottom: -2px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .tab-link:hover {
            color: var(--text-color);
        }
        .tab-link.active {
            color: var(--info-color);
            border-bottom-color: var(--info-color);
        }
        .tab-content {
            display: none;
            animation: fadeIn 0.5s;
        }
        .tab-content.active {
            display: block;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .expandable-row { cursor: pointer; }
        .details-row { display: none; }
        .details-row.active { display: table-row; }
        .details-row > td { padding: 0 !important; background-color: rgba(0,0,0,0.15); }
        .details-row-content { padding: 20px 25px; }
        .details-row-content h4 { margin-top: 0; color: var(--text-secondary-color); font-weight: 500; }
        .sub-table { width: 100%; border-collapse: collapse; margin-top: 10px; box-shadow: none; border-radius: 4px; overflow: hidden; }
        .sub-table th, .sub-table td { font-size: 0.9em; border-bottom: 1px solid var(--border-color); }
        .sub-table tr:last-child td { border-bottom: none; }
        .expandable-row .chevron { transition: transform 0.3s ease; }
        .expandable-row.active .chevron { transform: rotate(90deg); }
    </style>
</head>
<body>
    <div class="container">
        $body
    </div>
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
                        if(targetContent) {
                            targetContent.classList.add('active');
                        }
                        updateParentHeights(targetContent || link);
                    });
                });
            });

            document.querySelectorAll(".expandable-row").forEach(function(row) {
                row.addEventListener("click", function() {
                    this.classList.toggle("active");
                    var targetId = this.dataset.target;
                    var detailRow = document.getElementById(targetId);
                    if (detailRow) {
                        detailRow.classList.toggle("active");
                        updateParentHeights(detailRow);
                    }
                });
            });
        });
    </script>
</body>
</html>
'''

ACTION_NEEDED_FLAGS = [
    "Analisar intermitência na remediação",
    "Desenvolver remediação (nenhum sucesso registrado)",
    "Verificar coleta de dados da remediação (status ausente)",
    "Analisar causa raiz das falhas (remediação inconsistente)"
]

CASE_ID_COLS = ['assignment_group', 'short_description', 'node', 'cmdb_ci', 'source', 'metric_name', 'cmdb_ci.sys_class_name']

def sanitize_for_id(text):
    """Cria uma string segura para ser usada como ID HTML."""
    return re.sub(r'[^a-zA-Z0-9\-_]', '-', str(text)).lower()

def load_summary_from_json(filepath: str):
    try:
        df = pd.read_json(filepath, orient='records')
        print(f"✅ Resumo de problemas carregado de: {filepath}")
        return df
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ Erro ao carregar o arquivo JSON '{filepath}': {e}", file=sys.stderr)
        return None

def calculate_kpis_and_merged_df(df_p1, df_p2):
    """
    Calcula os KPIs e retorna o DataFrame mesclado que é a base para toda a análise.
    """
    df_p1_atuacao = df_p1[df_p1["acao_sugerida"].isin(ACTION_NEEDED_FLAGS)].copy()
    df_p2_atuacao = df_p2[df_p2["acao_sugerida"].isin(ACTION_NEEDED_FLAGS)].copy()
    
    valid_case_id_cols = [c for c in CASE_ID_COLS if c in df_p1_atuacao.columns and c in df_p2_atuacao.columns]
    merged_df = pd.merge(df_p1_atuacao, df_p2_atuacao, on=valid_case_id_cols, how='outer', suffixes=('_p1', '_p2'), indicator=True)
    
    total_p1 = len(df_p1_atuacao)
    total_p2 = len(df_p2_atuacao)
    resolved = merged_df['_merge'].eq('left_only').sum()
    new = merged_df['_merge'].eq('right_only').sum()
    persistent = merged_df['_merge'].eq('both').sum()
    
    alerts_total_p1 = df_p1_atuacao['alert_count'].sum()
    alerts_total_p2 = df_p2_atuacao['alert_count'].sum()
    alerts_resolved = merged_df[merged_df['_merge'] == 'left_only']['alert_count_p1'].sum()
    alerts_new = merged_df[merged_df['_merge'] == 'right_only']['alert_count_p2'].sum()
    alerts_persistent = merged_df[merged_df['_merge'] == 'both']['alert_count_p2'].sum()
    
    improvement_rate = (resolved / total_p1 * 100) if total_p1 > 0 else 100

    kpis = {
        'total_p1': total_p1, 'resolved': resolved, 'new': new, 'total_p2': total_p2, 'persistent': persistent, 
        'alerts_total_p1': int(alerts_total_p1), 'alerts_total_p2': int(alerts_total_p2),
        'alerts_resolved': int(alerts_resolved), 'alerts_new': int(alerts_new), 'alerts_persistent': int(alerts_persistent),
        'improvement_rate': improvement_rate
    }
    
    return kpis, merged_df

def analyze_persistent_cases(merged_df):
    """
    Analisa apenas os casos persistentes (existiam em ambos os períodos).
    """
    persistent_df = merged_df[merged_df['_merge'] == 'both'].copy()
    if persistent_df.empty:
        return pd.DataFrame()
    
    summary = persistent_df.groupby('assignment_group').agg(
        num_cases=('assignment_group', 'size'),
        alerts_p1=('alert_count_p1', 'sum'),
        alerts_p2=('alert_count_p2', 'sum')
    ).fillna(0).astype(int)
    summary['change'] = summary['alerts_p2'] - summary['alerts_p1']
    summary['abs_change'] = summary['change'].abs()
    return summary.sort_values(by=['num_cases', 'abs_change'], ascending=[False, False])


def generate_kpis_html(kpis):
    saldo_icon = ""
    if kpis['total_p2'] > kpis['total_p1']:
        saldo_icon = "<span style='font-size: 0.7em; color: var(--danger-color);'>▲</span>"
    elif kpis['total_p2'] < kpis['total_p1']:
        saldo_icon = "<span style='font-size: 0.7em; color: var(--success-color);'>▼</span>"

    kpi_html = "<h2>Panorama Geral: O Funil de Resolução</h2>"
    kpi_html += "<div class='definition-box'><strong>Definição:</strong> Um 'Caso' é um problema único que precisa de ação. O fluxo abaixo mostra a evolução do número de casos e do volume total de alertas entre os dois períodos.</div>"
    
    kpi_html += f'''<div class="kpi-flow-container">
        <div class="kpi-flow-item"><div class="kpi-card-enhanced">
            <p class="kpi-value" style="color: var(--info-color);">{kpis['total_p1']}</p>
            <p class="kpi-label">Casos em Aberto (Anterior)</p>
            <p class="kpi-subtitle" title="Total de problemas únicos do período anterior que não possuíam remediação bem-sucedida e exigiam ação.">{kpis['alerts_total_p1']} alertas</p>
        </div></div>
        <div class="kpi-flow-connector icon-minus"></div>
        <div class="kpi-flow-group">
            <div class="kpi-flow-item" style="flex:auto;"><div class="kpi-card-enhanced">
                <p class="kpi-value" style="color: var(--success-color);">{kpis['resolved']}</p>
                <p class="kpi-label">Casos Resolvidos</p>
                <p class="kpi-subtitle" title="Casos que passaram a ter remediação com sucesso (REM_OK) ou cujo volume de alertas foi zerado.">{kpis['alerts_resolved']} alertas resolvidos</p>
            </div></div>
            <div class="kpi-flow-item" style="flex:auto;"><div class="kpi-card-enhanced">
                <p class="kpi-value" style="color: var(--persistent-color);">{kpis['persistent']}</p>
                <p class="kpi-label">Casos Persistentes</p>
                <p class="kpi-subtitle" title="Problemas que já existiam no período anterior e que continuam sem uma remediação efetiva no período atual.">{kpis['alerts_persistent']} alertas</p>
            </div></div>
        </div>
        <div class="kpi-flow-connector icon-plus"></div>
        <div class="kpi-flow-item"><div class="kpi-card-enhanced">
            <p class="kpi-value" style="color: var(--warning-color);">{kpis['new']}</p>
            <p class="kpi-label">Novos Casos</p>
            <p class="kpi-subtitle" title="Problemas que não existiam no período anterior e que surgiram no período atual já necessitando de ação.">{kpis['alerts_new']} alertas</p>
        </div></div>
        <div class="kpi-flow-connector">=</div>
        <div class="kpi-flow-item"><div class="kpi-card-enhanced">
            <p class="kpi-value" style="color: {'var(--danger-color)' if kpis['total_p2'] > kpis['total_p1'] else 'var(--success-color)'};">{saldo_icon} {kpis['total_p2']}</p>
            <p class="kpi-label">Saldo Atual de Casos</p>
            <p class="kpi-subtitle" title="Resultado final: a soma dos Casos Persistentes com os Novos Casos. Representa o total de problemas que exigem ação neste período.">{kpis['alerts_total_p2']} alertas</p>
        </div></div>
    </div>'''

    kpi_html += f"""
    <div class="insight-box">
        💡 <strong>Análise e Insight:</strong> A taxa de resolução de <strong>{kpis['improvement_rate']:.1f}%</strong> indica a porcentagem de casos do período anterior que foram efetivamente resolvidos. O saldo atual é o resultado dos casos que persistiram somados aos novos que surgiram.
    </div>"""
    
    progress_percent = kpis['improvement_rate']
    resolved_count = kpis['resolved']
    total_previous = kpis['total_p1']
    
    gauge_color_var = "var(--success-color)"
    card_bg_style = "background-color: rgba(28, 200, 138, 0.1);"
    if kpis['improvement_rate'] < 70:
        gauge_color_var = "var(--warning-color)"
        card_bg_style = "background-color: rgba(246, 194, 62, 0.1);"
    if kpis['improvement_rate'] < 50:
        gauge_color_var = "var(--danger-color)"
        card_bg_style = "background-color: rgba(231, 74, 59, 0.1);"

    kpi_html += f"""
    <div class="card kpi-split-layout" style="{card_bg_style}">
        <div class="kpi-split-layout__chart">
            <div class="progress-donut" style="--p:{progress_percent}; --c:{gauge_color_var};">
                <div class="progress-donut-text-content"><div class="progress-donut__value">{progress_percent:.1f}%</div></div>
            </div>
        </div>
        <div class="kpi-split-layout__text">
            <h2>Taxa de Resolução de Casos - Perído Anterior</h2>
            <p>Dos <strong>{total_previous} casos</strong> que precisavam de ação no período anterior, <strong>{resolved_count} foram resolvidos</strong>, resultando na taxa de resolução ao lado.</p>
            <small>Este indicador mede a eficácia na eliminação de problemas pendentes de um período para o outro.</small>
        </div>
    </div>"""
    
    return kpi_html

def _generate_change_bar_html(change, max_abs_change):
    bar_html = ""
    change_sign = ""
    change_color = "var(--text-secondary-color)"

    if change > 0:
        bar_class = "negative"
        change_color = "var(--danger-color)"
        change_sign = "+"
    elif change < 0:
        bar_class = "positive"
        change_color = "var(--success-color)"
    else: # change == 0
        bar_class = "neutral"

    bar_width = (abs(change) / max_abs_change * 100) if max_abs_change > 0 else 0
    
    bar_html = f'''<div class="change-bar-container">
                    <div class="bar-wrapper"><div class="bar {bar_class}" style="width: {bar_width}%;"></div></div>
                    <span class="change-value" style="color: {change_color}">{change_sign}{change:,.0f}</span>
                 </div>'''
    return bar_html

def generate_persistent_cases_table_html(summary_df, detailed_df, label_p1, label_p2):
    if summary_df.empty:
        return "<p>Nenhum caso persistente foi identificado. Ótimo trabalho!</p>"
    
    max_abs_change = summary_df['abs_change'].max() if not summary_df.empty else 1
    
    # --- CÁLCULO DOS TOTAIS ---
    total_num_cases = summary_df['num_cases'].sum()
    total_alerts_p1 = summary_df['alerts_p1'].sum()
    total_alerts_p2 = summary_df['alerts_p2'].sum()
    total_change = summary_df['change'].sum()

    # --- GERAÇÃO DO CORPO DA TABELA ---
    table_body = "<tbody>"
    chevron_svg = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" class="chevron"><polyline points="9 18 15 12 9 6"></polyline></svg>'

    for name, row in summary_df.iterrows():
        squad_id = sanitize_for_id(name)
        details_id = f"details-{squad_id}"
        num_cases, p1_count, p2_count, change = row['num_cases'], row['alerts_p1'], row['alerts_p2'], row['change']
        bar_html = _generate_change_bar_html(change, max_abs_change)
        
        table_body += f"<tr class='expandable-row' data-target='{details_id}'>"
        table_body += f"<td><span style='display: flex; align-items: center; gap: 8px;'>{chevron_svg} {escape(str(name))}</span></td>"
        
        # --- ORDEM DAS COLUNAS ALTERADA AQUI ---
        table_body += f"<td>{bar_html}</td><td class='center'>{p2_count}</td><td class='center'>{p1_count}</td><td class='center' style='font-weight: bold;'>{num_cases}</td></tr>"
        
        squad_cases_df = detailed_df[detailed_df['assignment_group'] == name]
        details_content = "<h4>Detalhes dos Casos Persistentes</h4>"
        details_content += "<table class='sub-table'><thead><tr><th>Problema</th><th>Recurso Afetado</th><th>Alertas (Atual)</th><th>Alertas (Anterior)</th></tr></thead><tbody>"
        for _, case_row in squad_cases_df.iterrows():
            details_content += f"<tr><td>{escape(case_row['short_description'])}</td><td>{escape(case_row['cmdb_ci'])}</td><td>{int(case_row['alert_count_p2'])}</td><td>{int(case_row['alert_count_p1'])}</td></tr>"
        details_content += "</tbody></table>"
        
        table_body += f"<tr id='{details_id}' class='details-row'><td colspan='5'><div class='details-row-content'>{details_content}</div></td></tr>"
    table_body += "</tbody>"

    # --- GERAÇÃO DO RODAPÉ (TFOOT) ---
    total_change_sign = "+" if total_change > 0 else ""
    total_change_color = "var(--danger-color)" if total_change > 0 else "var(--success-color)" if total_change < 0 else "var(--text-secondary-color)"
    
    table_footer = "<tfoot><tr>"
    table_footer += f"<td>Total</td>"
    
    # --- ORDEM DAS COLUNAS DO RODAPÉ ALTERADA AQUI ---
    table_footer += f"<td><div class='change-bar-container'><span class='change-value' style='color: {total_change_color}; width: 100%; text-align: right;'>{total_change_sign}{total_change}</span></div></td>"
    table_footer += f"<td class='center'>{total_alerts_p2}</td>"
    table_footer += f"<td class='center'>{total_alerts_p1}</td>"
    table_footer += f"<td class='center'>{total_num_cases}</td>"
    table_footer += "</tr></tfoot>"

    # --- MONTAGEM FINAL DA TABELA (CABEÇALHO ALTERADO) ---
    table_html = f"<table><thead><tr><th style='width: 35%;'>Squad</th><th style='width: 25%;'>Variação de Alertas</th><th class='center'>Alertas ({escape(label_p2)})</th><th class='center'>Alertas ({escape(label_p1)})</th><th class='center'>Nº de Casos Persistentes</th></tr></thead>"
    table_html += table_body
    table_html += table_footer
    table_html += "</table>"
    
    return table_html

def generate_trend_table_html(df_merged, label_p1, label_p2):
    if df_merged.empty:
        return "<p>Nenhuma mudança registrada nesta categoria.</p>"
    
    df_merged['change'] = df_merged['count_p2'] - df_merged['count_p1']
    df_merged['abs_change'] = df_merged['change'].abs()
    df_sorted = df_merged.sort_values(by=['abs_change', 'count_p2'], ascending=[False, False])
    
    max_abs_change = df_sorted['abs_change'].max() if not df_sorted.empty else 1
    
    # --- CÁLCULO DOS TOTAIS ---
    total_p1 = df_sorted['count_p1'].sum()
    total_p2 = df_sorted['count_p2'].sum()
    total_change = df_sorted['change'].sum()
    
    # --- GERAÇÃO DO CORPO DA TABELA ---
    table_body = "<tbody>"
    for name, row in df_sorted.iterrows():
        p1_count, p2_count, change = row['count_p1'], row['count_p2'], row['change']
        bar_html = _generate_change_bar_html(change, max_abs_change)
        table_body += f"<tr><td>{escape(str(name))}</td><td>{bar_html}</td><td class='center'>{int(p2_count)}</td><td class='center'>{int(p1_count)}</td></tr>"
    table_body += "</tbody>"

    # --- GERAÇÃO DO RODAPÉ (TFOOT) ---
    total_change_sign = "+" if total_change > 0 else ""
    total_change_color = "var(--danger-color)" if total_change > 0 else "var(--success-color)" if total_change < 0 else "var(--text-secondary-color)"
    
    table_footer = "<tfoot><tr>"
    table_footer += f"<td>Total</td>"
    table_footer += f"<td><div class='change-bar-container'><span class='change-value' style='color: {total_change_color}; width: 100%; text-align: right;'>{total_change_sign}{total_change}</span></div></td>"
    table_footer += f"<td class='center'>{int(total_p2)}</td>"
    table_footer += f"<td class='center'>{int(total_p1)}</td>"
    table_footer += "</tr></tfoot>"

    # --- MONTAGEM FINAL DA TABELA ---
    table_html = f"<table><thead><tr><th>Item</th><th style='width: 35%;'>Variação de Alertas</th><th class='center'>Alertas ({escape(label_p2)})</th><th class='center'>Alertas ({escape(label_p1)})</th></tr></thead>"
    table_html += table_body
    table_html += table_footer
    table_html += "</table>"
    
    return table_html


def main():
    parser = argparse.ArgumentParser(description="Analisa a tendência entre dois resumos de problemas em JSON.")
    parser.add_argument("json_anterior", help="Caminho para o arquivo de resumo JSON do período anterior.")
    parser.add_argument("json_atual", help="Caminho para o arquivo de resumo JSON do período atual.")
    parser.add_argument("csv_anterior_name", help="Nome do arquivo CSV original do período anterior para usar como rótulo.")
    parser.add_argument("csv_atual_name", help="Nome do arquivo CSV original do período atual para usar como rótulo.")
    parser.add_argument("date_range_anterior", nargs='?', default=None, help="Intervalo de datas do período anterior (opcional).")
    parser.add_argument("date_range_atual", nargs='?', default=None, help="Intervalo de datas do período atual (opcional).")
    args = parser.parse_args()

    df_p1 = load_summary_from_json(args.json_anterior)
    df_p2 = load_summary_from_json(args.json_atual)

    if df_p1 is None or df_p2 is None:
        sys.exit("❌ Não foi possível continuar devido a erros na análise dos arquivos de resumo JSON.")

    kpis, merged_df = calculate_kpis_and_merged_df(df_p1, df_p2)
    
    new_cases_df = merged_df[merged_df['_merge'] == 'right_only'].copy()
    new_problems_summary = new_cases_df.groupby('short_description').agg(count_p2=('alert_count_p2', 'sum')).reset_index()
    new_problems_summary['count_p1'] = 0

    resolved_cases_df = merged_df[merged_df['_merge'] == 'left_only'].copy()
    resolved_problems_summary = resolved_cases_df.groupby('short_description').agg(count_p1=('alert_count_p1', 'sum')).reset_index()
    resolved_problems_summary['count_p2'] = 0

    both_cases_df = merged_df[merged_df['_merge'] == 'both'].copy()
    varying_problems_summary = both_cases_df.groupby('short_description').agg(
        count_p1=('alert_count_p1', 'sum'),
        count_p2=('alert_count_p2', 'sum')
    ).reset_index()

    persistent_squads_summary = analyze_persistent_cases(merged_df)

    squad_trends_p1 = df_p1[df_p1["acao_sugerida"].isin(ACTION_NEEDED_FLAGS)].groupby('assignment_group')['alert_count'].sum().reset_index().rename(columns={'alert_count': 'count_p1'})
    squad_trends_p2 = df_p2[df_p2["acao_sugerida"].isin(ACTION_NEEDED_FLAGS)].groupby('assignment_group')['alert_count'].sum().reset_index().rename(columns={'alert_count': 'count_p2'})
    squad_trends_merged = pd.merge(squad_trends_p1, squad_trends_p2, on='assignment_group', how='outer').fillna(0)

    title = "📊 Análise de Tendência de Alertas"
    body = f'<p><a href="resumo_geral.html">&larr; Voltar para o Dashboard</a></p><h1>Análise Comparativa de Alertas</h1>'
    
    periodo_anterior_text = f"<code>{escape(os.path.basename(args.csv_anterior_name))}</code>"
    if args.date_range_anterior and args.date_range_anterior != "N/A":
        periodo_anterior_text += f" <span style='color: var(--text-secondary-color);'>({escape(args.date_range_anterior)})</span>"
    periodo_atual_text = f"<code>{escape(os.path.basename(args.csv_atual_name))}</code>"
    if args.date_range_atual and args.date_range_atual != "N/A":
        periodo_atual_text += f" <span style='color: var(--text-secondary-color);'>({escape(args.date_range_atual)})</span>"
    
    body += f"<div class='definition-box' style='margin-bottom: 25px;'>"
    body += f"<strong>Período Anterior:</strong> {periodo_anterior_text}<br>"
    body += f"<strong>Período Atual:</strong> {periodo_atual_text}"
    body += "</div>"
    
    body += f"<div class='card'>{generate_kpis_html(kpis)}</div>"

    chevron_svg_collapsible = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="chevron"><polyline points="9 18 15 12 9 6"></polyline></svg>'

    body += f'<button type="button" class="collapsible active"><span>🔥 Foco de Atuação e Novos Riscos</span>{chevron_svg_collapsible}</button>'
    body += '<div class="collapsible-content">'
    body += '<div class="tab-container">'
    body += '<div class="tab-links">'
    body += '<button class="tab-link active" data-target="tab-persistentes">🚨 Casos Persistentes por Squad</button>'
    body += '<button class="tab-link" data-target="tab-novos-problemas">⚠️ Novos Problemas</button>'
    body += '</div>'
    body += '<div id="tab-persistentes" class="tab-content active">'
    body += "<div class='definition-box'>Casos que já precisavam de ação no período anterior e continuam precisando. <strong>Clique em uma linha da tabela para ver os detalhes.</strong></div>"
    body += generate_persistent_cases_table_html(persistent_squads_summary, both_cases_df, "Anterior", "Atual")
    body += '</div>'
    body += '<div id="tab-novos-problemas" class="tab-content">'
    body += "<div class='definition-box'>Problemas que não precisavam de ação no período anterior, mas que surgiram no período atual já necessitando de uma.</div>"
    body += generate_trend_table_html(new_problems_summary.set_index('short_description'), "Anterior", "Atual")
    body += '</div>'
    body += '</div></div>'

    body += f'<button type="button" class="collapsible"><span>📈 Tendências Gerais por Categoria</span>{chevron_svg_collapsible}</button>'
    body += '<div class="collapsible-content">'
    body += '<div class="tab-container">'
    body += '<div class="tab-links">'
    body += '<button class="tab-link active" data-target="tab-variacao-squad">📈 Variação de Alertas por Squad</button>'
    body += '<button class="tab-link" data-target="tab-variacao-problema">📊 Variação por Tipo de Problema</button>'
    body += '</div>'
    body += '<div id="tab-variacao-squad" class="tab-content active">'
    body += "<div class='definition-box'>Visão geral da variação no volume de alertas por squad, considerando todos os casos que necessitam de ação.</div>"
    body += generate_trend_table_html(squad_trends_merged.set_index('assignment_group'), "Anterior", "Atual")
    body += '</div>'
    body += '<div id="tab-variacao-problema" class="tab-content">'
    body += "<div class='definition-box'>Variação no volume de alertas para os tipos de problema que persistiram entre os dois períodos.</div>"
    body += generate_trend_table_html(varying_problems_summary.set_index('short_description'), "Anterior", "Atual")
    body += '</div>'
    body += '</div></div>'

    body += f'<button type="button" class="collapsible"><span>✅ Vitórias</span>{chevron_svg_collapsible}</button>'
    body += '<div class="collapsible-content">'
    body += '<div class="tab-container">'
    body += '<div class="tab-links">'
    body += '<button class="tab-link active" data-target="tab-resolvidos">✅ Problemas Resolvidos</button>'
    body += '</div>'
    body += '<div id="tab-resolvidos" class="tab-content active">'
    body += "<div class='definition-box'>Casos que necessitavam de ação no período anterior e que foram resolvidos, não precisando mais de atuação.</div>"
    body += generate_trend_table_html(resolved_problems_summary.set_index('short_description'), "Anterior", "Atual")
    body += '</div>'
    body += '</div></div>'

    template = Template(HTML_TEMPLATE)
    final_report = template.substitute(title=title, body=body)
    output_path = "resumo_tendencia.html"
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_report)
        print(f"✅ Relatório de tendência aprimorado (com totais) gerado em: {output_path}")
    except IOError as e:
        print(f"❌ Erro ao escrever o arquivo {output_path}: {e}")

if __name__ == "__main__":
    main()
