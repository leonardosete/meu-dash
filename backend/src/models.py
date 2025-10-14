"""
Módulo de Modelos de Dados (SQLAlchemy).

Este arquivo centraliza a definição de todos os modelos de banco de dados
da aplicação, seguindo as melhores práticas para evitar importações circulares
e manter a organização do código.
"""

from datetime import datetime, timezone
from . import db


class Report(db.Model):
    """Modelo para armazenar metadados de cada relatório gerado."""

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    original_filename = db.Column(db.String(255), nullable=False)
    report_path = db.Column(db.String(512), nullable=False, unique=True)
    json_summary_path = db.Column(db.String(512), nullable=False, unique=True)
    date_range = db.Column(db.String(100), nullable=True)

    # Relacionamento em cascata: ao excluir um Report, as TrendAnalysis associadas são excluídas.
    trend_analyses_as_previous = db.relationship(
        "TrendAnalysis",
        foreign_keys="TrendAnalysis.previous_report_id",
        backref="previous_report",
        lazy=True,
        cascade="all, delete-orphan",
    )
    trend_analysis_as_current = db.relationship(
        "TrendAnalysis",
        foreign_keys="TrendAnalysis.current_report_id",
        backref="current_report",
        lazy=True,
        cascade="all, delete-orphan",
    )


class TrendAnalysis(db.Model):
    """Modelo para armazenar metadados de cada análise de tendência."""

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    previous_report_id = db.Column(
        db.Integer, db.ForeignKey("report.id"), nullable=False
    )
    current_report_id = db.Column(
        db.Integer, db.ForeignKey("report.id"), nullable=False, unique=True
    )
    trend_report_path = db.Column(db.String(512), nullable=False, unique=True)
