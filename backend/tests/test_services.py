import json
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from src import services


@pytest.fixture
def mock_dependencies():
    """Cria mocks para as dependências externas do serviço."""
    mock_db = MagicMock()
    report_model_mock = MagicMock()
    trend_model_mock = MagicMock()  # Mock para o novo modelo
    mock_file = MagicMock()
    mock_file.filename = "test.csv"

    return {
        "db": mock_db,
        "Report": report_model_mock,
        "TrendAnalysis": trend_model_mock,  # Adiciona ao dicionário
        "file_recente": mock_file,
    }


@patch("src.services.os.path.exists", return_value=True)
@patch("src.services.gerar_analise_comparativa")
@patch("src.services.analisar_arquivo_csv")
@patch("src.services.gerador_paginas")
@patch("src.services.context_builder")
@patch("src.services.get_date_range_from_file", return_value="01/01/2025 a 02/01/2025")
def test_process_upload_and_generate_reports(
    mock_get_date,
    mock_context_builder,
    mock_gerador_paginas,
    mock_analisar_csv,
    mock_gerar_tendencia,
    mock_path_exists,
    tmp_path,
    mock_dependencies,
):
    """
    Testa o orquestrador principal, garantindo que ele salva a análise de tendência
    quando um relatório anterior existe.
    """
    # Arrange
    mock_last_report = MagicMock()
    mock_last_report.id = 1
    mock_last_report.json_summary_path = "fake/path/to/old_summary.json"
    mock_last_report.date_range = "01/01/2024 a 31/01/2024"

    # NOVO: Garante que o mock da TrendAnalysis retorne None.
    # Isso força o service a usar a lógica de fallback (buscar o último Report),
    # que é o cenário que este teste específico valida.
    mock_dependencies[
        "TrendAnalysis"
    ].query.order_by.return_value.first.return_value = None

    mock_new_report = mock_dependencies["Report"].return_value
    mock_new_report.id = 2

    report_model_from_fixture = mock_dependencies["Report"]
    report_model_from_fixture.query.order_by.return_value.first.return_value = (
        mock_last_report
    )

    upload_folder = tmp_path / "uploads"
    reports_folder = tmp_path / "reports"
    upload_folder.mkdir()
    reports_folder.mkdir()

    # A service chama analisar_arquivo_csv uma vez (análise completa)
    mock_analisar_csv.return_value = {
        "summary": MagicMock(),
        "df_atuacao": MagicMock(),
        "num_logs_invalidos": 0,
        "json_path": "fake/path/full_summary.json",
    }

    # CORREÇÃO: Configura o mock para retornar uma tupla válida, evitando o ValueError.
    mock_gerar_tendencia.return_value = (None, "<html></html>")

    # O gerador de páginas principal retorna o caminho do dashboard como uma STRING
    mock_dashboard_path = "fake/path/resumo_geral.html"
    mock_gerador_paginas.gerar_ecossistema_de_relatorios.return_value = (
        mock_dashboard_path
    )

    # Act
    result = services.process_upload_and_generate_reports(
        **mock_dependencies,
        upload_folder=str(upload_folder),
        reports_folder=str(reports_folder),
    )

    # Assert
    mock_db_session = mock_dependencies["db"].session
    NewTrendAnalysisInstance = mock_dependencies["TrendAnalysis"].return_value

    # Verifica se o novo Report e a nova TrendAnalysis foram adicionados
    mock_db_session.add.assert_any_call(mock_new_report)
    mock_db_session.add.assert_any_call(NewTrendAnalysisInstance)

    # Valida que a TrendAnalysis foi instanciada com o ID do relatório anterior
    # O caminho absoluto é dinâmico, então usamos ANY da unittest.mock
    from unittest.mock import ANY

    mock_dependencies["TrendAnalysis"].assert_called_with(
        trend_report_path=ANY,
        previous_report_id=mock_last_report.id,
    )

    # Valida que o ID do novo relatório foi atribuído à análise de tendência
    assert NewTrendAnalysisInstance.current_report_id == mock_new_report.id

    # Valida o commit final
    mock_db_session.commit.assert_called_once()

    # Valida o dicionário de retorno
    assert result["summary_report_filename"] == os.path.basename(mock_dashboard_path)


