"""Testes direcionados para os cenários de `_determine_verdict`."""

import pytest

from src.analise_tendencia import _determine_verdict


BASE_KPIS = {
    "total_p1": 5,
    "total_p2": 5,
    "resolved": 0,
    "new": 0,
    "persistent": 0,
    "alerts_total_p1": 0,
    "alerts_total_p2": 0,
    "alerts_resolved": 0,
    "alerts_new": 0,
    "alerts_persistent": 0,
    "alerts_persistent_p1": 0,
    "improvement_rate": 0,
    "regression_rate": 0,
}


def build_kpis(**overrides):
    """Garante que todos os cenários compartilhem as mesmas chaves básicas."""
    kpis = BASE_KPIS.copy()
    kpis.update(overrides)
    return kpis


@pytest.mark.parametrize(
    ("overrides", "expected_snippet", "expected_class", "expected_detail"),
    [
        (
            {"total_p1": 0, "total_p2": 0},
            "Excelência Operacional Mantida",
            "highlight-success",
            None,
        ),
        (
            {"total_p1": 0, "total_p2": 4, "new": 4},
            "Primeira Regressão",
            "highlight-warning",
            None,
        ),
        (
            {"total_p1": 3, "total_p2": 0, "resolved": 3, "alerts_resolved": 12},
            "Excelência Operacional Atingida",
            "highlight-success",
            None,
        ),
        (
            {
                "total_p1": 3,
                "total_p2": 5,
                "resolved": 1,
                "new": 3,
                "regression_rate": 60,
            },
            "Regressão",
            "highlight-danger",
            None,
        ),
        (
            {
                "total_p1": 8,
                "total_p2": 8,
                "resolved": 4,
                "new": 4,
                "alerts_resolved": 10,
                "improvement_rate": 100,
            },
            "Alta Eficácia | Baixa Estabilidade",
            "highlight-warning",
            "<strong>Todos os Casos</strong> do período anterior foram resolvidos.",
        ),
        (
            {
                "total_p1": 8,
                "total_p2": 8,
                "resolved": 4,
                "new": 4,
                "alerts_resolved": 8,
                "improvement_rate": 80,
            },
            "Alta Eficácia | Baixa Estabilidade",
            "highlight-warning",
            "Alta eficácia na resolução de Casos do período anterior.",
        ),
        (
            {
                "total_p1": 9,
                "total_p2": 5,
                "resolved": 3,
                "new": 1,
                "alerts_resolved": 9,
            },
            "Evolução Positiva",
            "highlight-success",
            None,
        ),
        (
            {"total_p1": 5, "total_p2": 5, "resolved": 0, "new": 0},
            "Estagnação por Inércia",
            "highlight-warning",
            None,
        ),
        (
            {
                "total_p1": 6,
                "total_p2": 6,
                "resolved": 2,
                "new": 1,
                "improvement_rate": 33.3,
            },
            "Estabilidade Neutra",
            "highlight-info",
            None,
        ),
    ],
)
def test_determine_verdict_paths(
    overrides, expected_snippet, expected_class, expected_detail
):
    verdict, css_class = _determine_verdict(build_kpis(**overrides))

    assert expected_snippet in verdict
    assert css_class == expected_class
    if expected_detail:
        assert expected_detail in verdict
