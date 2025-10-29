import pytest
from src.app import create_app, db


@pytest.fixture
def app():
    """Cria e configura uma nova instância da aplicação para cada teste."""
    # Cria a aplicação usando a factory com a configuração de teste.
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test-secret-key",
            "UPLOAD_FOLDER": "/tmp/pytest-uploads",
            "REPORTS_FOLDER": "/tmp/pytest-reports",
        }
    )

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
