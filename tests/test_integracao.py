import os
from io import BytesIO
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src import analisar_alertas, services, app as flask_app

# Define o caminho para os fixtures de teste
FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def client():
    """Configura o cliente de teste do Flask."""
    flask_app.app.config["TESTING"] = True
    with flask_app.app.test_client() as client:
        yield client


@pytest.mark.parametrize("sample_file", ["csv-dummy-1.csv", "csv-dummy-2.csv"])
def test_criar_relatorio_completo_gera_arquivos(tmp_path, sample_file):
    """
    Teste de integração que executa a análise completa e verifica se os
    artefatos de DADOS (CSV, JSON) são gerados corretamente.
    Este teste NÃO valida a geração de HTML, que agora é responsabilidade
    da camada de apresentação (app.py).
    """
    # Arrange: Prepara os caminhos de entrada e saída
    input_csv = os.path.join(FIXTURE_DIR, sample_file)
    output_dir = tmp_path / "report_output"
    output_dir.mkdir()

    # Act: Executa a função de análise principal
    result = analisar_alertas.analisar_arquivo_csv(
        input_file=str(input_csv), output_dir=str(output_dir), light_analysis=False
    )

    # Assert: Verifica se o resultado e os arquivos gerados estão corretos
    assert result is not None
    assert "json_path" in result
    assert "summary" in result
    assert "df_atuacao" in result

    assert os.path.exists(
        result["json_path"]
    ), "O arquivo de resumo JSON não foi gerado."
    assert os.path.exists(
        os.path.join(output_dir, "atuar.csv")
    ), "O CSV de atuação não foi gerado."
    assert os.path.exists(
        os.path.join(output_dir, "remediados.csv")
    ), "O CSV de remediados não foi gerado."


@pytest.mark.parametrize("file_order", ["normal", "inverted"])
def test_comparacao_direta_gera_relatorio_tendencia(tmp_path, file_order):
    """
    Testa o fluxo de comparação direta, garantindo que o relatório de tendência
    seja o artefato principal gerado, independentemente da ordem dos arquivos.
    """
    # Arrange: Prepara os caminhos de entrada e o serviço
    input_csv_anterior = os.path.join(FIXTURE_DIR, "csv-dummy-1.csv")
    input_csv_atual = os.path.join(FIXTURE_DIR, "csv-dummy-2.csv")

    # Simula os objetos de arquivo que o Flask forneceria
    class MockFile:
        def __init__(self, filepath):
            self.filepath = filepath
            self.filename = os.path.basename(filepath)

        def save(self, dest):
            import shutil

            shutil.copy(self.filepath, dest)

    # Parametriza a ordem dos arquivos para testar a lógica de ordenação
    if file_order == "normal":
        files = [MockFile(input_csv_anterior), MockFile(input_csv_atual)]
    else:  # inverted
        files = [MockFile(input_csv_atual), MockFile(input_csv_anterior)]

    # Act: Executa o serviço de comparação direta
    result = services.process_direct_comparison(
        files, upload_folder=str(tmp_path), reports_folder=str(tmp_path)
    )

    # Assert: Verifica se o resultado aponta para o relatório de tendência
    assert result is not None
    assert result["report_filename"] == "resumo_tendencia.html"
    assert os.path.exists(
        os.path.join(tmp_path, result["run_folder"], result["report_filename"])
    ), "O relatório de tendência da comparação direta não foi gerado."


def test_path_traversal_is_blocked(client):
    """
    Valida a correção de segurança, garantindo que tentativas de Path Traversal
    sejam bloqueadas com um erro 404.
    """
    # Tenta acessar um arquivo fora do diretório de relatórios permitido
    # (ex: o requirements.txt na raiz do projeto)
    response = client.get("/reports/some_run/../../requirements.txt")

    # Assert: Verifica se a resposta é 404 Not Found, e não 200 OK.
    assert (
        response.status_code == 404
    ), "A vulnerabilidade de Path Traversal ainda existe!"


@patch("src.app.services")
def test_upload_route_success(mock_service, client):
    """
    Testa a rota /upload com sucesso, garantindo que ela chama o serviço
    e redireciona corretamente.
    """
    # Arrange
    # Configura o retorno da função mockada dentro do módulo de serviço
    mock_service.process_upload_and_generate_reports.return_value = {
        "run_folder": "run_test_123",
        "report_filename": "resumo_geral.html",
    }

    # Cria um arquivo CSV em memória para o upload
    data = {
        # The key 'file_atual' must match the 'name' attribute of the file input in the HTML form.
        "file_atual": (BytesIO(b"header1;header2\nvalue1;value2"), "test.csv")
    }

    # Act
    # Envia uma requisição POST para a rota /upload, simulando o envio de um formulário
    response = client.post("/upload", data=data, content_type="multipart/form-data")

    # Assert
    # 1. Verifica se o serviço foi chamado com o arquivo correto
    mock_service.process_upload_and_generate_reports.assert_called_once()

    # 2. Verifica se a resposta é um redirecionamento (302 Found)
    assert response.status_code == 302, "A rota não redirecionou após o upload."

    # 3. Verifica se o redirecionamento aponta para a URL correta do relatório
    assert "/reports/run_test_123/resumo_geral.html" in response.location


@patch("src.app.services.process_direct_comparison")
def test_compare_route_success(mock_service, client):
    """
    Testa a rota /compare com sucesso, garantindo que ela chama o serviço
    e redireciona corretamente.
    """
    # Arrange
    # Configura o retorno do serviço de comparação mockado
    mock_service.return_value = {
        "run_folder": "run_compare_456",
        "report_filename": "resumo_tendencia.html",
    }

    # Cria dois arquivos CSV em memória para o upload
    data = {
        "files": [
            (BytesIO(b"header\nval1"), "file1.csv"),
            (BytesIO(b"header\nval2"), "file2.csv"),
        ]
    }

    # Act
    response = client.post("/compare", data=data, content_type="multipart/form-data")

    # Assert
    # 1. Verifica se o serviço de comparação foi chamado
    mock_service.assert_called_once()

    # 2. Verifica se a resposta é um redirecionamento
    assert response.status_code == 302, "A rota /compare não redirecionou."

    # 3. Verifica se o redirecionamento aponta para a URL correta
    assert "/reports/run_compare_456/resumo_tendencia.html" in response.location
