import pytest
from src.app import app as create_flask_app, db


@pytest.fixture
def app():
    """Cria e configura uma nova instância da aplicação para cada teste."""
    # Garante que a aplicação seja criada com a configuração de teste desde o início,
    # usando um banco de dados em memória para total isolamento.
    create_flask_app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "WTF_CSRF_ENABLED": False,  # Desativa CSRF para testes de formulário
            "SECRET_KEY": "test-secret-key",
            # Adiciona placeholders para as pastas, já que o app não as define mais em modo de teste.
            "UPLOAD_FOLDER": "/tmp/pytest-uploads",
            "REPORTS_FOLDER": "/tmp/pytest-reports",
        }
    )

    with create_flask_app.app_context():
        db.create_all()
        yield create_flask_app
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
