import os
from datetime import datetime, timedelta, timezone
from functools import wraps
import json

import jwt
from flasgger import Swagger
from flask import (Flask, abort, jsonify, request,
                   send_from_directory, url_for)
from flask_cors import CORS
from flask_migrate import Migrate

from . import db  # Importa a instância única de __init__.py


# Define o caminho dos templates de forma explícita para o ambiente de produção (Docker/K8s),
# onde os arquivos são copiados para /app/templates.
# CORREÇÃO: Define o caminho dos templates de forma relativa para maior portabilidade.
app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'))


# --- SWAGGER UI CONFIGURATION ---
# Flasgger is now only used to generate the /apispec_1.json definition.
# The UI is served as a static file by Nginx to prevent rendering bugs.
# --- CONFIGURAÇÃO DE CAMINHOS E BANCO DE DADOS ---
# Aponta para o diretório de dados montado via Docker Compose
DATA_DIR = "/app/data"
UPLOAD_FOLDER = os.path.join(DATA_DIR, "uploads")
REPORTS_FOLDER = os.path.join(DATA_DIR, "reports")
DB_PATH = os.path.join(DATA_DIR, "meu_dash.db")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["REPORTS_FOLDER"] = REPORTS_FOLDER
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# Carrega a chave secreta a partir de uma variável de ambiente para segurança.
# NUNCA deixe uma chave secreta fixa no código em produção.
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

# Aponta para o diretório de migrações dentro da estrutura do backend
MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "migrations")

# Inicializa a instância do DB com a aplicação Flask
db.init_app(app)
migrate = Migrate(app, db, directory=MIGRATIONS_DIR)

# Inicializa o Flasgger para documentação da API
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
            "description": "Token de autorização JWT. Exemplo: \"Bearer {token}\"",
        }
    },
    "definitions": {
        "Error": {
            "type": "object",
            "properties": {
                "error": {
                    "type": "string",
                    "description": "Mensagem de erro descritiva."
                }
            }
        }
    }
}
swagger = Swagger(app, template=swagger_template)

# --- CONFIGURAÇÃO DE CORS ---
# Configura o CORS para permitir requisições da nossa futura aplicação frontend
# em ambiente de desenvolvimento, apenas para as rotas de API.
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [
                "http://localhost:5173", "http://127.0.0.1:5173",
                "http://localhost:5174", "http://127.0.0.1:5174"
            ]
        },
        r"/admin/*": {  # Adiciona a regra para as rotas de admin
            "origins": [
                "http://localhost:5173", "http://127.0.0.1:5173",
                "http://localhost:5174", "http://127.0.0.1:5174"
            ]
        }
    },
    supports_credentials=True,
)


# Importações que dependem da inicialização do 'app' e 'db'
from . import services, models  # noqa: E42

# --- INICIALIZAÇÃO E AUTOCORREÇÃO DO BANCO DE DADOS ---
# A criação de tabelas foi movida para um comando explícito de migração
# (ex: 'make migrate-docker') para seguir as melhores práticas.
# Isso evita que a aplicação tente modificar o schema do banco de dados
# toda vez que ela é iniciada, o que é problemático em ambientes com múltiplos
# workers (Gunicorn) e pode causar 'race conditions'.
# with app.app_context():
#     db.metadata.create_all(db.engine, checkfirst=True)


os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["REPORTS_FOLDER"], exist_ok=True)


# --- ROTAS DE HEALTH CHECK PARA KUBERNETES ---


@app.route("/health")
def health_check():
    """Endpoint de Health Check para o Kubernetes.

    Usado pelo Liveness Probe e Readiness Probe do Kubernetes para verificar se a
    aplicação está em execução e pronta para receber tráfego.

    Returns:
        tuple: Uma tupla contendo a resposta JSON e o código de status HTTP.
               Ex: ({"status": "ok"}, 200)
    """
    return jsonify({"status": "ok"}), 200


def token_required(f):
    """Decorador para proteger rotas que exigem autenticação via token JWT."""

    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            parts = auth_header.split()
            # Se o formato for "Bearer <token>", pega apenas o token.
            if len(parts) == 2 and parts[0].lower() == "bearer":
                token = parts[1]
            # Se o formato for apenas "<token>", usa o valor diretamente.
            # Isso melhora a experiência de uso no Swagger UI.
            elif len(parts) == 1:
                token = parts[0]

        if not token:
            return jsonify({"error": "Token de autenticação ausente."}), 401

        try:
            # Decodifica e valida o token
            jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expirado."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token inválido."}), 401

        return f(*args, **kwargs)

    return decorated

