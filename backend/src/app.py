import os
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
import requests
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
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec_1",
                "route": "/apidocs/apispec_1.json",
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/apidocs/",
    }

    swagger_template = {
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
    }

    Swagger(app, config=swagger_config, template=swagger_template)

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
                )
            }
            if latest_files.get("action_plan"):
                urls["action_plan"] = url_for(
                    "serve_report",
                    run_folder=latest_files["run_folder"],
                    filename=latest_files["action_plan"],
                )
            if latest_files.get("trend"):
                urls["trend"] = url_for(
                    "serve_report",
                    run_folder=latest_files["trend_run_folder"],
                    filename=latest_files["trend"],
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
                )
            }
            if result.get("action_plan_filename"):
                report_urls["action_plan"] = url_for(
                    "serve_report",
                    run_folder=result["run_folder"],
                    filename=result["action_plan_filename"],
                )
            if result.get("trend_report_filename"):
                report_urls["trend"] = url_for(
                    "serve_report",
                    run_folder=result["run_folder"],
                    filename=result["trend_report_filename"],
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

    @app.route("/api/v1/feedback", methods=["POST"])
    def submit_feedback():
        """
        Submete feedback do usuário criando uma issue no GitHub.
        ---
        tags:
          - Feedback
        consumes:
          - application/json
        parameters:
          - name: body
            in: body
            required: true
            schema:
              type: object
              required:
                - type
                - title
                - description
              properties:
                type:
                  type: string
                  enum: [bug, feature, suggestion, other]
                  description: Tipo do feedback
                title:
                  type: string
                  description: Título do feedback
                description:
                  type: string
                  description: Descrição detalhada do feedback
                email:
                  type: string
                  description: Email opcional do usuário
                context:
                  type: string
                  description: Contexto adicional (ex: nome do relatório, arquivo CSV)
        responses:
          201:
            description: Feedback enviado com sucesso.
          400:
            description: Dados inválidos.
          500:
            description: Erro interno do servidor.
        """
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "Dados JSON são obrigatórios."}), 400

            # Validação dos campos obrigatórios
            required_fields = ["type", "title", "description"]
            for field in required_fields:
                if field not in data or not data[field].strip():
                    return jsonify({"error": f"Campo '{field}' é obrigatório."}), 400

            feedback_type = data["type"]
            title = data["title"].strip()
            description = data["description"].strip()
            email = data.get("email", "").strip()
            context = data.get("context", "").strip()

            # Validação do tipo
            valid_types = ["bug", "feature", "suggestion", "other"]
            if feedback_type not in valid_types:
                return jsonify(
                    {
                        "error": f"Tipo deve ser um dos seguintes: {', '.join(valid_types)}"
                    }
                ), 400

            # Validação básica de email se fornecido
            if email and "@" not in email:
                return jsonify({"error": "Email inválido."}), 400

            # Templates para cada tipo de feedback
            bug_template = """### 🐛 Detalhes do Bug
- **Passos para reproduzir:**
  1.
  2.
  3.

- **Comportamento esperado:**

- **Comportamento atual:**

- **Ambiente:**
  - Navegador:
  - Sistema Operacional:
  - Versão da aplicação:

### 📊 Dados relacionados
- Arquivo CSV utilizado:
- Relatório gerado:
- Outros detalhes:

---

## ✅ Checklist de Resolução
- [ ] Bug reproduzido
- [ ] Causa identificada
- [ ] Correção implementada
- [ ] Testes realizados
- [ ] Documentação atualizada"""

            feature_template = """### ✨ Detalhes da Nova Funcionalidade
- **Objetivo:**

- **Benefícios esperados:**

- **Público-alvo:**

- **Estimativa de complexidade:** (Baixa/Média/Alta)

### 📋 Requisitos Funcionais
- [ ]
- [ ]
- [ ]

### 📋 Requisitos Não-Funcionais
- [ ]
- [ ]

---

## ✅ Checklist de Implementação
- [ ] Análise de viabilidade concluída
- [ ] Design/protótipo aprovado
- [ ] Desenvolvimento concluído
- [ ] Testes realizados
- [ ] Documentação atualizada
- [ ] Usuários notificados"""

            suggestion_template = """### 💡 Detalhes da Sugestão
- **Problema que resolve:**

- **Solução proposta:**

- **Alternativas consideradas:**

- **Impacto estimado:** (Baixo/Médio/Alto)

---

## ✅ Checklist de Avaliação
- [ ] Sugestão analisada pela equipe
- [ ] Viabilidade técnica avaliada
- [ ] Prioridade definida
- [ ] Decisão tomada (aprovada/rejeitada)
- [ ] Feedback dado ao usuário"""

            other_template = """### ❓ Outros - Detalhes
- **Categoria específica:**

- **Urgência:** (Baixa/Média/Alta)

- **Informações adicionais:**

---

## ✅ Checklist de Tratamento
- [ ] Solicitação analisada
- [ ] Ação apropriada tomada
- [ ] Usuário informado sobre o andamento"""

            # Selecionar template baseado no tipo
            type_specific_content = ""
            if feedback_type == "bug":
                type_specific_content = bug_template
            elif feedback_type == "feature":
                type_specific_content = feature_template
            elif feedback_type == "suggestion":
                type_specific_content = suggestion_template
            elif feedback_type == "other":
                type_specific_content = other_template

            # Construir o corpo da issue com template estruturado
            issue_body = f"""## 📋 Feedback - {feedback_type.title()}

### ℹ️ Informações Gerais
- **Tipo:** {feedback_type.title()}
- **Data/Hora:** {datetime.now().strftime("%d/%m/%Y %H:%M")}
{f"- **Email:** {email}" if email else ""}

---

### 📝 Descrição Detalhada
{description}

---

### 🎯 Contexto Adicional
{context if context else "*Nenhum contexto adicional fornecido*"}

---

### ✅ Critérios de Aceitação
**Para que este feedback seja considerado resolvido:**

{type_specific_content}

---

### 📞 Contato
{f"**Email para contato:** {email}" if email else "*Email não fornecido*"}

### 🏷️ Labels
`{feedback_type}`, `user-feedback`, `pending-review`

---
*Feedback enviado automaticamente pelo sistema SmartRemedy*"""  # Configurar headers para GitHub API
            github_token = os.getenv("GITHUB_TOKEN")
            if not github_token:
                return jsonify(
                    {"error": "Serviço de feedback temporariamente indisponível."}
                ), 503

            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json",
            }

            # Dados da issue
            issue_data = {
                "title": f"[{feedback_type.upper()}] {title}",
                "body": issue_body,
                "labels": [feedback_type],
            }

            # Fazer a requisição para criar a issue
            repo_owner = os.getenv("GITHUB_REPO_OWNER", "leonardosete")
            repo_name = os.getenv("GITHUB_REPO_NAME", "meu-dash")

            api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues"
            response = requests.post(api_url, json=issue_data, headers=headers)

            if response.status_code == 201:
                issue_data = response.json()
                return jsonify(
                    {
                        "success": True,
                        "message": "Feedback enviado com sucesso!",
                        "issue_url": issue_data["html_url"],
                    }
                ), 201
            else:
                app.logger.error(
                    f"GitHub API error: {response.status_code} - {response.text}"
                )
                return jsonify(
                    {"error": "Erro ao enviar feedback. Tente novamente mais tarde."}
                ), 500

        except Exception as e:
            app.logger.error(f"Feedback submission error: {str(e)}")
            return jsonify({"error": "Erro interno do servidor."}), 500

    return app
