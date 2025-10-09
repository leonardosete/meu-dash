"""
Módulo de Serviço para encapsular a lógica de negócio principal da aplicação.
"""

import shutil
import os
from datetime import datetime
import logging
from werkzeug.utils import secure_filename

from .analisar_alertas import analisar_arquivo_csv
from .analise_tendencia import gerar_relatorio_tendencia
from .get_date_range import get_date_range_from_file
from . import context_builder, gerador_paginas
from .constants import MAX_REPORTS_HISTORY

logger = logging.getLogger(__name__)


def _enforce_report_limit(db, Report):
    """
    Garante que o número de relatórios no banco de dados não exceda o limite.

    Se o limite for excedido, os relatórios mais antigos são excluídos, tanto do
    banco de dados quanto do sistema de arquivos, para manter a aplicação
    performática e controlar o uso de disco.
    """
    try:
        total_reports = Report.query.count()
        reports_to_delete_count = total_reports - MAX_REPORTS_HISTORY

        if reports_to_delete_count > 0:
            logger.info(
                f"Limite de {MAX_REPORTS_HISTORY} relatórios excedido. "
                f"Excluindo {reports_to_delete_count} relatório(s) mais antigo(s)."
            )

            # Encontra os relatórios mais antigos para excluir, ordenando por timestamp
            oldest_reports = (
                Report.query.order_by(Report.timestamp.asc())
                .limit(reports_to_delete_count)
                .all()
            )

            for report in oldest_reports:
                logger.warning(
                    f"Excluindo relatório antigo: {report.original_filename} de {report.timestamp}"
                )
                report_dir = os.path.dirname(report.report_path)
                if os.path.isdir(report_dir):
                    shutil.rmtree(report_dir)
                db.session.delete(report)

            db.session.commit()
            logger.info("Limpeza de relatórios antigos concluída com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao tentar aplicar o limite de histórico: {e}")
        db.session.rollback()


def process_upload_and_generate_reports(
    file_atual,
    upload_folder: str,
    reports_folder: str,
    db,
    Report,
    TrendAnalysis,
    base_dir: str,
):
    """Orquestra o fluxo completo de processamento para um único arquivo de upload.

    Esta função atua como o coração da lógica de negócio, executando uma sequência
    de passos para analisar um arquivo CSV e gerar um ecossistema de relatórios.
    Os passos incluem:
    1. Salvar o arquivo de forma segura.
    2. Preparar os diretórios de saída.
    3. Realizar uma análise de tendência se um relatório anterior existir.
    4. Executar a análise principal e completa do arquivo.
    5. Construir o contexto de dados para os templates.
    6. Gerar todas as páginas HTML do relatório.
    7. Persistir os metadados da análise no banco de dados.
    8. Aplicar a política de retenção para limpar relatórios antigos.

    Args:
        file_atual (werkzeug.datastructures.FileStorage): O objeto do arquivo enviado
            pelo Flask.
        upload_folder (str): O caminho absoluto para a pasta de uploads.
        reports_folder (str): O caminho absoluto para a pasta onde os relatórios
            serão salvos.
        db (flask_sqlalchemy.SQLAlchemy): A instância do banco de dados SQLAlchemy.
        Report (db.Model): A classe do modelo `Report` para interagir com o banco.
        TrendAnalysis (db.Model): A classe do modelo `TrendAnalysis`.
        base_dir (str): O diretório base da aplicação, usado para resolver caminhos
            de templates.

    Returns:
        dict | None: Um dicionário contendo `run_folder` e `report_filename` para
        construir a URL de redirecionamento em caso de sucesso. Retorna `None` se
        ocorrer uma falha no processo.
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
    # LÓGICA REVISADA: Busca o relatório correto para comparação.
    # Prioriza o último relatório que foi 'current' em uma análise de tendência.
    last_trend_analysis_obj = TrendAnalysis.query.order_by(
        TrendAnalysis.timestamp.desc()
    ).first()
    previous_report_for_trend = None

    if last_trend_analysis_obj:
        # Se já existe uma tendência, o próximo ponto de comparação é o relatório 'atual' da última tendência.
        previous_report_for_trend = last_trend_analysis_obj.current_report
        logger.info(
            f"Última análise de tendência encontrada. Usando o relatório '{previous_report_for_trend.original_filename}' como base para a próxima tendência."
        )
    else:
        # Se não há tendências, usa o último relatório geral como base (para a primeira tendência).
        previous_report_for_trend = Report.query.order_by(
            Report.timestamp.desc()
        ).first()
        if previous_report_for_trend:
            logger.info(
                f"Nenhuma análise de tendência anterior encontrada. Usando o último relatório geral '{previous_report_for_trend.original_filename}' como base."
            )

    trend_report_path_relative = None
    new_trend_analysis = None

    if previous_report_for_trend and os.path.exists(
        previous_report_for_trend.json_summary_path
    ):
        date_range_anterior_obj = (
            datetime.strptime(
                previous_report_for_trend.date_range.split(" a ")[0], "%d/%m/%Y"
            )
            if previous_report_for_trend.date_range
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
                json_anterior=previous_report_for_trend.json_summary_path,
                json_atual=temp_analysis_results["json_path"],
                csv_anterior_name=previous_report_for_trend.original_filename,
                csv_atual_name=filename_atual,
                output_path=output_trend_path,
                date_range_anterior=previous_report_for_trend.date_range,
                date_range_atual=date_range_atual,
            )
            trend_report_path_relative = os.path.basename(output_trend_path)
            logger.info(f"Relatório de tendência gerado em: {output_trend_path}")

            # Prepara o objeto TrendAnalysis para ser salvo depois
            new_trend_analysis = TrendAnalysis(
                trend_report_path=output_trend_path,
                previous_report_id=previous_report_for_trend.id,
            )

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

    # Se uma análise de tendência foi criada, associa o ID do novo relatório e a salva
    if new_trend_analysis:
        db.session.flush()  # Garante que new_report receba um ID
        new_trend_analysis.current_report_id = new_report.id
        db.session.add(new_trend_analysis)

    db.session.commit()

    # 7. Aplicar política de retenção de histórico
    _enforce_report_limit(db, Report)

    return {
        "run_folder": run_folder_name,
        "report_filename": os.path.basename(summary_html_path),
    }


def process_direct_comparison(files: list, upload_folder: str, reports_folder: str):
    """Orquestra a comparação direta entre dois arquivos CSV.

    Este serviço lida com a funcionalidade de "comparar dois arquivos". Ele salva
    temporariamente os arquivos, determina sua ordem cronológica, executa uma
    análise completa em cada um e, finalmente, gera um relatório de tendência
    comparando os dois. Os arquivos temporários são limpos no final.

    Args:
        files (list): Uma lista de dois objetos `FileStorage` enviados pelo Flask.
        upload_folder (str): O caminho absoluto para a pasta de uploads temporários.
        reports_folder (str): O caminho absoluto para a pasta de relatórios.

    Returns:
        dict: Um dicionário com `run_folder` e `report_filename` para o
              redirecionamento para o relatório de tendência gerado.

    Raises:
        ValueError: Se não for possível determinar a ordem cronológica dos
            arquivos (por exemplo, se as datas não puderem ser extraídas de seus
            conteúdos).
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
