import os
import pytest
from datetime import datetime, timedelta, timezone
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

    # NOVO: Garante que o mock da TrendAnalysis retorne None.
    # Isso força o service a usar a lógica de fallback (buscar o último Report),
    # que é o cenário que este teste específico valida.
    mock_dependencies[
        "TrendAnalysis"
    ].query.order_by.return_value.first.return_value = None

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


@patch("src.services.os.path.exists", return_value=True)
@patch("src.services.gerar_relatorio_tendencia")
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
    MockReport = mock_dependencies["Report"]
    MockTrendAnalysis = mock_dependencies["TrendAnalysis"]

    # Simula o retorno da análise de CSV
    mock_analisar_csv.return_value = {
        "summary": MagicMock(),
        "df_atuacao": MagicMock(),
        "num_logs_invalidos": 0,
        "json_path": "fake/path/summary.json",
    }

    # --- 1. PRIMEIRO UPLOAD (ARQUIVO A) ---
    print("--- Testando Upload A ---")
    # Simula DB vazio
    MockReport.query.order_by.return_value.first.return_value = None
    MockTrendAnalysis.query.order_by.return_value.first.return_value = None
    # Mock para o novo objeto Report que será criado
    report_A = MagicMock(
        id=1,
        original_filename="file_A.csv",
        json_summary_path="path/A.json",
        date_range="01/01/2025 a 01/01/2025",
    )
    MockReport.return_value = report_A
    # Mock para a função get_date_range
    with patch(
        "src.services.get_date_range_from_file", return_value="01/01/2025 a 01/01/2025"
    ):
        services.process_upload_and_generate_reports(
            **mock_dependencies,
            upload_folder=str(upload_folder),
            reports_folder=str(reports_folder),
            base_dir=str(tmp_path),
        )

    # Assert A: Nenhuma tendência deve ser gerada
    mock_gerar_tendencia.assert_not_called()
    assert mock_db.session.add.call_count == 1  # Apenas o Report A
    mock_db.session.add.assert_called_with(report_A)
    mock_db.session.commit.assert_called_once()

    # --- 2. SEGUNDO UPLOAD (ARQUIVO B) ---
    print("--- Testando Upload B ---")
    # Resetar mocks de chamada
    mock_gerar_tendencia.reset_mock()
    mock_db.reset_mock()
    # Simula que o Report A é o mais recente, mas ainda não há TrendAnalysis
    MockReport.query.order_by.return_value.first.return_value = report_A
    MockTrendAnalysis.query.order_by.return_value.first.return_value = None
    # Mock para o novo objeto Report B
    report_B = MagicMock(
        id=2,
        original_filename="file_B.csv",
        json_summary_path="path/B.json",
        date_range="02/01/2025 a 02/01/2025",
    )
    MockReport.return_value = report_B
    # Mock para a nova TrendAnalysis
    trend_B_vs_A = MagicMock(current_report=report_B)
    MockTrendAnalysis.return_value = trend_B_vs_A

    with patch(
        "src.services.get_date_range_from_file", return_value="02/01/2025 a 02/01/2025"
    ):
        services.process_upload_and_generate_reports(
            **mock_dependencies,
            upload_folder=str(upload_folder),
            reports_folder=str(reports_folder),
            base_dir=str(tmp_path),
        )

    # Assert B: Tendência B vs A deve ser gerada
    mock_gerar_tendencia.assert_called_once()
    # Verifica se a comparação usou o JSON do relatório A
    # Usamos ANY para o output_path, pois o timestamp no nome da pasta é dinâmico
    from unittest.mock import ANY

    mock_gerar_tendencia.assert_called_with(
        json_anterior=report_A.json_summary_path,
        json_atual=mock_analisar_csv.return_value["json_path"],
        csv_anterior_name=report_A.original_filename,
        csv_atual_name=mock_dependencies["file_atual"].filename,
        output_path=ANY,
        date_range_anterior=report_A.date_range,
        date_range_atual="02/01/2025 a 02/01/2025",
    )
    # Verifica se o Report B e a Trend B vs A foram salvos
    assert mock_db.session.add.call_count == 2
    assert trend_B_vs_A.current_report_id == 2

    # --- 3. TERCEIRO UPLOAD (ARQUIVO C) ---
    print("--- Testando Upload C ---")
    # Resetar mocks de chamada
    mock_gerar_tendencia.reset_mock()
    mock_db.reset_mock()
    # Simula que a última TrendAnalysis é a B vs A. O sistema deve usar `trend_B_vs_A.current_report` (que é o report_B)
    MockTrendAnalysis.query.order_by.return_value.first.return_value = trend_B_vs_A
    # Mock para o novo objeto Report C
    report_C = MagicMock(
        id=3,
        original_filename="file_C.csv",
        json_summary_path="path/C.json",
        date_range="03/01/2025 a 03/01/2025",
    )
    MockReport.return_value = report_C
    # Mock para a nova TrendAnalysis
    trend_C_vs_B = MagicMock()
    MockTrendAnalysis.return_value = trend_C_vs_B

    with patch(
        "src.services.get_date_range_from_file", return_value="03/01/2025 a 03/01/2025"
    ):
        services.process_upload_and_generate_reports(
            **mock_dependencies,
            upload_folder=str(upload_folder),
            reports_folder=str(reports_folder),
            base_dir=str(tmp_path),
        )

    # Assert C: Tendência C vs B deve ser gerada
    mock_gerar_tendencia.assert_called_once()
    # Verifica se a comparação usou o JSON do relatório B
    mock_gerar_tendencia.assert_called_with(
        json_anterior=report_B.json_summary_path,
        json_atual=mock_analisar_csv.return_value["json_path"],
        csv_anterior_name=report_B.original_filename,
        csv_atual_name=mock_dependencies["file_atual"].filename,
        output_path=ANY,
        date_range_anterior=report_B.date_range,
        date_range_atual="03/01/2025 a 03/01/2025",
    )
    assert mock_db.session.add.call_count == 2
    assert trend_C_vs_B.current_report_id == 3


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
