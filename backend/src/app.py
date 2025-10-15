import os
from datetime import datetime, timedelta, timezone
from functools import wraps
import jwt
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
from . import db  # Importa a instância única de __init__.py


app = Flask(__name__, template_folder="../templates")

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
app.config["SECRET_KEY"] = (
    "uma-chave-secreta-forte-para-flash"  # NOVO: Chave secreta necessária para usar flash
)

# Aponta para o diretório de migrações dentro da estrutura do backend
MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "migrations")

# Inicializa a instância do DB com a aplicação Flask
db.init_app(app)
migrate = Migrate(app, db, directory=MIGRATIONS_DIR)

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
from . import services, models  # noqa: E402

# --- INICIALIZAÇÃO E AUTOCORREÇÃO DO BANCO DE DADOS ---
# Garante que o banco de dados e todas as tabelas sejam criados na inicialização.
# A chamada é idempotente: `checkfirst=True` verifica se a tabela já existe
# antes de tentar criá-la, evitando crashes em reinicializações.
with app.app_context():
    db.metadata.create_all(db.engine, checkfirst=True)


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


# --- ROTAS PRINCIPAIS DA APLICAÇÃO ---


@app.route("/api/v1/dashboard-summary")
def get_dashboard_summary():
    """
    Endpoint da API que retorna um resumo dos dados para o dashboard principal.

    Delega a busca dos dados para a camada de serviço e, em seguida, formata
    a resposta como JSON, enriquecendo-a com as URLs necessárias para o frontend.

    Returns:
        Response: Uma resposta JSON contendo os dados do dashboard.
    """
    # Delega a busca de dados para a camada de serviço
    summary_data = services.get_dashboard_summary_data(
        db=db,
        Report=models.Report,
        TrendAnalysis=models.TrendAnalysis,
        reports_folder=app.config["REPORTS_FOLDER"],
    )

    # Enriquece os dados com URLs geradas pelo Flask
    if summary_data.get("kpi_summary"):
        last_report_info = summary_data["last_report_info"]
        if last_report_info:
            summary_data["kpi_summary"]["report_url"] = url_for(
                "serve_report",
                run_folder=last_report_info["run_folder"],
                filename=last_report_info["filename"],
                _external=True,  # Gera uma URL absoluta (ex: http://127.0.0.1:5001/...)
            )

        # Adiciona a URL do plano de ação ao kpi_summary, se existir
        if summary_data.get("last_action_plan"):
            summary_data["kpi_summary"]["action_plan_url"] = url_for(
                "serve_report",
                run_folder=last_report_info["run_folder"],
                filename="atuar.html",
                _external=True,
            )

        # Adiciona a URL da última análise de tendência ao kpi_summary, se existir
        if summary_data.get("trend_history"):
            latest_trend = summary_data["trend_history"][0]
            summary_data["kpi_summary"]["trend_analysis_url"] = url_for(
                "serve_report",
                run_folder=latest_trend["run_folder"],
                filename=latest_trend["filename"],
                _external=True,
            )

    for trend in summary_data["trend_history"]:
        trend["url"] = url_for(
            "serve_report", run_folder=trend["run_folder"], filename=trend["filename"]
        )

    return jsonify(summary_data)


@app.route("/api/v1/upload", methods=["POST"])
def upload_file_api():
    """
    Endpoint da API para upload e processamento de um novo arquivo de análise.

    Recebe um arquivo, delega o processamento para a camada de serviço e
    retorna uma resposta JSON indicando sucesso ou falha.

    Returns:
        Response: Uma resposta JSON com o resultado do processamento.
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
            # Passa o caminho raiz do backend para que o serviço encontre os templates
            base_dir=os.path.dirname(__file__),
        )

        if result and result.get("warning"):
            return jsonify({"error": result["warning"]}), 400

        report_url = url_for(
            "serve_report",
            run_folder=result["run_folder"],
            filename=result["report_filename"],
        )
        new_kpi_summary = (
            services.calculate_kpi_summary(result["json_summary_path"])
            if result.get("json_summary_path")
            else None
        )

        return jsonify(success=True, report_url=report_url, kpi_summary=new_kpi_summary)

    except Exception as e:
        return jsonify({"error": f"Erro fatal no processo de upload: {str(e)}"}), 500


@app.route("/api/v1/compare", methods=["POST"])
def compare_files_api():
    """
    Endpoint da API para comparação direta entre dois arquivos.

    Recebe dois arquivos, delega a comparação para a camada de serviço e
    retorna uma resposta JSON com a URL do relatório de tendência gerado.

    Returns:
        Response: Uma resposta JSON com o resultado da comparação.
    """
    if "files" not in request.files or len(request.files.getlist("files")) == 0:
        return jsonify({"error": "Nenhum arquivo enviado."}), 400

    files = request.files.getlist("files")

    if len(files) != 2:
        return (
            jsonify({"error": "Por favor, selecione exatamente dois arquivos."}),
            400,
        )

    try:
        result = services.process_direct_comparison(
            files=files,
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
        return jsonify({"error": "Não foi possível processar a comparação."}), 500
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Erro inesperado: {str(e)}"}), 500


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
    # O diretório 'docs' está montado em /app/docs no contêiner.
    docs_directory = "/app/docs"  # Caminho dentro do contêiner
    # Renderiza o HTML para injetar a variável de ambiente, tornando o link dinâmico.
    from flask import render_template_string
    
    with open(os.path.join(docs_directory, filename), 'r') as f:
        content = f.read()
    return render_template_string(content, FRONTEND_BASE_URL=os.getenv("FRONTEND_BASE_URL", "/"))


@app.route("/api/v1/reports")
def get_reports():
    """
    Endpoint da API que retorna a lista de todos os relatórios gerados.

    Delega a busca dos dados para a camada de serviço e formata a resposta
    como uma lista de objetos JSON, cada um representando um relatório.

    Returns:
        Response: Uma resposta JSON contendo a lista de relatórios.
    """
    # Delega a busca para a camada de serviço
    reports_data = services.get_reports_list(models.Report)

    # Enriquece com as URLs antes de retornar
    for report in reports_data:
        report["url"] = url_for(
            "serve_report", run_folder=report["run_folder"], filename=report["filename"]
        )

    return jsonify(reports_data)


def token_required(f):
    """Decorador para proteger rotas que exigem autenticação via token JWT."""

    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            # Extrai o token do cabeçalho 'Bearer <token>'
            token = request.headers["Authorization"].split(" ")[1]

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


# --- NOVA ROTA PARA EXCLUSÃO ---
@app.route("/api/v1/reports/<int:report_id>", methods=["DELETE"])
@token_required
def delete_report_api(report_id):
    """
    Endpoint da API para excluir um relatório e seus artefatos.

    Args:
        report_id (int): O ID do relatório a ser excluído, capturado da URL.

    Returns:
        Response: Uma resposta JSON indicando sucesso ou falha.
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
    """Endpoint da API para autenticação e geração de token JWT."""
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
        payload = {
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
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
