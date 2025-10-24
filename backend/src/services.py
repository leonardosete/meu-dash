"""
Módulo de Serviço para encapsular a lógica de negócio principal da aplicação.
"""

import json
import shutil
import os
from datetime import datetime
import logging
from werkzeug.utils import secure_filename

from .analisar_alertas import analisar_arquivo_csv
from .analise_tendencia import gerar_relatorio_tendencia
from .get_date_range import get_date_range_from_file
from . import context_builder, gerador_paginas
from .constants import (
    MAX_REPORTS_HISTORY,
    ACAO_FLAGS_ATUACAO,
    ACAO_FLAGS_INSTABILIDADE,
)

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


def calculate_kpi_summary(report_path: str) -> dict | None:
    """Calcula os KPIs gerenciais a partir de um arquivo de resumo JSON.

    Args:
        report_path (str): O caminho para o arquivo JSON de resumo.

    Returns:
        dict | None: Um dicionário com os KPIs ou None se ocorrer um erro.
    """
    try:
        with open(report_path, "r") as f:
            summary_data = json.load(f)

        if not summary_data:
            return None

        total_casos = len(summary_data)
        casos_atuacao = sum(
            1
            for item in summary_data
            if item.get("acao_sugerida") in ACAO_FLAGS_ATUACAO
        )
        casos_instabilidade = sum(
            1
            for item in summary_data
            if item.get("acao_sugerida") in ACAO_FLAGS_INSTABILIDADE
        )
        alertas_instabilidade = sum(
            item.get("alert_count", 0)
            for item in summary_data
            if item.get("acao_sugerida") in ACAO_FLAGS_INSTABILIDADE
        )
        alertas_sucesso = sum(
            item.get("alert_count", 0)
            for item in summary_data
            if item.get("acao_sugerida") not in ACAO_FLAGS_ATUACAO
        )
        alertas_atuacao = sum(
            item.get("alert_count", 0)
            for item in summary_data
            if item.get("acao_sugerida") in ACAO_FLAGS_ATUACAO
        )
        taxa_sucesso = (
            (1 - (casos_atuacao / total_casos)) * 100 if total_casos > 0 else 100
        )
        casos_sucesso = total_casos - casos_atuacao

        return {
            "casos_atuacao": casos_atuacao,
            "alertas_atuacao": alertas_atuacao,
            "casos_instabilidade": casos_instabilidade,
            "alertas_instabilidade": alertas_instabilidade,
            "alertas_sucesso": alertas_sucesso,
            "taxa_sucesso_automacao": f"{taxa_sucesso:.1f}%",
            "taxa_sucesso_valor": taxa_sucesso,
            "casos_sucesso": casos_sucesso,
            "total_casos": total_casos,
        }
    except (json.JSONDecodeError, FileNotFoundError, Exception) as e:
        logger.error(f"Erro ao ler ou processar o JSON de resumo: {e}")
        return None


def get_dashboard_summary_data(db, Report, TrendAnalysis) -> dict:
    """
    Busca e consolida todos os dados necessários para o dashboard principal.

    Esta função é chamada pelo endpoint da API e encapsula a lógica de negócio
    de buscar o último relatório, calcular KPIs, verificar o plano de ação e
    obter o histórico de tendências.

    Args:
        db: Instância do SQLAlchemy.
        Report: Modelo Report.
        TrendAnalysis: Modelo TrendAnalysis.

    Returns:
        Um dicionário contendo os dados brutos para o dashboard.
    """
    kpi_summary = None
    latest_report_files = None

    last_report = Report.query.order_by(Report.timestamp.desc()).first()
    if last_report:
        run_folder_path = os.path.dirname(last_report.report_path)
        run_folder_name = os.path.basename(run_folder_path)

        # Calcula os KPIs do último relatório
        if last_report.json_summary_path and os.path.exists(
            last_report.json_summary_path
        ):
            kpi_summary = calculate_kpi_summary(last_report.json_summary_path)

        # Prepara os nomes dos arquivos do último relatório para a API construir as URLs
        latest_report_files = {
            "run_folder": run_folder_name,
            "summary": os.path.basename(last_report.report_path),
        }
        action_plan_path = os.path.join(run_folder_path, "atuar.html")
        if os.path.exists(action_plan_path):
            latest_report_files["action_plan"] = "atuar.html"

    # Busca o histórico de tendências separadamente
    trend_history = []
    trend_analyses = (
        TrendAnalysis.query.order_by(TrendAnalysis.timestamp.desc()).limit(60).all()
    )
    for i, analysis in enumerate(trend_analyses):
        try:
            run_folder = os.path.basename(os.path.dirname(analysis.trend_report_path))
            filename = os.path.basename(analysis.trend_report_path)
            trend_info = {
                "run_folder": run_folder,
                "filename": filename,
                "date": analysis.timestamp,
            }
            trend_history.append(trend_info)
            # Se for a análise de tendência mais recente, adiciona ao `latest_report_files`
            if i == 0 and latest_report_files:
                latest_report_files["trend_run_folder"] = run_folder
                latest_report_files["trend"] = filename
        except Exception as e:
            logger.warning(
                f"Erro ao processar histórico de tendência para o relatório {analysis.id}: {e}"
            )
            continue

    return {
        "kpi_summary": kpi_summary,
        "trend_history": trend_history,
        "latest_report_files": latest_report_files,
    }


