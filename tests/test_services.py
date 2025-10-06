import os
import pytest
from src import analisar_alertas as services

# Define o caminho para os fixtures de teste
FIXTURE_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')

@pytest.mark.parametrize("sample_file", [
    "csv-dummy-1.csv",
    "csv-dummy-2.csv"
])
def test_criar_relatorio_completo_gera_arquivos(tmp_path, sample_file):
    """
    Testa o fluxo de criação de relatório completo, garantindo que os principais
    artefatos sejam gerados no diretório de saída.
    """
    # Arrange: Prepara os caminhos de entrada e saída
    input_csv = os.path.join(FIXTURE_DIR, sample_file)
    output_dir = tmp_path / "report_output"
    output_dir.mkdir()

    # Act: Executa a função de serviço principal
    result = services.analisar_arquivo_csv(
        input_file=str(input_csv),
        output_dir=str(output_dir)
    )

    # Assert: Verifica se o resultado e os arquivos gerados estão corretos
    assert result is not None
    assert "html_path" in result
    assert "json_path" in result

    # Verifica se os caminhos retornados existem
    assert os.path.exists(result["html_path"]), "O relatório HTML principal não foi gerado."
    assert os.path.exists(result["json_path"]), "O arquivo de resumo JSON não foi gerado."

    # Verifica se o nome do arquivo HTML está correto
    assert os.path.basename(result["html_path"]) == "resumo_geral.html"

    # Verifica a existência de outros artefatos importantes
    assert os.path.exists(os.path.join(output_dir, "atuar.csv")), "O CSV de atuação não foi gerado."
    assert os.path.exists(os.path.join(output_dir, "remediados.csv")), "O CSV de remediados não foi gerado."
    assert os.path.isdir(os.path.join(output_dir, "planos_de_acao")), "O diretório de planos de ação não foi criado."
    assert os.path.isdir(os.path.join(output_dir, "detalhes")), "O diretório de detalhes não foi criado."
