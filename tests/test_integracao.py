import os
import pytest
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src import analisar_alertas, services

# Define o caminho para os fixtures de teste
FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


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