@patch("src.services.os.path.exists", return_value=True)
@patch("src.services.gerar_analise_comparativa")
@patch("src.services.analisar_arquivo_csv")
@patch("src.services.gerador_paginas")
@patch("src.services.context_builder")
@patch("src.services.get_date_range_from_file", return_value="04/01/2025 a 04/01/2025")
def test_process_upload_skips_trend_for_non_recent_file(
    _mock_get_date,
    mock_context_builder,
    mock_gerador_paginas,
    mock_analisar_csv,
    mock_gerar_tendencia,
    mock_path_exists,
    tmp_path,
    mock_dependencies,
):
    """Valida que uploads não mais recentes retornam apenas o aviso de tendência pulada."""

    upload_folder = tmp_path / "uploads"
    reports_folder = tmp_path / "reports"
    upload_folder.mkdir()
    reports_folder.mkdir()

    mock_db = mock_dependencies["db"]
    report_model = mock_dependencies["Report"]
    trend_model = mock_dependencies["TrendAnalysis"]

    previous_report = MagicMock(
        id=99,
        original_filename="file_prev.csv",
        json_summary_path="fake/path/prev_summary.json",
        date_range="05/01/2025 a 05/01/2025",
    )
    report_model.query.order_by.return_value.first.return_value = previous_report
    trend_model.query.order_by.return_value.first.return_value = None

    mock_analisar_csv.return_value = {
        "summary": MagicMock(),
        "df_atuacao": MagicMock(),
        "num_logs_invalidos": 0,
        "json_path": "fake/path/new_summary.json",
    }

    result = services.process_upload_and_generate_reports(
        **mock_dependencies,
        upload_folder=str(upload_folder),
        reports_folder=str(reports_folder),
    )

    assert result == {
        "warning": "Análise de tendência pulada: o arquivo enviado não é mais recente. Para comparar arquivos específicos, use a aba 'Comparação Direta'."
    }
    mock_gerar_tendencia.assert_not_called()
    mock_context_builder.build_dashboard_context.assert_not_called()
    mock_gerador_paginas.gerar_ecossistema_de_relatorios.assert_not_called()
    mock_db.session.add.assert_not_called()


