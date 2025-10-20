import os
import re
from html import escape
from typing import Dict, Any

from jinja2 import Template
# =============================================================================
# CONSTANTES VISUAIS
# =============================================================================

# Ícones SVG para o HTML
SQUAD_ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="squad-icon"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>"""
DOWNLOAD_ICON_SVG = """<svg class="download-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>"""
VIEW_ICON_SVG = """<svg class="download-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>"""
EDIT_ICON_SVG = """<svg class="download-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>"""
CHEVRON_SVG = """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="chevron"><polyline points="9 18 15 12 9 6"></polyline></svg>"""

# =============================================================================
# FUNÇÕES AUXILIARES DE RENDERIZAÇÃO
# =============================================================================


def gerar_cores_para_barra(
    valor: float, valor_min: float, valor_max: float
) -> tuple[str, str]:
    """Gera uma tupla com (cor de fundo, cor de texto) para a barra do gráfico."""
    if valor_max == valor_min:
        return "hsl(0, 90%, 55%)", "white"
    fracao = (
        (valor - valor_min) / (valor_max - valor_min) if valor_max > valor_min else 0
    )
    hue = 60 - (fracao * 60)
    background_color = f"hsl({hue:.0f}, 90%, 55%)"
    text_color = "var(--text-color-dark)" if hue > 35 else "white"
    return background_color, text_color


def renderizar_template_string(template_string: str, **kwargs: Any) -> str:
    """Renderiza uma string de template usando Jinja2, de forma segura."""
    template = Template(template_string)
    return template.render(**kwargs)


def renderizar_pagina_csv_viewer(
    template: str, csv_content: str, page_title: str, csv_filename: str
) -> str:
    """Renderiza um template de visualizador de CSV (como Handsontable)."""
    # CORREÇÃO: Usa uma "raw string" (r'...') para criar a sequência de escape de forma explícita e segura.
    csv_payload = csv_content.replace("`", r"\`")

    # Usa um placeholder improvável para evitar colisões
    placeholder = "___CSV_DATA_PAYLOAD_PLACEHOLDER___"

    # Substitui o placeholder no template
    final_html = template.replace(
        "const csvDataPayload = `__CSV_DATA_PLACEHOLDER__`",
        f"const csvDataPayload = `{placeholder}`",
    )

    # Injeta o payload real
    final_html = final_html.replace(placeholder, csv_payload)

    # MELHORIA: Usa placeholders dedicados para os títulos, tornando o código mais robusto.
    # Garante a substituição tanto no <title> quanto no <h1>
    final_html = final_html.replace("__PAGE_TITLE__", escape(page_title))
    final_html = final_html.replace("__CSV_FILENAME__", csv_filename)

    return final_html


def renderizar_visualizador_json(json_data_str: str) -> str:
    """Cria um arquivo HTML estático para visualizar o JSON de forma formatada."""
    return f"""
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
        // Os dados do JSON sÃ£o injetados aqui pelo script Python
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
"""


