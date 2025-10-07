import os
import pytest
import sys
from unittest.mock import MagicMock, patch

from src import services


@pytest.fixture
def mock_dependencies():
    """Cria mocks para as dependências externas do serviço."""
    mock_db = MagicMock()
    mock_Report = MagicMock()
    mock_file = MagicMock()
    mock_file.filename = "test.csv"

    return {"db": mock_db, "Report": mock_Report, "file_atual": mock_file}


@patch("src.services.analisar_arquivo_csv")
@patch("src.services.gerador_paginas")
@patch("src.services.context_builder")
@patch("src.services.get_date_range_from_file", return_value="01/01/2025 a 02/01/2025")
def test_process_upload_and_generate_reports(
    mock_get_date,
    mock_context_builder,
    mock_gerador_paginas,
    mock_analisar_csv,
    tmp_path,
    mock_dependencies,
):
    """
    Testa o orquestrador principal na camada de serviço, garantindo que ele
    chama os submódulos corretos na sequência esperada.
    """
    # Arrange
    # Simula um relatório anterior encontrado no banco de dados.
    # Isso é feito configurando o mock do 'Report' que já está na fixture.
    mock_last_report = MagicMock()
    mock_last_report.json_summary_path = "fake/path/to/old_summary.json"
    mock_last_report.date_range = "01/01/2024 a 31/01/2024"

    # Pega o mock do Report da fixture e configura seu comportamento
    mock_Report_from_fixture = mock_dependencies["Report"]
    mock_Report_from_fixture.query.order_by.return_value.first.return_value = (
        mock_last_report
    )

    upload_folder = tmp_path / "uploads"
    reports_folder = tmp_path / "reports"
    upload_folder.mkdir()
    reports_folder.mkdir()

    # Configura o retorno do mock da análise
    mock_analisar_csv.return_value = {
        "summary": MagicMock(),
        "df_atuacao": MagicMock(),
        "num_logs_invalidos": 0,
        "json_path": "fake/path/summary.json",
    }

    # Act
    result = services.process_upload_and_generate_reports(
        **mock_dependencies,
        upload_folder=str(upload_folder),
        reports_folder=str(reports_folder),
        base_dir=str(tmp_path),
    )

    # Assert
    assert (
        mock_analisar_csv.call_count >= 1
    ), "A função de análise de CSV deveria ter sido chamada pelo menos uma vez."
    assert (
        mock_context_builder.build_dashboard_context.called
    ), "O construtor de contexto deveria ter sido chamado."
    assert (
        mock_gerador_paginas.gerar_resumo_executivo.called
    ), "A geração do resumo executivo deveria ter sido chamada."
    assert (
        mock_dependencies["db"].session.add.called
    ), "Um novo relatório deveria ter sido adicionado à sessão do DB."
    assert (
        mock_dependencies["db"].session.commit.called
    ), "A sessão do DB deveria ter sido 'commitada'."
    assert "run_folder" in result
    assert "report_filename" in result