@patch("src.services.os.path.exists", return_value=True)
@patch("src.services.gerar_analise_comparativa")
@patch("src.services.analisar_arquivo_csv")
@patch("src.services.gerador_paginas")
@patch("src.services.context_builder")
def test_process_upload_for_continuous_trend_analysis(
    mock_context_builder,
    mock_gerador_paginas,
    mock_analisar_csv,
    mock_gerar_tendencia,
    mock_path_exists,
    tmp_path,
    mock_dependencies,
):
    """
    Testa o fluxo de análise de tendência contínua (A -> B -> C).

    - Upload A: Nenhum relatório anterior, sem tendência.
    - Upload B: Compara com A, cria a primeira tendência.
    - Upload C: Compara com B (o 'current' da última tendência), cria a segunda tendência.
    """
    # Arrange - Configuração geral
    upload_folder = tmp_path / "uploads"
    reports_folder = tmp_path / "reports"
    upload_folder.mkdir()
    reports_folder.mkdir()

    mock_db = mock_dependencies["db"]
    report_model = mock_dependencies["Report"]
    trend_model = mock_dependencies["TrendAnalysis"]

    # Simula o retorno da análise de CSV
    mock_analisar_csv.return_value = {
        "summary": MagicMock(),
        "df_atuacao": MagicMock(),
        "num_logs_invalidos": 0,
        "json_path": "fake/path/summary.json",
    }

    # CORREÇÃO: Configura o mock para retornar uma tupla válida.
    mock_gerar_tendencia.return_value = (None, "<html></html>")

    # --- 1. PRIMEIRO UPLOAD (ARQUIVO A) ---
    # Simula DB vazio
    report_model.query.order_by.return_value.first.return_value = None
    trend_model.query.order_by.return_value.first.return_value = None
    # Mock para o novo objeto Report que será criado
    report_a = MagicMock(
        id=1,
        original_filename="file_A.csv",
        json_summary_path="path/A.json",
        date_range="01/01/2025 a 01/01/2025",
    )
    report_model.return_value = report_a
    # Mock para a função get_date_range
    with patch(
        "src.services.get_date_range_from_file", return_value="01/01/2025 a 01/01/2025"
    ):
        services.process_upload_and_generate_reports(
            **mock_dependencies,
            upload_folder=str(upload_folder),
            reports_folder=str(reports_folder),
        )

    # Assert A: Nenhuma tendência deve ser gerada
    mock_gerar_tendencia.assert_not_called()
    assert mock_db.session.add.call_count == 1  # Apenas o Report A
    mock_db.session.add.assert_called_with(report_a)
    mock_db.session.commit.assert_called_once()

    # --- 2. SEGUNDO UPLOAD (ARQUIVO B) ---
    # Resetar mocks de chamada
    mock_gerar_tendencia.reset_mock()
    mock_db.reset_mock()
    mock_db.session.reset_mock()
    # Simula que o Report A é o mais recente, mas ainda não há TrendAnalysis
    report_model.query.order_by.return_value.first.return_value = report_a
    trend_model.query.order_by.return_value.first.return_value = None
    # Mock para o novo objeto Report B
    report_b = MagicMock(
        id=2,
        original_filename="file_B.csv",
        json_summary_path="path/B.json",
        date_range="02/01/2025 a 02/01/2025",
    )
    report_model.return_value = report_b
    # Mock para a nova TrendAnalysis
    trend_b_vs_a = MagicMock(current_report=report_b)
    trend_model.return_value = trend_b_vs_a

    with patch(
        "src.services.get_date_range_from_file", return_value="02/01/2025 a 02/01/2025"
    ):
        services.process_upload_and_generate_reports(
            **mock_dependencies,
            upload_folder=str(upload_folder),
            reports_folder=str(reports_folder),
        )

    # Assert B: Tendência B vs A deve ser gerada
    mock_gerar_tendencia.assert_called_once()
    # Verifica se a comparação usou o JSON do relatório A
    # Usamos ANY para o output_path, pois o timestamp no nome da pasta é dinâmico
    from unittest.mock import ANY

    mock_gerar_tendencia.assert_called_with(
        json_anterior=report_a.json_summary_path,
        json_recente=mock_analisar_csv.return_value["json_path"],
        csv_anterior_name=report_a.original_filename,
        csv_recente_name=mock_dependencies["file_recente"].filename,
        output_path=ANY,
        date_range_anterior=report_a.date_range,
        date_range_recente="02/01/2025 a 02/01/2025",
        frontend_url=os.getenv("FRONTEND_BASE_URL", "/"),
        run_folder=ANY,
        base_url=ANY,
    )
    # Verifica se o Report B e a Trend B vs A foram salvos
    assert mock_db.session.add.call_count == 2
    assert trend_b_vs_a.current_report_id == 2

    # --- 3. TERCEIRO UPLOAD (ARQUIVO C) ---
    # Resetar mocks de chamada
    mock_gerar_tendencia.reset_mock()
    mock_db.reset_mock()
    mock_db.session.reset_mock()
    # Simula que a última TrendAnalysis é a B vs A. O sistema deve usar `trend_B_vs_A.current_report` (que é o report_B)
    trend_model.query.order_by.return_value.first.return_value = trend_b_vs_a
    # Mock para o novo objeto Report C
    report_c = MagicMock(
        id=3,
        original_filename="file_C.csv",
        json_summary_path="path/C.json",
        date_range="03/01/2025 a 03/01/2025",
    )
    report_model.return_value = report_c
    # Mock para a nova TrendAnalysis
    trend_c_vs_b = MagicMock()
    trend_model.return_value = trend_c_vs_b

    with patch(
        "src.services.get_date_range_from_file", return_value="03/01/2025 a 03/01/2025"
    ):
        services.process_upload_and_generate_reports(
            **mock_dependencies,
            upload_folder=str(upload_folder),
            reports_folder=str(reports_folder),
        )

    # Assert C: Tendência C vs B deve ser gerada
    mock_gerar_tendencia.assert_called_once()
    # Verifica se a comparação usou o JSON do relatório B
    mock_gerar_tendencia.assert_called_with(
        json_anterior=report_b.json_summary_path,
        json_recente=mock_analisar_csv.return_value["json_path"],
        csv_anterior_name=report_b.original_filename,
        csv_recente_name=mock_dependencies["file_recente"].filename,
        output_path=ANY,
        date_range_anterior=report_b.date_range,
        date_range_recente="03/01/2025 a 03/01/2025",
        frontend_url=os.getenv("FRONTEND_BASE_URL", "/"),
        run_folder=ANY,
        base_url=ANY,
    )
    assert mock_db.session.add.call_count == 2
    assert trend_c_vs_b.current_report_id == 3