def get_reports_list(Report) -> list:
    """
    Busca e retorna uma lista de todos os relatórios do banco de dados.

    Args:
        Report: Modelo Report do SQLAlchemy.

    Returns:
        Uma lista de dicionários, onde cada dicionário contém os metadados
        de um relatório.
    """
    reports = Report.query.order_by(Report.timestamp.desc()).all()
    report_data = []
    for report in reports:
        try:
            report_data.append(
                {
                    "id": report.id,
                    "timestamp": report.timestamp,
                    "original_filename": report.original_filename,
                    "date_range": report.date_range,
                    "run_folder": os.path.basename(os.path.dirname(report.report_path)),
                    "filename": os.path.basename(report.report_path),
                }
            )
        except Exception as e:
            logger.warning(
                f"Erro ao processar dados do relatório {report.id} para a lista: {e}"
            )
            continue
    return report_data


def delete_report_and_artifacts(report_id: int, db, Report) -> bool:
    """
    Exclui um relatório e todos os seus artefatos associados (arquivos e registro no DB).

    Args:
        report_id (int): O ID do relatório a ser excluído.
        db (SQLAlchemy): A instância do banco de dados.
        Report (Model): A classe do modelo Report.

    Returns:
        bool: True se a exclusão for bem-sucedida, False caso contrário.
    """
    report = db.session.get(Report, report_id)
    if not report:
        logger.warning(
            f"Tentativa de excluir relatório inexistente com ID: {report_id}"
        )
        return False

    try:
        # Pega o diretório do relatório (ex: '.../data/reports/run_20251005_103000')
        report_dir = os.path.dirname(report.report_path)

        # Deleta a pasta inteira do 'run', garantindo que todos os arquivos associados sejam removidos
        if os.path.isdir(report_dir):
            shutil.rmtree(report_dir)
            logger.info(f"Diretório '{report_dir}' excluído com sucesso.")

        # Deleta o registro do banco de dados (e TrendAnalysis em cascata)
        db.session.delete(report)
        db.session.commit()
        logger.info(
            f"Relatório '{report.original_filename}' (ID: {report_id}) excluído do banco de dados."
        )
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao excluir o relatório {report_id}: {e}", exc_info=True)
        return False


