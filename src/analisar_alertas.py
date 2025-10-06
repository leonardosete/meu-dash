import pandas as pd
import numpy as np
import os
from typing import Tuple, Dict
from datetime import datetime
from .constants import (
    ACAO_ESTABILIZADA, ACAO_INCONSISTENTE, ACAO_INTERMITENTE, ACAO_FALHA_PERSISTENTE, ACAO_STATUS_AUSENTE,
    ACAO_SEMPRE_OK, ACAO_INSTABILIDADE_CRONICA, ACAO_FLAGS_ATUACAO,
    ACAO_FLAGS_OK, ACAO_FLAGS_INSTABILIDADE, SEVERITY_WEIGHTS, PRIORITY_GROUP_WEIGHTS, ACAO_WEIGHTS,
    COL_CREATED_ON, COL_NODE, COL_CMDB_CI, COL_SELF_HEALING_STATUS, COL_ASSIGNMENT_GROUP,
    COL_SHORT_DESCRIPTION, COL_NUMBER, COL_SOURCE, COL_METRIC_NAME, COL_CMDB_CI_SYS_CLASS_NAME,
    COL_SEVERITY, COL_PRIORITY_GROUP, GROUP_COLS, ESSENTIAL_COLS, STATUS_OK, STATUS_NOT_OK,
    UNKNOWN, NO_STATUS, LOG_INVALIDOS_FILENAME, LIMIAR_ALERTAS_RECORRENTES
)
from . import gerador_paginas

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
        ACAO_INTERMITENTE: "⚠️", ACAO_FALHA_PERSISTENTE: "❌", ACAO_STATUS_AUSENTE: "❓",
        ACAO_INCONSISTENTE: "🔍", ACAO_SEMPRE_OK: "✅", ACAO_ESTABILIZADA: "⚠️✅",
        ACAO_INSTABILIDADE_CRONICA: "🔁"
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
# EXECUÇÃO PRINCIPAL
# =============================================================================

def analisar_arquivo_csv(input_file: str, output_dir: str, light_analysis: bool = False, trend_report_path: str = None) -> Dict[str, str]:
    """
    Função principal que orquestra a análise de um arquivo CSV e a geração de relatórios.
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

    # 1. Análise de Dados
    df, num_logs_invalidos = carregar_dados(input_file, output_dir)
    summary = analisar_grupos(df)
    export_summary_to_json(summary.copy(), output_json)

    if light_analysis:
        print("💡 Análise leve concluída. Apenas o resumo JSON foi gerado.")
        return {'html_path': None, 'json_path': output_json}

    # 2. Geração de Relatórios CSV
    df_atuacao = gerar_relatorios_csv(summary, output_actuation_csv, output_ok_csv, output_instability_csv)
    
    # 3. Geração de Todas as Páginas HTML
    df_ok_filtered = summary[summary["acao_sugerida"].isin(ACAO_FLAGS_OK)]
    df_instabilidade_filtered = summary[summary["acao_sugerida"].isin(ACAO_FLAGS_INSTABILIDADE)]
    
    top_problemas_atuacao = df_atuacao.groupby(COL_SHORT_DESCRIPTION, observed=True)['alert_count'].sum().nlargest(5)
    top_problemas_remediados = df_ok_filtered.groupby(COL_SHORT_DESCRIPTION, observed=True)['alert_count'].sum().nlargest(5)
    top_problemas_geral = summary.groupby(COL_SHORT_DESCRIPTION, observed=True)['alert_count'].sum().nlargest(10)
    top_problemas_instabilidade = df_instabilidade_filtered.groupby(COL_SHORT_DESCRIPTION, observed=True)['alert_count'].sum().nlargest(5)
    
    metric_counts = df_atuacao[COL_METRIC_NAME].value_counts()
    top_metrics = metric_counts[metric_counts > 0].nlargest(5)

    summary_filename = os.path.basename(output_summary_html)
    plan_dir_base_name = os.path.basename(plan_dir)

    gerador_paginas.gerar_paginas_detalhe_problema(df_atuacao, top_problemas_atuacao.index, details_dir, summary_filename, 'aberto_', plan_dir_base_name, timestamp_str)
    gerador_paginas.gerar_paginas_detalhe_problema(df_ok_filtered, top_problemas_remediados.index, details_dir, summary_filename, 'remediado_', plan_dir_base_name, timestamp_str)
    gerador_paginas.gerar_paginas_detalhe_problema(summary, top_problemas_geral.index, details_dir, summary_filename, 'geral_', plan_dir_base_name, timestamp_str)
    gerador_paginas.gerar_paginas_detalhe_problema(df_instabilidade_filtered, top_problemas_instabilidade.index, details_dir, summary_filename, 'instabilidade_', plan_dir_base_name, timestamp_str)
    gerador_paginas.gerar_paginas_detalhe_metrica(df_atuacao, top_metrics.index, details_dir, summary_filename, plan_dir_base_name, timestamp_str)

    gerador_paginas.gerar_resumo_executivo(summary, df_atuacao, num_logs_invalidos, output_summary_html, plan_dir, details_dir, timestamp_str, trend_report_path)
    gerador_paginas.gerar_planos_por_squad(df_atuacao, plan_dir, timestamp_str)
    
    all_squads = df_atuacao[COL_ASSIGNMENT_GROUP].value_counts()
    gerador_paginas.gerar_pagina_squads(all_squads, plan_dir, output_dir, os.path.basename(output_summary_html), timestamp_str)
    
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    base_template_dir = os.path.join(SCRIPT_DIR, '..', 'templates')
    sucesso_template_file = os.path.join(base_template_dir, 'sucesso_template.html')
    editor_template_file = os.path.join(base_template_dir, 'editor_template.html')

    gerador_paginas.gerar_pagina_sucesso(output_dir, output_ok_csv, sucesso_template_file)
    gerador_paginas.gerar_pagina_instabilidade(output_dir, output_instability_csv, sucesso_template_file)
    gerador_paginas.gerar_pagina_editor_atuacao(output_dir, output_actuation_csv, editor_template_file)
    
    if num_logs_invalidos > 0:
        log_invalidos_path = os.path.join(output_dir, LOG_INVALIDOS_FILENAME)
        gerador_paginas.gerar_pagina_logs_invalidos(output_dir, log_invalidos_path, sucesso_template_file)

    print(f"✅ Análise completa finalizada. Relatório principal em: {output_summary_html}")
    return {'html_path': output_summary_html, 'json_path': output_json}