@patch("src.services.shutil.rmtree")
def test_enforce_report_limit_deletes_oldest(
    mock_rmtree, mock_dependencies, tmp_path, monkeypatch
):
    """
    Testa se a política de retenção de histórico funciona corretamente,
    excluindo os relatórios mais antigos quando o limite é excedido.
    """
    # Arrange
    # 1. Configurar um limite de histórico baixo para o teste
    TEST_LIMIT = 5
    monkeypatch.setattr(services, "MAX_REPORTS_HISTORY", TEST_LIMIT)

    # 2. Criar mais relatórios mock do que o limite
    total_reports_to_create = TEST_LIMIT + 3  # 8 relatórios
    reports_to_delete_count = total_reports_to_create - TEST_LIMIT  # 3 relatórios

    mock_reports = []
    for i in range(total_reports_to_create):
        # Criar diretórios e mocks de relatório com timestamps crescentes
        run_folder = tmp_path / f"run_{i}"
        run_folder.mkdir()
        report_file_path = run_folder / "resumo_geral.html"
        report_file_path.touch()

        report_mock = MagicMock()
        report_mock.timestamp = datetime.now(timezone.utc) - timedelta(
            days=total_reports_to_create - i
        )
        report_mock.original_filename = f"report_{i}.csv"
        report_mock.report_path = str(report_file_path)
        mock_reports.append(report_mock)

    # 3. Configurar os mocks do banco de dados
    mock_db = mock_dependencies["db"]
    report_model_mock = mock_dependencies["Report"]

    # Simular que o DB tem 8 relatórios
    report_model_mock.query.count.return_value = total_reports_to_create

    # Simular que a query pelos mais antigos retorna os 3 primeiros
    oldest_reports_to_return = mock_reports[:reports_to_delete_count]
    report_model_mock.query.order_by.return_value.limit.return_value.all.return_value = oldest_reports_to_return

    # Act
    services._enforce_report_limit(mock_db, report_model_mock)

    # Assert
    # 1. Verifica se a contagem foi feita
    report_model_mock.query.count.assert_called_once()

    # 2. Verifica se a query para encontrar os mais antigos foi feita corretamente
    report_model_mock.query.order_by.return_value.limit.assert_called_with(
        reports_to_delete_count
    )

    # 3. Verifica se a exclusão no DB foi chamada para cada relatório antigo
    assert mock_db.session.delete.call_count == reports_to_delete_count
    mock_db.session.delete.assert_any_call(oldest_reports_to_return[0])
    mock_db.session.delete.assert_any_call(oldest_reports_to_return[2])

    # 4. Verifica se a exclusão dos diretórios foi chamada para cada relatório antigo
    assert mock_rmtree.call_count == reports_to_delete_count
    mock_rmtree.assert_any_call(
        os.path.dirname(oldest_reports_to_return[0].report_path)
    )
    mock_rmtree.assert_any_call(
        os.path.dirname(oldest_reports_to_return[2].report_path)
    )

    # 5. Verifica se o commit foi feito no final
    mock_db.session.commit.assert_called_once()