def process_upload_and_generate_reports(
    file_recente,
    upload_folder: str,
    reports_folder: str,
    db,
    Report,
    TrendAnalysis,
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
        file_recente (werkzeug.datastructures.FileStorage): O objeto do arquivo enviado
            pelo Flask.
        upload_folder (str): O caminho absoluto para a pasta de uploads.
        reports_folder (str): O caminho absoluto para a pasta onde os relatórios
            serão salvos.
        db (flask_sqlalchemy.SQLAlchemy): A instância do banco de dados SQLAlchemy.
        Report (db.Model): A classe do modelo `Report` para interagir com o banco.
        TrendAnalysis (db.Model): A classe do modelo `TrendAnalysis`.

    Returns:
        dict | None: Um dicionário contendo `run_folder` e `report_filename` para
        construir a URL de redirecionamento em caso de sucesso. Retorna `None` se
        ocorrer uma falha no processo.
    """
    # 1. Salvar arquivo, preparar ambiente e executar a análise completa UMA VEZ
    filename_recente = secure_filename(file_recente.filename)
    filepath_recente = os.path.join(
        upload_folder, f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename_recente}"
    )
    file_recente.save(filepath_recente)
    date_range_recente = get_date_range_from_file(filepath_recente)

    run_folder_name = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_dir = os.path.join(reports_folder, run_folder_name)
    os.makedirs(output_dir, exist_ok=True)

    # Lê a URL do frontend UMA VEZ para garantir consistência em todos os relatórios gerados.
    frontend_url = os.getenv("FRONTEND_BASE_URL", "/")

    logger.info(f"Executando análise completa para o arquivo: {filename_recente}")
    analysis_results = analisar_arquivo_csv(
        input_file=filepath_recente, output_dir=output_dir, light_analysis=False
    )

    # 2. Análise de Tendência (se aplicável)
    # LÓGICA REVISADA: Busca o relatório correto para comparação.
    # Prioriza o último relatório que foi 'current' em uma análise de tendência.
    last_trend_analysis_obj = TrendAnalysis.query.order_by(
        TrendAnalysis.timestamp.desc()
    ).first()
    previous_report_for_trend = None

    if last_trend_analysis_obj:
        # Se já existe uma tendência, o próximo ponto de comparação é o relatório 'recente' da última tendência.
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
        date_range_recente_obj = (
            datetime.strptime(date_range_recente.split(" a ")[0], "%d/%m/%Y")
            if date_range_recente
            else None
        )

        if (
            date_range_anterior_obj
            and date_range_recente_obj
            and date_range_recente_obj > date_range_anterior_obj
        ):
            logger.info("Período do upload é mais recente. Gerando tendência...")
            output_trend_path = os.path.join(output_dir, "comparativo_periodos.html")

            # REFATORADO: Usa o resultado da análise completa já executada
            gerar_relatorio_tendencia(
                json_anterior=previous_report_for_trend.json_summary_path,
                json_recente=analysis_results[
                    "json_path"
                ],  # Alterado para usar o resultado da análise completa
                csv_anterior_name=previous_report_for_trend.original_filename,
                csv_recente_name=filename_recente,
                output_path=output_trend_path,
                date_range_anterior=previous_report_for_trend.date_range,
                date_range_recente=date_range_recente,
                frontend_url=frontend_url,  # Passa a URL para o relatório de tendência
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
            # Retorna um dicionário com o aviso para ser exibido na interface
            return {
                "warning": "Análise de tendência pulada: o arquivo enviado não é mais recente. Para comparar arquivos específicos, use a aba 'Comparação Direta'."
            }
    else:
        logger.info(
            "Nenhum relatório anterior encontrado para comparação de tendência."
        )

    # 3. Construção do Contexto (Análise principal já foi feita)
    dashboard_context = context_builder.build_dashboard_context(
        summary_df=analysis_results["summary"],
        df_atuacao=analysis_results["df_atuacao"],
        num_logs_invalidos=analysis_results["num_logs_invalidos"],
        output_dir=output_dir,
        plan_dir=os.path.join(output_dir, "planos_de_acao"),
        details_dir=os.path.join(output_dir, "detalhes"),
        trend_report_path=trend_report_path_relative,
    )

    # 4. Geração de todas as páginas HTML
    summary_html_path = gerador_paginas.gerar_ecossistema_de_relatorios(
        dashboard_context=dashboard_context,
        analysis_results=analysis_results,
        output_dir=output_dir,
        frontend_url=frontend_url,
    )

    # 5. Salvar registro no banco de dados
    new_report = Report(
        original_filename=filename_recente,
        report_path=summary_html_path,
        json_summary_path=analysis_results["json_path"],
        date_range=date_range_recente,
    )
    db.session.add(new_report)

    # Se uma análise de tendência foi criada, associa o ID do novo relatório e a salva
    if new_trend_analysis:
        db.session.flush()  # Garante que new_report receba um ID
        new_trend_analysis.current_report_id = new_report.id
        db.session.add(new_trend_analysis)

    db.session.commit()

    # 6. Aplicar política de retenção de histórico
    _enforce_report_limit(db, Report)

    # 7. Retornar resultado
    # Verifica a existência dos arquivos opcionais antes de incluir no retorno
    action_plan_filename = "atuar.html" if os.path.exists(os.path.join(output_dir, "atuar.html")) else None

    return {
        "run_folder": run_folder_name,
        "summary_report_filename": os.path.basename(summary_html_path),
        "action_plan_filename": action_plan_filename,
        "trend_report_filename": trend_report_path_relative,
        "json_summary_path": analysis_results["json_path"],
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
    # Lê a URL do frontend UMA VEZ para garantir consistência.
    frontend_url = os.getenv("FRONTEND_BASE_URL", "/")

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

        filepath_recente, filepath_anterior = sorted_paths
        filename_recente = os.path.basename(filepath_recente).replace(
            f"temp_{os.path.basename(filepath_recente).split('_')[1]}_", ""
        )
        filename_anterior = os.path.basename(filepath_anterior).replace(
            f"temp_{os.path.basename(filepath_anterior).split('_')[1]}_", ""
        )

        run_folder_name = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_compare"
        output_dir = os.path.join(reports_folder, run_folder_name)
        output_dir_anterior = os.path.join(output_dir, "anterior")
        output_dir_recente = os.path.join(output_dir, "recente")

        logger.info(
            f"Executando análise completa para o arquivo ATUAL: {filename_recente}"
        )
        results_recente = analisar_arquivo_csv(
            filepath_recente, output_dir_recente, light_analysis=False
        )
        logger.info(
            f"Executando análise completa para o arquivo ANTERIOR: {filename_anterior}"
        )
        results_anterior = analisar_arquivo_csv(
            filepath_anterior, output_dir_anterior, light_analysis=False
        )

        output_trend_path = os.path.join(output_dir, "comparativo_periodos.html")
        gerar_relatorio_tendencia(
            json_anterior=results_anterior["json_path"],
            json_recente=results_recente["json_path"],
            csv_anterior_name=filename_anterior,
            csv_recente_name=filename_recente,
            output_path=output_trend_path,
            date_range_anterior=get_date_range_from_file(filepath_anterior),
            date_range_recente=get_date_range_from_file(filepath_recente),
            is_direct_comparison=True,
            frontend_url=frontend_url,
        )
        return {
            "run_folder": run_folder_name,
            "report_filename": "comparativo_periodos.html",
        }

    finally:
        for p in saved_filepaths:
            if os.path.exists(p):
                os.remove(p)