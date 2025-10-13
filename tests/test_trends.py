"""
Testes para a lógica de Análise de Tendência.
"""

from datetime import datetime, timezone
from src.app import TrendAnalysis


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
