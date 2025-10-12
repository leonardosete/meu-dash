import os
from datetime import datetime, timezone
from flask import abort
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_from_directory,
    jsonify,
    flash,
)
from . import services
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__, template_folder="../templates")

# --- CONFIGURAÇÃO DE CAMINHOS E BANCO DE DADOS ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "..", "data", "uploads")
REPORTS_FOLDER = os.path.join(BASE_DIR, "..", "data", "reports")
DB_PATH = os.path.join(BASE_DIR, "..", "data", "meu_dash.db")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["REPORTS_FOLDER"] = REPORTS_FOLDER
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = (
    "uma-chave-secreta-forte-para-flash"  # NOVO: Chave secreta necessária para usar flash
)
app.config["ADMIN_TOKEN"] = os.getenv("ADMIN_TOKEN")
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    original_filename = db.Column(db.String(255))
    report_path = db.Column(db.String(255))
    json_summary_path = db.Column(db.String(255))
    date_range = db.Column(db.String(100), nullable=True)

    # Relacionamentos com TrendAnalysis para exclusão em cascata
    trends_as_current = db.relationship(
        "TrendAnalysis",
        foreign_keys="TrendAnalysis.current_report_id",
        back_populates="current_report",
        cascade="all, delete-orphan",
    )
    trends_as_previous = db.relationship(
        "TrendAnalysis",
        foreign_keys="TrendAnalysis.previous_report_id",
        back_populates="previous_report",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Report {self.original_filename}>"


class TrendAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    trend_report_path = db.Column(db.String(255), nullable=False)

    # Chaves estrangeiras para os relatórios que geraram a tendência
    current_report_id = db.Column(
        db.Integer, db.ForeignKey("report.id"), nullable=False
    )
    previous_report_id = db.Column(
        db.Integer, db.ForeignKey("report.id"), nullable=False
    )

    # Relacionamentos para fácil acesso aos objetos Report
    current_report = db.relationship(
        "Report", foreign_keys=[current_report_id], back_populates="trends_as_current"
    )
    previous_report = db.relationship(
        "Report", foreign_keys=[previous_report_id], back_populates="trends_as_previous"
    )

    def __repr__(self):
        return f"<TrendAnalysis {self.timestamp}>"


os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["REPORTS_FOLDER"], exist_ok=True)

# --- FILTRO DE TEMPLATE PARA TIMEZONE ---


@app.template_filter("localtime")
def localtime_filter(utc_dt):
    """Converte um datetime UTC para o fuso horário local (America/Sao_Paulo)."""
    if not utc_dt:
        return ""
    try:
        # Garante que o datetime de entrada é 'aware' (tem timezone)
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
        # Tenta importar a biblioteca pytz, se não, usa a nativa (Python 3.9+)
        from zoneinfo import ZoneInfo

        local_tz = ZoneInfo("America/Sao_Paulo")
        return utc_dt.astimezone(local_tz).strftime("%d/%m/%Y às %H:%M")
    except (ImportError, Exception):
        # Fallback para um formato simples se a conversão falhar
        return utc_dt.strftime("%d/%m/%Y %H:%M (UTC)")


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


@app.route("/")
def index():
    """Renderiza a página de upload principal (`upload.html`).

    Busca no banco de dados os links para o último relatório de tendência e para o
    plano de ação mais recente. Esses links são passados para o template para
    serem exibidos como atalhos na interface do usuário.

    Returns:
        str: O conteúdo HTML renderizado da página de upload.
    """
    trend_history = []
    last_action_plan = None
    kpi_summary = None  # NOVO: Dicionário para os KPIs do dashboard

    # Lógica para o plano de ação continua a mesma: sempre o mais recente.
    last_report = Report.query.order_by(Report.timestamp.desc()).first()
    if last_report:
        run_folder_path = os.path.dirname(last_report.report_path)
        run_folder_name = os.path.basename(run_folder_path)
        # CORREÇÃO: Verifica a existência e o conteúdo do CSV, não do HTML.
        action_plan_csv_path = os.path.join(run_folder_path, "atuar.csv")
        if (
            os.path.exists(action_plan_csv_path)
            and os.path.getsize(action_plan_csv_path) > 100
        ):  # Um tamanho arbitrário para garantir que não está vazio
            last_action_plan = {
                "url": url_for(
                    "serve_report",
                    run_folder=run_folder_name,
                    filename="atuar.html",
                ),
                "date": last_report.timestamp,  # Passa o objeto datetime diretamente
            }
        # NOVO: Extrai KPIs do último relatório para o Dashboard Gerencial
        if last_report.json_summary_path and os.path.exists(
            last_report.json_summary_path
        ):
            kpi_data = services.calculate_kpi_summary(last_report.json_summary_path)
            if kpi_data:
                # Adiciona a URL do relatório aos dados do KPI
                kpi_data["report_url"] = url_for(
                    "serve_report",
                    run_folder=os.path.basename(
                        os.path.dirname(last_report.report_path)
                    ),
                    filename=os.path.basename(last_report.report_path),
                )
                kpi_summary = kpi_data

    # NOVA LÓGICA: Busca o histórico de tendências diretamente do banco de dados.
    trend_analyses = (
        TrendAnalysis.query.order_by(TrendAnalysis.timestamp.desc()).limit(60).all()
    )
    for analysis in trend_analyses:
        try:
            run_folder = os.path.basename(os.path.dirname(analysis.trend_report_path))
            filename = os.path.basename(analysis.trend_report_path)
            trend_history.append(
                {
                    "url": url_for(
                        "serve_report", run_folder=run_folder, filename=filename
                    ),
                    "date": analysis.timestamp,  # Passa o objeto datetime diretamente
                }
            )
        except Exception:
            continue  # Ignora entradas com caminhos inválidos

    return render_template(
        "index.html",
        trend_history=trend_history,
        last_action_plan=last_action_plan,
        kpi_summary=kpi_summary,  # Passa os KPIs para o template
    )