def test_calculate_kpi_summary_success(tmp_path):
    """
    GIVEN um arquivo JSON de resumo válido,
    WHEN a função calculate_kpi_summary é chamada,
    THEN ela deve retornar um dicionário com os KPIs calculados corretamente.
    """
    # Arrange
    # Importa as constantes reais para garantir que o teste use os mesmos valores da aplicação
    from src.constants import (
        ACAO_FALHA_PERSISTENTE,
        ACAO_INSTABILIDADE_CRONICA,
        ACAO_SEMPRE_OK,
    )

    # Simula os diferentes tipos de Casos que a função espera
    summary_data = [
        # Usa as constantes reais para garantir a consistência do teste
        {"acao_sugerida": ACAO_FALHA_PERSISTENTE, "alert_count": 10},
        {"acao_sugerida": ACAO_INSTABILIDADE_CRONICA, "alert_count": 5},
        {"acao_sugerida": ACAO_SEMPRE_OK, "alert_count": 2},
    ]
    json_path = tmp_path / "summary.json"
    with open(json_path, "w") as f:
        json.dump(summary_data, f)

    # Act
    result = services.calculate_kpi_summary(str(json_path))

    # Assert
    assert result is not None
    assert result["total_casos"] == 3
    assert result["casos_atuacao"] == 1
    assert result["casos_instabilidade"] == 1
    # CORREÇÃO: O teste estava validando uma lógica antiga. A nova lógica conta apenas os sucessos plenos.
    # Com os dados do teste, há apenas 1 caso de sucesso pleno (ACAO_SEMPRE_OK).
    assert result["casos_sucesso"] == 1
    assert result["alertas_atuacao"] == 10
    assert result["alertas_instabilidade"] == 5
    # CORREÇÃO: O teste estava validando uma lógica antiga. A nova lógica conta apenas os alertas de sucessos plenos.
    # Com os dados do teste, há apenas 1 caso de sucesso pleno (ACAO_SEMPRE_OK) com 2 alertas.
    assert result["alertas_sucesso"] == 2
    # CORREÇÃO: O teste estava validando uma lógica antiga. A nova lógica calcula a taxa de sucesso
    # com base nos sucessos plenos (1) sobre o total de casos (3).
    assert result["taxa_sucesso_automacao"] == "33.3%"


@pytest.mark.parametrize(
    "file_content, file_exists",
    [
        ("[]", True),  # Arquivo JSON vazio
        ('{"key": "value"}', False),  # Arquivo não existe
        ("{malformed", True),  # JSON inválido
    ],
)
def test_calculate_kpi_summary_failures(tmp_path, file_content, file_exists):
    """Testa se a função retorna None em cenários de falha."""
    json_path = tmp_path / "summary.json"
    if file_exists:
        json_path.write_text(file_content)

    assert services.calculate_kpi_summary(str(json_path)) is None


@patch("src.services.shutil.rmtree")
@patch("src.services.os.path.isdir", return_value=True)
def test_delete_report_and_artifacts_success(
    mock_isdir, mock_rmtree, mock_dependencies
):
    """
    GIVEN um report_id válido,
    WHEN delete_report_and_artifacts é chamado,
    THEN o diretório do relatório e o registro no DB devem ser excluídos.
    """
    # Arrange
    mock_db = mock_dependencies["db"]
    report_model = mock_dependencies["Report"]

    mock_report_instance = MagicMock()
    mock_report_instance.report_path = "/fake/dir/report.html"
    mock_db.session.get.return_value = mock_report_instance

    # Act
    result = services.delete_report_and_artifacts(1, mock_db, report_model)

    # Assert
    assert result is True
    mock_db.session.get.assert_called_once_with(report_model, 1)
    mock_isdir.assert_called_once_with("/fake/dir")
    mock_rmtree.assert_called_once_with("/fake/dir")
    mock_db.session.delete.assert_called_once_with(mock_report_instance)
    mock_db.session.commit.assert_called_once()
    mock_db.session.rollback.assert_not_called()


def test_delete_report_and_artifacts_not_found(mock_dependencies):
    """Testa se a função retorna False se o relatório não for encontrado."""
    mock_db = mock_dependencies["db"]
    report_model = mock_dependencies["Report"]
    mock_db.session.get.return_value = None

    result = services.delete_report_and_artifacts(999, mock_db, report_model)

    assert result is False
    mock_db.session.delete.assert_not_called()
    mock_db.session.commit.assert_not_called()


@patch("src.services.shutil.rmtree", side_effect=Exception("Permission denied"))
@patch("src.services.os.path.isdir", return_value=True)
def test_delete_report_and_artifacts_exception(
    mock_isdir, mock_rmtree, mock_dependencies
):
    """Testa se a função faz rollback em caso de exceção."""
    mock_db = mock_dependencies["db"]
    report_model = mock_dependencies["Report"]
    mock_report_instance = MagicMock()
    mock_db.session.get.return_value = mock_report_instance

    result = services.delete_report_and_artifacts(1, mock_db, report_model)

    assert result is False
    mock_db.session.delete.assert_not_called()
    mock_db.session.commit.assert_not_called()
    mock_db.session.rollback.assert_called_once()
