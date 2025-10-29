import pytest
from src.app import create_app, db


@pytest.fixture
def app():
    """Cria e configura uma nova instância da aplicação para cada teste."""
    # Cria a aplicação usando a factory e passando a configuração de teste.
    # Isso garante que a aplicação é criada desde o início com o ambiente correto.
    flask_app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test-secret-key",
            "UPLOAD_FOLDER": "/tmp/pytest-uploads",
            "REPORTS_FOLDER": "/tmp/pytest-reports",
        }
    )

    with flask_app.app_context():
        db.create_all()
        yield flask_app
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