@app.route("/upload", methods=["POST"])
def upload_file():
    """Recebe o arquivo enviado pelo usuário e orquestra a análise.

    Este endpoint é ativado pelo formulário de upload de arquivo único. Ele
    valida o arquivo, delega o processamento completo para a camada de serviço
    (`services.process_upload_and_generate_reports`) e, se bem-sucedido,
    redireciona o usuário para o relatório recém-gerado.

    Em caso de erro, exibe uma mensagem flash para o usuário e o redireciona
    de volta para a página inicial.

    Returns:
        werkzeug.wrappers.Response: Uma resposta de redirecionamento para a página
        do relatório gerado ou de volta para a página inicial em caso de erro.
    """
    file_recente = request.files.get("file_recente")

    if not file_recente or file_recente.filename == "":
        flash("Nenhum arquivo selecionado.", "error")
        return redirect(url_for("index"))

    try:
        # Delega toda a lógica de negócio para a camada de serviço
        result = services.process_upload_and_generate_reports(
            file_recente=file_recente,
            upload_folder=app.config["UPLOAD_FOLDER"],
            reports_folder=app.config["REPORTS_FOLDER"],
            db=db,
            Report=Report,
            TrendAnalysis=TrendAnalysis,  # Passa o novo modelo
            base_dir=BASE_DIR,
        )

        # Se a requisição for AJAX (feita pelo nosso script), retorna JSON
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            if result and result.get("warning"):
                return jsonify(success=False, error=result["warning"]), 400

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

            return jsonify(
                success=True, report_url=report_url, kpi_summary=new_kpi_summary
            )

        # Comportamento padrão (fallback para clientes sem JS): redireciona.
        if result and not result.get("warning"):
            return redirect(
                url_for(
                    "serve_report",
                    run_folder=result["run_folder"],
                    filename=result["report_filename"],
                )
            )

        flash(
            result.get("warning")
            or "Ocorreu um erro durante o processamento do arquivo.",
            "error",
        )
        return redirect(url_for("index"))

    except Exception as e:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return (
                jsonify(
                    success=False, error=f"Erro fatal no processo de upload: {str(e)}"
                ),
                500,
            )
        flash(f"Erro fatal no processo de upload: {str(e)}", "error")
        return redirect(url_for("index"))


@app.route("/compare", methods=["POST"])
def compare_files():
    """Recebe dois arquivos e orquestra a comparação direta entre eles.

    Este endpoint é ativado pelo formulário de comparação. Ele espera exatamente
    dois arquivos, delega a lógica de comparação para a camada de serviço
    (`services.process_direct_comparison`), e redireciona o usuário para o
    relatório de tendência resultante.

    Returns:
        werkzeug.wrappers.Response: Uma resposta de redirecionamento para o
        relatório de tendência ou de volta para a página inicial em caso de erro.
    """
    if "files" not in request.files:
        flash("Nenhum arquivo enviado.", "error")
        return redirect(url_for("index"))

    files = request.files.getlist("files")

    if len(files) != 2:
        flash("Por favor, selecione exatamente dois arquivos para comparação.", "error")
        return redirect(url_for("index"))

    try:
        # Delega toda a lógica de negócio para a camada de serviço
        result = services.process_direct_comparison(
            files=files,
            upload_folder=app.config["UPLOAD_FOLDER"],
            reports_folder=app.config["REPORTS_FOLDER"],
        )
        if result:
            return redirect(
                url_for(
                    "serve_report",
                    run_folder=result["run_folder"],
                    filename=result["report_filename"],
                )
            )
        else:
            flash("Não foi possível processar a comparação.", "error")
            return redirect(url_for("index"))
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("index"))
    except Exception:
        flash(
            "Ocorreu um erro inesperado durante a comparação. Verifique os logs.",
            "error",
        )
        return redirect(url_for("index"))


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
    docs_dir = os.path.abspath(os.path.join(app.root_path, "..", "docs"))
    return secure_send_from_directory(docs_dir, filename)