# --- ROTAS PRINCIPAIS DA APLICAÇÃO ---


@app.route("/api/v1/dashboard-summary")
def get_dashboard_summary():
    """Obtém um resumo dos KPIs e do histórico de análises.
    Este endpoint retorna os principais indicadores de performance (KPIs) da última análise
    e uma lista do histórico de relatórios de tendência gerados.
    ---
    tags:
      - Dashboard
    responses:
      200:
        description: Resumo do dashboard retornado com sucesso.
        schema:
          type: object
          properties:
            kpi_summary:
              type: object
              description: Objeto com os KPIs da última análise.
            trend_history:
              type: array
              description: Lista de análises de tendência anteriores.
              items:
                type: object
      500:
        description: Erro interno ao processar a solicitação.
    Returns:
        Response: Uma resposta JSON contendo os dados do dashboard.
    """
    # Delega a busca de dados para a camada de serviço
    summary_data = services.get_dashboard_summary_data(
        db=db,
        Report=models.Report,
        TrendAnalysis=models.TrendAnalysis,
    )

    # Constrói as URLs para os relatórios mais recentes, se existirem
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

    # Enriquece o histórico de tendências com URLs
    for trend in summary_data["trend_history"]:
        trend["url"] = url_for(
            "serve_report", run_folder=trend["run_folder"], filename=trend["filename"]
        )

    return jsonify(summary_data)


@app.route("/api/v1/upload", methods=["POST"])
@token_required
def upload_file_api():
    """Processa um novo arquivo para análise (Análise Padrão).
    Este endpoint recebe um arquivo .csv, dispara o processo de análise completo,
    gera os relatórios e retorna um JSON com o resultado.
    ---
    tags:
      - Upload
    security:
      - Bearer: []
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: file_recente
        type: file
        required: true
        description: O arquivo .csv a ser analisado.
    responses:
      200:
        description: Arquivo processado com sucesso.
        schema:
          type: object
          properties:
            success:
              type: boolean
            report_urls:
              type: object
              description: URLs para os relatórios gerados.
            kpi_summary:
              type: object
              description: Resumo dos KPIs da nova análise.
      400:
        description: Erro na requisição, como arquivo ausente ou inválido.
        schema:
          $ref: '#/definitions/Error'
      500:
        description: Erro interno no servidor durante o processamento.
        schema:
          $ref: '#/definitions/Error'
    """
    file_recente = request.files.get("file_recente")

    if not file_recente or file_recente.filename == "":
        return jsonify({"error": "Nenhum arquivo selecionado."}), 400

    try:
        # Delega toda a lógica de negócio para a camada de serviço
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
        
        quick_diagnosis_html = result.get("quick_diagnosis_html")

        return jsonify(
            success=True, 
            report_urls=report_urls, 
            kpi_summary=new_kpi_summary,
            quick_diagnosis_html=quick_diagnosis_html,
            date_range=result.get("date_range")
        )

    except Exception as e:
        return jsonify({"error": f"Erro fatal no processo de upload: {str(e)}"}), 500


