import pytest
import os
from src.app import create_app, db


@pytest.fixture
def app(tmp_path):
    """Cria e configura uma nova instância da aplicação para cada teste."""
    # Usa a fixture 'tmp_path' do pytest para criar diretórios temporários.
    upload_folder = tmp_path / "uploads"
    reports_folder = tmp_path / "reports"
    upload_folder.mkdir()
    reports_folder.mkdir()

    # CORREÇÃO: Adapta os testes para usar PostgreSQL se as variáveis de ambiente estiverem definidas (no CI),
    # ou usa SQLite como fallback para testes locais simples.
    if "TEST_DB_HOST" in os.environ:
        db_uri = "postgresql://{user}:{password}@{host}:{port}/{db}".format(
            user=os.getenv("TEST_DB_USER"),
            password=os.getenv("TEST_DB_PASSWORD"),
            host=os.getenv("TEST_DB_HOST"),
            port=os.getenv("TEST_DB_PORT"),
            db=os.getenv("TEST_DB_NAME"),
        )
    else:
        db_uri = "sqlite:///:memory:"

    test_config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": db_uri,
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-secret-key",
        "UPLOAD_FOLDER": str(upload_folder),
        "REPORTS_FOLDER": str(reports_folder),
    }

    # Cria a aplicação usando a factory com a configuração de teste.
    app = create_app(test_config)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Um cliente de teste para a aplicação, derivado da fixture 'app'."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Um runner para executar comandos CLI do Flask, derivado da fixture 'app'."""
    return app.test_cli_runner()