def _render_conceitos_section() -> str:
    """Renderiza a seção 'Conceitos' do dashboard."""
    return """
    <div style="margin-bottom: 25px;">
        <button type="button" class="collapsible collapsible-main-header">{{ CHEVRON_SVG }}Conceitos</button>
        <div class="content" style="display: none; padding: 0; border: none; background: none;">
            <div class="card" style="margin-top: 10px; padding: 20px;">

                <button type="button" class="collapsible active">{{ CHEVRON_SVG }}<strong>Casos vs. Alertas</strong></button>
                <div class="content" style="display: block; padding-left: 28px;">
                    <div style="padding: 15px 0 15px 15px; border-left: 2px solid var(--accent-color); color: var(--text-secondary-color);">
                        <br><br>
                        Um <strong>Alerta</strong> é uma notificação individual — pense nele como o "ruído" que você recebe.
                        <br><br>
                        Um <strong>Caso</strong> é a causa raiz de um problema. Ele agrupa todos os alertas do mesmo tipo em um único recurso.
                        <br><br>
                        <strong>Exemplo:</strong> Um servidor com pouco espaço em disco pode gerar 100 <strong>Alertas</strong> de "disco cheio". No entanto, como todos esses alertas são sobre o mesmo problema, eles são agrupados em apenas <strong>1 Caso</strong>. Se esse servidor também apresentar um problema de CPU, isso será um <strong>2º Caso</strong>, porque exige uma ação diferente.
                    </div>
                </div>

                <button type="button" class="collapsible" style="margin-top: 15px;">{{ CHEVRON_SVG }}<strong>Como a Prioridade dos Casos é Definida?</strong></button>
                <div class="content" style="display: none; padding-left: 28px;">
                     <div style="padding: 15px 0 15px 15px; border-left: 2px solid var(--danger-color); color: var(--text-secondary-color);">
                        A pontuação de prioridade não é um valor arbitrário. Ela é calculada pela fórmula: <br>
                        <code>Score = (Pilar 1: Risco) * (Pilar 2: Ineficiência) * (Pilar 3: Impacto)</code>
                        <br><br>
                        <h4 style="color: var(--text-color); margin-top: 15px; margin-bottom: 5px;">Pilar 1: Score de Risco</h4>
                        Mede a gravidade base do problema. É a soma dos pesos da Severidade e Prioridade do alerta, valores extraídos diretamente das colunas <strong>severity</strong> e <strong>sn_priority_group</strong> do arquivo de dados.
                        <table class="sub-table">
                            <thead><tr><th>Severidade</th><th>Peso</th><th>Prioridade</th><th>Peso</th></tr></thead>
                            <tbody>
                                <tr><td>Crítico</td><td style="color: var(--danger-color); font-weight: 500;">10</td><td>Urgente</td><td style="color: var(--danger-color); font-weight: 500;">10</td></tr>
                                <tr><td>Alto / Major</td><td style="color: var(--warning-color); font-weight: 500;">8</td><td>Alto(a)</td><td style="color: var(--warning-color); font-weight: 500;">8</td></tr>
                                <tr><td>Médio / Minor</td><td style="color: var(--accent-color); font-weight: 500;">5</td><td>Moderado(a)</td><td style="color: var(--accent-color); font-weight: 500;">5</td></tr>
                                <tr><td>Aviso / Baixo</td><td>2-3</td><td>Baixo(a)</td><td>2</td></tr>
                            </tbody>
                        </table>
                        <h4 style="color: var(--text-color); margin-top: 15px; margin-bottom: 5px;">Pilar 2: Multiplicador de Ineficiência</h4>
                        Penaliza Casos onde a automação falhou. Quanto pior a falha, maior o multiplicador.
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

                <button type="button" class="collapsible" style="margin-top: 15px;">{{ CHEVRON_SVG }}<strong>Como a Remediação é Contabilizada?</strong></button>
                <div class="content" style="display: none; padding-left: 28px;">
                    <div style="padding: 15px 0 15px 15px; border-left: 2px solid var(--accent-color); color: var(--text-secondary-color);">
                        <p>A análise da remediação se baseia em uma etapa de preparação dos dados. Nesse passo anterior, cada alerta é verificado para identificar se existe uma "Tarefa de Correção" (<strong>REM00XXXXX</strong>) associada a ele. É a presença desse registro que confirma que uma automação foi <strong>executada</strong>.</p>
                        <p style="margin-top: 10px;">Para definir o <strong>resultado</strong>, o processo então analisa o status dessa tarefa. O texto exato encontrado nesse campo determina o desfecho: <strong>"REM_OK"</strong> é contabilizado como <strong>sucesso</strong>, enquanto <strong>"REM_NOT_OK"</strong> é contabilizado como <strong>falha</strong>. A detecção de um desses dois "eventos" no alerta é o que classifica o status da remediação.</p>
                        
                        <div style="background-color: #fffbe6; border-left: 5px solid #ffe58f; padding: 15px 20px; margin-top: 15px; color: #665424;">
                            <strong>Ponto de Atenção:</strong> Este método confirma a <em>execução</em> de uma automação, mas não garante, por si só, que a remediação foi de fato <em>efetiva</em> para solucionar a causa raiz do problema. Uma investigação futura é necessária para aprofundar essa análise. O próximo passo será um trabalho em conjunto com o time de Automação para entender o significado detalhado dos status dentro de uma tarefa REM00XXXXX e como extrair essa informação para o relatório.
                        </div>
                    </div>
                </div>

                <button type="button" class="collapsible" style="margin-top: 15px;">{{ CHEVRON_SVG }}<strong>Como Interpretar o quadro de Remediações?</strong></button>
                <div class="content" style="display: none; padding-left: 28px;">
                    <div style="padding: 15px 0 15px 15px; border-left: 2px solid var(--warning-color); color: var(--text-secondary-color);">
                        Um número alto neste quadro é bom (a automação está funcionando), mas também é um sinal de alerta. Ele indica <strong>instabilidade crônica</strong>: um problema que ocorre e é remediado com muita frequência. Esses são candidatos ideais para uma análise de causa raiz mais profunda, visando a solução definitiva.
                    </div>
                </div>

                <button type="button" class="collapsible" style="margin-top: 15px;">{{ CHEVRON_SVG }}<strong>O que significa o valor "DESCONHECIDO"?</strong></button>
                <div class="content" style="display: none; padding-left: 28px;">
                    <div style="padding: 15px 0 15px 15px; border-left: 2px solid var(--text-secondary-color); color: var(--text-secondary-color);">
                        Quando o valor "DESCONHECIDO" aparece em campos como Squad, Métrica ou Recurso, significa que a informação estava <strong>ausente no arquivo de dados original</strong>. Isso geralmente aponta para uma oportunidade de melhorar a qualidade e o enriquecimento dos dados na origem (o sistema de monitoramento), garantindo que todo alerta seja corretamente categorizado.
                    </div>
                </div>
            </div>
        </div>
    </div>
    """