# =================================================================
# FUNÇÃO CORRIGIDA (Contornando o bug do Swagger)
# =================================================================
@app.route("/api/v1/compare", methods=["POST"])
@token_required
def compare_files_api():
    """Compara dois arquivos de dados para análise de tendência direta.
    Este endpoint recebe dois arquivos .csv (um "antigo" e um "recente"),
    dispara o processo de comparação e retorna um JSON com a URL para o
    relatório de tendência gerado.
    ---
    tags:
      - Upload
    security:
      - Bearer: []
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: file_antigo
        type: file
        required: true
        description: O arquivo .csv "antigo" (base) para comparação.
      - in: formData
        name: file_recente
        type: file
        required: true
        description: O arquivo .csv "recente" para comparação.
    responses:
      200:
        description: Arquivos comparados com sucesso.
        schema:
          type: object
          properties:
            success:
              type: boolean
            report_url:
              type: string
              description: URL para o relatório de tendência gerado.
      400:
        description: Erro na requisição, como arquivos ausentes.
        schema:
          $ref: '#/definitions/Error'
      500:
        description: Erro interno no servidor durante o processamento.
        schema:
          $ref: '#/definitions/Error'
    """
    # Busca os arquivos por chaves nomeadas (file_antigo, file_recente)
    file_antigo = request.files.get("file_antigo")
    file_recente = request.files.get("file_recente")

    # Validação se os dois arquivos foram enviados
    if not file_antigo or file_antigo.filename == "":
        return jsonify({"error": "O 'file_antigo' é obrigatório."}), 400

    if not file_recente or file_recente.filename == "":
        return jsonify({"error": "O 'file_recente' é obrigatório."}), 400

    # Agrupa os arquivos em uma lista para enviar ao serviço
    # Sua lógica de serviço que ordena os arquivos continuará funcionando.
    files_list = [file_antigo, file_recente]

    try:
        # O service.process_direct_comparison já espera uma lista
        result = services.process_direct_comparison(
            files=files_list,
            upload_folder=app.config["UPLOAD_FOLDER"],
            reports_folder=app.config["REPORTS_FOLDER"],
        )
        if result:
            report_url = url_for(
                "serve_report",
                run_folder=result["run_folder"],
                filename=result["report_filename"],
                _external=True,  # Garante que a URL seja absoluta (ex: http://127.0.0.1:5001/...)
            )
            return jsonify({"success": True, "report_url": report_url})
        return jsonify({"error": "Não foi possível processar a comparação."}), 500
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Erro inesperado: {str(e)}"}), 500
# =================================================================
# FIM DA FUNÇÃO
# =================================================================


# --- FUNÇÃO DE SEGURANÇA PARA SERVIR ARQUIVOS ---


def secure_send_from_directory(base_directory, path):
    """Serve um arquivo de um diretório de forma segura, prevenindo Path Traversal.

    Esta função é um wrapper de segurança em torno da `send_from_directory` do Flask.
    Ela garante que o caminho do arquivo solicitado esteja contido estritamente
    dentro do diretório base permitido, prevenindo que um usuário mal-intencionado
    acesse arquivos arbitrários no sistema de arquivos (e.g., `../../etc/passwd`).

    Args:
        base_directory (str): O caminho absoluto para o diretório a partir do qual
                              os arquivos podem ser servidos.
        path (str): O caminho relativo para o arquivo solicitado, fornecido pelo
                    usuário.

    Returns:
        werkzeug.wrappers.Response: A resposta do Flask para servir o arquivo
        solicitado.

    Raises:
        werkzeug.exceptions.NotFound: Lança uma exceção 404 Not Found se o caminho
        resolvido estiver fora do `base_directory`, tratando-o como um recurso
        não encontrado para evitar vazamento de informações.
    """
    # Constrói o caminho absoluto do arquivo solicitado
    requested_path = os.path.normpath(os.path.join(base_directory, path))

    # Garante que o caminho resolvido está dentro do diretório base
    if not requested_path.startswith(os.path.abspath(base_directory)):
        # Se não estiver, é uma tentativa de Path Traversal.
        abort(404)  # Usar 404 para não vazar informação de que o recurso existe.

    # Usa a função segura do Flask para servir o arquivo
    return send_from_directory(base_directory, path)


# --- ROTAS PARA SERVIR ARQUIVOS ESTÁTICOS ---


@app.route("/reports/<run_folder>/planos_de_acao/<filename>")
def serve_planos(run_folder, filename):
    """Serve os arquivos de plano de ação que estão em um subdiretório."""
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
    # O diretório 'docs' foi copiado para /app/docs durante o build do Docker.
    docs_directory = "/app/docs"
    # Usa a função segura para servir o arquivo, que já previne Path Traversal.
    return secure_send_from_directory(docs_directory, filename)


