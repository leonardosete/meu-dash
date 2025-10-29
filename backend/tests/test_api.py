"""
Testes de Integração para os endpoints da API.

Estes testes validam os contratos da API (formato JSON, status codes)
e garantem que a refatoração não quebre a funcionalidade principal.
"""

import io
from unittest.mock import patch

from src.models import Report, db


def test_get_dashboard_summary(client):
    """
    Valida o endpoint GET /api/v1/dashboard-summary.

    Verifica se a resposta é 200 OK, o content-type é JSON e se a estrutura
    principal do JSON (o contrato) está correta.
    """
    # ARRANGE: Adiciona um relatório de teste para garantir que a rota não retorne vazio
    with client.application.app_context():
        report = Report(
            original_filename="test.csv",
            report_path="/data/reports/run_test/report.html",
            json_summary_path="/data/reports/run_test/summary.json",
            date_range="01/01/2024 a 31/01/2024",
        )
        db.session.add(report)
        db.session.commit()
    response = client.get("/api/v1/dashboard-summary")
    assert response.status_code == 200
    assert response.content_type == "application/json"

    data = response.get_json()
    assert "kpi_summary" in data
    assert "trend_history" in data
    assert isinstance(data["trend_history"], list)


def test_get_reports(client):
    """
    Valida o endpoint GET /api/v1/reports.

    Verifica se a resposta é 200 OK e se o corpo da resposta é uma lista JSON.
    """
    # ARRANGE: Adiciona um relatório de teste
    with client.application.app_context():
        report = Report(
            original_filename="test.csv",
            report_path="/data/reports/run_test/report.html",
            json_summary_path="/data/reports/run_test/summary.json",
            date_range="01/01/2024 a 31/01/2024",
        )
        db.session.add(report)
        db.session.commit()

    response = client.get("/api/v1/reports")
    assert response.status_code == 200
    assert response.content_type == "application/json"
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["original_filename"] == "test.csv"


def test_upload_file_success(client, monkeypatch):
    """
    Valida o endpoint POST /api/v1/upload em caso de sucesso.

    Usa um mock para a camada de serviço para isolar o teste na camada da API.
    Verifica se a API retorna 200 OK e o JSON de sucesso esperado.
    """
    # ARRANGE: Configura as variáveis de ambiente para autenticação no escopo do teste.
    monkeypatch.setenv("ADMIN_USER", "testadmin")
    monkeypatch.setenv("ADMIN_PASSWORD", "testpass")

    # ARRANGE: Obter um token JWT válido para a requisição.
    with client.application.app_context():
        login_response = client.post(
            "/admin/login",
            json={"username": "testadmin", "password": "testpass"},
        )
        assert login_response.status_code == 200
        jwt_token = login_response.get_json()["access_token"]

    # ARRANGE: Configura o mock do serviço e os dados do arquivo.
    mock_result = {
        "run_folder": "run_20240101_120000",
        "summary_report_filename": "resumo_geral.html",
        "action_plan_filename": "atuar.html",
        "json_summary_path": "/fake/path/summary.json",
    }

    # O patch substitui a função real pela simulação durante este teste
    with patch("src.services.process_upload_and_generate_reports") as mock_service:
        mock_service.return_value = mock_result

        # Cria um arquivo em memória para o upload
        data = {
            "file_recente": (io.BytesIO(b"col1;col2\nval1;val2"), "test_upload.csv")
        }

        # ACT: Envia a requisição com o token de autorização.
        response = client.post(
            "/api/v1/upload",
            headers={"Authorization": f"Bearer {jwt_token}"},
            data=data,
            content_type="multipart/form-data",
        )

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data["success"] is True
        assert "report_urls" in json_data


def test_delete_report_with_valid_token(client, monkeypatch):
    """
    Valida o endpoint DELETE /api/v1/reports/<id> com um token JWT válido.

    Verifica se a API retorna 200 OK com sucesso, e se o relatório
    é de fato removido do banco de dados.
    """
    # ARRANGE: Configura as variáveis de ambiente para autenticação.
    monkeypatch.setenv("ADMIN_USER", "testadmin")
    monkeypatch.setenv("ADMIN_PASSWORD", "testpass")

    # ARRANGE: Cria um token JWT válido
    with client.application.app_context():
        login_response = client.post(
            "/admin/login",
            json={"username": "testadmin", "password": "testpass"},
        )
        assert login_response.status_code == 200
        jwt_token = login_response.get_json()["access_token"]

    # ARRANGE: Cria um relatório para ser excluído no escopo do teste
    with client.application.app_context():
        report_to_delete = Report(
            original_filename="delete_me.csv",
            report_path="/fake/path/to_delete/report.html",
            json_summary_path="/fake/path/to_delete/summary.json",  # Campo obrigatório
        )
        db.session.add(report_to_delete)
        db.session.commit()
        report_id = report_to_delete.id

        # ACT: Chama o endpoint de exclusão com o token.
        # Mockamos tanto o rmtree quanto o isdir para simular a existência do diretório.
        with (
            patch("src.services.shutil.rmtree") as mock_rmtree,
            patch("src.services.os.path.isdir", return_value=True) as mock_isdir,
        ):
            response = client.delete(
                f"/api/v1/reports/{report_id}",
                headers={"Authorization": f"Bearer {jwt_token}"},
            )

            # ASSERT
            assert response.status_code == 200
            assert response.get_json() == {"success": True}
            assert db.session.get(Report, report_id) is None
            mock_isdir.assert_called_once()
            mock_rmtree.assert_called_once()  # Verifica se a exclusão de arquivos foi chamada


def test_delete_report_no_token(client):
    """
    Valida que o endpoint DELETE /api/v1/reports/<id> retorna 401 sem um token.
    """
    # ACT: Chama o endpoint sem o cabeçalho de autorização
    response = client.delete("/api/v1/reports/1")

    # ASSERT
    assert response.status_code == 401
    assert "Token" in response.get_json()["error"]


def test_compare_files_success(client, monkeypatch):
    """
    Valida o endpoint POST /api/v1/compare em caso de sucesso.

    Usa um mock para a camada de serviço para isolar o teste na camada da API.
    """
    # ARRANGE: Configura as variáveis de ambiente para autenticação.
    monkeypatch.setenv("ADMIN_USER", "testadmin")
    monkeypatch.setenv("ADMIN_PASSWORD", "testpass")

    # ARRANGE: Obter um token JWT válido para a requisição.
    with client.application.app_context():
        login_response = client.post(
            "/admin/login",
            json={"username": "testadmin", "password": "testpass"},
        )
        assert login_response.status_code == 200
        jwt_token = login_response.get_json()["access_token"]

    # ARRANGE: Configura o mock do serviço e os dados dos arquivos.
    mock_result = {
        "run_folder": "run_compare_123",
        "report_filename": "comparativo.html",
    }

    with patch("src.services.process_direct_comparison") as mock_service:
        mock_service.return_value = mock_result

        data = {
            "file_antigo": (io.BytesIO(b"file1"), "file1.csv"),
            "file_recente": (io.BytesIO(b"file2"), "file2.csv"),
        }
        # ACT: Envia a requisição com o token de autorização.
        response = client.post(
            "/api/v1/compare",
            headers={"Authorization": f"Bearer {jwt_token}"},
            data=data,
            content_type="multipart/form-data",
        )

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data["success"] is True
        assert "report_url" in json_data