def _render_notification_banners(num_logs_invalidos: int, trend_report_path: str) -> str:
    """Renderiza os banners de notificação para qualidade de dados e análise de tendência."""
    banners_html = ""
    # Define os estilos do banner uma vez para ser usado por ambos os avisos
    notification_banner_styles = """
    <style>
    .notification-banner { display: flex; align-items: center; gap: 15px; padding: 15px 20px; border-radius: 8px; margin: 25px 0; color: var(--text-color); }
    .notification-banner.warning { background-color: rgba(231, 74, 59, 0.1); border: 1px solid var(--danger-color); }
    .notification-banner.trend { background-color: rgba(78, 115, 223, 0.1); border: 1px solid var(--accent-color); }
    .notification-banner .icon { font-size: 1.5em; }
    .notification-banner .text { flex-grow: 1; }
    .notification-banner .details-link { font-weight: bold; white-space: nowrap; }
    .notification-banner.warning .details-link { color: var(--danger-color); }
    .notification-banner.trend .details-link { color: var(--accent-color); }
    </style>
    """

    # Injeta os estilos apenas se um dos banners for ser exibido
    if num_logs_invalidos > 0 or trend_report_path:
        banners_html += notification_banner_styles

    # Gera o banner de Qualidade de Dados
    if num_logs_invalidos > 0:
        banners_html += f"""
        <div class="notification-banner warning">
            <span class="icon">📜</span>
            <div class="text">
                <strong>Aviso de Qualidade de Dados:</strong> Foram encontrados <strong>{num_logs_invalidos} alertas</strong> com status de remediação inválido.
            </div>
            <a href="qualidade_dados_remediacao.html?back=resumo_geral.html" class="details-link">Detalhes &rarr;</a>
        </div>
        """

    # Gera o banner de Relatório de Tendência
    if trend_report_path:
        banners_html += f"""
        <div class="notification-banner trend">
            <span class="icon">📈</span>
            <div class="text">
                <strong>Análise Comparativa Disponível:</strong> Compare os resultados atuais com o período anterior para identificar novas tendências, regressões e melhorias.
            </div>
            <a href="{os.path.basename(trend_report_path)}?back=resumo_geral.html" class="details-link">Relatório de Tendência &rarr;</a>
        </div>
        """
    return banners_html


# =============================================================================
# RENDERIZAÇÃO DE COMPONENTES E PÁGINAS
# =============================================================================


