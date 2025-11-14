"""
Módulo de Serviço para encapsular a lógica de negócio principal da aplicação.
"""

import io
import json
import os
import shutil
import zipfile
from datetime import datetime
import logging
from werkzeug.utils import secure_filename

from .analisar_alertas import analisar_arquivo_csv
from .analise_tendencia import (
    gerar_analise_comparativa,
    load_summary_from_json,
    calculate_kpis_and_merged_df,
    prepare_trend_dataframes,
    generate_executive_summary_html,
)
from .get_date_range import get_date_range_from_file
from . import context_builder, gerador_paginas
from .models import ReportBundle
from .constants import (
    MAX_REPORTS_HISTORY,
    ACAO_FLAGS_ATUACAO,
    ACAO_FLAGS_INSTABILIDADE,
    ACAO_SUCESSO_PARCIAL,
    ACAO_FLAGS_OK,
)

logger = logging.getLogger(__name__)

ACTION_PLAN_FILENAME = "atuar.html"


def _enforce_report_limit(db, report_model):
    """
    Garante que o número de relatórios no banco de dados não exceda o limite.

    Se o limite for excedido, os relatórios mais antigos são excluídos, tanto do
    banco de dados quanto do sistema de arquivos, para manter a aplicação
    performática e controlar o uso de disco.
    """
    try:
        total_reports = report_model.query.count()
        reports_to_delete_count = total_reports - MAX_REPORTS_HISTORY

        if reports_to_delete_count > 0:
            logger.info(
                f"Limite de {MAX_REPORTS_HISTORY} relatórios excedido. "
                f"Excluindo {reports_to_delete_count} relatório(s) mais antigo(s)."
            )

            # Encontra os relatórios mais antigos para excluir, ordenando por timestamp
            oldest_reports = (
                report_model.query.order_by(report_model.timestamp.asc())
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


def _zip_directory(source_dir: str) -> bytes:
    """Compacta o conteúdo de um diretório e retorna os bytes do arquivo ZIP."""

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(source_dir):
            for filename in files:
                file_path = os.path.join(root, filename)
                arcname = os.path.relpath(file_path, source_dir)
                zipf.write(file_path, arcname)
    buffer.seek(0)
    return buffer.read()


def _extract_bundle_to_directory(bundle_bytes: bytes, destination_dir: str) -> None:
    """Extrai um arquivo ZIP armazenado em memória para o diretório de destino."""

    with zipfile.ZipFile(io.BytesIO(bundle_bytes)) as zipf:
        for member in zipf.infolist():
            extracted_path = os.path.join(destination_dir, member.filename)
            if member.is_dir():
                os.makedirs(extracted_path, exist_ok=True)
                continue
            os.makedirs(os.path.dirname(extracted_path), exist_ok=True)
            with zipf.open(member, "r") as src, open(extracted_path, "wb") as dst:
                shutil.copyfileobj(src, dst)


def ensure_run_folder_available(run_folder: str, reports_folder: str) -> bool:
    """Garante que os artefatos de um relatório estejam disponíveis no filesystem."""

    run_folder_path = os.path.join(reports_folder, run_folder)
    if os.path.exists(run_folder_path):
        return True

    bundle = ReportBundle.query.filter_by(run_folder=run_folder).first()
    if not bundle:
        logger.warning(
            "Bundle não encontrado para o diretório de execução '%s'.", run_folder
        )
        return False

    os.makedirs(run_folder_path, exist_ok=True)
    _extract_bundle_to_directory(bundle.bundle, run_folder_path)
    logger.info(
        "Artefatos do relatório restaurados a partir do bundle para '%s'.",
        run_folder_path,
    )
    return True


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
        casos_sucesso_parcial = sum(
            1
            for item in summary_data
            if item.get("acao_sugerida") == ACAO_SUCESSO_PARCIAL
        )
        alertas_instabilidade = sum(
            item.get("alert_count", 0)
            for item in summary_data
            if item.get("acao_sugerida") in ACAO_FLAGS_INSTABILIDADE
        )
        alertas_sucesso = sum(
            item.get("alert_count", 0)
            for item in summary_data
            if item.get("acao_sugerida") in ACAO_FLAGS_OK
        )
        alertas_atuacao = sum(
            item.get("alert_count", 0)
            for item in summary_data
            if item.get("acao_sugerida") in ACAO_FLAGS_ATUACAO
        )
        alertas_sucesso_parcial = sum(
            item.get("alert_count", 0)
            for item in summary_data
            if item.get("acao_sugerida") == ACAO_SUCESSO_PARCIAL
        )

        # CORREÇÃO: A lógica de sucesso agora considera todos os tipos de não-sucesso.
        casos_sucesso = (
            total_casos - casos_atuacao - casos_instabilidade - casos_sucesso_parcial
        )
        taxa_sucesso = (casos_sucesso / total_casos) * 100 if total_casos > 0 else 0

        return {
            "casos_atuacao": casos_atuacao,
            "alertas_atuacao": alertas_atuacao,
            "casos_instabilidade": casos_instabilidade,
            "alertas_instabilidade": alertas_instabilidade,
            "casos_sucesso_parcial": casos_sucesso_parcial,
            "alertas_sucesso_parcial": alertas_sucesso_parcial,
            "alertas_sucesso": alertas_sucesso,
            "taxa_sucesso_automacao": f"{taxa_sucesso:.1f}%",
            "taxa_sucesso_valor": taxa_sucesso,
            "casos_sucesso": casos_sucesso,
            "total_casos": total_casos,
        }
    except (json.JSONDecodeError, FileNotFoundError, Exception) as e:
        logger.error(f"Erro ao ler ou processar o JSON de resumo: {e}")
        return None


def get_dashboard_summary_data(report_model, trend_model, reports_folder: str) -> dict:
    """Monta os dados necessários para o dashboard principal."""

    kpi_summary = None
    latest_report_files: dict | None = None
    quick_diagnosis_html = None
    latest_report_date_range = None

    last_report = report_model.query.order_by(report_model.timestamp.desc()).first()
    if last_report:
        latest_report_date_range = last_report.date_range
        run_folder_name = os.path.basename(os.path.dirname(last_report.report_path))

        if ensure_run_folder_available(run_folder_name, reports_folder):
            run_folder_path = os.path.join(reports_folder, run_folder_name)
            summary_filename = os.path.basename(last_report.report_path)
            json_summary_filename = os.path.basename(last_report.json_summary_path)

            json_summary_full_path = os.path.join(
                run_folder_path, json_summary_filename
            )
            if os.path.exists(json_summary_full_path):
                kpi_summary = calculate_kpi_summary(json_summary_full_path)

            latest_report_files = {
                "run_folder": run_folder_name,
                "summary": summary_filename,
            }

            action_plan_path = os.path.join(run_folder_path, ACTION_PLAN_FILENAME)
            if os.path.exists(action_plan_path):
                latest_report_files["action_plan"] = ACTION_PLAN_FILENAME
        else:
            logger.warning(
                "Não foi possível restaurar os artefatos do relatório '%s'.",
                run_folder_name,
            )

    trend_history = []
    trend_analyses = (
        trend_model.query.order_by(trend_model.timestamp.desc()).limit(60).all()
    )
    for index, analysis in enumerate(trend_analyses):
        try:
            run_folder = os.path.basename(os.path.dirname(analysis.trend_report_path))
            ensure_run_folder_available(run_folder, reports_folder)

            filename = os.path.basename(analysis.trend_report_path)
            trend_info = {
                "run_folder": run_folder,
                "filename": filename,
                "date": analysis.timestamp,
            }
            trend_history.append(trend_info)

            if index == 0 and latest_report_files:
                latest_report_files["trend_run_folder"] = run_folder
                latest_report_files["trend"] = filename
        except Exception as exc:  # pragma: no cover - logging defensivo
            logger.warning(
                "Erro ao processar histórico de tendência %s: %s",
                analysis.id,
                exc,
            )

    if latest_report_files and latest_report_files.get("trend"):
        latest_trend_analysis = trend_model.query.order_by(
            trend_model.timestamp.desc()
        ).first()
        if latest_trend_analysis:
            prev_report = latest_trend_analysis.previous_report
            curr_report = latest_trend_analysis.current_report

            if prev_report and curr_report:
                prev_run_folder = os.path.basename(
                    os.path.dirname(prev_report.report_path)
                )
                curr_run_folder = os.path.basename(
                    os.path.dirname(curr_report.report_path)
                )

                prev_available = ensure_run_folder_available(
                    prev_run_folder, reports_folder
                )
                curr_available = ensure_run_folder_available(
                    curr_run_folder, reports_folder
                )

                if prev_available and curr_available:
                    prev_json_path = os.path.join(
                        reports_folder,
                        prev_run_folder,
                        os.path.basename(prev_report.json_summary_path),
                    )
                    curr_json_path = os.path.join(
                        reports_folder,
                        curr_run_folder,
                        os.path.basename(curr_report.json_summary_path),
                    )

                    if os.path.exists(prev_json_path) and os.path.exists(
                        curr_json_path
                    ):
                        df_p1 = load_summary_from_json(prev_json_path)
                        df_p2 = load_summary_from_json(curr_json_path)

                        if df_p1 is not None and df_p2 is not None:
                            df_p1_atuacao = df_p1[
                                df_p1["acao_sugerida"].isin(ACAO_FLAGS_ATUACAO)
                            ].copy()
                            df_p2_atuacao = df_p2[
                                df_p2["acao_sugerida"].isin(ACAO_FLAGS_ATUACAO)
                            ].copy()

                            kpis, merged_df = calculate_kpis_and_merged_df(
                                df_p1_atuacao, df_p2_atuacao
                            )
                            trend_data = prepare_trend_dataframes(
                                merged_df, df_p1_atuacao, df_p2_atuacao
                            )

                            current_run_folder = os.path.basename(
                                os.path.dirname(curr_report.report_path)
                            )
                            base_url = os.getenv("FRONTEND_BASE_URL", "/")

                            quick_diagnosis_html = generate_executive_summary_html(
                                kpis,
                                trend_data["persistent_squads_summary"],
                                trend_data["new_cases"],
                                is_direct_comparison=False,
                                run_folder=current_run_folder,
                                base_url=base_url,
                            )

    return {
        "kpi_summary": kpi_summary,
        "trend_history": trend_history,
        "latest_report_files": latest_report_files,
        "quick_diagnosis_html": quick_diagnosis_html,
        "latest_report_date_range": latest_report_date_range,
    }


def get_unified_history_list(report_model, trend_model) -> list:
    """
    Busca e retorna uma lista unificada de todos os relatórios e análises de tendência.
    """
    history_items = []

    # 1. Busca relatórios de Análise Padrão
    reports = report_model.query.order_by(report_model.timestamp.desc()).all()
    for report in reports:
        try:
            history_items.append(
                {
                    "id": f"standard-{report.id}",
                    "type": "standard",
                    "timestamp": report.timestamp,
                    "original_filename": report.original_filename,
                    "date_range": report.date_range,
                    "run_folder": os.path.basename(os.path.dirname(report.report_path)),
                    "filename": os.path.basename(report.report_path),
                }
            )
        except Exception as e:
            logger.warning(f"Erro ao processar relatório padrão {report.id}: {e}")

    # 2. Busca relatórios de Análise Comparativa (Tendência)
    analyses = trend_model.query.order_by(trend_model.timestamp.desc()).all()
    for analysis in analyses:
        try:
            # Constrói um nome descritivo para a análise de tendência
            prev_file = (
                analysis.previous_report.original_filename
                if analysis.previous_report
                else "N/A"
            )
            curr_file = (
                analysis.current_report.original_filename
                if analysis.current_report
                else "N/A"
            )
            filename = f"Comparativo: {os.path.basename(curr_file)} vs {os.path.basename(prev_file)}"

            # Constrói o intervalo de datas combinado
            date_range = "N/A"
            if analysis.current_report and analysis.current_report.date_range:
                date_range = analysis.current_report.date_range

            history_items.append(
                {
                    "id": f"comparative-{analysis.id}",
                    "type": "comparative",
                    "timestamp": analysis.timestamp,
                    "original_filename": filename,
                    "date_range": date_range,
                    "run_folder": os.path.basename(
                        os.path.dirname(analysis.trend_report_path)
                    ),
                    "filename": os.path.basename(analysis.trend_report_path),
                }
            )
        except Exception as e:
            logger.warning(f"Erro ao processar análise de tendência {analysis.id}: {e}")

    # 3. Ordena a lista combinada pela data
    history_items.sort(key=lambda x: x["timestamp"], reverse=True)

    return history_items


def delete_report_and_artifacts(report_id: int, db, report_model) -> bool:
    """
    Exclui um relatório e todos os seus artefatos associados (arquivos e registro no DB).

    Args:
    report_id (int): O ID do relatório a ser excluído.
    db (SQLAlchemy): A instância do banco de dados.
    report_model (Model): A classe do modelo Report.

    Returns:
        bool: True se a exclusão for bem-sucedida, False caso contrário.
    """
    report = db.session.get(report_model, report_id)
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
    report_model=None,
    trend_model=None,
    **legacy_models,
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
        report_model (db.Model, opcional): Classe do modelo `Report` utilizada para persistência.
        trend_model (db.Model, opcional): Classe do modelo `TrendAnalysis` utilizada para persistência.
        legacy_models: parâmetros legados (`Report` e `TrendAnalysis`) aceitos para
            compatibilidade retroativa com chamadas antigas.

    Returns:
        dict | None: Um dicionário contendo `run_folder` e `report_filename` para
        construir a URL de redirecionamento em caso de sucesso. Retorna `None` se
        ocorrer uma falha no processo.
    """
    report_model = report_model or legacy_models.pop("Report", None)
    trend_model = trend_model or legacy_models.pop("TrendAnalysis", None)

    if legacy_models:
        unexpected = ", ".join(sorted(legacy_models.keys()))
        raise TypeError(f"Argumentos inesperados: {unexpected}")

    if report_model is None or trend_model is None:
        raise ValueError("Modelos Report/TrendAnalysis não fornecidos.")

    # 1. Salvar arquivo, preparar ambiente e executar a análise completa UMA VEZ
    os.makedirs(upload_folder, exist_ok=True)
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

    # 2. Análise Comparativa (se aplicável)
    # LÓGICA REVISADA: Busca o relatório correto para comparação.
    # Prioriza o último relatório que foi 'current' em uma análise de tendência.
    last_trend_analysis_obj = trend_model.query.order_by(
        trend_model.timestamp.desc()
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
        previous_report_for_trend = report_model.query.order_by(
            report_model.timestamp.desc()
        ).first()
        if previous_report_for_trend:
            logger.info(
                f"Nenhuma análise de tendência anterior encontrada. Usando o último relatório geral '{previous_report_for_trend.original_filename}' como base."
            )

    trend_report_path_relative = None
    new_trend_analysis = None
    quick_diagnosis_html = None

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
            _kpis, diagnosis_html = gerar_analise_comparativa(
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
                run_folder=run_folder_name,
                base_url=frontend_url,  # CORREÇÃO: Passa a URL pública correta
            )
            quick_diagnosis_html = diagnosis_html
            trend_report_path_relative = os.path.basename(output_trend_path)
            logger.info(f"Relatório de tendência gerado em: {output_trend_path}")

            # Prepara o objeto TrendAnalysis para ser salvo depois
            new_trend_analysis = trend_model(
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

    # 5. Compacta os artefatos gerados para armazenamento persistente
    bundle_bytes = _zip_directory(output_dir)
    report_bundle = ReportBundle(run_folder=run_folder_name, bundle=bundle_bytes)
    # 6. Salvar registro no banco de dados
    new_report = report_model(
        original_filename=filename_recente,
        report_path=summary_html_path,
        json_summary_path=analysis_results["json_path"],
        date_range=date_range_recente,
        bundle=report_bundle,
    )
    db.session.add(new_report)

    # Se uma análise de tendência foi criada, associa o ID do novo relatório e a salva
    if new_trend_analysis:
        db.session.flush()  # Garante que new_report receba um ID
        new_trend_analysis.current_report_id = new_report.id
        db.session.add(new_trend_analysis)

    db.session.commit()

    # 7. Aplicar política de retenção de histórico
    _enforce_report_limit(db, report_model)

    # 8. Retornar resultado
    # Verifica a existência dos arquivos opcionais antes de incluir no retorno
    action_plan_filename = (
        ACTION_PLAN_FILENAME
        if os.path.exists(os.path.join(output_dir, ACTION_PLAN_FILENAME))
        else None
    )

    return {
        "run_folder": run_folder_name,
        "summary_report_filename": os.path.basename(summary_html_path),
        "action_plan_filename": action_plan_filename,
        "trend_report_filename": trend_report_path_relative,
        "json_summary_path": analysis_results["json_path"],
        "quick_diagnosis_html": quick_diagnosis_html,
        "date_range": date_range_recente,
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
        os.makedirs(upload_folder, exist_ok=True)
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

        gerar_analise_comparativa(
            json_anterior=results_anterior["json_path"],
            json_recente=results_recente["json_path"],
            csv_anterior_name=filename_anterior,
            csv_recente_name=filename_recente,
            output_path=output_trend_path,
            date_range_anterior=get_date_range_from_file(filepath_anterior),
            date_range_recente=get_date_range_from_file(filepath_recente),
            is_direct_comparison=True,
            frontend_url=frontend_url,
            run_folder=run_folder_name,
            base_url=frontend_url,  # CORREÇÃO: Passa a URL pública correta
        )
        return {
            "run_folder": run_folder_name,
            "report_filename": "comparativo_periodos.html",
        }

    finally:
        for p in saved_filepaths:
            if os.path.exists(p):
                os.remove(p)
