"""
Módulo de Serviço para encapsular a lógica de negócio principal da aplicação.
"""

import os
from datetime import datetime
import logging
from werkzeug.utils import secure_filename

from .analisar_alertas import analisar_arquivo_csv
from .analise_tendencia import gerar_relatorio_tendencia
from .get_date_range import get_date_range_from_file
from . import context_builder, gerador_paginas
from .constants import (
    ACAO_FLAGS_INSTABILIDADE,
    ACAO_FLAGS_OK,
    COL_ASSIGNMENT_GROUP,
    COL_METRIC_NAME,
    COL_SHORT_DESCRIPTION,
    LOG_INVALIDOS_FILENAME,
)

logger = logging.getLogger(__name__)


def process_upload_and_generate_reports(
    file_atual, upload_folder: str, reports_folder: str, db, Report, base_dir: str
):
    """
    Serviço que orquestra todo o processo de análise de um arquivo de upload.
    1. Salva o arquivo.
    2. Executa a análise de tendência (se aplicável).
    3. Executa a análise completa.
    4. Constrói o contexto para os templates.
    5. Gera todas as páginas HTML.
    6. Salva o registro no banco de dados.

    Retorna um dicionário com informações para o redirecionamento ou None em caso de falha.
    """
    # 1. Salvar arquivo e preparar ambiente
    filename_atual = secure_filename(file_atual.filename)
    filepath_atual = os.path.join(
        upload_folder, f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename_atual}"
    )
    file_atual.save(filepath_atual)
    date_range_atual = get_date_range_from_file(filepath_atual)

    run_folder_name = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_dir = os.path.join(reports_folder, run_folder_name)
    os.makedirs(output_dir, exist_ok=True)

    # 2. Análise de Tendência (se aplicável)
    last_report = Report.query.order_by(Report.timestamp.desc()).first()
    trend_report_path_relative = None

    if (
        last_report
        and last_report.json_summary_path
        and os.path.exists(last_report.json_summary_path)
    ):
        logger.info("Relatório anterior encontrado. Iniciando análise de tendência.")
        date_range_anterior_obj = (
            datetime.strptime(last_report.date_range.split(" a ")[0], "%d/%m/%Y")
            if last_report.date_range
            else None
        )
        date_range_atual_obj = (
            datetime.strptime(date_range_atual.split(" a ")[0], "%d/%m/%Y")
            if date_range_atual
            else None
        )

        if (
            date_range_anterior_obj
            and date_range_atual_obj
            and date_range_atual_obj > date_range_anterior_obj
        ):
            logger.info("Período do upload é mais recente. Gerando tendência...")
            temp_analysis_results = analisar_arquivo_csv(
                filepath_atual, output_dir, light_analysis=True
            )
            output_trend_path = os.path.join(output_dir, "resumo_tendencia.html")

            gerar_relatorio_tendencia(
                json_anterior=last_report.json_summary_path,
                json_atual=temp_analysis_results["json_path"],
                csv_anterior_name=last_report.original_filename,
                csv_atual_name=filename_atual,
                output_path=output_trend_path,
                date_range_anterior=last_report.date_range,
                date_range_atual=date_range_atual,
            )
            trend_report_path_relative = os.path.basename(output_trend_path)
            logger.info(f"Relatório de tendência gerado em: {output_trend_path}")
        else:
            logger.warning(
                "O arquivo enviado não é cronologicamente mais recente. A análise de tendência será pulada."
            )
    else:
        logger.info(
            "Nenhum relatório anterior encontrado para comparação de tendência."
        )

    # 3. Análise Principal (Completa)
    analysis_results = analisar_arquivo_csv(
        input_file=filepath_atual, output_dir=output_dir, light_analysis=False
    )

    # 4. Construção do Contexto
    dashboard_context = context_builder.build_dashboard_context(
        summary_df=analysis_results["summary"],
        df_atuacao=analysis_results["df_atuacao"],
        num_logs_invalidos=analysis_results["num_logs_invalidos"],
        output_dir=output_dir,
        plan_dir=os.path.join(output_dir, "planos_de_acao"),
        details_dir=os.path.join(output_dir, "detalhes"),
        trend_report_path=trend_report_path_relative,
    )

    # 5. Geração de todas as páginas HTML
    # Encapsula a geração de todas as páginas em uma única chamada de orquestração
    summary_html_path = gerador_paginas.gerar_ecossistema_de_relatorios(
        dashboard_context=dashboard_context,
        analysis_results=analysis_results,
        output_dir=output_dir,
        base_dir=base_dir,
    )

    # 6. Salvar registro no banco de dados
    new_report = Report(
        original_filename=filename_atual,
        report_path=summary_html_path,
        json_summary_path=analysis_results["json_path"],
        date_range=date_range_atual,
    )
    db.session.add(new_report)
    db.session.commit()

    return {
        "run_folder": run_folder_name,
        "report_filename": os.path.basename(summary_html_path),
    }


def process_direct_comparison(files: list, upload_folder: str, reports_folder: str):
    """
    Serviço que orquestra a comparação direta entre dois arquivos.
    """
    saved_filepaths = []
    try:
        for f in files:
            filename = secure_filename(f.filename)
            filepath = os.path.join(
                upload_folder,
                f"temp_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}",
            )
            f.save(filepath)
            saved_filepaths.append(filepath)

        from .utils import (
            sort_files_by_date,
        )  # Importação local para evitar dependência circular

        sorted_paths = sort_files_by_date(saved_filepaths)
        if not sorted_paths:
            raise ValueError(
                "Não foi possível determinar a ordem cronológica dos arquivos."
            )

        filepath_atual, filepath_anterior = sorted_paths
        filename_atual = os.path.basename(filepath_atual).replace(
            f"temp_{os.path.basename(filepath_atual).split('_')[1]}_", ""
        )
        filename_anterior = os.path.basename(filepath_anterior).replace(
            f"temp_{os.path.basename(filepath_anterior).split('_')[1]}_", ""
        )

        run_folder_name = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_compare"
        output_dir = os.path.join(reports_folder, run_folder_name)
        output_dir_anterior = os.path.join(output_dir, "anterior")
        output_dir_atual = os.path.join(output_dir, "atual")

        logger.info(
            f"Executando análise completa para o arquivo ATUAL: {filename_atual}"
        )
        results_atual = analisar_arquivo_csv(
            filepath_atual, output_dir_atual, light_analysis=False
        )
        logger.info(
            f"Executando análise completa para o arquivo ANTERIOR: {filename_anterior}"
        )
        results_anterior = analisar_arquivo_csv(
            filepath_anterior, output_dir_anterior, light_analysis=False
        )

        output_trend_path = os.path.join(output_dir, "resumo_tendencia.html")
        gerar_relatorio_tendencia(
            json_anterior=results_anterior["json_path"],
            json_atual=results_atual["json_path"],
            csv_anterior_name=filename_anterior,
            csv_atual_name=filename_atual,
            output_path=output_trend_path,
            date_range_anterior=get_date_range_from_file(filepath_anterior),
            date_range_atual=get_date_range_from_file(filepath_atual),
            is_direct_comparison=True,
        )
        return {
            "run_folder": run_folder_name,
            "report_filename": "resumo_tendencia.html",
        }

    finally:
        for p in saved_filepaths:
            if os.path.exists(p):
                os.remove(p)