def renderizar_resumo_executivo(
    context: Dict[str, Any], frontend_url: str = "/"
) -> str:
    """Gera o corpo HTML do dashboard principal com base no contexto de dados."""

    # Desempacota o dicionário de contexto para variáveis locais
    (
        total_grupos,
        grupos_atuacao,
        grupos_instabilidade,
        taxa_sucesso,
        casos_ok_estaveis,
        top_squads,
        top_metrics,
        top_problemas_atuacao,
        top_problemas_remediados,
        top_problemas_geral,
        top_problemas_instabilidade,
        total_alertas_remediados_ok,
        total_alertas_instabilidade,
        total_alertas_problemas,
        total_alertas_geral,
        all_squads,
        top_5_squads_agrupadas,
        num_logs_invalidos,
        trend_report_path,
        date_range_text,
        summary_filename,
        plan_dir_base_name,
        details_dir_base_name,
        ai_summary,
    ) = [
        context.get(k)
        for k in [
            "total_grupos",
            "grupos_atuacao",
            "grupos_instabilidade",
            "taxa_sucesso",
            "casos_ok_estaveis",
            "top_squads",
            "top_metrics",
            "top_problemas_atuacao",
            "top_problemas_remediados",
            "top_problemas_geral",
            "top_problemas_instabilidade",
            "total_alertas_remediados_ok",
            "total_alertas_instabilidade",
            "total_alertas_problemas",
            "total_alertas_geral",
            "all_squads",
            "top_5_squads_agrupadas",
            "num_logs_invalidos",
            "trend_report_path",
            "date_range_text",
            "summary_filename",
            "plan_dir_base_name",
            "details_dir_base_name",
            "ai_summary",
        ]
    ]

    list_card_styles = """
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
    """
    body_content = list_card_styles
    
    # Adiciona o cabeçalho com o link de volta e o título principal
    body_content += f"""
    <div class="report-header">
        <a href="{frontend_url}" class="home-button">Página Inicial</a>
    </div>
    """
    
    body_content += f"<div class='definition-box' style='text-align: center;'>{date_range_text}</div><!-- AI_SUMMARY_PLACEHOLDER -->"
    body_content += renderizar_template_string(_render_conceitos_section(), CHEVRON_SVG=CHEVRON_SVG)
    body_content += _render_notification_banners(num_logs_invalidos, trend_report_path)

    # Renderiza o restante do corpo, que já usa f-strings de forma segura
    body_content += renderizar_template_string(
        '<button type="button" class="collapsible-row active">{{ CHEVRON_SVG }}VISÃO GERAL</button>', CHEVRON_SVG=CHEVRON_SVG
    )
    body_content += '<div class="content" style="display: block; padding-top: 20px;">'

    body_content += '<div class="grid-container" style="grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));">'

    gauge_color_class = "var(--success-color)"
    automation_card_class = "card-neon-green"
    if taxa_sucesso < 50:
        gauge_color_class = "var(--danger-color)"
        automation_card_class = "card-neon-red"
    elif taxa_sucesso < 70:
        gauge_color_class = "var(--warning-color)"
        automation_card_class = "card-neon-warning"

    if grupos_atuacao > 0:
        view_icon_html = f'<a href="atuar.html?back=resumo_geral.html" class="download-link" title="Abrir editor para atuar.csv">{VIEW_ICON_SVG}</a>'
    else:
        disabled_svg = VIEW_ICON_SVG.replace(
            'class="download-icon"', 'class="download-icon" style="opacity: 0.4;"'
        )
        view_icon_html = f'<span class="download-link" title="Nenhum arquivo de atuação gerado." style="cursor: not-allowed;">{disabled_svg}</span>'
    card_class = "card-fire-shake" if grupos_atuacao > 0 else "card-neon card-neon-blue"
    tooltip_text = (
        "Casos que precisam de revisão: Remediação Pendente."
        if grupos_atuacao > 0
        else "Tudo certo! Nenhum caso precisa de intervenção manual."
    )
    status_icon_html = f"""<div class="tooltip-container" style="position: absolute; top: 15px; left: 15px;"><span class="{"flashing-icon" if grupos_atuacao > 0 else ""}" style="font-size: 1.5em;">{"🚨" if grupos_atuacao > 0 else "✅"}</span><div class="tooltip-content" style="width: 240px; left: 0; margin-left: 0;">{escape(tooltip_text)}</div></div>"""
    kpi_color_style = (
        "color: var(--danger-color);"
        if grupos_atuacao > 0
        else "color: var(--accent-color);"
    )
    body_content += f"""
    <div class="card kpi-card {card_class}">
        {status_icon_html}
        <p class="kpi-value" style="{kpi_color_style}">{grupos_atuacao}</p>
        <p class="kpi-label">Casos sem Remediação | Foco de Atuação</p>
        {view_icon_html}
    </div>
    """

    if grupos_instabilidade > 0:
        instabilidade_view_icon_html = f'<a href="instabilidade_cronica.html?back=resumo_geral.html" class="download-link" title="Visualizar detalhes dos Casos de instabilidade">{VIEW_ICON_SVG}</a>'
    else:
        disabled_svg = VIEW_ICON_SVG.replace(
            'class="download-icon"', 'class="download-icon" style="opacity: 0.4;"'
        )
        instabilidade_view_icon_html = f'<span class="download-link" title="Nenhum caso de instabilidade crônica detectado." style="cursor: not-allowed;">{disabled_svg}</span>'
    instabilidade_card_class = (
        "card-neon card-neon-warning"
        if grupos_instabilidade > 0
        else "card-neon card-neon-blue"
    )
    instabilidade_kpi_color = (
        "color: var(--warning-color);"
        if grupos_instabilidade > 0
        else "color: var(--accent-color);"
    )
    tooltip_instabilidade_text = (
        "Casos que são remediados, mas ocorrem com alta frequência. Oportunidades para análise de causa raiz."
        if grupos_instabilidade > 0
        else "Nenhum ponto de alta recorrência crônica detectado."
    )
    instabilidade_status_icon_html = f"""<div class="tooltip-container" style="position: absolute; top: 15px; left: 15px;"><span class="{"flashing-icon" if grupos_instabilidade > 0 else ""}" style="font-size: 1.5em;">{"⚠️" if grupos_instabilidade > 0 else "✅"}</span><div class="tooltip-content" style="width: 280px; left: 0; margin-left: 0;">{escape(tooltip_instabilidade_text)}</div></div>"""

    body_content += f"""
    <div class="card kpi-card {instabilidade_card_class}">
        {instabilidade_status_icon_html}
        <p class="kpi-value" style="{instabilidade_kpi_color}">{grupos_instabilidade}</p>
        <p class="kpi-label">Casos Remediados com Frequência</p>
        {instabilidade_view_icon_html}
    </div>
    """

    casos_sucesso = total_grupos - grupos_atuacao
    tooltip_gauge = f"Percentual e contagem de Casos resolvidos automaticamente: {casos_sucesso} de {total_grupos} problemas tiveram a remediação executada com sucesso."
    sucesso_page_name = "sucesso_automacao.html"
    if casos_sucesso > 0:
        sucesso_view_icon_html = f'<a href="{sucesso_page_name}?back=resumo_geral.html" class="download-link" title="Visualizar detalhes dos Casos resolvidos">{VIEW_ICON_SVG}</a>'
    else:
        disabled_svg = VIEW_ICON_SVG.replace(
            'class="download-icon"', 'class="download-icon" style="opacity: 0.4;"'
        )
        sucesso_view_icon_html = f'<span class="download-link" title="Nenhum caso resolvido automaticamente." style="cursor: not-allowed;">{disabled_svg}</span>'
    body_content += f"""
    <div class="card kpi-card card-neon {automation_card_class}">
        <div class="tooltip-container" style="position: absolute; top: 15px; left: 15px;"><span style="font-size: 1.5em;">🤖</span><div class="tooltip-content" style="width: 280px; left: 0; margin-left: 0;">{escape(tooltip_gauge)}</div></div>
        <p class="kpi-value" style="color: {gauge_color_class}; font-size: 4em; margin: 0;">{taxa_sucesso:.1f}%</p>
        <p class="kpi-label" style="margin-top: 0px; margin-bottom: 10px;">Sucesso da Automação</p>
        <p style="font-size: 1.2em; color: var(--text-secondary-color); margin: 0;">{casos_sucesso} <span style="font-size: 0.8em;">de</span> {total_grupos} <span style="font-size: 0.8em;">Casos</span></p>
        {sucesso_view_icon_html}
    </div>
    """

    tooltip_volume_casos = (
        "Distribuição do total de Casos únicos analisados no período."
    )
    body_content += f"""
    <div class="card">
        <h3><span class="card-title">Volume de Casos</span><div class="tooltip-container"><span class="info-icon">i</span><div class="tooltip-content">{escape(tooltip_volume_casos)}</div></div></h3>
        <div class="volume-card-item"><span class="volume-card-label">Total de Casos</span><span class="volume-card-value">{total_grupos}</span></div>
        <div class="volume-card-item"><span class="volume-card-label">Remediados (Estável)</span><span class="volume-card-value" style="color: var(--success-color);">{casos_ok_estaveis}</span></div>
        <div class="volume-card-item"><span class="volume-card-label">Remediados (Frequente)</span><span class="volume-card-value" style="color: var(--warning-color);">{grupos_instabilidade}</span></div>
        <div class="volume-card-item"><span class="volume-card-label">Sem Remediação</span><span class="volume-card-value" style="color: var(--danger-color);">{grupos_atuacao}</span></div>
    </div>
    """

    tooltip_volume = "Distribuição do total de alertas únicos analisados no período."
    sem_remediacao_color_style = (
        "color: var(--danger-color);"
        if total_alertas_problemas > 0
        else "color: var(--text-secondary-color);"
    )
    remediados_color_style = "color: var(--success-color);"
    body_content += f"""
    <div class="card">
        <h3><span class="card-title">Volume de Alertas</span><div class="tooltip-container"><span class="info-icon">i</span><div class="tooltip-content">{escape(tooltip_volume)}</div></div></h3>
        <div class="volume-card-item"><span class="volume-card-label">Total de Alertas</span><span class="volume-card-value">{total_alertas_geral}</span></div>
        <div class="volume-card-item"><span class="volume-card-label">Remediados (Estável)</span><span class="volume-card-value" style="{remediados_color_style}">{total_alertas_remediados_ok}</span></div>
        <div class="volume-card-item"><span class="volume-card-label">Remediados (Frequente)</span><span class="volume-card-value" style="color: var(--warning-color);">{total_alertas_instabilidade}</span></div>
        <div class="volume-card-item"><span class="volume-card-label">Sem Remediação</span><span class="volume-card-value" style="{sem_remediacao_color_style}">{total_alertas_problemas}</span></div>
        <a href="visualizador_json.html" target="_blank" class="download-link" title="Visualizar JSON com todos os Casos">{VIEW_ICON_SVG}</a>
    </div>
    """

    tooltip_top5 = "As 5 squads com maior carga de criticidade, classificadas pela soma da prioridade de todos os seus Casos em aberto."

    body_content += f"""
    <div class="card" style="padding-bottom: 15px;">
        <h3><span class="card-title">Top 5 Squads Prioritárias</span><div class="tooltip-container"><span class="info-icon">i</span><div class="tooltip-content" style="width: 280px; margin-left: -140px;">{escape(tooltip_top5)}</div></div></h3>
        <div style="flex-grow: 1; display: flex; flex-direction: column;">
    """
    if not top_5_squads_agrupadas.empty:
        max_score = (
            top_5_squads_agrupadas["score_acumulado"].max()
            if not top_5_squads_agrupadas.empty
            else 20
        )
        min_score = 0
        for _, row in top_5_squads_agrupadas.iterrows():
            score_color, _ = gerar_cores_para_barra(
                row["score_acumulado"], min_score, max_score * 1.1
            )
            squad_name = escape(row["assignment_group"])
            plural_casos = "Casos" if row["total_casos"] > 1 else "caso"
            total_casos_txt = f"({row['total_casos']} {plural_casos})"
            sanitized_squad_name = re.sub(
                r"[^a-zA-Z0-9_-]", "", squad_name.replace(" ", "_")
            )
            plan_path = (
                f"{plan_dir_base_name}/plano-de-acao-{sanitized_squad_name}.html"
            )

            body_content += f"""
            <a href="{plan_path}" class="priority-list-item-new" title="Ver plano de ação para {squad_name}">
                <div class="squad-info-new">
                    {SQUAD_ICON_SVG}
                    <span class="squad-name-new">{squad_name} <small style="color:var(--text-secondary-color)">{total_casos_txt}</small></span>
                </div>
                <span class="priority-score-new" style="background-color: {score_color};">{row["score_acumulado"]:.1f}</span>
            </a>
            """
    else:
        body_content += "<p>Nenhum caso prioritário precisa de atuação. ✅</p>"
    body_content += "</div></div>"
    body_content += "</div></div>"

    body_content += renderizar_template_string(
        '<button type="button" class="collapsible-row active">{{ CHEVRON_SVG }}TOP 5 - SEM REMEDIAÇÃO</button>', CHEVRON_SVG=CHEVRON_SVG
    )
    body_content += '<div class="content" style="display: none; padding-top: 20px;"><div class="grid-container" style="grid-template-columns: 1fr 1fr; align-items: stretch; gap: 20px;">'
    tooltip_squads = "Squads com maior número de Casos sem remediação."
    body_content += f'<div class="card"><h3><span class="card-title">TOP 5 SQUADS</span><div class="tooltip-container"><span class="info-icon">i</span><div class="tooltip-content">{escape(tooltip_squads)}</div></div></h3>'
    if not top_squads.empty:
        body_content += '<div class="bar-chart-container">'
        min_squad_val, max_squad_val = top_squads.min(), top_squads.max()
        for squad, count in top_squads.items():
            bar_width = (count / max_squad_val) * 100
            background_color, text_color = gerar_cores_para_barra(
                count, min_squad_val, max_squad_val
            )
            sanitized_name = re.sub(r"[^a-zA-Z0-9_-]", "", squad.replace(" ", "_"))
            # CORREÇÃO: O caminho correto para esta seção é para os relatórios de squad, não para os planos de ação.
            squad_report_path = f"squads/squad-{sanitized_name}.html"
            body_content += f'<div class="bar-item"><div class="bar-label"><a href="{squad_report_path}" title="Ver relatório para {escape(squad)}">{escape(squad)}</a></div><div class="bar-wrapper"><div class="bar" style="width: {bar_width}%; background-color: {background_color}; color: {text_color};">{count}</div></div></div>'
        body_content += "</div>"
    else:
        body_content += "<p>Nenhuma squad com Casos que precisam de atuação. ✅</p>"
    squads_com_casos_count = len(all_squads[all_squads > 0])
    if squads_com_casos_count > len(top_squads):
        body_content += f'<div class="footer-link"><a href="todas_as_squads.html">Ver todas as squads ({squads_com_casos_count}) &rarr;</a></div>'
    body_content += "</div>"

    tooltip_abertos = "Tipos de problemas que mais geraram alertas sem remediação."
    body_content += f'<div class="card"><h3><span class="card-title">TOP 5 ALERTAS</span><div class="tooltip-container"><span class="info-icon">i</span><div class="tooltip-content">{escape(tooltip_abertos)}</div></div></h3>'
    if not top_problemas_atuacao.empty:
        body_content += '<div class="bar-chart-container">'
        min_val, max_val = top_problemas_atuacao.min(), top_problemas_atuacao.max()
        for problem, count in top_problemas_atuacao.items():
            bar_width = (count / max_val) * 100
            background_color, text_color = gerar_cores_para_barra(
                count, min_val, max_val
            )
            sanitized_name = re.sub(
                r"[^a-zA-Z0-9_-]", "", problem[:50].replace(" ", "_")
            )
            details_path = os.path.join(
                details_dir_base_name, f"detalhe_aberto_{sanitized_name}.html"
            )
            body_content += f'<div class="bar-item"><div class="bar-label"><a href="{details_path}" title="Ver detalhes">{escape(problem)}</a></div><div class="bar-wrapper"><div class="bar" style="width: {bar_width}%; background-color: {background_color}; color: {text_color};">{count}</div></div></div>'
        body_content += "</div>"
    else:
        body_content += "<p>Nenhum caso em aberto. ✅</p>"
    body_content += "</div></div>"

    tooltip_metricas = (
        "Categorias de métricas com maior número de Casos sem remediação."
    )
    body_content += f'<div class="card full-width"><h3><span class="card-title">TOP 5 CATEGORias</span><div class="tooltip-container"><span class="info-icon">i</span><div class="tooltip-content">{escape(tooltip_metricas)}</div></div></h3>'
    if not top_metrics.empty:
        body_content += '<div class="bar-chart-container">'
        min_metric_val, max_metric_val = top_metrics.min(), top_metrics.max()
        for metric, count in top_metrics.items():
            bar_width = (count / max_metric_val) * 100
            background_color, text_color = gerar_cores_para_barra(
                count, min_metric_val, max_metric_val
            )
            sanitized_name = re.sub(r"[^a-zA-Z0-9_-]", "", metric.replace(" ", "_"))
            details_path = os.path.join(
                details_dir_base_name, f"detalhe_metrica_{sanitized_name}.html"
            )
            label_html = (
                f'<a href="{details_path}" title="Ver detalhes">{escape(metric)}</a>'
            )
            body_content += f'<div class="bar-item"><div class="bar-label">{label_html}</div><div class="bar-wrapper"><div class="bar" style="width: {bar_width}%; background-color: {background_color}; color: {text_color};">{count}</div></div></div>'
        body_content += "</div>"
    else:
        body_content += "<p>Nenhuma categoria com Casos em aberto. ✅</p>"
    body_content += "</div></div>"

    body_content += renderizar_template_string(
        '<button type="button" class="collapsible-row active">{{ CHEVRON_SVG }}TENDÊNCIAS E OPORTUNIDADES</button>', CHEVRON_SVG=CHEVRON_SVG
    )
    body_content += '<div class="content" style="display: none; padding-top: 20px;"><div class="grid-container" style="grid-template-columns: 1fr; gap: 20px;">'

    tooltip_instabilidade_chart = "Problemas que mais geram alertas recorrentes, mesmo com a remediação funcionando. Indicam instabilidade crônica."
    body_content += f'<div class="card"><h3><span class="card-title">TOP 5 PONTOS DE ATENÇÃO</span><div class="tooltip-container"><span class="flashing-icon">🚨</span><div class="tooltip-content" style="width: 300px;">{escape(tooltip_instabilidade_chart)}</div></div></h3>'
    if not top_problemas_instabilidade.empty:
        body_content += '<div class="bar-chart-container">'
        min_val, max_val = (
            top_problemas_instabilidade.min(),
            top_problemas_instabilidade.max(),
        )
        for problem, count in top_problemas_instabilidade.items():
            bar_width = (count / max_val) * 100
            background_color, text_color = "hsl(45, 90%, 55%)", "var(--text-color-dark)"
            sanitized_name = re.sub(
                r"[^a-zA-Z0-9_-]", "", problem[:50].replace(" ", "_")
            )
            details_path = os.path.join(
                details_dir_base_name, f"detalhe_instabilidade_{sanitized_name}.html"
            )
            body_content += f'<div class="bar-item"><div class="bar-label"><a href="{details_path}" title="Ver detalhes">{escape(problem)}</a></div><div class="bar-wrapper"><div class="bar" style="width: {bar_width}%; background-color: {background_color}; color: {text_color};">{count}</div></div></div>'
        body_content += "</div>"
    else:
        body_content += "<p>Nenhum ponto de alta recorrência crônica detectado. ✅</p>"
    body_content += "</div>"

    mensagem_tooltip = "Problemas com menor frequência de remediação, mas que também podem indicar instabilidade e são candidatos a uma análise de causa raiz definitiva."
    body_content += f'<div class="card"><h3><span class="card-title">TOP 5 REMEDIAÇÕES EXECUTADAS</span><div class="tooltip-container"><span class="flashing-icon">⚠️</span><div class="tooltip-content">{escape(mensagem_tooltip)}</div></div></h3>'
    if not top_problemas_remediados.empty:
        body_content += '<div class="bar-chart-container">'
        min_val, max_val = (
            top_problemas_remediados.min(),
            top_problemas_remediados.max(),
        )
        for problem, count in top_problemas_remediados.items():
            bar_width = (count / max_val) * 100
            background_color, text_color = "hsl(155, 60%, 45%)", "white"
            sanitized_name = re.sub(
                r"[^a-zA-Z0-9_-]", "", problem[:50].replace(" ", "_")
            )
            details_path = os.path.join(
                details_dir_base_name, f"detalhe_remediado_{sanitized_name}.html"
            )
            body_content += f'<div class="bar-item"><div class="bar-label"><a href="{details_path}" title="Ver detalhes">{escape(problem)}</a></div><div class="bar-wrapper"><div class="bar" style="width: {bar_width}%; background-color: {background_color}; color: {text_color};">{count}</div></div></div>'
        body_content += "</div>"
    else:
        body_content += (
            "<p><strong>⚠️ Nenhum problema remediado automaticamente.</strong></p>"
        )
    body_content += "</div></div></div>"

    body_content += renderizar_template_string(
        '<button type="button" class="collapsible-row active">{{ CHEVRON_SVG }}TOP 10 - ALERTAS (GERAL)</button>', CHEVRON_SVG=CHEVRON_SVG
    )
    body_content += '<div class="content" style="display: none; padding-top: 20px;">'
    tooltip_recorrentes = "Os 10 tipos de problemas que mais ocorreram (volume total de alertas), independente da automação."
    body_content += f'<div class="card"><h3><span class="card-title">TOP 10 ALERTAS</span><div class="tooltip-container"><span class="info-icon">i</span><div class="tooltip-content">{escape(tooltip_recorrentes)}</div></div></h3>'
    if not top_problemas_geral.empty:
        body_content += '<div class="bar-chart-container">'
        min_prob_val, max_prob_val = (
            top_problemas_geral.min(),
            top_problemas_geral.max(),
        )
        for problem, count in top_problemas_geral.items():
            bar_width = (count / max_prob_val) * 100
            background_color, text_color = gerar_cores_para_barra(
                count, min_prob_val, max_prob_val
            )
            sanitized_name = re.sub(
                r"[^a-zA-Z0-9_-]", "", problem[:50].replace(" ", "_")
            )
            details_path = os.path.join(
                details_dir_base_name, f"detalhe_geral_{sanitized_name}.html"
            )
            body_content += f'<div class="bar-item"><div class="bar-label"><a href="{details_path}" title="Ver detalhes">{escape(problem)}</a></div><div class="bar-wrapper"><div class="bar" style="width: {bar_width}%; background-color: {background_color}; color: {text_color};">{count}</div></div></div>'
        body_content += "</div>"
    else:
        body_content += "<p>Nenhum problema recorrente. ✅</p>"
    body_content += "</div></div>"

    return body_content
