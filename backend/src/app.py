import os
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flasgger import Swagger
from flask import (
    Flask,
    abort,
    jsonify,
    request,
    send_from_directory,
    url_for,
)
from flask_cors import CORS
from flask_migrate import Migrate
from werkzeug.middleware.proxy_fix import ProxyFix

from . import db


def create_app(test_config=None):
    """
    Application Factory: Cria e configura a instância da aplicação Flask.
    """
    from . import models, services

    # SIMPLIFICAÇÃO: O argumento 'template_folder' foi removido, pois os templates
    # são carregados diretamente pelos módulos, não pelo motor de renderização do Flask.
    app = Flask(__name__)

    # Adiciona o middleware para corrigir o schema (http/https) atrás de um proxy.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # --- CONFIGURAÇÃO CENTRALIZADA ---
    app.config.from_mapping(
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-secret-key-that-should-be-changed"),
    )

    if test_config is None:
        # Configuração de produção/desenvolvimento
        app.config.from_mapping(
            UPLOAD_FOLDER=os.path.join("/app/data", "uploads"),
            REPORTS_FOLDER=os.path.join("/app/data", "reports"),
            # --- INÍCIO DA MIGRAÇÃO POSTGRESQL ---
            # A URI de conexão agora é construída dinamicamente a partir de variáveis de ambiente
            # que serão fornecidas pelo Kubernetes (via Secrets e ConfigMaps).
            SQLALCHEMY_DATABASE_URI="postgresql://{user}:{password}@{host}:{port}/{db}".format(
                user=os.getenv("POSTGRES_USER"),
                password=os.getenv("POSTGRES_PASSWORD"),
                host=os.getenv("POSTGRES_HOST"),
                port=os.getenv("POSTGRES_PORT", 5432),
                db=os.getenv("POSTGRES_DB"),
            ),
            # --- FIM DA MIGRAÇÃO POSTGRESQL ---
        )
    else:
        # Carrega a configuração de teste
        app.config.from_mapping(test_config)

    # Garante que as pastas existam APÓS a configuração ser carregada
    if not app.config.get("TESTING"):
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        os.makedirs(app.config["REPORTS_FOLDER"], exist_ok=True)

    MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "migrations")
    db.init_app(app)
    Migrate(app, db, directory=MIGRATIONS_DIR)

    # --- CONFIGURAÇÃO DO SWAGGER ---
    swagger_config = {
        "swagger": "2.0",
        "info": {
            "title": "SmartRemedy API",
            "description": "Priorização Inteligente de Casos com Foco em Remediação",
            "version": "1.0.0",
        },
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": 'Token de autorização JWT. Exemplo: "Bearer {token}"',
            }
        },
        "definitions": {
            "Error": {
                "type": "object",
                "properties": {
                    "error": {
                        "type": "string",
                        "description": "Mensagem de erro descritiva.",
                    }
                },
            }
        },
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec_1",
                # Garante que a especificação da API seja servida sob o mesmo prefixo da UI do Swagger,
                # evitando problemas de roteamento com o Ingress.
                "route": "/apidocs/apispec_1.json",
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        # Define um caminho URL dedicado para os assets estáticos do Flasgger (JS, CSS).
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/apidocs/",
    }

    Swagger(app, config=swagger_config)

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": [
                    "http://localhost:5173",
                    "http://127.0.0.1:5173",
                    "http://localhost:5174",
                    "http://127.0.0.1:5174",
                ]
            },
            r"/admin/*": {
                "origins": [
                    "http://localhost:5173",
                    "http://127.0.0.1:5173",
                    "http://localhost:5174",
                    "http://127.0.0.1:5174",
                ]
            },
        },
        supports_credentials=True,
    )

    # --- DECORADOR DE AUTENTICAÇÃO ---
    def token_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            if "Authorization" in request.headers:
                auth_header = request.headers["Authorization"]
                parts = auth_header.split()
                if len(parts) == 2 and parts[0].lower() == "bearer":
                    token = parts[1]
                elif len(parts) == 1:
                    token = parts[0]

            if not token:
                return jsonify({"error": "Token de autenticação ausente."}), 401
            try:
                jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Token expirado."}), 401
            except jwt.InvalidTokenError:
                return jsonify({"error": "Token inválido."}), 401
            return f(*args, **kwargs)

        return decorated

    # --- ROTAS DA APLICAÇÃO ---

    @app.route("/health")
    def health_check():
        """
        Verifica a saúde da aplicação.
        ---
        tags:
          - Health
        responses:
          200:
            description: A aplicação está funcionando.
        """
        return jsonify({"status": "ok"}), 200

    @app.route("/api/v1/dashboard-summary")
    def get_dashboard_summary():
        """
        Busca o resumo de dados para o dashboard principal.
        ---
        tags:
          - Dashboard
        responses:
          200:
            description: Resumo dos dados do dashboard retornado com sucesso.
        """
        summary_data = services.get_dashboard_summary_data(
            db=db, Report=models.Report, TrendAnalysis=models.TrendAnalysis
        )
        latest_files = summary_data.get("latest_report_files")
        if latest_files:
            urls = {
                "summary": url_for(
                    "serve_report",
                    run_folder=latest_files["run_folder"],
                    filename=latest_files["summary"],
                    _external=True,
                )
            }
            if latest_files.get("action_plan"):
                urls["action_plan"] = url_for(
                    "serve_report",
                    run_folder=latest_files["run_folder"],
                    filename=latest_files["action_plan"],
                    _external=True,
                )
            if latest_files.get("trend"):
                urls["trend"] = url_for(
                    "serve_report",
                    run_folder=latest_files["trend_run_folder"],
                    filename=latest_files["trend"],
                    _external=True,
                )
            summary_data["latest_report_urls"] = urls
        for trend in summary_data["trend_history"]:
            trend["url"] = url_for(
                "serve_report",
                run_folder=trend["run_folder"],
                filename=trend["filename"],
            )
        return jsonify(summary_data)

    @app.route("/api/v1/upload", methods=["POST"])
    @token_required
    def upload_file_api():
        """
        Realiza o upload de um arquivo CSV para análise padrão.
        ---
        tags:
          - Analysis
        security:
          - Bearer: []
        consumes:
          - multipart/form-data
        parameters:
          - name: file_recente
            in: formData
            type: file
            required: true
        responses:
          200:
            description: Análise concluída com sucesso.
        """
        file_recente = request.files.get("file_recente")
        if not file_recente or file_recente.filename == "":
            return jsonify({"error": "Nenhum arquivo selecionado."}), 400
        try:
            result = services.process_upload_and_generate_reports(
                file_recente=file_recente,
                upload_folder=app.config["UPLOAD_FOLDER"],
                reports_folder=app.config["REPORTS_FOLDER"],
                db=db,
                Report=models.Report,
                TrendAnalysis=models.TrendAnalysis,
            )
            if result and result.get("warning"):
                return jsonify({"error": result["warning"]}), 400
            report_urls = {
                "summary": url_for(
                    "serve_report",
                    run_folder=result["run_folder"],
                    filename=result["summary_report_filename"],
                    _external=True,
                )
            }
            if result.get("action_plan_filename"):
                report_urls["action_plan"] = url_for(
                    "serve_report",
                    run_folder=result["run_folder"],
                    filename=result["action_plan_filename"],
                    _external=True,
                )
            if result.get("trend_report_filename"):
                report_urls["trend"] = url_for(
                    "serve_report",
                    run_folder=result["run_folder"],
                    filename=result["trend_report_filename"],
                    _external=True,
                )
            new_kpi_summary = (
                services.calculate_kpi_summary(result["json_summary_path"])
                if result.get("json_summary_path")
                else None
            )
            return jsonify(
                success=True,
                report_urls=report_urls,
                kpi_summary=new_kpi_summary,
                quick_diagnosis_html=result.get("quick_diagnosis_html"),
                date_range=result.get("date_range"),
            )
        except Exception as e:
            return (
                jsonify({"error": f"Erro fatal no processo de upload: {str(e)}"}),
                500,
            )

    @app.route("/api/v1/compare", methods=["POST"])
    @token_required
    def compare_files_api():
        """
        Realiza a comparação direta entre dois arquivos CSV.
        ---
        tags:
          - Analysis
        security:
          - Bearer: []
        consumes:
          - multipart/form-data
        parameters:
          - name: file_antigo
            in: formData
            type: file
            required: true
          - name: file_recente
            in: formData
            type: file
            required: true
        responses:
          200:
            description: Comparação concluída com sucesso.
        """
        file_antigo = request.files.get("file_antigo")
        file_recente = request.files.get("file_recente")
        if not file_antigo or file_antigo.filename == "":
            return jsonify({"error": "O 'file_antigo' é obrigatório."}), 400
        if not file_recente or file_recente.filename == "":
            return jsonify({"error": "O 'file_recente' é obrigatório."}), 400
        try:
            result = services.process_direct_comparison(
                files=[file_antigo, file_recente],
                upload_folder=app.config["UPLOAD_FOLDER"],
                reports_folder=app.config["REPORTS_FOLDER"],
            )
            if result:
                report_url = url_for(
                    "serve_report",
                    run_folder=result["run_folder"],
                    filename=result["report_filename"],
                    _external=True,
                )
                return jsonify({"success": True, "report_url": report_url})
            return (
                jsonify({"error": "Não foi possível processar a comparação."}),
                500,
            )
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            return jsonify({"error": f"Erro inesperado: {str(e)}"}), 500

    def secure_send_from_directory(base_directory, path):
        requested_path = os.path.normpath(os.path.join(base_directory, path))
        if not requested_path.startswith(os.path.abspath(base_directory)):
            abort(404)
        return send_from_directory(base_directory, path)

    @app.route("/reports/<run_folder>/planos_de_acao/<filename>")
    def serve_planos(run_folder, filename):
        safe_path = os.path.join(run_folder, "planos_de_acao", filename)
        return secure_send_from_directory(app.config["REPORTS_FOLDER"], safe_path)

    @app.route("/reports/<run_folder>/detalhes/<filename>")
    def serve_detalhes(run_folder, filename):
        safe_path = os.path.join(run_folder, "detalhes", filename)
        return secure_send_from_directory(app.config["REPORTS_FOLDER"], safe_path)

    @app.route("/reports/<run_folder>/<path:filename>")
    def serve_report(run_folder, filename):
        safe_path = os.path.join(run_folder, filename)
        return secure_send_from_directory(app.config["REPORTS_FOLDER"], safe_path)

    @app.route("/docs/<path:filename>")
    def serve_docs(filename):
        docs_directory = "/app/docs"
        return secure_send_from_directory(docs_directory, filename)

    @app.route("/api/v1/reports")
    def get_reports():
        """
        Lista todos os relatórios de análise disponíveis.
        ---
        tags:
          - Reports
        responses:
          200:
            description: Lista de relatórios retornada com sucesso.
        """
        reports_data = services.get_unified_history_list(
            models.Report, models.TrendAnalysis
        )
        for report in reports_data:
            report["url"] = url_for(
                "serve_report",
                run_folder=report["run_folder"],
                filename=report["filename"],
            )
        return jsonify(reports_data)

    @app.route("/api/v1/reports/<int:report_id>", methods=["DELETE"])
    @token_required
    def delete_report_api(report_id):
        """
        Exclui um relatório específico e seus artefatos.
        ---
        tags:
          - Reports
        security:
          - Bearer: []
        parameters:
          - name: report_id
            in: path
            type: integer
            required: true
        responses:
          200:
            description: Relatório excluído com sucesso.
        """
        try:
            success = services.delete_report_and_artifacts(
                report_id=report_id, db=db, Report=models.Report
            )
            if success:
                return jsonify({"success": True}), 200
            else:
                return (
                    jsonify({"error": f"Relatório com ID {report_id} não encontrado."}),
                    404,
                )
        except Exception as e:
            return (
                jsonify({"error": f"Erro interno ao tentar excluir o relatório: {e}"}),
                500,
            )

    @app.route("/admin/login", methods=["POST"])
    def login_api():
        """
        Autentica um usuário administrativo e retorna um token JWT.
        ---
        tags:
          - Authentication
        consumes:
          - application/json
        parameters:
          - name: body
            in: body
            required: true
            schema:
              type: object
              required:
                - username
                - password
              properties:
                username:
                  type: string
                password:
                  type: string
        responses:
          200:
            description: Autenticação bem-sucedida.
        """
        auth_data = request.get_json()
        if (
            not auth_data
            or not auth_data.get("username")
            or not auth_data.get("password")
        ):
            return jsonify({"error": "Usuário e senha são obrigatórios."}), 400
        username = auth_data.get("username")
        password = auth_data.get("password")
        admin_user = os.getenv("ADMIN_USER")
        admin_password = os.getenv("ADMIN_PASSWORD")
        if username == admin_user and password == admin_password:
            expiration_hours = int(os.getenv("JWT_EXPIRATION_HOURS", "1"))
            payload = {
                "exp": datetime.now(timezone.utc) + timedelta(hours=expiration_hours),
                "iat": datetime.now(timezone.utc),
                "sub": "admin",
            }
            access_token = jwt.encode(
                payload, app.config["SECRET_KEY"], algorithm="HS256"
            )
            return jsonify({"access_token": access_token})
        else:
            return jsonify({"error": "Credenciais inválidas."}), 401

    return app
