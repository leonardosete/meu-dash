import os
import pytest
import sys
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src import services


@pytest.fixture
def mock_dependencies():
    """Cria mocks para as dependências externas do serviço."""
    mock_db = MagicMock()
    mock_Report = MagicMock()
    mock_TrendAnalysis = MagicMock()  # Mock para o novo modelo
    mock_file = MagicMock()
    mock_file.filename = "test.csv"

    return {
        "db": mock_db,
        "Report": mock_Report,
        "TrendAnalysis": mock_TrendAnalysis,  # Adiciona ao dicionário
        "file_atual": mock_file,
    }


@patch("src.services.os.path.exists", return_value=True)
@patch("src.services.gerar_relatorio_tendencia")
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

    mock_new_report = mock_dependencies["Report"].return_value
    mock_new_report.id = 2

    mock_Report_from_fixture = mock_dependencies["Report"]
    mock_Report_from_fixture.query.order_by.return_value.first.return_value = (
        mock_last_report
    )

    upload_folder = tmp_path / "uploads"
    reports_folder = tmp_path / "reports"
    upload_folder.mkdir()
    reports_folder.mkdir()

    # A service chama analisar_arquivo_csv duas vezes (light e full)
    mock_analisar_csv.side_effect = [
        {"json_path": "fake/path/light_summary.json"},
        {
            "summary": MagicMock(),
            "df_atuacao": MagicMock(),
            "num_logs_invalidos": 0,
            "json_path": "fake/path/full_summary.json",
        },
    ]

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
        base_dir=str(tmp_path),
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
    assert result["report_filename"] == os.path.basename(mock_dashboard_path)


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
        report_mock.timestamp = datetime.now() - timedelta(
            days=total_reports_to_create - i
        )
        report_mock.original_filename = f"report_{i}.csv"
        report_mock.report_path = str(report_file_path)
        mock_reports.append(report_mock)

    # 3. Configurar os mocks do banco de dados
    mock_db = mock_dependencies["db"]
    mock_Report = mock_dependencies["Report"]

    # Simular que o DB tem 8 relatórios
    mock_Report.query.count.return_value = total_reports_to_create

    # Simular que a query pelos mais antigos retorna os 3 primeiros
    oldest_reports_to_return = mock_reports[:reports_to_delete_count]
    mock_Report.query.order_by.return_value.limit.return_value.all.return_value = (
        oldest_reports_to_return
    )

    # Act
    services._enforce_report_limit(mock_db, mock_Report)

    # Assert
    # 1. Verifica se a contagem foi feita
    mock_Report.query.count.assert_called_once()

    # 2. Verifica se a query para encontrar os mais antigos foi feita corretamente
    mock_Report.query.order_by.return_value.limit.assert_called_with(
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
