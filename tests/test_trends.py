import os
from datetime import datetime, timedelta, timezone
from src.app import app, db, Report, TrendAnalysis


def test_trend_history_on_index_page(client):
    """
    GIVEN um banco de dados com relatórios e uma análise de tendência,
    WHEN a página inicial ('/') é acessada,
    THEN a página deve exibir um link para a análise de tendência mais recente.
    """
    with app.app_context():
        # Limpa o banco para garantir um teste limpo
        db.session.query(TrendAnalysis).delete()
        db.session.query(Report).delete()
        db.session.commit()

        # GIVEN: Cria dois relatórios
        report1 = Report(
            timestamp=datetime.now(timezone.utc) - timedelta(days=1),
            original_filename="report1.csv",
            report_path="/fake/path/run1/report1.html",
            json_summary_path="/fake/path/run1/summary.json",
            date_range="01/01/2025 a 07/01/2025",
        )
        report2 = Report(
            timestamp=datetime.now(timezone.utc),
            original_filename="report2.csv",
            report_path="/fake/path/run2/report2.html",
            json_summary_path="/fake/path/run2/summary.json",
            date_range="08/01/2025 a 14/01/2025",
        )
        db.session.add_all([report1, report2])
        db.session.flush()  # Garante que report1 e report2 tenham IDs

        # GIVEN: Cria uma análise de tendência associada aos relatórios
        trend_run_folder = "run_trend_12345"
        trend_filename = "resumo_tendencia.html"
        trend_path = os.path.join(
            app.config["REPORTS_FOLDER"], trend_run_folder, trend_filename
        )

        # Cria os diretórios e o arquivo para que o os.path.basename funcione
        os.makedirs(os.path.dirname(trend_path), exist_ok=True)
        with open(trend_path, "w") as f:
            f.write("<html>Fake Trend Report</html>")

        trend_analysis = TrendAnalysis(
            previous_report_id=report1.id,
            current_report_id=report2.id,
            trend_report_path=trend_path,
        )
        db.session.add(trend_analysis)
        db.session.commit()

    # WHEN: Acessa a página inicial
    response = client.get("/")
    assert response.status_code == 200

    # THEN: Verifica se o link para a análise de tendência está na página
    response_data = response.get_data(as_text=True)
    assert "Ver Última Análise de Tendência" in response_data
    assert trend_run_folder in response_data
    assert trend_filename in response_data


def test_trend_analysis_model_creation():
    """
    GIVEN dados para uma análise de tendência,
    WHEN um objeto TrendAnalysis é criado,
    THEN os atributos devem ser definidos corretamente.
    """
    # GIVEN
    now = datetime.now(timezone.utc)
    trend_path = "/fake/path/trend.html"

    # WHEN
    trend_analysis = TrendAnalysis(
        timestamp=now,
        previous_report_id=1,
        current_report_id=2,
        trend_report_path=trend_path,
    )

    # THEN
    assert trend_analysis.timestamp == now
    assert trend_analysis.previous_report_id == 1
    assert trend_analysis.current_report_id == 2
    assert trend_analysis.trend_report_path == trend_path