@app.route("/api/v1/reports")
def get_reports():
    """Lista todos os relatórios de análise de tendência gerados.
    Este endpoint retorna uma lista com os metadados de todos os relatórios
    de análise de tendência que foram gerados e estão armazenados.
    ---
    tags:
      - Reports
    responses:
      200:
        description: Lista de relatórios retornada com sucesso.
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                description: ID único do relatório no banco de dados.
              run_folder:
                type: string
                description: Diretório onde os artefatos do relatório estão armazenados.
              filename:
                type: string
                description: Nome do arquivo principal do relatório.
              created_at:
                type: string
                format: date-time
                description: Data e hora da criação do relatório.
    """
    reports_data = services.get_unified_history_list(models.Report, models.TrendAnalysis)

    # Enriquece com as URLs antes de retornar
    for report in reports_data:
        report["url"] = url_for(
            "serve_report", run_folder=report["run_folder"], filename=report["filename"]
        )

    return jsonify(reports_data)


# --- NOVA ROTA PARA EXCLUSÃO ---
@app.route("/api/v1/reports/<int:report_id>", methods=["DELETE"])
@token_required
def delete_report_api(report_id):
    """Exclui um relatório de análise de tendência e seus artefatos.
    Este endpoint é protegido e requer um token de autenticação JWT.
    ---
    tags:
      - Reports
    security:
      - Bearer: []
    parameters:
      - in: path
        name: report_id
        type: integer
        required: true
        description: O ID do relatório a ser excluído.
    responses:
      200:
        description: Relatório excluído com sucesso.
        schema:
          type: object
          properties:
            success:
              type: boolean
      401:
        description: Erro de autenticação (token ausente, inválido ou expirado).
        schema:
          $ref: '#/definitions/Error'
      404:
        description: Relatório não encontrado.
        schema:
          $ref: '#/definitions/Error'
      500:
        description: Erro interno no servidor durante a exclusão.
        schema:
          $ref: '#/definitions/Error'
    """
    try:
        # Delega a lógica de exclusão para a camada de serviço
        success = services.delete_report_and_artifacts(
            report_id=report_id, db=db, Report=models.Report
        )

        if success:
            return jsonify({"success": True}), 200
        else:
            # O serviço já logou o erro, aqui apenas informamos o cliente.
            # O relatório pode não ter sido encontrado no serviço.
            return (
                jsonify({"error": f"Relatório com ID {report_id} não encontrado."}),
                404,
            )
    except Exception as e:
        # Captura qualquer outra exceção inesperada durante o processo.
        return (
            jsonify({"error": f"Erro interno ao tentar excluir o relatório: {e}"}),
            500,
        )


@app.route("/admin/login", methods=["POST"])
def login_api():
    """Autentica um administrador e retorna um token JWT.
    Este endpoint recebe as credenciais de administrador e, se válidas,
    retorna um token de acesso JWT para ser usado em rotas protegidas.
    ---
    tags:
      - Authentication
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
              description: Nome de usuário do administrador.
              example: "admin"
            password:
              type: string
              description: Senha do administrador.
              format: password
              example: "your_secret_password"
    responses:
      200:
        description: Autenticação bem-sucedida.
        schema:
          type: object
          properties:
            access_token:
              type: string
              description: Token JWT para autorização.
      400:
        description: Requisição inválida (usuário ou senha ausentes).
        schema:
          $ref: '#/definitions/Error'
      401:
        description: Credenciais inválidas.
        schema:
          $ref: '#/definitions/Error'
    """
    auth_data = request.get_json()
    if not auth_data or not auth_data.get("username") or not auth_data.get("password"):
        return jsonify({"error": "Usuário e senha são obrigatórios."}), 400

    username = auth_data.get("username")
    password = auth_data.get("password")

    # Carrega as credenciais do administrador a partir das variáveis de ambiente
    admin_user = os.getenv("ADMIN_USER")
    admin_password = os.getenv("ADMIN_PASSWORD")

    if username == admin_user and password == admin_password:
        # Gera o token JWT
        # Torna o tempo de expiração configurável, com padrão de 1 hora.
        expiration_hours = int(os.getenv("JWT_EXPIRATION_HOURS", "1"))
        payload = {
            "exp": datetime.now(timezone.utc)
            + timedelta(hours=expiration_hours),
            "iat": datetime.now(timezone.utc),
            "sub": "admin",
        }
        access_token = jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")
        return jsonify({"access_token": access_token})
    else:
        return jsonify({"error": "Credenciais inválidas."}), 401


# --- INICIALIZAÇÃO DA APLICAÇÃO ---

if __name__ == "__main__":
    # Executa em modo debug apenas se a variável de ambiente FLASK_DEBUG for 'True'
    is_debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    app.run(debug=is_debug_mode)