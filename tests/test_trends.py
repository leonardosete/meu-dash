import os
from datetime import datetime, timedelta, timezone
from flask import url_for
from unittest.mock import patch
from src.app import app, db, Report, TrendAnalysis


@patch("src.app.os.path.getsize", return_value=101)
@patch("src.app.os.path.exists", return_value=True)
@patch("src.app.services.calculate_kpi_summary")
def test_trend_history_on_index_page(
    mock_calculate_kpi, mock_path_exists, mock_getsize, client
):
    """
    GIVEN um banco de dados com relatórios e uma análise de tendência,
    WHEN a página inicial ('/') é acessada,
    THEN a página deve conter um link (na forma de "orelha") para a análise de
    tendência mais recente, mesmo sem o card dedicado.
    """
    # Limpa o banco para garantir um teste limpo
    trend_run_folder = "run_trend_12345"
    trend_filename = "resumo_tendencia.html"

    with app.app_context():
        # ARRANGE: Mocka o retorno do KPI, pois o template agora depende dele
        # para renderizar o contêiner dos links. O mock deve ser completo.
        mock_calculate_kpi.return_value = {
            "casos_atuacao": 0,
            "alertas_atuacao": 0,
            "casos_instabilidade": 0,
            "alertas_instabilidade": 0,
            "casos_sucesso": 1,
            "total_casos": 1,
            "taxa_sucesso_automacao": "100.0%",
            "taxa_sucesso_valor": 100.0,
            "report_url": "/fake/report/url",
        }

        # Limpa o banco para garantir um teste limpo
        TrendAnalysis.query.delete()
        Report.query.delete()
        db.session.commit()

        # GIVEN: Cria dois relatórios
        report1 = Report(
            timestamp=datetime.now(timezone.utc) - timedelta(days=1),
            original_filename="report1.csv",
            report_path="/fake/path/run1/report1.html",
            json_summary_path="/fake/path/run1/summary.json",
        )
        report2 = Report(
            timestamp=datetime.now(timezone.utc),
            original_filename="report2.csv",
            report_path="/fake/path/run2/report2.html",
            json_summary_path="/fake/path/run2/summary.json",
        )
        db.session.add_all([report1, report2])
        db.session.flush()

        # GIVEN: Cria uma análise de tendência associada aos relatórios
        trend_path = os.path.join(
            app.config["REPORTS_FOLDER"], trend_run_folder, trend_filename
        )
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
        response_data = response.get_data(as_text=True)

        # THEN: Verifica se o link para a análise de tendência está na página.
        expected_url = url_for(
            "serve_report",
            run_folder=trend_run_folder,
            filename=trend_filename,
            _external=False,  # Garante que a URL gerada seja relativa, como na aplicação
        )
        assert f'href="{expected_url}"' in response_data


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
