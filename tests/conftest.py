import pytest
from src.app import app as flask_app, db

@pytest.fixture
def app():
    """Cria e configura uma nova instância da aplicação para cada teste."""
    # Configurações de teste
    flask_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",  # Usa um banco de dados em memória
    })

    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Um cliente de teste para a aplicação."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Um runner para executar comandos CLI do Flask."""
    return app.test_cli_runner()
