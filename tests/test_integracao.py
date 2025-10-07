import os
import pytest
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src import analisar_alertas

# Define o caminho para os fixtures de teste
FIXTURE_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')

@pytest.mark.parametrize("sample_file", [
    "csv-dummy-1.csv",
    "csv-dummy-2.csv"
])
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
        input_file=str(input_csv),
        output_dir=str(output_dir),
        light_analysis=False
    )

    # Assert: Verifica se o resultado e os arquivos gerados estão corretos
    assert result is not None
    assert "json_path" in result
    assert "summary" in result
    assert "df_atuacao" in result
    
    assert os.path.exists(result["json_path"]), "O arquivo de resumo JSON não foi gerado."
    assert os.path.exists(os.path.join(output_dir, "atuar.csv")), "O CSV de atuação não foi gerado."
    assert os.path.exists(os.path.join(output_dir, "remediados.csv")), "O CSV de remediados não foi gerado."