@app.route("/relatorios")
def relatorios():
    """Renderiza a página de histórico de relatórios (`relatorios.html`).

    Consulta o banco de dados para obter uma lista de todos os relatórios gerados,
    ordenados do mais recente para o mais antigo. Os dados são então passados
    para o template para exibição em uma tabela.

    Returns:
        str: O conteúdo HTML renderizado da página de histórico.
    """
    reports = Report.query.order_by(Report.timestamp.desc()).all()
    report_data = []
    for report in reports:
        report_data.append(
            {
                "id": report.id,  # NOVO: Passando o ID para a exclusão
                "timestamp": report.timestamp,
                "original_filename": report.original_filename,
                "url": url_for(
                    "serve_report",
                    run_folder=os.path.basename(os.path.dirname(report.report_path)),
                    filename=os.path.basename(report.report_path),
                ),
            }
        )
    return render_template("relatorios.html", reports=report_data)


# --- NOVA ROTA PARA EXCLUSÃO ---
@app.route("/report/delete/<int:report_id>", methods=["POST"])
def delete_report(report_id):
    """Processa a exclusão de um relatório específico.

    Ativado por um POST na página de histórico. A função localiza o relatório
    no banco de dados pelo seu ID, remove a pasta de execução correspondente
    (que contém todos os arquivos HTML e JSON daquela análise) do sistema de
    arquivos e, em seguida, remove o registro do banco de dados.

    Args:
        report_id (int): O ID do relatório a ser excluído, capturado da URL.

    Returns:
        werkzeug.wrappers.Response: Uma resposta de redirecionamento de volta
        para a página de histórico de relatórios.
    """
    # Protege a rota, permitindo acesso apenas a administradores.
    if not session.get("is_admin"):
        flash(
            "Acesso negado. Você precisa ser um administrador para excluir relatórios.",
            "error",
        )
        return redirect(url_for("admin_login_page"))

    report = Report.query.get_or_404(report_id)
    report_filename = report.original_filename  # Salva o nome para a mensagem flash

    # Delega a lógica de exclusão para a camada de serviço
    success = services.delete_report_and_artifacts(
        report_id=report_id, db=db, Report=Report
    )

    if success:
        flash(
            f"Relatório '{report_filename}' e seus arquivos foram excluídos com sucesso.",
            "success",
        )
    else:
        flash(
            f"Erro ao tentar excluir o relatório '{report_filename}'. Consulte os logs.",
            "error",
        )

    return redirect(url_for("relatorios"))


# --- NOVAS ROTAS DE ADMINISTRAÇÃO ---


@app.route("/admin", methods=["GET"])
def admin_login_page():
    """Renderiza a página de login do administrador."""
    # O template admin_login.html será criado na próxima etapa do plano.
    return render_template("admin_login.html")


@app.route("/admin/login", methods=["POST"])
def admin_login():
    """Processa a tentativa de login do administrador."""
    token_fornecido = request.form.get("token")
    admin_token_config = app.config.get("ADMIN_TOKEN")

    # Verifica se o token de admin está configurado e se corresponde ao fornecido
    if admin_token_config and token_fornecido == admin_token_config:
        session["is_admin"] = True
        flash("Login de administrador realizado com sucesso!", "success")
        return redirect(url_for("index"))
    else:
        flash("Token de administrador inválido.", "error")
        return redirect(url_for("admin_login_page"))


@app.route("/admin/logout")
def admin_logout():
    """Remove o status de administrador da sessão."""
    session.pop("is_admin", None)
    flash("Logout realizado com sucesso.", "info")
    return redirect(url_for("index"))


# --- INICIALIZAÇÃO DA APLICAÇÃO ---

if __name__ == "__main__":
    # Executa em modo debug apenas se a variável de ambiente FLASK_DEBUG for 'True'
    is_debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    app.run(debug=is_debug_mode)
